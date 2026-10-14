import unittest
import pandas as pd
from src.dld_reddit.sensitivity import augment_weekly, peak_shape


class SensitivityTests(unittest.TestCase):
    def fixture(self):
        w=pd.DataFrame({'week':['2026-01-05'],'reddit_total':[3],'reddit_posts':[1],'reddit_comments':[2],'dld_sales':[2]})
        d=pd.DataFrame({'transaction_id':['a','b','c'],'instance_date':['2026-01-06']*3,
                        'trans_group_en':['Sales','Sales','Mortgages'],
                        'reg_type_en':['Off-Plan Properties','Existing Properties','Off-Plan Properties'],
                        'reg_type_id':[0,1,0]})
        return w,d

    def test_segments_exclude_mortgages(self):
        w,d=self.fixture();f=augment_weekly(w,d)
        self.assertEqual(f.dld_offplan_sales.iloc[0],1)
        self.assertEqual(f.dld_ready_sales.iloc[0],1)

    def test_unmapped_sales_not_ready(self):
        w,d=self.fixture();d.loc[0,'reg_type_en']='Unknown'
        with self.assertRaises(ValueError):augment_weekly(w,d)

    def test_disagreeing_registration_id_rejected(self):
        w,d=self.fixture();d.loc[0,'reg_type_id']=1
        with self.assertRaises(ValueError):augment_weekly(w,d)

    def test_peak_requires_weaker_neighbors_and_rejects_boundary(self):
        p=pd.DataFrame({'lag_weeks':[-2,-1,0,1,2],'correlation':[.1,.3,.7,.4,.2]})
        self.assertTrue(peak_shape(p,2)['weaker_on_both_adjacent_lags'])
        p.loc[4,'correlation']=.8
        self.assertTrue(peak_shape(p,2)['boundary'])
        self.assertFalse(peak_shape(p,2)['weaker_on_both_adjacent_lags'])


if __name__=='__main__':unittest.main()
