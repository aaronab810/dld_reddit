"""Reproducible checks requested by the professor; aggregate-only outputs."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from analysis_core import regular_weekly, coefficient, lag_profile, peak_summary, REDDIT_VARS

DICTIONARY = [
    ('reddit_total','Reddit total activity','All retained posts + comments in both subreddits','Primary'),
    ('reddit_posts','Reddit posts','Retained top-level submissions (post_type = reddit_post)','Primary'),
    ('reddit_comments','Reddit comments','Retained comments (post_type = reddit_comment)','Secondary'),
    ('reddit_dubai','r/dubai activity','All retained posts + comments in r/dubai','Primary'),
    ('reddit_dubairealestate','r/DubaiRealEstate activity','All retained posts + comments in r/dubairealestate; case normalized','Primary'),
    ('dld_total','Total DLD transactions','Unique transaction IDs across Sales, Mortgages and Gifts','Primary'),
    ('dld_sales','DLD sales','Unique transaction IDs with trans_group_en = Sales','Primary'),
    ('dld_mortgages','DLD mortgages','Unique transaction IDs with trans_group_en = Mortgages','Primary'),
    ('dld_gifts','DLD gifts','Unique transaction IDs with trans_group_en = Gifts','Primary'),
    ('dld_offplan_sales','Off-plan sales','Sales AND reg_type_en = Off-Plan Properties (reg_type_id = 0)','Secondary'),
    ('dld_ready_sales','Ready/existing sales','Sales AND reg_type_en = Existing Properties (reg_type_id = 1)','Secondary'),
]
FULL_REDDIT = [row[0] for row in DICTIONARY[:5]]
FULL_DLD = [row[0] for row in DICTIONARY[5:]]
LABELS = {row[0]:row[1] for row in DICTIONARY}


def augment_weekly(weekly, dld):
    d = dld.copy()
    if d.transaction_id.isna().any() or d.transaction_id.duplicated().any():
        raise ValueError('DLD transaction IDs must be unique and nonmissing')
    d['instance_date'] = pd.to_datetime(d.instance_date, format='%Y-%m-%d', errors='raise')
    sales = d.trans_group_en.eq('Sales')
    mapping = {'Off-Plan Properties':0, 'Existing Properties':1}
    if not d.loc[sales,'reg_type_en'].isin(mapping).all():
        raise ValueError('Unmapped sales registration category; do not silently classify as ready')
    if not (d.loc[sales,'reg_type_en'].map(mapping).to_numpy() == pd.to_numeric(d.loc[sales,'reg_type_id']).to_numpy()).all():
        raise ValueError('Sales registration labels and IDs disagree')
    d['week'] = d.instance_date.dt.to_period('W-SUN').dt.start_time
    d['dld_offplan_sales'] = (sales & d.reg_type_en.eq('Off-Plan Properties')).astype(int)
    d['dld_ready_sales'] = (sales & d.reg_type_en.eq('Existing Properties')).astype(int)
    seg = d.groupby('week')[['dld_offplan_sales','dld_ready_sales']].sum()
    f = regular_weekly(weekly).merge(seg,on='week',how='left',validate='one_to_one')
    valid = f.dld_sales.notna()
    if not (f.loc[valid,'dld_sales'] == f.loc[valid,['dld_offplan_sales','dld_ready_sales']].sum(axis=1)).all():
        raise ValueError('Off-plan + ready does not reconcile to sales')
    if not (f.loc[f.reddit_total.notna(),'reddit_total'] == (f.reddit_posts + f.reddit_comments).loc[f.reddit_total.notna()]).all():
        raise ValueError('Posts + comments does not reconcile to Reddit total')
    return f


def peak_shape(profile, window=8):
    info = peak_summary(profile,window)
    p = profile.loc[profile.lag_weeks.abs().le(window)].set_index('lag_weeks')
    if info['status']=='undefined' or info['boundary']:
        info['weaker_on_both_adjacent_lags'] = False
    else:
        winners = [int(k) for k in info['peak_lags'].split(',')]
        info['weaker_on_both_adjacent_lags'] = len(winners)==1 and all(
            abs(p.loc[winners[0]+j,'correlation']) < info['max_abs_r']-1e-10 for j in [-1,1])
    return info


def run_professor_checks(weekly, dld, output_dir):
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    f=regular_weekly(weekly) if dld is None else augment_weekly(weekly,dld)
    dictionary=pd.DataFrame(DICTIONARY,columns=['variable','label','definition','role'])
    dictionary['aggregation']='Weekly count; Monday–Sunday, Dubai local time'
    dictionary.to_csv(out/'variable_dictionary.csv',index=False)
    f.to_csv(out/'weekly_all_variables.csv',index=False)
    f[['week']].join(f[FULL_REDDIT+FULL_DLD].diff()).to_csv(out/'weekly_changes.csv',index=False)
    rows=[]
    for x in FULL_REDDIT:
        for y in FULL_DLD:
            row=dict(reddit=x,dld=y)
            for transform in ['levels','differences']:
                a,b=(f[x],f[y]) if transform=='levels' else (f[x].diff(),f[y].diff())
                for method in ['pearson','spearman']:
                    r,_,n,_=coefficient(a,b,method)
                    row[f'{transform}_{method}']=r;row[f'{transform}_n']=n
            rows.append(row)
    comparison=pd.DataFrame(rows)
    comparison.to_csv(out/'levels_vs_changes_all_30_pairs.csv',index=False)
    profiles=pd.concat([lag_profile(f,x,y,max_lag=8,transform=tr)
        for x in FULL_REDDIT for y in FULL_DLD for tr in ['levels','detrended','differences']],ignore_index=True)
    # Preserve every one of the 17 values, including undefined values, with pair counts.
    profiles.to_csv(out/'lag_profiles_minus8_plus8_all_30_pairs.csv',index=False)
    peaks=[]
    for key,g in profiles.groupby(['reddit','dld','transform'],sort=False):
        peaks.append(dict(zip(['reddit','dld','transform'],key))|peak_shape(g))
    pd.DataFrame(peaks).to_csv(out/'lag_shape_checks.csv',index=False)
    colors={'levels':'#64748b','detrended':'#007e87','differences':'#c36a19'}
    for x in REDDIT_VARS:
        fig,axes=plt.subplots(2,1,figsize=(7,4.6),sharex=True,layout='constrained')
        for ax,change in zip(axes,[False,True]):
            for col,color in [(x,'#007e87'),('dld_sales','#c36a19')]:
                values=f[col].diff() if change else f[col]
                z=(values-values.mean())/values.std(ddof=1)
                ax.plot(f.week,z,label=LABELS[col],color=color,lw=1.1)
            ax.axhline(0,color='#bbb',lw=.5);ax.set_ylabel('Standardized change' if change else 'Standardized count',fontsize=9)
            ax.tick_params(labelsize=8)
        axes[0].legend(fontsize=8,ncol=2);axes[0].set_title(LABELS[x]+' and DLD sales',fontsize=10)
        for ext in ['png','pdf']:fig.savefig(out/f'weekly_pair_{x}.{ext}',dpi=180)
        plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(7,5),sharex=True,sharey=True,layout='constrained')
    for x,ax in zip(REDDIT_VARS,axes.flat):
        for tr,color in colors.items():
            p=profiles.loc[profiles.reddit.eq(x)&profiles.dld.eq('dld_sales')&profiles['transform'].eq(tr)]
            ax.plot(p.lag_weeks,p.correlation,label=tr,color=color,lw=1.2,marker='.',ms=3)
        ax.set_title(LABELS[x]+' vs sales',fontsize=9);ax.set_xlim(-8,8);ax.set_ylim(-1,1)
        ax.set_xticks([-8,-4,0,4,8]);ax.axhline(0,color='#bbb',lw=.5);ax.axvline(0,color='#bbb',lw=.5)
        ax.tick_params(labelsize=8);ax.set_xlabel('Lag (weeks)',fontsize=9);ax.set_ylabel('Pearson r',fontsize=9)
    axes[0,0].legend(fontsize=7)
    for ext in ['png','pdf']:fig.savefig(out/f'lag_profiles_minus8_plus8.{ext}',dpi=180)
    plt.close(fig)
    # Common measurement across time; this is not a replication of topic-share findings.
    window=f.week.between('2026-01-05','2026-04-20')
    period_rows=[]
    for label,mask in [('extended_58',np.ones(len(f),bool)),('earlier_16_window',window),('outside_earlier_window',~window)]:
        t=np.arange(1,len(f)+1,dtype=float)
        for x in REDDIT_VARS:
            a,b=f[x].where(mask),f.dld_sales.where(mask)
            r,_,n,_=coefficient(a,b);partial,_,_,_=coefficient(a,b,control=t)
            dr,_,dn,_=coefficient(a.diff(),b.diff())
            period_rows.append(dict(period=label,reddit=x,dld='dld_sales',n=n,pearson=r,partial_pearson=partial,change_n=dn,change_pearson=dr))
    periods=pd.DataFrame(period_rows);periods.to_csv(out/'activity_period_comparison.csv',index=False)
    audit={'lag_convention':'corr(R[t], D[t+k]); positive k = Reddit precedes DLD',
           'control':'One deterministic weekly index t, intercept included; no same-week or lagged market covariates',
           'primary_pairs':16,'all_defined_pairs_for_change_and_lag_checks':30,'lag_values_per_profile':17,
           'offplan_sales':int(f.dld_offplan_sales.sum()),'ready_sales':int(f.dld_ready_sales.sum()),
           'earlier_window':'Monday labels 2026-01-05 to 2026-04-20 (ending Sunday 2026-04-26)',
           'comparison_limit':'Activity counts are not the earlier topic shares; no direct semantic replication claimed'}
    (out/'checks_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    return f,comparison,periods


def reproduce_earlier(earlier_domains, earlier_dld, saved_associations, extended_weekly, out):
    out=Path(out)
    rows=[]
    for _,row in saved_associations.loc[saved_associations.platform.eq('reddit')].iterrows():
        series=earlier_domains.loc[earlier_domains.platform.eq('reddit')&earlier_domains.domain_id.eq(row.domain_id),['week','share_all']]
        pair=series.merge(earlier_dld[['week',row.outcome]],on='week',validate='one_to_one').sort_values('week')
        r,_,n,_=coefficient(pair.share_all,pair[row.outcome]);dr,_,dn,_=coefficient(pair.share_all.diff(),pair[row.outcome].diff())
        if not np.isclose(r,row.pearson_r,atol=1e-10) or not np.isclose(dr,row.difference_r,atol=1e-10):
            raise ValueError('Earlier published coefficients do not reproduce from saved aggregates')
        rows.append(dict(domain_id=row.domain_id,outcome=row.outcome,n=n,pearson=r,change_n=dn,change_pearson=dr,
                         extended_replication='Not estimable: extended topic shares unavailable'))
    pd.DataFrame(rows).to_csv(out/'earlier_findings_reproduced.csv',index=False)
    old=earlier_dld.copy();old['week']=pd.to_datetime(old.week)
    checks=extended_weekly.merge(old,on='week',validate='one_to_one')
    for new,previous in [('dld_sales','sales_registrations'),('dld_offplan_sales','offplan_count'),('dld_ready_sales','ready_count')]:
        checks[new+'_minus_prior']=checks[new]-checks[previous]
    checks.to_csv(out/'earlier_dld_count_reconciliation.csv',index=False)


if __name__=='__main__':
    weekly=pd.read_csv('results/observed_58_weeks/weekly_aggregates.csv',parse_dates=['week'])
    dld=pd.read_csv('data/DLD_transactions_1year.csv',usecols=['transaction_id','instance_date','trans_group_en','reg_type_en','reg_type_id'],dtype={'transaction_id':'string'})
    out=Path('results/professor_checks')
    f,comparison,periods=run_professor_checks(weekly,dld,out)
    reproduce_earlier(pd.read_csv('reference/earlier_domain_weekly.csv'),pd.read_csv('reference/earlier_dld_weekly.csv'),pd.read_csv('reference/earlier_primary_contemporaneous.csv'),f,out)
    print(comparison.loc[comparison.reddit.isin(REDDIT_VARS)&comparison.dld.eq('dld_sales')].to_string(index=False))
    print(periods.to_string(index=False))
