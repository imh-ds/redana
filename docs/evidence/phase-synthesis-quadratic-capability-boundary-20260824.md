# Phase synthesis: quadratic nonlinear capability boundary

## Purpose and scope of this document

This document extends `phase-synthesis-linear-capability-boundary-20260824.md`
with everything established since that boundary was recorded: the F5
nonlinear-null repair and its matched Candidate 1 alternative. It exists so
that anyone (human or AI) picking this project back up later can reconstruct
exactly what has been proven, what has explicitly not been proven, and what
the next authorized step is, without re-reading the full evidence trail.

Nothing in this document is a new claim. It restates and cross-references
already-committed, hash-verified evidence.

## Where this sits in the overall project plan

The master plan (`outline/plan.md`) defines 13 build steps. Everything below
falls entirely inside **Step 3: Gate 0, population-level mathematical
sanity** -- the very first substantive step, before any reusable prototype,
benchmark stage, comparator study, stability validation, real-data phase, or
package decision. Steps 4 through 13 have not started.

Gate 0's own canonical-structure checklist (`plan.md` §3) lists ten
structures to sanity-check. This work has gone deep on exactly two of them:
one linear direct-edge case and one nonlinear common-cause case. The other
eight -- fork (as a plain linear common cause), collider, nonlinear indirect
path without a direct edge, nonlinear direct+indirect combined, and mixed
linear/nonlinear edges -- have not been taken through this protocol. Only one
nonlinear shape (a pure quadratic, `Z^2`) has been tested; sine, threshold,
and non-monotonic shapes have not.

## Completed evidence, in order

1. **Raw independent-reference calibration** -- READY. A finite-sample
   1,000-row dCor decision boundary, `0.058242447845091264`, was selected
   before any transfer study and has not changed since.
   (`artifacts/batch-null-calibration/batch-null-calibration-20260821-001`)
2. **Fresh independent-reference confirmation** -- PASS. The frozen boundary
   behaved as expected on fresh independent pairs.
3. **F4 linear residual-null transfer** -- PASS. The general-purpose
   spline/Ridge residualizer correctly nulls a linear mediated (chain)
   relationship.
4. **F4 matched residual-link alternative** -- PASS. The same workflow
   reliably detects a clear, planted linear residual link.
5. **F5 nonlinear residual-null transfer** -- STOP. The same general-purpose
   spline/Ridge residualizer did *not* cleanly null a quadratic common-cause
   relationship (74 null-like batches against a required 85; 81 low
   p-values). This is the finding that motivated everything below.
6. **F5 oracle forensic spike** -- narrowly informative. True-null oracle
   noise stayed borderline (NARROW), while residuals from the actual fitted
   spline residualizer showed a clear upward dCor/low-p shift -- evidence
   that the STOP in (5) reflected a real residualizer limitation, not
   sampling noise.
7. **F5 explicit-quadratic repair** -- PASS. A narrowly precommitted,
   structure-matched repair (raw value plus its square for each adjustment
   variable, scaled Ridge, unchanged five-fold cross-fitting) correctly
   nulls the same quadratic common cause: 90 of 100 batches null-like
   (>= 85 required), 44 of 1,000 low p-values (<= 67 allowed), no warnings or
   exceptions.
   (`artifacts/batch-f5-quadratic-repair/batch-f5-quadratic-repair-20260824-001`;
   see `docs/evidence/f5-quadratic-repair-batch-f5-quadratic-repair-20260824-001.md`)
8. **F5 quadratic-residual-link alternative ("Candidate 1")** -- PASS. Using
   the exact same repair basis, a second, deliberately different nonlinear
   relationship (zero linear covariance, planted through a shared latent
   noise term, excluded from the adjustment set by construction) was
   detected in all 100 of 100 batches (>= 85 required), with 1,000 of 1,000
   individual p-values at or below 0.05. This rules out the possibility that
   the repair in (7) passed only by over-smoothing away curvature in
   general rather than by correctly modeling the specific common cause.
   (`artifacts/batch-f5-quadratic-residual-link/batch-f5-quadratic-residual-link-20260824-001`;
   see `docs/evidence/f5-quadratic-residual-link-alternative-batch-f5-quadratic-residual-link-20260824-001.md`)
9. **Independent review of Candidate 1** -- CONFIRMED. A second AI, with no
   access to the development conversation, was given only the design and
   plan documents, the source, the tests, and the committed artifacts. It
   independently re-derived the population math, re-verified the residualizer
   cannot structurally see the planted effect, hand-recomputed dCor and
   permutation p-values from raw files for three spot-checked cells (exact
   matches), and confirmed no scope, threshold, or calibration drift against
   the approved spec. Its only caveat -- that the spec/plan documents were
   not yet committed to git at review time -- has been treated as a non-issue
   per owner instruction.

## Supported capability, stated precisely

At the tested 1,000-row / 100-batch x 10-replication / 199-permutation /
five-fold-cross-fitted dimensions, with the frozen raw-reference boundary:

- The workflow correctly handles one linear pair in both directions (null
  and clear-link), using the general-purpose spline/Ridge residualizer.
- The workflow correctly handles one specific nonlinear common-cause
  structure (a pure quadratic-in-one-adjustment-variable common cause), but
  only when the general-purpose residualizer is replaced by a narrow,
  structure-matched raw-plus-square basis. That repaired workflow both (a)
  nulls the intended common cause and (b) still detects an unrelated planted
  nonlinear residual dependence layered on top of it, without absorbing it.

## Explicit boundary -- what remains unestablished

Everything from the prior boundary document still holds: no general
nonlinear robustness, no weak-effect sensitivity, no arbitrary-alternative
detection, no conditional-independence or causal claims, no network
recovery, no real-data use, no package implementation.

In addition, specific to this phase:

- **Untested canonical structures** (present as fixtures in
  `research/gate0/fixtures.py` but never run through calibration + repair +
  alternative the way F4 and F5 were): F1 (plain independence), F2/F3
  (direct edges, linear and nonlinear, with no common cause), F6 (nonlinear
  indirect/mediated path), F7 (collider), F8 (mixed direct+indirect path).
- **Untested nonlinear shapes**: only a pure quadratic (`Z^2`) has been
  tested. Sine, threshold/non-monotonic, and any other shape from `plan.md`
  Stage I's list are untested.
- **No reusable prototype yet exists.** The residualizer, statistic, and
  batch policy code are explicitly disposable Gate 0 research code, not the
  frozen minimal prototype `plan.md` Step 4 describes.
- **Steps 4 through 13 of the master plan have not started**: no benchmark
  stages, no controlled-degradation study, no realistic hybrid psychometric
  benchmark, no comparator-fairness protocol, no stability validation, no
  edge typology, no detectability reporting, no real-data phase, no package
  decision.

## Governance status

Every result above was produced under a narrowly precommitted, single-cell
design: one frozen DGP, one frozen adjustment basis, one frozen detection
rule, hash-pinned parent evidence, a single official run with no retries,
and independent from-raw-file recomputation. Candidate 1 additionally
received a fully independent second-AI review before being treated as
settled. No threshold, calibration, seed, or scope was changed after seeing
any result.

## Next decision

Per `outline/plan.md` §18 (rule 10: after every gate, ask whether the
project still deserves to continue) and owner direction recorded in this
project's working history, the authorized next action is to continue
**within Gate 0** by selecting one additional narrowly chartered canonical
structure or nonlinear shape from the untested list above, and to take it
through the same sequence used for Candidate 1: design proposal, explicit
owner approval, spec, plan, implementation, one official run, and
independent verification. Structures are not to be batched into a matrix,
and no step in that sequence is to be skipped or auto-triggered by a prior
PASS.
