# Sample-size dependence design

## Purpose

Every study in this project so far -- Gate 0, Step 4, Stage I, and all
seven Stage II rounds -- has been run at a single fixed sample size,
`n = 1,000`. This was inherited from Gate 0's original calibration and
never varied. `outline/plan.md` §1 scopes the project to "target
`n >= 200` for nonlinear inference," and §10 explicitly names "behavior
as `n/p` changes" as a metric to track -- so sample-size dependence is
part of the project's own stated scope, just not yet touched.

This matters concretely because of Stage II round 1's headline finding:
a sharp detectability cliff for the residual layer between
`coefficient = 0.10` and `0.20` (roughly 2%-7% of variance explained),
at `n = 1,000`. Every discussion of that finding since has had to add
the same caveat: we don't know whether that boundary shifts with sample
size. Basic statistical power theory says it should -- more data should
let the mechanism detect weaker signals, and less data should make the
same coefficient level harder to detect -- but this project has never
tested that expectation directly.

## Scope: two stages, not one combined sweep

Per this project's practice of characterizing one new dimension alone
before combining it with another, this investigation is split into two
stages.

### Stage A: does sample size matter at all, holding a strong signal fixed?

Reuse `generate_stage1_nonlinear_fixture` at `coefficient = 0.7`
(Stage I's strong baseline, already near-ceiling at `n = 1,000` in every
prior round) and sweep only `n_rows` across a range including values
below and above `plan.md` §1's stated floor of `200`. This establishes
whether sample size affects detection at all when the signal is strong,
and identifies whether there is a lower `n` floor below which even a
strong signal breaks down (e.g. too few rows for cross-fitted
residualization or stable EBIC selection).

Candidate levels: `n in {100, 200, 500, 1000, 2000}`. `100` is below
`plan.md`'s stated floor deliberately, to check what "below scope"
failure looks like; `1000` reproduces every prior round's setting as a
built-in consistency check.

### Stage B: does the effect-strength cliff shift with sample size?

The load-bearing question. Cross a small grid of `coefficient` values
spanning round 1's already-found cliff (`{0.10, 0.15, 0.20}`, the exact
three levels round 1's boundary follow-up used) against a small grid of
sample sizes (`{500, 1000, 2000}`, centered on the already-used `1000`).
Nine conditions. This directly tests whether more data pushes the cliff
toward weaker coefficients (expected, per standard statistical power
theory) and whether less data pushes it toward stronger coefficients
(also expected) -- or whether, surprisingly, the boundary is insensitive
to sample size within this range.

This does not attempt to trace the full detectability curve at every
`n` -- three coefficient levels and three sample sizes is enough to
establish *direction and rough magnitude* of the shift, which is the
open question every prior evidence note has flagged, not to produce a
publication-grade power curve.

## Everything else held constant

- `p = 6`, pure nonlinear fixture (the shape every effect-strength
  finding to date has used), `noise_scale = 1.0`, `distribution =
  "gaussian"`, `heteroskedasticity = 0.0`, `measurement_error = 0.0`
  (every other dimension at its Stage I baseline).
- `199` permutations per pair, BH-FDR `alpha = 0.05` (unchanged).
- `NetworkConfig()` and `PrototypeConfig()` frozen defaults (unchanged,
  not tuned against these or any prior results).

## Replication design

**50 replications per condition**, matching every prior round. Stage A:
5 conditions (250 replications total). Stage B: 9 conditions (450
replications total). Total compute is larger than any single prior
round (700 replications vs. round 1's 300), but each replication at
smaller `n` runs faster (permutation test and graphical-lasso cost both
scale with `n`), so wall-clock time should be comparable to or less than
the larger prior rounds.

## Metrics and reporting

Reuse `redana.benchmark.run_replicated_condition` completely unchanged
-- `n_rows` is already a first-class parameter, so this investigation
requires **zero new `redana` source code**, only new orchestration
scripts. Stage A reports per-edge detection fraction and recall across
the five sample sizes. Stage B reports per-edge detection fraction as a
`coefficient x n` grid, making the shape of the boundary's shift
directly visible.

## Execution and verification

Same lighter-than-Gate-0 approach as every Stage II round: no
hash-pinned calibration, no per-replication artifact retention, no new
tests needed (no new source). Run Stage A first; if it reveals a
low-`n` floor below which the mechanism breaks outright (e.g. the
residualization step failing or degenerating at very small `n`), that
would need to be understood before Stage B's smallest level (`n=500`)
is trusted. Independently spot-recompute a handful of seeds and fixture
values at a few `n` levels. Record results in a single evidence note
covering both stages, reporting the shift (or lack of one) honestly.

## Governance

This is not one of `plan.md` §6's seven named dimensions -- sample size
is scoped separately in §1 and §10. It does not authorize the
comparator-fairness protocol (`plan.md` §8), Stage III (`plan.md` §7),
real-data work, or any package decision. Per `outline/plan.md` §18 rule
10, this investigation exists to close a specific, repeatedly-flagged
open question (does the effect-strength cliff shift with `n`), not to
open a general sample-size sweep across every other dimension -- doing
that for every one of the seven Stage II dimensions would be a much
larger undertaking and is explicitly out of scope here.
