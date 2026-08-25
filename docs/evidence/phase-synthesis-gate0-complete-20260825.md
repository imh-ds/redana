# Phase synthesis: Gate 0 canonical structures complete

## Purpose and scope of this document

This document extends `phase-synthesis-linear-capability-boundary-20260824.md`
and `phase-synthesis-quadratic-capability-boundary-20260824.md` with
everything established since: the completion of F1, F2, F3, F6, F7, and F8,
which together with the earlier F4 and F5 work means every fixture in
`research/gate0/fixtures.py` (F1 through F8) has now been taken through the
full calibration-pinned, hash-verified, independently-recomputed evidence
protocol. It exists so that anyone (human or AI) picking this project back
up later can reconstruct exactly what has been proven, what has explicitly
not been proven, and what the next authorized step is, without re-reading
the full evidence trail.

Nothing in this document is a new claim. It restates and cross-references
already-committed, hash-verified evidence.

## Where this sits in the overall project plan

The master plan (`outline/plan.md`) defines 13 build steps. Everything
below falls entirely inside **Step 3: Gate 0, population-level mathematical
sanity** -- the very first substantive step, before any reusable prototype,
benchmark stage, comparator study, stability validation, real-data phase,
or package decision. Steps 4 through 13 have not started.

`outline/plan.md` §3 lists ten canonical structures for Gate 0 to
sanity-check:

1. independent variables
2. Gaussian linear chain
3. fork (plain linear common cause)
4. collider
5. linear direct + indirect paths
6. nonlinear direct edge
7. nonlinear common cause
8. nonlinear indirect path without a direct edge
9. nonlinear direct + indirect path
10. mixed linear/nonlinear edge

This project's own operational checklist, `research/gate0/fixtures.py`
(fixtures F1 through F8), does not enumerate these ten one-for-one --
it is the working translation the project actually built and ran. The
mapping below is deliberately explicit so nothing is silently claimed
that was not tested.

| `plan.md` §3 structure | Fixture | Status |
| --- | --- | --- |
| Independent variables | F1 | Tested -- PASS |
| Gaussian linear chain | F4 | Tested -- PASS |
| Fork (plain linear common cause) | -- | **Not tested** |
| Collider | F7 | Tested -- PASS |
| Linear direct + indirect paths | F8 | Tested -- PASS |
| Nonlinear direct edge | F3 | Tested -- PASS |
| Nonlinear common cause | F5 | Tested -- STOP on the general-purpose residualizer; PASS only after a structure-matched repair |
| Nonlinear indirect path without a direct edge | F6 | Tested -- PASS |
| Nonlinear direct + indirect path | -- | **Not tested** (F8 is the linear-only analogue) |
| Mixed linear/nonlinear edge | -- | **Not tested** |

Seven of the ten `plan.md` structures have direct evidence. Three remain
open: a plain linear fork (distinct from F5's nonlinear fork), a nonlinear
version of F8's direct-plus-indirect structure, and any structure that
mixes a linear edge with a nonlinear edge on the same pair. All eight
fixtures the project itself defined (F1--F8) have now been run.

Also unstarted: only one nonlinear shape (a pure quadratic, `Z^2` /
`0.7*X1` for the mediated case) has been used throughout. Sine, threshold,
and other non-monotonic shapes named in `plan.md` Stage I have not been
tested at all, in any structure.

## Completed evidence, in order

1. **Raw independent-reference calibration** -- READY. A finite-sample
   1,000-row dCor decision boundary, `0.058242447845091264`, was selected
   before any transfer study and has not changed since.
   (`artifacts/batch-null-calibration/batch-null-calibration-20260821-001`;
   `docs/evidence/batch-null-calibration-batch-null-calibration-20260821-001.md`)
2. **Fresh independent-reference confirmation** -- PASS. The frozen
   boundary behaved as expected on fresh independent pairs.
   (`docs/evidence/batch-null-confirmation-batch-null-confirmation-20260821-001.md`)
3. **F4 linear residual-null transfer** (Gaussian linear chain) -- PASS.
   The general-purpose spline/Ridge residualizer correctly nulls a linear
   mediated (chain) relationship.
   (`docs/evidence/f4-linear-residual-null-transfer-batch-f4-linear-null-transfer-20260822-001.md`)
4. **F4 matched residual-link alternative** -- PASS. The same workflow
   reliably detects a clear, planted linear residual link.
   (`docs/evidence/f4-residual-link-alternative-batch-f4-residual-link-20260822-001.md`)
5. **F5 nonlinear residual-null transfer** (nonlinear common cause) --
   STOP. The same general-purpose spline/Ridge residualizer did *not*
   cleanly null a quadratic common-cause relationship (74 null-like
   batches against a required 85; 81 low p-values). This is the finding
   that motivated the repair line of work.
   (`docs/evidence/f5-residual-null-transfer-batch-f5-null-transfer-20260821-001.md`)
6. **F5 oracle forensic spike** -- narrowly informative. True-null oracle
   noise stayed borderline (NARROW), while residuals from the actual
   fitted spline residualizer showed a clear upward dCor/low-p shift --
   evidence that the STOP in (5) reflected a real residualizer
   limitation, not sampling noise.
   (`docs/evidence/f5-oracle-forensic-spike-20260822.md`)
7. **F5 explicit-quadratic repair** -- PASS. A narrowly precommitted,
   structure-matched repair (raw value plus its square for each
   adjustment variable, scaled Ridge, unchanged five-fold cross-fitting)
   correctly nulls the same quadratic common cause: 90 of 100 batches
   null-like (>= 85 required), 44 of 1,000 low p-values (<= 67 allowed),
   no warnings or exceptions.
   (`docs/evidence/f5-quadratic-repair-batch-f5-quadratic-repair-20260824-001.md`)
8. **F5 quadratic-residual-link alternative ("Candidate 1")** -- PASS.
   Using the exact same repair basis, a second, deliberately different
   nonlinear relationship (zero linear covariance, planted through a
   shared latent noise term, excluded from the adjustment set by
   construction) was detected in all 100 of 100 batches (>= 85 required),
   with 1,000 of 1,000 individual p-values at or below 0.05. This rules
   out the possibility that the repair in (7) passed only by
   over-smoothing away curvature in general rather than by correctly
   modeling the specific common cause.
   (`docs/evidence/f5-quadratic-residual-link-alternative-batch-f5-quadratic-residual-link-20260824-001.md`)
9. **Independent review of Candidate 1** -- CONFIRMED. A second AI, with
   no access to the development conversation, independently re-derived
   the population math, re-verified the residualizer cannot structurally
   see the planted effect, hand-recomputed dCor and permutation p-values
   from raw files for spot-checked cells (exact matches), and confirmed
   no scope, threshold, or calibration drift against the approved spec.
10. **F6 nonlinear residual-null transfer** (nonlinear indirect path,
    no direct edge) -- PASS. `X2 = 0.7*(X1^2-1)+e2` mediates a nonlinear
    effect onto `X3` with no direct `X1`-`X3` edge; the unrepaired
    general-purpose residualizer correctly nulled the pair: 90 of 100
    batches null-like, 53 of 1,000 low p-values. Unlike F5, no repair
    was needed -- the residualizer handles a pure nonlinear mediator
    correctly even though it fails on a nonlinear common cause.
    (`docs/evidence/f6-residual-null-transfer-batch-f6-null-transfer-20260824-001.md`)
11. **F7 collider detection** -- PASS. `X3 = 0.7*X1+0.7*X2+e3` is a
    collider on the tested pair `(X1, X2)`; conditioning on `X3` (which
    the residualizer does automatically, since it adjusts for every
    other column) induces exactly the "explaining away" dependence the
    estimand is defined to report. Detected in 100 of 100 batches,
    1,000 of 1,000 low p-values, saturated.
    (`docs/evidence/f7-collider-detection-batch-f7-collider-detection-20260824-001.md`)
12. **F1 plain independence** -- PASS. `X1 = e1`, `X2 = e2`, fully
    independent; the most basic possible baseline. 87 of 100 batches
    null-like, 53 of 1,000 low p-values -- a bad result here would have
    indicated a fundamental problem with the statistic or calibration
    itself, independent of any structural question.
    (`docs/evidence/f1-independence-null-transfer-batch-f1-null-transfer-20260824-001.md`)
13. **F3 nonlinear direct-edge detection** -- PASS. `X2 =
    0.7*(X1^2-1)+e2` with no common cause, mediator, or collider;
    adjustment is fully inert. Detected in 100 of 100 batches, 1,000 of
    1,000 low p-values, observed dCor 0.26-0.35 (four to six times the
    boundary). Confirms F5's original STOP was specifically an
    adjustment-transfer problem, not a basic incapacity to see nonlinear
    signal.
    (`docs/evidence/f3-nonlinear-direct-edge-detection-batch-f3-nonlinear-direct-edge-detection-20260825-001.md`)
14. **F2 linear direct-edge detection** -- PASS. `X2 = 0.7*X1+e2`, the
    linear counterpart to F3, also with fully inert adjustment. Detected
    in 100 of 100 batches, 1,000 of 1,000 low p-values, observed dCor
    0.46-0.61 (roughly eight to ten times the boundary). Completes the
    direct-edge pair (linear and nonlinear) alongside F3.
    (`docs/evidence/f2-linear-direct-edge-detection-batch-f2-linear-direct-edge-detection-20260825-001.md`)
15. **F8 mixed direct-and-indirect path detection** -- PASS. `X3 =
    0.7*X1+e3` (mediator), `X2 = 0.7*X1+0.7*X3+e2`: `X1` affects `X2`
    both directly and indirectly through `X3`, with the mediator sitting
    inside the automatic adjustment set. Detected in 100 of 100 batches,
    1,000 of 1,000 low p-values, observed dCor 0.37-0.54. Linear
    adjustment for the mediator does not fully null the pair's
    dependence, both because part of it is a direct edge and because the
    tested left variable is excluded from its own predictor set.
    (`docs/evidence/f8-mixed-direct-indirect-path-detection-batch-f8-mixed-direct-indirect-path-detection-20260825-001.md`)

Every PASS/STOP outcome from items 3 onward was additionally confirmed by
a separate, from-raw-files verifier script that never imports the
project's own runner, report, or policy modules -- re-deriving seeds,
recomputing dCor and permutation nulls, recomputing SHA-256 hashes, and
reapplying the detection or null-like rule independently. All matched the
retained manifest exactly.

## Supported capability, stated precisely

At the tested 1,000-row / 100-batch x 10-replication / 199-permutation /
five-fold-cross-fitted dimensions, with the frozen raw-reference boundary:

- The workflow correctly handles plain independence (F1): no spurious
  detection when there is genuinely nothing to find.
- The workflow correctly handles a linear chain, nulling the induced
  chain relationship (F4), and correctly detects a planted linear
  residual link (F4-link) and a plain linear direct edge (F2).
- The workflow correctly detects a raw nonlinear direct edge (F3) using
  the same unrepaired general-purpose residualizer, showing the earlier
  F5 failure was not a basic incapacity to see nonlinear signal.
- The workflow correctly nulls a nonlinear mediator with no direct edge
  (F6) -- unlike the nonlinear common-cause case, no repair was needed
  here.
- The workflow correctly detects the "explaining away" dependence induced
  by conditioning on a collider (F7), consistent with the project's
  narrow "dependence given the stated adjustment set" estimand.
- The workflow correctly detects dependence from a pair connected by both
  a direct edge and a mediated indirect path simultaneously (F8), even
  though the mediator sits inside the automatic adjustment set.
- The workflow does **not** correctly handle a nonlinear common cause
  (F5) using the general-purpose residualizer alone -- it requires
  replacing that residualizer with a narrow, structure-matched
  raw-plus-square basis. That repaired workflow both (a) nulls the
  intended common cause and (b) still detects an unrelated planted
  nonlinear residual dependence layered on top of it (Candidate 1),
  without absorbing it.

Put together: across all eight fixtures the project defined, the
unrepaired general-purpose residualizer is correct everywhere except one
specific structure -- a nonlinear common cause -- where it requires a
structure-matched repair. No other structure tested has shown a false
positive, a false negative, or required any deviation from the frozen
general-purpose workflow.

## Explicit boundary -- what remains unestablished

Everything from the prior two boundary documents still holds: no general
nonlinear robustness, no weak-effect sensitivity, no arbitrary-alternative
detection, no conditional-independence or causal claims, no network
recovery, no real-data use, no package implementation.

In addition, specific to this phase:

- **Three `plan.md` §3 structures remain untested**: a plain linear fork
  (as distinct from F5's nonlinear fork/common cause), a nonlinear
  version of F8's direct-plus-indirect structure, and any mixed
  linear/nonlinear edge on the same pair. These were never implemented
  as fixtures in this project's own `research/gate0/fixtures.py` and
  would require new fixture definitions, not just new runners.
- **Only one nonlinear shape has been tested anywhere**: a pure quadratic
  (`0.7*(Z^2-1)`, or the linear mediator weight `0.7*Z` for the
  already-linear cases). Sine, threshold/non-monotonic, and any other
  shape named in `plan.md` Stage I are completely untested, in every
  structure, including the ones already marked PASS above.
- **The nonlinear common-cause repair is narrow by design.** It has only
  been shown to work for the one quadratic common-cause shape it was
  built to fix, verified against exactly one deliberately different
  alternative signal (Candidate 1). It has not been generalized or
  tested against any other common-cause shape.
- **No reusable prototype yet exists.** The residualizer, statistic, and
  batch policy code are explicitly disposable Gate 0 research code, not
  the frozen minimal prototype `plan.md` Step 4 describes.
- **Steps 4 through 13 of the master plan have not started**: no
  benchmark stages, no controlled-degradation study, no realistic hybrid
  psychometric benchmark, no comparator-fairness protocol, no stability
  validation, no edge typology, no detectability reporting, no real-data
  phase, no package decision.

## Governance status

Every result above was produced under a narrowly precommitted,
single-cell design: one frozen DGP, one frozen adjustment basis, one
frozen detection or null-like rule, hash-pinned parent evidence, a single
official run with no retries, and independent from-raw-file
recomputation. Candidate 1 additionally received a fully independent
second-AI review before being treated as settled. No threshold,
calibration, seed, or scope was changed after seeing any result, in any
of the fifteen studies listed above.

## Next decision

Per `outline/plan.md` §18 (rule 10: after every gate, ask whether the
project still deserves to continue) and owner direction recorded in this
project's working history, this document does not itself authorize any
next action. Reaching PASS on all eight of this project's own fixtures is
a natural pause point, and three separate paths are now open for an
explicit owner decision:

1. **Close remaining `plan.md` §3 gaps** -- add fixtures for a plain
   linear fork, a nonlinear direct+indirect path, and a mixed
   linear/nonlinear edge, and take each through the same sequence used
   for every study above (design proposal, explicit owner approval,
   spec, plan, implementation, one official run, independent
   verification).
2. **Broaden the tested nonlinear shape** -- repeat select structures
   (most importantly the common-cause case, where a repair was needed)
   using a different nonlinear shape such as sine or threshold, to test
   whether the quadratic-specific repair generalizes or was overfit to
   one shape.
3. **Treat Gate 0 as sufficient for now and move toward `plan.md` Step 4**
   (the minimal residual-dependence prototype), on the reasoning that
   seven of ten canonical structures plus all eight project-defined
   fixtures have direct, independently-verified evidence, and the one
   confirmed failure mode (nonlinear common cause) already has a working,
   verified repair.

Whichever path is chosen, no step in that path's sequence is to be
skipped or auto-triggered by this document, and structures are not to be
batched into a matrix.
