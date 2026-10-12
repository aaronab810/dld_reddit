"""Reproduce downstream results without private Reddit text or DLD source rows."""
from pathlib import Path
import pandas as pd
from analysis_core import run_analysis
from professor_checks import run_professor_checks, reproduce_earlier
from dependence_checks import run_dependence_checks

root=Path(__file__).resolve().parent
weekly=pd.read_csv(root/'results/professor_checks/weekly_all_variables.csv',parse_dates=['week'])
out=root/'aggregate_rerun'
primary=weekly.drop(columns=['dld_offplan_sales','dld_ready_sales'])
run_analysis(primary,out/'observed_58_weeks')
run_analysis(primary.iloc[1:-1],out/'conservative_complete_weeks')
f,comparison,periods=run_professor_checks(weekly,None,out/'professor_checks')
reproduce_earlier(pd.read_csv(root/'reference/earlier_domain_weekly.csv'),
                 pd.read_csv(root/'reference/earlier_dld_weekly.csv'),
                 pd.read_csv(root/'reference/earlier_primary_contemporaneous.csv'),
                 f,out/'professor_checks')
expected=pd.read_csv(root/'results/professor_checks/levels_vs_changes_all_30_pairs.csv')
pd.testing.assert_frame_equal(comparison,expected,check_exact=False,rtol=1e-12,atol=1e-12)
bootstrap=run_dependence_checks(weekly,out/'dependence_checks')
expected_bootstrap=pd.read_csv(root/'results/dependence_checks/stationary_bootstrap_changes.csv')
pd.testing.assert_frame_equal(bootstrap,expected_bootstrap,check_exact=False,rtol=1e-10,atol=1e-10)
verified=0
for folder in ['observed_58_weeks','conservative_complete_weeks','professor_checks','dependence_checks']:
    for saved in (root/'results'/folder).glob('*.csv'):
        actual=out/folder/saved.name
        if not actual.is_file(): raise FileNotFoundError(f'Missing reproduced table: {actual}')
        pd.testing.assert_frame_equal(pd.read_csv(actual),pd.read_csv(saved),check_exact=False,
                                      check_dtype=False,rtol=1e-10,atol=1e-10)
        verified+=1
print(f'Downstream results reproduced: {verified} CSV tables verified. Historical checks passed.')
