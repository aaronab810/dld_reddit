"""Exploratory paired stationary-bootstrap intervals for same-week changes.

Configuration chosen for this revision before inspecting bootstrap outputs.
No selected-lag inference, null permutation p-values or causal claims.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from analysis_core import regular_weekly, REDDIT_VARS

CONFIG = dict(seed=20261012, replicates=10000, expected_block_lengths=[2,4,8],
              confidence=.95, estimand='same-week Pearson correlation of first weekly differences',
              pairs=[(x,'dld_sales') for x in REDDIT_VARS],
              selection='Existing four main sales pairs; exploratory, chosen after prior analyses',
              assumptions='Weakly dependent approximately stationary changes; not established by differencing',
              interval='Pointwise percentile; not simultaneous and not a test of zero correlation')


def stationary_indices(n, replicates, block_length, seed):
    if n < 4 or replicates < 1 or not 1 <= block_length <= n:
        raise ValueError('Invalid bootstrap dimensions')
    rng=np.random.default_rng(seed)
    idx=np.empty((replicates,n),dtype=np.int64)
    idx[:,0]=rng.integers(n,size=replicates)
    for t in range(1,n):
        restart=rng.random(replicates) < 1/block_length
        start=rng.integers(n,size=replicates)
        idx[:,t]=np.where(restart,start,(idx[:,t-1]+1)%n)
    return idx


def bootstrap_correlations(x,y,indices):
    x,y=np.asarray(x,float),np.asarray(y,float)
    if x.shape!=y.shape or x.ndim!=1 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Require complete aligned one-dimensional series')
    if np.ptp(x)==0 or np.ptp(y)==0:
        raise ValueError('Correlation undefined for constant series')
    a,b=x[indices],y[indices]
    a=a-a.mean(axis=1,keepdims=True);b=b-b.mean(axis=1,keepdims=True)
    den=np.sqrt(np.sum(a*a,axis=1)*np.sum(b*b,axis=1))
    values=np.divide(np.sum(a*b,axis=1),den,out=np.full(len(indices),np.nan),where=den>0)
    return np.clip(values,-1,1)


def run_dependence_checks(weekly,out_dir,replicates=10000):
    f=regular_weekly(weekly)
    columns=REDDIT_VARS+['dld_sales']
    if f[columns].isna().any().any():
        raise ValueError('Missing weeks: bootstrap must not compress the calendar')
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    rows=[];acf=[]
    for coverage,frame in [('observed_58_weeks',f),('interior_56_weeks',f.iloc[1:-1])]:
        delta=frame[columns].diff().iloc[1:]
        for col in columns:
            for transform,series in [('levels',frame[col]),('differences',delta[col])]:
                for lag in range(1,9):
                    acf.append(dict(coverage=coverage,variable=col,transform=transform,lag=lag,
                                    correlation=series.autocorr(lag),n_pairs=len(series)-lag))
        for length in CONFIG['expected_block_lengths']:
            # Same row indices for every variable preserve contemporaneous dependence.
            idx=stationary_indices(len(delta),replicates,length,CONFIG['seed']+length+len(delta))
            for x in REDDIT_VARS:
                draws=bootstrap_correlations(delta[x],delta.dld_sales,idx)
                finite=draws[np.isfinite(draws)]
                if len(finite)<.99*replicates:
                    raise ValueError('Too many degenerate bootstrap samples')
                lo,hi=np.quantile(finite,[.025,.975],method='linear')
                rows.append(dict(coverage=coverage,reddit=x,dld='dld_sales',n=len(delta),
                    expected_block_length=length,replicates=replicates,valid_replicates=len(finite),
                    correlation=delta[x].corr(delta.dld_sales),ci_low=lo,ci_high=hi))
    result=pd.DataFrame(rows);result.to_csv(out/'stationary_bootstrap_changes.csv',index=False)
    pd.DataFrame(acf).to_csv(out/'autocorrelation_diagnostics.csv',index=False)
    (out/'bootstrap_specification.json').write_text(json.dumps(CONFIG|{'replicates':replicates},indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    root=Path(__file__).resolve().parent
    f=pd.read_csv(root/'results/professor_checks/weekly_all_variables.csv',parse_dates=['week'])
    print(run_dependence_checks(f,root/'results/dependence_checks').round(4).to_string(index=False))
