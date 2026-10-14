# Methods and interpretation

## Weekly measurements

The analysis uses 58 observed Monday–Sunday bins in Asia/Dubai, labelled **28 July 2025 to 31 August 2026**. A sensitivity analysis excludes the first and last bins, leaving 56 interior bins.

The primary analysis combines four Reddit counts with four DLD counts. The complete dictionary covers eleven variables; adding Reddit comments and the sales subdivisions gives 30 Reddit–DLD pairs. All measurements are activity or registration counts, rather than sentiment or speculative intent.

## Correlations and lag direction

Same-week analyses include Pearson, Spearman and Kendall correlations. Partial Pearson correlation controls for the weekly calendar index. Rank-based partial correlation uses ranked variables and ranked calendar time. Calendar time is the sole control.

The lag convention is:

```text
r(k) = corr(Reddit[t], DLD[t + k])
```

Positive `k` means Reddit precedes DLD by `k` weeks. Negative `k` means DLD precedes Reddit. The calendar is aligned before shifting; missing weeks are never compressed into adjacent observations.

Full −8 to +8 profiles are retained, with exploratory −16 to +16 and fixed-support checks. Levels, detrended series and weekly changes are compared. An extremum at the boundary does not establish a true peak. The analysis does not identify a robust single lead–lag delay across these choices.

## Time-series dependence

The paired stationary bootstrap estimates pointwise 95% percentile intervals for same-week Pearson correlations of first weekly differences. It covers the four primary Reddit measures against DLD sales, using both the 58-bin and 56-bin supports.

- Replicates: **10,000** per configuration.
- Expected block lengths: **2, 4 and 8** weeks.
- Base seed: **20261012**; the exact derivation is recorded in the implementation.
- Paired series share the same resampling indices; changes are calculated before resampling.

These exploratory, pointwise percentile intervals require approximately stationary, weakly dependent changes. The bootstrap targets uncertainty in same-week change correlations. Conventional correlation p-values and multiplicity adjustments are retained as diagnostics; the paired bootstrap supplies the dependence-aware sensitivity.

The full specification is in [`provenance/analysis_specification.json`](provenance/analysis_specification.json). A rerun writes bootstrap outputs to `outputs/bootstrap/`.

## Reproduction and provenance

`scripts/reproduce.py` compares every saved CSV result with its regenerated counterpart, with numerical tolerance up to `1e-10`. The historical comparison computationally reproduces coefficients from the archived weekly inputs in `data/historical/`.

Provenance manifests retain source checksums. Local workstation and Drive directory prefixes are omitted from the standalone manifests. All empirical aggregates are observed data; synthetic arrays are used only in tests.

The extraction notebook documents the model identifier and inference settings and records the resolved weight revision for each run. The study measures activity counts; relevance-filter performance is described using the development sample used for threshold selection.
