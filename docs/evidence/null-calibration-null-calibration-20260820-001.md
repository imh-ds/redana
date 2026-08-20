# Null-calibration evidence: null-calibration-20260820-001

The immutable null-calibration diagnostic completed on 2026-08-20 with the
owner-facing outcome **CALIBRATION QUESTION**. This is calibration evidence,
not a revised Gate 0 conclusion; no threshold, estimator, fixture, statistic,
or scope changed.

## Retained evidence

- Run directory: `artifacts/null-calibration/null-calibration-20260820-001/`
- [Run manifest](../../artifacts/null-calibration/null-calibration-20260820-001/manifest.json)
- [Complete records](../../artifacts/null-calibration/null-calibration-20260820-001/records.csv)
- [Calibration memo](../../artifacts/null-calibration/null-calibration-20260820-001/calibration-memo.md)
- [Distribution summary](../../artifacts/null-calibration/null-calibration-20260820-001/calibration-summary.csv)
- Paired reference-versus-fitted plots: `plots/evaluation-{250,500,1000,2000}-reference-vs-fitted.png`

The manifest fixes the diagnostic matrix at 30 replications, 50,000 source
rows, four evaluation sizes (250, 500, 1,000, and 2,000), and 199 permutations.
The retained records contain 600 completed cells with no recorded exceptions.

## Exact-seed correction (v1)

The completed `records.csv` serialised nullable seed columns through pandas
floating-point columns. Consequently, several seed values above `2**53` appear
in rounded scientific notation in that immutable file. This is an audit-trail
precision flaw only: each seed had already been used to execute the diagnostic,
so no numerical result, classification, or owner-facing outcome changed.

No diagnostic was rerun and the immutable run directory was not modified. The
[versioned exact-seed correction sidecar](./null-calibration-null-calibration-20260820-001-seed-correction-v1/README.md)
derives every seed field for all 600 retained record identities from the frozen
deterministic schedule. Its [manifest](./null-calibration-null-calibration-20260820-001-seed-correction-v1/manifest.json)
links the original records by relative path and SHA-256
`57160bf69892c4047e8a089487d5b894d09243c1a3bcf60164f4daa881369197`, records
the frozen source revision, and documents the schedule. Read sidecar seed
columns as strings; blank cells are null.

Owner decision required; this result does not authorize estimator redesign, a
new simulation family, or package work.
