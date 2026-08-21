# Reference-Calibrated Gate 0 Confirmation Design

## Status and purpose

This is the owner-approved follow-up to Gate 0 run `gate0-20260820-001` and
the null-calibration diagnostic `null-calibration-20260820-001`.

The earlier calibration diagnostic returned `CALIBRATION QUESTION`: at an
evaluation size of 1,000, known-independent standard-normal reference pairs
had an observed distance-correlation baseline above the original `< 0.05`
practical-null clause. Its permutation p-values were not concentrated near
zero, and the fitted residual fixtures did not show a clear excess over the
same-size reference distribution.

This design defines one fresh confirmatory simulation. Its purpose is to test
one precommitted, reference-calibrated decision rule under the existing Gate 0
fixtures. It is not a threshold search, estimator redesign, new simulation
family, Stage I transition, or package implementation.

## Scope and frozen pipeline

The confirmation is scoped only to the planned 1,000-row residual-pair
workflow. It preserves all of the following unchanged:

- the continuous six-variable F1--F8 fixtures and their equations;
- 50,000 source rows per fixture replication;
- pair-specific adjustment excluding both endpoints;
- five-fold cross-fitted cubic spline adjustment with five knots, degree
  three, `StandardScaler`, and `Ridge(alpha=1.0)`;
- distance correlation;
- 199 permutations and the existing empirical p-value formula;
- the existing non-null classification criterion;
- 10 replications for each F1--F8 fixture pair.

The completed Gate 0 and calibration artifact directories are immutable and
must not be overwritten, edited, or reused.

## Frozen practical-null boundary

The practical-null boundary is exactly:

```text
0.07078970914915612
```

It is the 95th percentile, with pandas' `linear` interpolation convention, of
the 30 independent standard-normal reference observed dCor values at 1,000
rows retained in the calibration run.

The frozen calibration input is:

```text
artifacts/null-calibration/null-calibration-20260820-001/records.csv
SHA-256: 57160bf69892c4047e8a089487d5b894d09243c1a3bcf60164f4daa881369197
```

This is an individual-reference 95th percentile, used deliberately as a
conservative practical boundary for a fixture batch's median over ten
replications. It is not represented as a 95th percentile for a ten-replication
median. No later result may modify it automatically.

## Revised fixture classification

For every F1--F8 target and null-control pair, classify exactly ten completed
replications as follows:

- `null-like`: no more than 2 of 10 empirical permutation p-values are at or
  below 0.05, and the median observed dCor is strictly below
  `0.07078970914915612`;
- `non-null`: at least 8 of 10 empirical permutation p-values are at or below
  0.01, and the median observed dCor is at least 0.10;
- `ambiguous`: every other complete, non-exceptional case.

The original non-null criterion is unchanged. The only classification change
is the practical-null boundary.

## Independent reference confirmation

Run 30 fresh, identity-seeded pairs of independent standard-normal variables
at 1,000 rows. This arm does not invoke fixtures or residualization.

The reference check passes only when all of the following hold:

- at least 27 of 30 observed dCor values are strictly below
  `0.07078970914915612`;
- no more than 4 of 30 empirical permutation p-values are at or below 0.05;
- every reference record is complete and has no exception.

The first condition checks the new practical boundary against independent data.
The second checks that permutation p-values are not unexpectedly concentrated
near zero. The run retains every reference dCor value and permutation array.

## Confirmation execution and terminal outcome

The substantive confirmation has two components, executed under a new,
domain-separated seed namespace and a new immutable run identity:

1. the 30-replication independent-reference component; and
2. the complete F1--F8, 10-replication fixture component.

For every attempt, retain identity-derived seeds, observed dCor, permutation
p-value, permutation array, residual sample when applicable, warnings,
exceptions, elapsed runtime, source revision, and exact frozen configuration.

Terminal outcomes are evaluated in this order:

1. `STOP`: any exception, malformed or incomplete required matrix, or
   suspicious reference p-value behavior (more than 4 of 30 reference
   p-values at or below 0.05);
2. `NARROW`: a failed reference practical-boundary count, or any fixture
   pair classified `ambiguous`;
3. `MIXED / OWNER DECISION`: the reference check passes and a fixture has a
   definite class that contradicts its expected class;
4. `PASS`: the reference check passes and every fixture pair has its expected
   class.

`PASS` is confirmation only for this diagnostic under these fixtures and this
frozen pipeline. It does not establish causal edges, general conditional
independence, direct network recovery, or readiness for a researcher-facing
package.

## Evidence, lifecycle, and governance

The confirmation writes one new, initially empty artifact directory. It must
refuse any nonempty output directory. On completion it writes raw records,
arrays, samples, manifest, terminal state, figures, and an owner-facing memo.
The source/configuration change is committed before the evidence artifact
commit. A fresh independent code review follows implementation and evidence
generation.

The memo must identify the calibration source file and hash, quantile method,
exact boundary, reference-check counts, fixture classifications, terminal
outcome, exceptions and warnings. It must end with:

> Owner decision required; this result does not authorize estimator redesign,
> a new simulation family, or package work.

No output from this confirmation automatically changes a threshold, estimator,
fixture, simulation family, package scope, or roadmap. Any successor requires
a separate owner-approved protocol.

## Verification requirements

Implementation must test:

- exact calibration-source hash, quantile convention, and frozen boundary;
- revised null-like boundary behavior and unchanged non-null criterion;
- reference pass/fail thresholds and terminal-outcome precedence;
- seed namespace separation and complete record/array retention;
- output-directory immutability and no reuse of prior evidence directories;
- report/memo inclusion of all frozen decision information.

Before the substantive run, execute the full test suite and lint check. The
run is retained regardless of terminal outcome, then reviewed independently.
