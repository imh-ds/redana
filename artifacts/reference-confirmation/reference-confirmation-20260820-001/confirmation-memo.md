# Reference-calibrated confirmation memo

Run ID: `reference-confirmation-20260820-001`
Terminal outcome: **NARROW**

## Immutable calibration provenance

- Calibration records: `artifacts/null-calibration/null-calibration-20260820-001/records.csv`
- SHA-256: `57160bf69892c4047e8a089487d5b894d09243c1a3bcf60164f4daa881369197`
- Practical-null boundary: `0.07078970914915612`
- Reference quantile: `0.95` using `linear` interpolation

## Reference acceptance check

- Complete: `True`; count: `25` below boundary (requires 27 of 30)
- Low p-values: `3` at p <= 0.05 (allows at most 4)

## Frozen execution identity

- Configuration: `{"evaluation_rows": 1000, "fixture_replications": 10, "permutations": 199, "reference_replications": 30, "source_rows": 50000}`
- Seed namespace: `reference-confirmation`
- Source revision: `67415f1dc983630c2735b52cc041485172cf0b0d`

## Fixture-pair classes

| Fixture | Pair | Expected | Observed | Count |
| --- | --- | --- | --- | ---: |
| F1 | target | null-like | null-like | 10 |
| F1 | null-control | null-like | null-like | 10 |
| F2 | target | non-null | non-null | 10 |
| F2 | null-control | null-like | null-like | 10 |
| F3 | target | non-null | non-null | 10 |
| F3 | null-control | null-like | null-like | 10 |
| F4 | target | null-like | null-like | 10 |
| F4 | null-control | null-like | null-like | 10 |
| F5 | target | null-like | null-like | 10 |
| F5 | null-control | null-like | null-like | 10 |
| F6 | target | null-like | null-like | 10 |
| F6 | null-control | null-like | null-like | 10 |
| F7 | target | non-null | non-null | 10 |
| F7 | null-control | null-like | null-like | 10 |
| F8 | target | non-null | non-null | 10 |
| F8 | null-control | null-like | null-like | 10 |

The unchanged non-null rule is median dCor >= 0.10 with at least eight p-values <= 0.01.
Warnings, retained exceptions, and artifact paths are recorded in `confirmation-summary.csv` and `manifest.json`.
This confirms or fails to confirm behavior of this residual-dependence diagnostic under the specified fixtures and frozen pipeline. It does not establish causal edges, conditional independence in general, or researcher-facing network recovery.

Owner decision required; this result does not authorize estimator redesign, a new simulation family, or package work.
