"""DLD--Reddit weekly analysis. Positive k means corr(Reddit[t], DLD[t+k]).

All analytical p-values assume independent observations. They are diagnostics,
not time-series-valid evidence. No causal or forecasting interpretation is made.
"""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
from scipy import stats

REDDIT_VARS = ['reddit_total', 'reddit_posts', 'reddit_dubai', 'reddit_dubairealestate']
DLD_VARS = ['dld_total', 'dld_sales', 'dld_mortgages', 'dld_gifts']
ALL_VARS = REDDIT_VARS + DLD_VARS


def regular_weekly(frame):
    """Restore missing calendar weeks; NEVER compress time or infer zero counts."""
    f = frame.copy()
    f['week'] = pd.to_datetime(f['week'], errors='raise')
    if f.empty or f['week'].isna().any() or f['week'].duplicated().any():
        raise ValueError('Weekly dates must be nonmissing, nonempty and unique.')
    if (f['week'].dt.dayofweek != 0).any():
        raise ValueError('Weeks must be Monday labels.')
    f = f.sort_values('week').set_index('week')
    f = f.reindex(pd.date_range(f.index.min(), f.index.max(), freq='W-MON'))
    f.index.name = 'week'
    return f.reset_index()


def bh_adjust(p):
    p = np.asarray(p, dtype=float)
    out = np.full(p.shape, np.nan)
    valid = np.flatnonzero(np.isfinite(p))
    order = valid[np.argsort(p[valid])]
    if len(order):
        adjusted = p[order] * len(order) / np.arange(1, len(order)+1)
        out[order] = np.clip(np.minimum.accumulate(adjusted[::-1])[::-1], 0, 1)
    return out


def usable(a):
    a = np.asarray(a, float)
    return len(a) > 1 and np.linalg.norm(a-a.mean()) > 1e-12 * max(1., np.linalg.norm(a))


def coefficient(x, y, method='pearson', control=None):
    x, y = np.asarray(x, float), np.asarray(y, float)
    mask = np.isfinite(x) & np.isfinite(y)
    if control is not None:
        control = np.asarray(control, float)
        mask &= np.isfinite(control)
    x, y = x[mask], y[mask]
    n = len(x)
    df = n-2
    if n < 4:
        return np.nan, np.nan, n, df
    if control is not None:
        z = control[mask]
        if method == 'spearman':
            x, y, z = stats.rankdata(x), stats.rankdata(y), stats.rankdata(z)
        design = np.column_stack([np.ones(n), z])
        rank = np.linalg.matrix_rank(design)
        x = x - design @ np.linalg.lstsq(design, x, rcond=None)[0]
        y = y - design @ np.linalg.lstsq(design, y, rcond=None)[0]
        df = n-rank-1  # n-3 for one nonconstant control, NOT n-2
        if not usable(x) or not usable(y) or df <= 0:
            return np.nan, np.nan, n, df
        r = float(np.clip(np.corrcoef(x, y)[0, 1], -1, 1))
        p = 0. if abs(r) >= 1 else float(2*stats.t.sf(abs(r)*np.sqrt(df/(1-r*r)), df))
        return r, p, n, df
    if not usable(x) or not usable(y):
        return np.nan, np.nan, n, df
    fn = {'pearson': stats.pearsonr, 'spearman': stats.spearmanr, 'kendall': stats.kendalltau}[method]
    r, p = fn(x, y)
    return float(r), float(p), n, df


def same_week(frame):
    f = regular_weekly(frame)
    t = np.arange(1, len(f)+1, dtype=float)
    rows = []
    for x in REDDIT_VARS:
        for y in DLD_VARS:
            for method, partial in [('pearson',False), ('spearman',False), ('kendall',False), ('pearson',True), ('spearman',True)]:
                r, p, n, df = coefficient(f[x], f[y], method, t if partial else None)
                rows.append(dict(reddit=x, dld=y, method=('partial_' if partial else '')+method,
                                 correlation=r, p_iid=p, n=n, degrees_freedom=df))
    out = pd.DataFrame(rows)
    out['q_iid_bh_all_80'] = bh_adjust(out.p_iid)
    return out


def lag_profile(frame, x, y, max_lag=16, transform='levels', fixed_support=False, min_n=20):
    """Overlap-specific Pearson; detrending refitted on each lag's paired weeks.

    Missingness is removed AFTER calendar shifting. Fixed support holds the
    Reddit anchor weeks constant across the entire +/-max_lag window.
    """
    f = regular_weekly(frame)
    if transform not in ('levels', 'detrended', 'differences'):
        raise ValueError('Unknown transform')
    if max_lag < 0 or max_lag >= len(f):
        raise ValueError('Invalid lag window')
    xv, yv = f[x].astype(float), f[y].astype(float)
    if transform == 'differences':
        xv, yv = xv.diff(), yv.diff()
    t = np.arange(1, len(f)+1, dtype=float)
    anchor = np.ones(len(f), dtype=bool)
    if fixed_support:
        anchor[:] = False
        anchor[max_lag:len(f)-max_lag] = True
        anchor &= np.isfinite(xv)
        for k in range(-max_lag, max_lag+1):
            anchor &= np.isfinite(yv.shift(-k))
    rows = []
    for k in range(-max_lag, max_lag+1):
        shifted = yv.shift(-k)  # Reddit[t] paired with DLD[t+k]
        mask = anchor & np.isfinite(xv) & np.isfinite(shifted)
        r, p, n, df = coefficient(xv[mask], shifted[mask], control=t[mask] if transform == 'detrended' else None)
        if n < min_n:
            r, p = np.nan, np.nan
        rows.append(dict(reddit=x, dld=y, transform=transform, fixed_support=fixed_support,
                         lag_weeks=k, correlation=r, p_iid=p, n=n, degrees_freedom=df))
    return pd.DataFrame(rows)


def all_lags(frame, max_lag=16, fixed_support=False):
    out = pd.concat([lag_profile(frame,x,y,max_lag,tr,fixed_support)
                     for tr in ('levels','detrended','differences')
                     for x in REDDIT_VARS for y in DLD_VARS], ignore_index=True)
    out['q_iid_bh_all_1584'] = bh_adjust(out.p_iid)
    return out


def peak_summary(profile, window):
    p = profile.loc[profile.lag_weeks.abs() <= window].copy()
    p = p.loc[np.isfinite(p.correlation)]
    if p.empty:
        return dict(window=window, peak_lags='', max_abs_r=np.nan, boundary=False, status='undefined')
    magnitude = p.correlation.abs().max()
    winners = p.loc[np.isclose(p.correlation.abs(), magnitude, rtol=1e-8, atol=1e-10)]
    lags = winners.lag_weeks.astype(int).tolist()
    boundary = any(abs(k) == window for k in lags)
    return dict(window=window, peak_lags=','.join(map(str,lags)), max_abs_r=float(magnitude),
                boundary=boundary, status='boundary maximum' if boundary else 'interior maximum (descriptive)')


def boundary_comparison(profiles):
    rows = []
    for key, group in profiles.groupby(['reddit','dld','transform','fixed_support'], sort=False):
        a, b = peak_summary(group,8), peak_summary(group,16)
        row = dict(zip(['reddit','dld','transform','fixed_support'],key))
        row.update({k+'_8':v for k,v in a.items()})
        row.update({k+'_16':v for k,v in b.items()})
        rows.append(row)
    return pd.DataFrame(rows)


def _unique(frame, keys, audit, label):
    if frame[keys].isna().any().any() or frame[keys].astype(str).apply(lambda s: s.str.strip().eq('')).any().any():
        raise ValueError(label+': missing identity; resolve before counting')
    before = len(frame)
    frame = frame.drop_duplicates()
    audit[label+'_exact_duplicate_rows_removed'] = before-len(frame)
    if frame.duplicated(keys).any():
        raise ValueError(label+': conflicting repeated identifiers; review source records')
    return frame.copy()


def aggregate_inputs(reddit, dld):
    """The supplied eligible corpus is an upstream input, not reclassified here."""
    audit = dict(reddit_input_rows=len(reddit), dld_input_rows=len(dld))
    r = _unique(reddit, ['post_type','id'], audit, 'reddit')
    d = _unique(dld, ['transaction_id'], audit, 'dld')
    if 'platform' in r and not r.platform.eq('reddit').all():
        raise ValueError('Input contains non-Reddit platforms')
    if 'eligible' in r and not r.eligible.eq(True).all():
        raise ValueError('Use the eligible corpus, not all_flags')
    r['timestamp_utc'] = pd.to_datetime(r.timestamp_utc, utc=True, errors='raise')
    d['instance_date'] = pd.to_datetime(d.instance_date, format='%Y-%m-%d', errors='raise')
    if r.timestamp_utc.isna().any() or d.instance_date.isna().any():
        raise ValueError('Missing dates must be resolved before aggregation')
    r['subreddit'] = r.subreddit.astype(str).str.lower().str.strip().str.removeprefix('r/')
    if not r.subreddit.isin(['dubai','dubairealestate']).all():
        raise ValueError('Unexpected subreddit')
    if not r.post_type.isin(['reddit_post','reddit_comment']).all():
        raise ValueError('Unexpected record type')
    if not d.trans_group_en.isin(['Sales','Mortgages','Gifts']).all():
        raise ValueError('Unexpected DLD transaction group; inspect before changing denominator')
    r['week'] = r.timestamp_utc.dt.tz_convert('Asia/Dubai').dt.tz_localize(None).dt.to_period('W-SUN').dt.start_time
    d['week'] = d.instance_date.dt.to_period('W-SUN').dt.start_time
    r['reddit_posts'] = r.post_type.eq('reddit_post').astype(int)
    r['reddit_comments'] = r.post_type.eq('reddit_comment').astype(int)
    r['reddit_dubai'] = r.subreddit.eq('dubai').astype(int)
    r['reddit_dubairealestate'] = r.subreddit.eq('dubairealestate').astype(int)
    for col, label in [('dld_sales','Sales'),('dld_mortgages','Mortgages'),('dld_gifts','Gifts')]:
        d[col] = d.trans_group_en.eq(label).astype(int)
    rw = r.groupby('week').agg(reddit_total=('id','size'),reddit_posts=('reddit_posts','sum'),
                              reddit_comments=('reddit_comments','sum'),reddit_dubai=('reddit_dubai','sum'),
                              reddit_dubairealestate=('reddit_dubairealestate','sum'))
    dw = d.groupby('week').agg(dld_total=('transaction_id','size'),dld_sales=('dld_sales','sum'),
                              dld_mortgages=('dld_mortgages','sum'),dld_gifts=('dld_gifts','sum'))
    start, end = max(rw.index.min(),dw.index.min()), min(rw.index.max(),dw.index.max())
    weekly = regular_weekly(rw.join(dw,how='outer').loc[start:end].reset_index())
    # Retain missing weeks as NaN. Zero filling requires independent capture evidence.
    assert (rw.reddit_total == rw.reddit_posts+rw.reddit_comments).all()
    assert (rw.reddit_total == rw.reddit_dubai+rw.reddit_dubairealestate).all()
    assert (dw.dld_total == dw[DLD_VARS[1:]].sum(axis=1)).all()
    audit.update(reddit_min_utc=str(r.timestamp_utc.min()), reddit_max_utc=str(r.timestamp_utc.max()),
                 dld_min_date=str(d.instance_date.min()),dld_max_date=str(d.instance_date.max()),
                 common_week_labels=len(weekly),first_week=str(start.date()),last_week=str(end.date()))
    return weekly, audit


def coverage_mask(weekly, reddit_start_utc, reddit_end_utc, dld_start_local, dld_end_exclusive_local):
    """Conservative full-week eligibility given declared extraction bounds.

    Observed max transaction date alone does not establish an extraction bound.
    Record the source/assumption for every bound alongside the results.
    """
    rs = pd.Timestamp(reddit_start_utc).tz_convert('Asia/Dubai').tz_localize(None)
    re = pd.Timestamp(reddit_end_utc).tz_convert('Asia/Dubai').tz_localize(None)
    ds, de = pd.Timestamp(dld_start_local), pd.Timestamp(dld_end_exclusive_local)
    w = pd.to_datetime(weekly.week)
    return (w >= max(rs,ds)) & (w+pd.Timedelta(days=7) <= min(re,de))


def file_hash(path):
    h = hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def run_analysis(weekly, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    weekly = regular_weekly(weekly)
    weekly.to_csv(output_dir/'weekly_aggregates.csv',index=False)
    same = same_week(weekly)
    ccf = all_lags(weekly)
    fixed = all_lags(weekly,fixed_support=True)
    boundary = boundary_comparison(pd.concat([ccf,fixed],ignore_index=True))
    same.to_csv(output_dir/'same_week.csv',index=False)
    ccf.to_csv(output_dir/'lag_profiles.csv',index=False)
    fixed.to_csv(output_dir/'lag_profiles_fixed_support.csv',index=False)
    boundary.to_csv(output_dir/'boundary_comparison.csv',index=False)
    return same, ccf, fixed, boundary
