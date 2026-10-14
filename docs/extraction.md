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

Use a separate environment and install `environments/extraction.txt`. A compatible PyTorch installation is needed. A GPU is recommended, with CPU fallback in the notebook. Transformers, SentencePiece and Hugging Face Hub versions come from the supplied notebook's saved installation output; each new run records its installed dependency versions.

Configure posts (`post_id`, `post_text`), comments (`comment_id`, `post_id`) and an optional **development** label CSV (`post_text`, binary `actual_label`). Metadata columns are preserved. IDs must be nonmissing and unique; blank text fails before model loading. Outputs are written under ignored `private/extraction_outputs/`, and no raw rows are displayed.

## Run provenance and evaluation scope

`MODEL_REVISION = "main"` resolves a current revision, records it and uses that exact SHA for loading. Replace `main` with the recorded SHA to repeat that run. Each completed run records model revision, settings, dependency versions and input hashes. These provenance records identify the configuration of the specific extraction run.

Optional evaluation reports **development-sample diagnostics** for threshold selection. Use development labels for this step and keep any independent evaluation sample separate. Syntax checks and synthetic-fixture tests cover the notebook and filtering logic.

This component produces scored r/dubai submissions and linked comments. The downstream statistical analysis uses the separately supplied weekly aggregates for both communities.
