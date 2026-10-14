# Data and reproducibility scope

| Location | Contents |
| --- | --- |
| `data/weekly_counts.csv` | 58 weekly rows, Monday labels and eleven Reddit/DLD count variables. |
| `data/variables.csv` | Definitions, aggregation and primary/secondary roles. |
| `data/historical/` | Archived inputs for four earlier coefficients and DLD count reconciliation. |
| `data/reference_results.zip` | 21 expected CSV tables, checked numerically without extracting the archive. |
| `docs/provenance/` | Source metadata and hashes, analysis specification, notebook provenance and file checksums. |

The common weekly input contains 175,090 Reddit records and 270,558 DLD registrations. The corpus manifest describes 175,133 eligible Reddit records overall; 43 fall outside the common overlap. Empirical inputs are observed, not simulated. Synthetic arrays occur only in tests.

Dates use Asia/Dubai, Monday–Sunday weeks. Labels run from 2025-07-28 to 2026-08-31. Coverage sensitivity is assessed by omitting both edge bins in the interior analysis.

## Generated results

```text
outputs/
  primary_58/   Primary correlations and extended lag sensitivities
  interior_56/  Sensitivity excluding both edge bins
  sensitivity/ Weekly changes, full ±8 profiles, plots and historical comparisons
  bootstrap/   Stationary-bootstrap intervals and autocorrelation diagnostics
```

All 21 reference CSVs must match the regenerated tables within tolerance up to `1e-10`; a missing or mismatched result fails the run. Figures are regenerated from the aggregates. The manuscript and supplement remain separate from this code repository.

## Scope

The aggregate workflow reproduces the statistical analysis from the supplied weekly counts. The separate DeBERTa workflow scores r/dubai submissions and retains comments by parent-post membership. Its outputs represent that relevance-filtering stage; the statistical workflow takes the published weekly counts as its inputs.

Original Reddit text, identifiers, source DLD rows and annotation sheets are excluded. Authorized extraction inputs and outputs belong under ignored `private/`. The supplied original notebooks are preserved outside the repository.

The original 500-item relevance assessment informed threshold selection. Its reported metrics describe development-sample performance for scored r/dubai submissions.
