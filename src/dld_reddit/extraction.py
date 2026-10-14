"""Input checks and filtering for the optional r/dubai extraction notebook."""
import numpy as np
import pandas as pd

LABELS = ['real estate', 'not real estate']
HYPOTHESIS = 'This example is {}.'


def validate_inputs(posts, comments):
    for frame, columns, identity in [(posts, ['post_id', 'post_text'], 'post_id'),
                                      (comments, ['comment_id', 'post_id'], 'comment_id')]:
        missing = set(columns) - set(frame.columns)
        if missing:
            raise ValueError(f'Missing required columns: {sorted(missing)}')
        for column in [c for c in columns if c.endswith('_id')]:
            if frame[column].isna().any() or frame[column].astype(str).str.strip().eq('').any():
                raise ValueError(f'{column} must be nonmissing and nonblank')
        if frame[identity].duplicated().any():
            raise ValueError(f'Duplicate {identity}; resolve upstream before extraction')
    if posts.post_text.fillna('').astype(str).str.strip().eq('').any():
        raise ValueError('Blank post_text; resolve upstream before inference')


def score_texts(texts, classifier):
    """Preserve the source's sequential scoring and 1,024-character truncation."""
    texts = pd.Series(texts).fillna('').astype(str)
    if texts.str.strip().eq('').any():
        raise ValueError('Blank post_text; resolve upstream before inference')
    scores = []
    for text in texts:
        result = classifier(text[:1024], candidate_labels=LABELS,
                            hypothesis_template=HYPOTHESIS, multi_label=False)
        score = float(result['scores'][result['labels'].index('real estate')])
        if not np.isfinite(score) or not 0 <= score <= 1:
            raise ValueError('Invalid relevance score')
        scores.append(score)
    return scores


def select_records(scored_posts, comments, threshold=0.4):
    validate_inputs(scored_posts, comments)
    scores = pd.to_numeric(scored_posts.deberta_score, errors='raise')
    if not scores.between(0, 1).all() or not 0 <= threshold <= 1:
        raise ValueError('Scores and threshold must lie in [0, 1]')
    # Strict comparison is the production rule in the supplied source notebook.
    selected = scored_posts.loc[scores.gt(threshold)].copy()
    retained_comments = comments.loc[comments.post_id.isin(selected.post_id)].copy()
    joined = retained_comments.merge(selected, on='post_id', how='inner',
                                      suffixes=('_comment', '_post'), validate='many_to_one')
    return selected, retained_comments, joined
