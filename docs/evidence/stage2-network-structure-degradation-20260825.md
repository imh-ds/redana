# Stage II round 7 network-structure degradation results

Per `docs/superpowers/specs/2026-08-25-stage2-network-structure-degradation-design.md`.
Not a Gate 0 study: no hash-pinned calibration, no single-official-run
ceremony, no per-replication artifact retention. Four conditions
(`chain`, `hub`, `community`, `redundant_predictors`), 50 replications
each at `n = 1,000` rows, `coefficient = 0.7` for every true edge, all
other parameters at Stage I's baseline throughout. `chain` reuses
`generate_stage1_linear_fixture` unchanged; `hub`, `community`, and
`redundant_predictors` use three new fixture generators. This is the
seventh and last of `plan.md` §6's named degradation dimensions. Source
revision: `48548a18`.

## A fixture-labeling artifact, reported first because it changes how to read the redundant_predictors results below

The `redundant_predictors` fixture was designed to test whether a
predictor highly correlated with a true cause (`X2`, correlated `0.9`
with `X1`) gets spuriously flagged as if it were itself a direct cause
of the outcome (`X3`). Its declared true-edge set was `{(X1,X3)}` only
-- deliberately excluding `(X1,X2)` on the reasoning that the fixture's
"interesting" question was about `X2`'s relationship to `X3`, not to
`X1`.

**This labeling choice does not match how every other fixture in this
project defines a true edge.** `X2 = 0.9*X1 + 0.436*e2` is a genuine,
direct structural dependency -- by the same standard used everywhere
else (Gate 0, Stage I, and every prior Stage II round), `(X1,X2)` *is* a
true edge, and detecting it is correct, not a false positive. A
diagnostic check confirms this is exactly what happened: the residual
layer flagged `(X1,X2)` in **50/50 replications** -- every single one.
Because this fixture has only one *declared* true edge, that one
mislabeled pair alone drags the measured precision down substantially,
even though the underlying detection is accurate.

**The redundant_predictors condition's low precision numbers below are
therefore mostly a labeling artifact, not a genuine finding about
network-structure degradation**, and are not directly comparable to
`chain`/`hub`/`community`'s precision (which have 2, 3, and 4 declared
true edges respectively -- precision is also mechanically more sensitive
to a fixed rate of incidental false positives when there are fewer true
edges to divide by, a second, independent reason precision is not
comparable across these four conditions at face value).

**The question this fixture actually set out to answer -- does
collinearity with a true cause spuriously drag the *redundant* variable
into being flagged against the *outcome* -- is answered cleanly and
separately: `(X2,X3)` was flagged as a false positive in only 1/50
replications (2%), the same order of magnitude as this round's other
incidental false positives (`(X5,X6)`: 1/50, `(X3,X4)`: 1/50, `(X3,X6)`:
1/50 -- an isolated one-off each, consistent with ordinary finite-sample
noise, not a systematic collinearity-driven artifact).** The residual
layer did not fall into the collinearity trap this fixture was designed
to probe.

## Results across topologies

`redundant_predictors`' precision/exact-match columns should be read
with the note above in mind -- they measure a labeling artifact more
than a real degradation.

| Condition | Incumbent precision (mean/median) | Residual precision (mean/median) | Incumbent recall | Residual recall | Incumbent exact-match | Residual exact-match |
| --- | --- | --- | --- | --- | --- | --- |
| chain | 0.586 / 0.667 | 0.950 / 1.000 | 1.000 | 1.000 | 0.060 | 0.860 |
| hub | 0.561 / 0.550 | 0.955 / 1.000 | 1.000 | 1.000 | 0.060 | 0.840 |
| community | 0.670 / 0.667 | 0.953 / 1.000 | 1.000 | 1.000 | 0.060 | 0.820 |
| redundant_predictors | 0.169 / 0.167 | 0.487 / 0.500 | 1.000 | 1.000 | 0.000 | 0.000 |

Residual per-edge detection fraction: **1.000 for every declared true
edge in every condition**, including all three of `hub`'s spokes, all
four of `community`'s edges across its two clusters, and
`redundant_predictors`' single declared edge `(X1,X3)`.

`redundant_predictors`' `(X2,X3)` false-positive rate: **0.020** (1/50
replications) -- the condition's one genuinely clean, meaningful number.

## Independent spot recompute

Without importing `redana.benchmark`, seed derivation and all four
fixture generators' formulas were reimplemented independently and
evaluated at replication indices 0, 25, and 49 for every condition. All
twelve recomputed seeds, frame shapes, and true edge sets matched the
actual project code exactly -- zero mismatches.

## Interpretation

**Recall stayed at ceiling (1.000) for every declared true edge across
all four topologies, for both mechanisms.** Neither a high-degree hub
node nor a second independent structural cluster (community) measurably
changed detection relative to the already-validated chain baseline.

**Hub and community show no meaningful precision difference from chain**
(incumbent: 0.586, 0.561, 0.670; residual: 0.950, 0.955, 0.953) -- within
the range of run-to-run variability already seen across every prior
round's chain-based conditions. Neither topology introduced a new
failure mode.

**The redundant_predictors condition's actual, cleanly-measured finding
is that the residual layer resisted the collinearity trap it was
designed to test** -- a 2% false-positive rate on `(X2,X3)` is
unremarkable noise, not evidence of confusion between a redundant
predictor and a true cause. This is a positive result for the
mechanism, buried underneath a labeling artifact that made the
condition's headline precision numbers look far worse than the
underlying detection actually was.

## A convergence warning worth reporting

`sklearn.covariance.graphical_lasso` again emitted `ConvergenceWarning:
did not converge after 100 iterations` on a substantial number of fits,
across all four conditions, matching every prior round's evidence notes.
Reported plainly again rather than investigated or suppressed.

## Explicit boundary

This round tested `plan.md` §6's seventh and last named degradation
dimension. It does not:

- provide a clean precision comparison for `redundant_predictors`, due
  to the labeling artifact identified above -- a corrected fixture
  (declaring `{(X1,X2),(X1,X3)}` as true edges, or restructuring the
  redundancy so `X2` has no genuine direct dependency on `X1`) would be
  needed to isolate the collinearity question with a clean precision
  metric; the 2% `(X2,X3)` false-positive rate is offered as the clean
  substitute finding, not a full replacement for that comparison;
- test network-structure degradation at any effect strength other than
  `0.7`, or combined with any of rounds 1-6's other degradation
  dimensions;
- compare methods at a matched operating point (`plan.md` §8);
- touch real data or make any package-readiness claim.

## Governance

Per `outline/plan.md` §18 rule 10, this result does not authorize a
corrected redundant-predictors re-run, the comparator-fairness protocol
(`plan.md` §8), Stage III (`plan.md` §7), real-data work, or any package
decision. **This round completes every one of `plan.md` §6's seven named
degradation dimensions.** Per the project's own governance rule 10, this
is an explicit, appropriate point to ask whether the project still
deserves to continue past Stage II, rather than an automatic trigger to
proceed to Stage III -- that decision is deliberately left to the
project owner, not made by this note.
