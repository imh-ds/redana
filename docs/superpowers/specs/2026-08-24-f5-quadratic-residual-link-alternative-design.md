# F5 quadratic-residual-link alternative design

## Purpose

Test whether the frozen 1,000-row workflow, using the explicit-quadratic
repair basis that already passed the F5 common-cause null, still detects a
genuine nonlinear residual dependence planted underneath that same common
cause. This is the matched alternative to the reviewed F5 quadratic-repair
PASS: it rules out the failure mode in which the repair passed the null only
because it over-fits away curvature in general, rather than because it
correctly represents the quadratic common cause specifically.

This is Candidate 1 from the design-review record
`docs/evidence/phase-synthesis-linear-capability-boundary-20260824.md`. It is
not a new calibration, not a general nonlinear-power claim, and it does not
start package work.

## Fixed scenario and sole design change

Reuse the F5 common-cause null unmodified and add exactly one term to `X2`:

```text
Z  = X3
P  = 0.7 * (Z^2 - 1)
X1 = P + e1
X2 = P + 0.7 * (e1^2 - 1) + e2
```

`e1`, `e2`, and `X4`--`X6` are mutually independent standard-normal draws.
`Z = X3` and `P` are identical to the frozen F5 fixture. The fixture
standardizes the six-column frame once, after generation, exactly as every
other Gate 0 fixture does: `(frame - mean) / std(ddof=0)`.

Test `(X1, X2)` after cross-fitted adjustment for `(X3, X4, X5, X6)` using
the existing raw-plus-square quadratic basis
(`cross_fitted_pair_quadratic_residuals` in `research/gate0/residuals.py`,
already implemented and tested for the F5 quadratic-repair study). Do not
modify that residualizer. `X1` is excluded from `X2`'s adjustment set and
`X2` is excluded from `X1`'s, exactly as `predictor_columns` already
enforces.

### Why this isolates the planted link

The oracle (population) residuals are, up to the deterministic per-column
rescaling caused by standardization:

```text
r1 = e1
r2 = 0.7 * (e1^2 - 1) + e2
```

`e1` is a latent noise term: it is not an observed column, it is independent
of `(X3, X4, X5, X6)`, and `X1` itself is excluded from `X2`'s adjustment
set. The raw-plus-square basis over `(X3, X4, X5, X6)` therefore has no way
to represent `e1` or `e1^2`; it can only remove the shared quadratic-in-`X3`
term `P`, which is exactly what it is supposed to remove. `Cov(e1, e1^2-1)
= E[e1^3] = 0` for standard normal `e1`, so the planted relationship has
exactly zero linear covariance in population; dCor is required because a
linear statistic would report zero dependence here by construction.

Freeze five shuffled cross-fitting folds, scaling, Ridge alpha 1, all 1,000
residual rows, and 199 permutations -- identical dimensions to the F5
quadratic-repair study and to the F4 residual-link alternative.

## Detection rule

Reuse the existing, fixture-agnostic `F4LinkConfig` / detection-policy
dataclasses in `research/gate0/f4_link_policy.py` unchanged. Do not write a
new policy module: `summarize_detection_batches`, `check_detection`, and
`detection_terminal_status` operate only on the generic columns `batch`,
`replication`, `observed_statistic`, `permutation_p_value`, and
`exception_text`, and are already fixture-agnostic.

Copy the raw-reference boundary `0.058242447845091264` as the dCor
effect-size threshold only; do not recalibrate. Across 100 batches of 10
replications:

- detected batch: median dCor strictly above the boundary and at least 8/10
  p-values at or below 0.05;
- PASS: at least 85 detected batches, complete evidence;
- NARROW: complete evidence but fewer than 85 detected batches;
- STOP: incomplete or malformed evidence, any retained exception, or any
  retained warning (the report layer's STOP override takes precedence over
  the batch count regardless of outcome).

This is a clear-signal sensitivity check, not a weak-effect power claim. The
`0.7` coefficient is the project's existing `FIXTURE_COEFFICIENT` constant
(`research/gate0/config.py`), already used uniformly across F2--F8 and the
F4 alternative before this design existed; it is not chosen or tuned for
this study.

## Retention and governance

Use namespace `batch-f5-quadratic-residual-link`. Retain every attempted
record's exact unsigned fixture, residual, and permutation seeds; dCor;
p-value; warnings; exception text; elapsed time; a 1,000-row two-column
residual sample; and a 199-value permutation-null array. Atomically write
records, input manifest, report manifest, summary, plot, memo, and state.

Pin two parents by exact SHA-256, unchanged:

- the raw independent-reference calibration
  (`artifacts/batch-null-calibration/batch-null-calibration-20260821-001`),
  records SHA-256 `267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5`,
  input manifest SHA-256 `7737bf6b9f57ed0072843df8dd639e603dee3ebb2a9ad85b7d9d22703279ce9c`,
  report manifest SHA-256 `639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`,
  boundary `0.058242447845091264`;
- the reviewed F5 quadratic-repair PASS evidence
  (`artifacts/batch-f5-quadratic-repair/batch-f5-quadratic-repair-20260824-001`),
  records SHA-256 `f4fbf588fdd66198fcbce18fdb0031f41e4d42787922bfa4cdd1f4a745277836`,
  input manifest SHA-256 `6da7a9684409b2091aa3eb21534df0900336cfdb8b3ce5541a4d9f5c39153e30`,
  report manifest SHA-256 `9f45b9c0c80b050fe6e8fd6353b79ed45b1f3076b7e5b07140890f925ed098a7`,
  recorded terminal outcome `PASS` (90 null-like batches; 44 low p-values).

Official output is
`artifacts/batch-f5-quadratic-residual-link/batch-f5-quadratic-residual-link-20260824-001`
with run ID `batch-f5-quadratic-residual-link-20260824-001`. Refuse a
non-empty output directory.

Write tests first, pass preflight, commit source, run exactly once,
independently recompute the committed evidence from raw files, and commit
the evidence note regardless of outcome. Do not change the signal,
residualizer, boundary, dimensions, or rule after results are known; do not
retry with changed seeds; do not add interactions, higher powers, or a
different residualizer.

## Interpretation

- `PASS` supports only that this raw-plus-square repair basis detects this
  one planted nonlinear (zero-linear-covariance) residual dependence,
  layered on the F5 quadratic common cause, under this frozen 1,000-row
  procedure. It authorizes only a later, separate owner decision about
  whether to document or implement this one matched pair of findings. It
  does not authorize a simulation matrix, other nonlinear shapes, weaker
  effect sizes, recalibration, or package work.
- `NARROW` means the repair basis under-detects this planted link; record it
  without tuning, changing the coefficient, retrying seeds, or adding
  another alternative.
- `STOP` means the repair basis does not reliably detect this planted link
  under the frozen rule; record it and stop for diagnosis. `STOP` does not
  authorize rescue tuning or a broader nonlinear program.
