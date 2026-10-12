import unittest
import numpy as np
import pandas as pd
from scipy import stats
from analysis_core import lag_profile, coefficient, peak_summary, bh_adjust, coverage_mask, regular_weekly


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(873)
        self.weeks = pd.date_range('2025-07-28',periods=58,freq='W-MON')

    def test_known_positive_and_negative_lag(self):
        x = self.rng.normal(size=58)
        y = np.r_[self.rng.normal(size=3), x[:-3]]
        f = pd.DataFrame({'week':self.weeks,'x':x,'y':y})
        p = lag_profile(f,'x','y',8)
        self.assertEqual(p.loc[p.correlation.abs().idxmax(),'lag_weeks'],3)
        self.assertAlmostEqual(p.loc[p.lag_weeks.eq(3),'correlation'].iloc[0],1)
        reverse = lag_profile(f,'y','x',8)
        np.testing.assert_allclose(p.correlation,reverse.correlation.iloc[::-1],atol=1e-12)
        self.assertEqual(p.loc[p.lag_weeks.eq(3),'n'].iloc[0],55)

    def test_missing_week_not_compressed(self):
        f = pd.DataFrame({'week':self.weeks,'x':self.rng.normal(size=58),'y':self.rng.normal(size=58)})
        f = f.drop(index=20)
        p = lag_profile(f,'x','y',8)
        self.assertEqual(p.loc[p.lag_weeks.eq(1),'n'].iloc[0],55)
        self.assertEqual(len(regular_weekly(f)),58)

    def test_partial_matches_formula_and_df(self):
        z = np.arange(58.)
        x = z+self.rng.normal(size=58)*10
        y = z+self.rng.normal(size=58)*10
        r,p,n,df = coefficient(x,y,control=z)
        xy,xz,yz = np.corrcoef([x,y,z])[[0,0,1],[1,2,2]]
        expected = (xy-xz*yz)/np.sqrt((1-xz*xz)*(1-yz*yz))
        self.assertAlmostEqual(r,expected)
        self.assertEqual(df,55)
        self.assertAlmostEqual(p,2*stats.t.sf(abs(r)*np.sqrt(55/(1-r*r)),55))

    def test_constant_and_perfect_trend_undefined(self):
        z=np.arange(58.)
        self.assertTrue(np.isnan(coefficient(z,z,control=z)[0]))
        self.assertTrue(np.isnan(coefficient(np.ones(58),z)[0]))

    def test_fixed_support(self):
        f=pd.DataFrame({'week':self.weeks,'x':self.rng.normal(size=58),'y':self.rng.normal(size=58)})
        p=lag_profile(f,'x','y',16,fixed_support=True)
        self.assertEqual(set(p.n),{26})
        self.assertEqual(len(p),33)

    def test_difference_across_gap_is_not_invented(self):
        f=pd.DataFrame({'week':self.weeks,'x':self.rng.normal(size=58),'y':self.rng.normal(size=58)}).drop(index=20)
        p=lag_profile(f,'x','y',8,transform='differences')
        self.assertEqual(p.loc[p.lag_weeks.eq(0),'n'].iloc[0],55)

    def test_ties_and_window_boundaries(self):
        p=pd.DataFrame({'lag_weeks':[-16,-8,0,8,16],'correlation':[.9,.8,.1,-.8,-.9]})
        self.assertEqual(peak_summary(p,8)['peak_lags'],'-8,8')
        self.assertTrue(peak_summary(p,16)['boundary'])

    def test_conservative_coverage(self):
        f=pd.DataFrame({'week':self.weeks})
        mask=coverage_mask(f,'2025-07-28T00:00:00Z','2026-09-07T00:00:00Z','2025-07-28','2026-09-05')
        self.assertEqual(int(mask.sum()),56)
        self.assertFalse(mask.iloc[0])
        self.assertFalse(mask.iloc[-1])

    def test_bh_missing_values(self):
        np.testing.assert_allclose(bh_adjust([.01,.04,np.nan,.03]),[.03,.04,np.nan,.04],equal_nan=True)

    def test_duplicate_weeks_rejected(self):
        with self.assertRaises(ValueError):
            regular_weekly(pd.DataFrame({'week':[self.weeks[0],self.weeks[0]]}))


if __name__ == '__main__':
    unittest.main()
