# DeBERTa relevance extraction

The [extraction notebook](../notebooks/deberta_extraction.ipynb) is a cleaned adaptation of `dubai_deberta_extraction (3).ipynb`. The original is unchanged. Saved Reddit text, exploratory row displays, scratch cells, duplicated model loading and personal Drive paths have been removed.

## Method

The notebook scores **r/dubai submissions**, retains selected posts, and selects comments whose parent `post_id` is retained. Comments are linked by post membership, not individually classified. It also writes a comment/post join for authorized local use.

| Setting | Value |
| --- | --- |
| Model | `MoritzLaurer/deberta-v3-large-zeroshot-v2.0` |
| Task | Zero-shot classification |
| Labels | `real estate`, `not real estate` |
| Input | First 1,024 **characters** of `post_text` |
| Hypothesis | `This example is {}.` — explicitly states the default used implicitly in the source |
| Multi-label | `False` |
| Production selection | `deberta_score > 0.4` |
| Comments | Keep comments whose parent post is selected |

See the [model card](https://huggingface.co/MoritzLaurer/deberta-v3-large-zeroshot-v2.0) and [Transformers pipeline documentation](https://huggingface.co/docs/transformers/main_classes/pipelines#transformers.ZeroShotClassificationPipeline).

The original development threshold sweep used `>=`; production filtering used strict `>`. The cleaned notebook explicitly preserves both. The prior saved-score audit found no score exactly equal to 0.4, so both rules agreed there; this cannot be assumed for future scores. Published aggregate counts are unchanged.

## Running extraction

Use a separate environment and install `environments/extraction.txt`. A compatible PyTorch installation is needed. A GPU is recommended, with CPU fallback in the notebook. Transformers, SentencePiece and Hugging Face Hub versions come from the supplied notebook's saved installation output; the other original versions were not fully pinned.

Configure posts (`post_id`, `post_text`), comments (`comment_id`, `post_id`) and an optional **development** label CSV (`post_text`, binary `actual_label`). Metadata columns are preserved. IDs must be nonmissing and unique; blank text fails before model loading. Outputs are written under ignored `private/extraction_outputs/`, and no raw rows are displayed.

## Provenance and limits

The historical model-weight revision is unknown. `MODEL_REVISION = "main"` resolves a current revision, records it and uses that exact SHA for loading. Replace `main` with the recorded SHA to repeat that new run. This does not recover historical weights or guarantee the original scores. Each completed run records model revision, settings, dependency versions and input hashes.

Optional development evaluation is **not held-out validation**. Do not use the pending held-out sample for threshold selection. The cleaned notebook is syntax-checked and its filtering logic is tested with synthetic fixtures; no new full-corpus inference or human-validation metrics are claimed.

This is one component of corpus construction. It does not recreate r/DubaiRealEstate processing, later eligibility decisions or final corpus assembly. Its outputs are not automatically equivalent to the published aggregates.
