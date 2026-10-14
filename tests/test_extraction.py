import unittest
import pandas as pd
from src.dld_reddit.extraction import score_texts, select_records, validate_inputs


class ExtractionTests(unittest.TestCase):
    def fixture(self):
        posts = pd.DataFrame({'post_id':['a','b','c'], 'post_text':['one','two','three'],
                              'deberta_score':[0.4,0.40001,0.9]})
        comments = pd.DataFrame({'comment_id':['x','y','z'], 'post_id':['a','b','absent']})
        return posts, comments

    def test_strict_threshold_and_parent_membership(self):
        posts, comments = self.fixture()
        selected, kept, joined = select_records(posts, comments)
        self.assertEqual(selected.post_id.tolist(), ['b','c'])
        self.assertEqual(kept.comment_id.tolist(), ['y'])
        self.assertEqual(joined.post_id.tolist(), ['b'])

    def test_truncation_and_label_order(self):
        seen=[]
        def classifier(text, **kwargs):
            seen.append((text,kwargs))
            return {'labels':['not real estate','real estate'], 'scores':[0.2,0.8]}
        self.assertEqual(score_texts(['x'*1100],classifier), [0.8])
        self.assertEqual(len(seen[0][0]),1024)
        self.assertEqual(seen[0][1]['hypothesis_template'],'This example is {}.')
        self.assertFalse(seen[0][1]['multi_label'])

    def test_duplicate_ids_and_empty_text_fail_before_inference(self):
        posts,comments=self.fixture()
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            validate_inputs(pd.concat([posts,posts.iloc[:1]]),comments)
        posts.loc[0,'post_text']=' '
        with self.assertRaisesRegex(ValueError,'Blank post_text'):
            validate_inputs(posts,comments)


if __name__ == '__main__':
    unittest.main()
