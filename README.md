# Reddit Activity and Dubai Real Estate Registrations

[![Reproduce analysis](https://github.com/aaronab810/dld_reddit/actions/workflows/reproduce.yml/badge.svg)](https://github.com/aaronab810/dld_reddit/actions/workflows/reproduce.yml)

### An Exploratory Weekly Association Study

**Muath Alrammal · Milan Dordevic · Nourchène Elleuch Ben Ayed · Aaron Saji Abraham · Prajwal Kokatnur · Keletso J. Letsholo · Sana Amir · Hazem Gouda**

[Study](#the-study) · [Reproduce](#reproduce-the-analysis) · [Notebooks](#notebooks) · [Data](docs/data.md) · [Methods](docs/methods.md) · [Citation](#citation)

## The study

Do relationships between online housing discussion and property-market activity persist when we account for time trends and examine week-to-week changes?

This study compares **175,090 retained Reddit submissions and comments** from r/dubai and r/DubaiRealEstate with **270,558 Dubai Land Department registrations** across **58 observed weekly bins**, labelled 28 July 2025 to 31 August 2026. We examine activity counts against sales, mortgages and gifts, with additional analyses of off-plan and ready/existing sales.

The analysis combines contemporaneous correlations, adjustment for calendar time, weekly changes, complete lag profiles and a paired stationary bootstrap. Its purpose is to assess how stable the associations are under different analytical choices.

### Main findings

- **Time trends matter.** The r/dubai–sales correlation falls from **0.572** in levels to **0.231** after linear time adjustment.
- **Some same-week change associations persist.** Submissions and sales have a weekly-change correlation of **0.508**. Submissions and r/dubai have positive pointwise bootstrap intervals across the tested block lengths; pooled activity and r/DubaiRealEstate intervals include zero.
- **There is no robust single lead–lag delay.** Lag profiles change across levels, detrended series, weekly changes and temporal support.

![Full lag profiles for four Reddit–DLD sales pairs](docs/assets/lag_profiles.png)

*Positive lag means Reddit precedes DLD. The figure shows the complete −8 to +8 week window, rather than selecting one maximum.*

The findings describe exploratory associations between aggregate platform activity and administrative registrations. Interpretation is at the weekly aggregate level.

## Reproduce the analysis

The public analysis runs from included weekly aggregates. No Reddit account, private text, GPU or DeBERTa download is needed. Use **Python 3.12**.

```sh
git clone https://github.com/aaronab810/dld_reddit.git
cd dld_reddit
python -m venv .venv
```

Activate with `.\.venv\Scripts\Activate.ps1` on Windows PowerShell, or `source .venv/bin/activate` on macOS/Linux. Then:

```sh
python -m pip install -r requirements.txt
python scripts/reproduce.py
```

The command regenerates tables and figures in `outputs/` and verifies **all 21 reference tables**, including bootstrap results and the historical aggregate comparison. It finishes with `Reproduction complete: 21 reference tables verified.` followed by the output path. Generated outputs stay out of Git.

Run the tests with:

```sh
python -m unittest discover -s tests
```

## Notebooks

| Notebook | Role | Inputs and use |
| --- | --- | --- |
| [Analysis](notebooks/analysis.ipynb) | Runs the shared analysis code and displays principal results. | Included aggregates; executed and verified. |
| [DeBERTa extraction](notebooks/deberta_extraction.ipynb) | Scores r/dubai posts and retains comments linked to selected posts. | Authorized private CSVs and model weights; records the configuration and provenance of each run. |

The extraction notebook covers the **r/dubai relevance-filtering stage**. The analysis notebook starts from the published weekly aggregates for both communities. These are distinct entry points, with inputs and scope described in [extraction details](docs/extraction.md).

## Repository structure

```text
data/          Weekly inputs, variable dictionary, historical aggregates and reference tables
docs/          Methods, data provenance, extraction notes and the overview figure
environments/  Optional dependencies for DeBERTa extraction
notebooks/     Analysis and relevance-extraction workflows
scripts/       Reproduction entry point
src/           Shared statistical implementation
tests/         Regression tests
```

Start with [`data/weekly_counts.csv`](data/weekly_counts.csv) and its [variable dictionary](data/variables.csv). The 21 expected tables are bundled in [`data/reference_results.zip`](data/reference_results.zip), keeping generated files out of the main repository view. [Checksums](docs/provenance/checksums.json) identify the published files.

## Reproducibility and interpretation

- **Verified:** aggregate analyses, the 21 reference tables and statistical tests.
- **Extraction workflow:** the DeBERTa notebook records the exact model revision, inference settings, dependency versions and input hashes for each run.
- **Historical comparison:** four earlier coefficients are computationally reproduced from archived aggregates. The later DLD extract has different counts for overlapping weeks, so the comparison retains the original aggregate inputs.
- **Interpretation:** the primary analysis uses 58 observed bins, with a 56-bin sensitivity excluding both edges. Bootstrap intervals are exploratory and pointwise, conditional on approximate stationarity and weak dependence. The unit of inference is the weekly aggregate.

Raw Reddit text, usernames, private annotations and credentials are not distributed. SMDIS and sentiment analysis are outside this study. See [data and reproducibility scope](docs/data.md).

## Citation

Use GitHub's **Cite this repository** entry or [`CITATION.cff`](CITATION.cff) to reference the software and aggregate reproduction materials, and record the commit used.

Rights remain with the respective authors and data owners.
