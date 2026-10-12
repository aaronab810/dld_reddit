import unittest
import numpy as np
import pandas as pd
from dependence_checks import stationary_indices,bootstrap_correlations,run_dependence_checks

class DependenceTests(unittest.TestCase):
    def test_reproducible_circular_blocks(self):
        a=stationary_indices(57,2000,4,42)
        np.testing.assert_array_equal(a,stationary_indices(57,2000,4,42))
        self.assertTrue(((a>=0)&(a<57)).all())
        continuation=(a[:,1:]==(a[:,:-1]+1)%57).mean()
        self.assertTrue(.73<continuation<.79)
    def test_paired_sampling_preserves_perfect_relationship(self):
        x=np.arange(57,dtype=float)
        r=bootstrap_correlations(x,-3*x+10,stationary_indices(57,500,8,7))
        np.testing.assert_allclose(r,-1,atol=1e-12)
    def test_vectorized_matches_individual_correlations(self):
        rng=np.random.default_rng(3);x=rng.normal(size=57);y=rng.normal(size=57)
        idx=stationary_indices(57,50,4,9)
        expected=[np.corrcoef(x[i],y[i])[0,1] for i in idx]
        np.testing.assert_allclose(bootstrap_correlations(x,y,idx),expected,atol=1e-12)
    def test_missing_week_rejected(self):
        f=pd.DataFrame({'week':pd.date_range('2025-07-28',periods=58,freq='7D')})
        for c in ['reddit_total','reddit_posts','reddit_dubai','reddit_dubairealestate','dld_sales']:
            f[c]=np.arange(58)
        with self.assertRaisesRegex(ValueError,'Missing weeks'):
            run_dependence_checks(f.drop(index=20),'unused_missing_week_test_output',20)

if __name__=='__main__': unittest.main()
