"""Reproduce the paper's aggregate analyses and verify all reference tables."""
from pathlib import Path
from io import BytesIO
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import pandas as pd
from dld_reddit.analysis import run_analysis
from dld_reddit.sensitivity import run_sensitivity_analysis, reproduce_earlier
from dld_reddit.bootstrap import run_bootstrap_analysis


def reproduce(root=ROOT):
    root = Path(root)
    weekly = pd.read_csv(root/'data/weekly_counts.csv', parse_dates=['week'])
    out = root/'outputs'
    primary = weekly.drop(columns=['dld_offplan_sales', 'dld_ready_sales'])
    run_analysis(primary, out/'primary_58')
    run_analysis(primary.iloc[1:-1], out/'interior_56')
    full, _, _ = run_sensitivity_analysis(weekly, None, out/'sensitivity')
    historical = root/'data/historical'
    reproduce_earlier(pd.read_csv(historical/'earlier_domain_weekly.csv'),
                     pd.read_csv(historical/'earlier_dld_weekly.csv'),
                     pd.read_csv(historical/'earlier_primary_contemporaneous.csv'),
                     full, out/'sensitivity')
    run_bootstrap_analysis(weekly, out/'bootstrap')
    verified = 0
    with ZipFile(root/'data/reference_results.zip') as archive:
        expected = archive.namelist()
        if len(expected) != 21 or len(set(expected)) != 21:
            raise ValueError('Expected exactly 21 distinct reference tables')
        for name in expected:
            if not name.endswith('.csv') or '..' in Path(name).parts:
                raise ValueError(f'Unexpected reference entry: {name}')
            pd.testing.assert_frame_equal(
                pd.read_csv(out/name), pd.read_csv(BytesIO(archive.read(name))),
                check_exact=False, check_dtype=False, rtol=1e-10, atol=1e-10)
            verified += 1
    print(f'Reproduction complete: {verified} reference tables verified. Outputs: outputs/')
    return out


if __name__ == '__main__':
    reproduce()
