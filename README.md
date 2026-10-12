# Reddit activity and Dubai real estate registrations

Code and weekly aggregate data for **Reddit Activity and Dubai Real Estate Registrations: An Exploratory Weekly Association Study**.

The study examines associations between Reddit activity and Dubai Land Department (DLD) registration counts across 58 observed weekly bins. It does not establish causal effects, real-estate speculation, or a validated forecasting signal.

## Reproduce the results

Use **Python 3.12**. Clone or download this repository, then run these commands from its root folder:

```sh
git clone https://github.com/aaronab810/dld_reddit.git
cd dld_reddit
python -m venv .venv
```

Activate the environment:

- **Windows PowerShell:** `.\.venv\Scripts\Activate.ps1`
- **macOS / Linux:** `source .venv/bin/activate`

Then install the dependencies and run the analysis:

```sh
python -m pip install -r requirements.txt
python reproduce_from_aggregates.py
```

This regenerates the tables and figures in `aggregate_rerun/` and compares **21 CSV tables** with the saved reference results, including the stationary bootstrap and historical aggregate comparison. A successful run ends with:

```text
Downstream results reproduced: 21 CSV tables verified. Historical checks passed.
```

To run the 18 analysis tests:

```sh
python -m unittest discover -s tests
```

## What is included

| File or folder | Purpose |
| --- | --- |
| [`reproduce_from_aggregates.py`](reproduce_from_aggregates.py) | Main entry point: rerun and check the results. |
| [`analysis_core.py`](analysis_core.py) | Weekly alignment, correlations and lag analysis. |
| [`professor_checks.py`](professor_checks.py) | Variable definitions, weekly changes, sensitivity analyses and historical comparison. |
| [`dependence_checks.py`](dependence_checks.py) | Stationary bootstrap and autocorrelation diagnostics. |
| [`notebooks/analysis.ipynb`](notebooks/analysis.ipynb) | Executed, self-contained notebook with embedded aggregate inputs; suitable for Colab. |
| [`results/`](results/) | Aggregate inputs and expected numerical outputs. |
| [`reference/`](reference/) | Earlier aggregate inputs and source provenance. |
| [`tests/`](tests/) | Checks for lag direction, missing weeks, controls and bootstrap behaviour. |
| [`docs/methods.md`](docs/methods.md) | Analytical choices and interpretation limits. |
| [`SHA256.json`](SHA256.json) | Checksums for the published files. |

The main input is [`weekly_all_variables.csv`](results/professor_checks/weekly_all_variables.csv). The [variable dictionary](results/professor_checks/variable_dictionary.csv) defines its columns. Generated outputs are ignored by Git so rerunning the analysis keeps the checkout clean.

## Scope and limitations

The public workflow reproduces the analysis **from saved aggregates**. It does not rerun data collection, relevance classification or human annotation. Raw Reddit records, private annotation sheets and credentials are not included. Independent held-out annotation remains unfinished; no completed held-out validation is claimed.

The earlier-study comparison reproduces four coefficients from archived aggregates. It is not a direct raw-data replication: the later DLD extract has different counts for overlapping weeks.

The notebook defaults to aggregate mode. Its optional raw-data mode requires the original authorized inputs, configured paths and `requirements-raw.txt`; those inputs are not supplied here. The current revision was verified in aggregate mode. The local raw-data rerun was blocked by an operating-system restriction on PyArrow.

No reuse licence has yet been specified by the authors. Public access alone does not grant a reuse licence.
