# Step 4 minimal statistical prototype charter

## Purpose

This is a charter document, not an implementation-ready spec. It exists
because `outline/plan.md` §18 rule 1 requires an explicit new charter
before building any new subsystem following a hard-stop failure (F5's
STOP), and because moving from Gate 0 to Step 4 is a materially larger
scope jump than any single canonical-structure study: it creates the
project's first reusable, non-disposable code.

Per `docs/evidence/phase-synthesis-gate0-complete-20260825.md`, the owner
decision was to treat Gate 0 as sufficient for now (path 3: seven of ten
`plan.md` §3 structures and all eight project-defined fixtures have
independently-verified evidence, and the one confirmed failure mode has a
working, independently-confirmed repair) and move toward `plan.md` Step 4.

## What Step 4 is, per `outline/plan.md` §4

> Build Only the Minimal Statistical Prototype. Do not build a package,
> GUI, polished plotting layer, or broad API yet.

Required components, exactly six, no more:

1. a frozen incumbent linear network;
2. pair-specific cross-fitted residualization;
3. an ordinary nonlinear dependence statistic on residual pairs;
4. a permutation/null procedure;
5. multiplicity control, initially BH-FDR;
6. simulation scoring.

The sole question at this stage is: **does the core mechanism work?**

Explicitly out of scope for Step 4 (per `plan.md` §4): stability
rendering, edge typology, detectability reporting, mixed-data handling,
sophisticated visualization, functional-form classification. These are
Steps 12, 13, 15, and later -- not now.

## Why this needs a charter, not just a plan

Everything built so far under Gate 0 (`research/gate0/`) is explicitly
disposable: single-purpose runners and reports for one frozen scenario
each, never intended for reuse, and the module docstring for
`research/gate0/fixtures.py` says so directly ("disposable Gate 0
simulation"). Step 4 is different in kind: it is the first code in this
project meant to be *used*, across multiple simulated networks and
eventually real data, rather than run once for one narrow claim. That
changes what "done" means (general correctness, not one pinned scenario)
and requires decisions Gate 0 never had to make.

## Open architectural decisions requiring explicit confirmation

### 1. Location and promotion of already-validated Gate 0 code

Two of the six required components (#2 pair-specific cross-fitted
residualization, and the dCor/permutation half of #3-#4) already exist,
validated across eight canonical structures, in `research/gate0/residuals.py`
and `research/gate0/metrics.py`. Two options:

- **(a) Promote by copying.** Create a new top-level package (proposed
  name: `redana/`, sibling to `research/`) and copy the validated
  `cross_fitted_pair_residuals` and `permutation_distance_correlation`
  functions into it verbatim as their permanent home. `research/gate0/`
  keeps its own copies untouched, since it remains disposable and its
  own studies must stay reproducible exactly as run. No runtime
  dependency from the reusable prototype onto disposable research code.
- **(b) Import directly.** The prototype imports from
  `research.gate0.residuals` and `research.gate0.metrics` rather than
  duplicating them, avoiding drift between two copies of the same
  function.

**Recommendation: (a), promote by copying.** `research/gate0` is
documented as disposable; a reusable subsystem should not depend on code
whose module docstring says it is not meant to be relied on. The
duplication is small (two short functions) and each copy's correctness
is independently testable.

### 2. Frozen incumbent linear network implementation

`plan.md` names EBICglasso (`qgraph::EBICglasso` in R) as the standard
comparator in the psychometric-network literature. There is no direct
Python equivalent in common use. Two options:

- **(a) Implement EBIC-selected graphical lasso natively in Python.** Fit
  a graphical-lasso path (via `sklearn.covariance.graphical_lasso`) over
  a fixed grid of regularization strengths, compute the extended BIC
  (`EBIC_gamma`, gamma fixed at 0.5, the standard default) for each fit,
  and select the minimum-EBIC model. This is buildable with existing
  dependencies (`scikit-learn` is already a project dependency) and
  matches the literature's estimator, just without calling into R.
- **(b) Call out to R via `rpy2`** to use `qgraph::EBICglasso` directly.
  This is the literal reference implementation but adds a heavy,
  fragile cross-language dependency to a project that has otherwise been
  pure Python throughout.

**Recommendation: (a), native Python EBIC-selected graphical lasso.**
Avoids the R dependency; the EBIC selection formula is well-documented
and independently verifiable; and this "frozen incumbent" only needs to
be a reasonable, unchanging linear-network baseline, not a byte-for-byte
match to one R package's implementation.

### 3. Multiplicity control

BH-FDR (Benjamini-Hochberg false discovery rate) is explicitly named and
has no ambiguity in its definition. This does not need a decision --
standard BH-FDR applied to the vector of pairwise permutation p-values
within one network.

### 4. Simulation scoring

`plan.md` does not specify exact metrics at this stage (`plan.md` §10's
fuller metric set is for later benchmark stages, not Step 4). For Step 4,
the minimal scoring needed to answer "does the core mechanism work?" is:
given a known ground-truth simulated network, compute precision, recall,
and F1 for (a) the frozen incumbent linear network's selected edges and
(b) the residual layer's BH-FDR-significant pairs, each against the true
edge set. This is the smallest scoring that lets the two mechanisms be
compared on the same simulated ground truth.

## What Step 4 does not decide

Building the minimal prototype does not itself validate anything about
real psychometric data, does not claim the nonlinear layer is useful in
any practical sense, and does not authorize Stage I/II/III benchmarking
(`plan.md` §5-§7) or any package decision. Those remain separate, later
owner decisions per `plan.md` §17 and §18 rule 10.

## Requested confirmation

This charter requests explicit approval on:

1. Proceeding with `plan.md` Step 4 at all (already given via "move
   toward Step 4").
2. Promotion approach 2(a): copy, do not import, the validated
   residualization and dCor/permutation code into a new `redana/`
   package.
3. Incumbent-network approach 2(b)-recommendation: native Python
   EBIC-selected graphical lasso, not an R dependency.

If approved, the next step is a full implementation plan (task
breakdown, TDD sequence, and a first synthetic validation scenario with
a known ground-truth network) built the same way every Gate 0 study's
plan was built, followed by the same explicit-approval-to-implement
pattern used throughout this project.
