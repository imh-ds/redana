# Batch-Level Null Calibration Design

## Status and purpose

This owner-approved protocol follows the reference-calibrated confirmation
`reference-confirmation-20260820-001`, which returned `NARROW`. That run had
25 of 30 fresh independent reference values below the former boundary when
27 were required. Its p-values were acceptable, every F1--F8 fixture pair
matched its expected class, and it had no warnings or exceptions.

The problem is therefore not an established residualization or fixture
failure. The former boundary was estimated from only 30 individual reference
observations but was applied to a ten-replication batch decision. This protocol
calibrates the decision at the same ten-replication batch level used by the
diagnostic.

This is a reference-only calibration study. It does not rerun F1--F8, alter a
completed artifact, implement package features, establish causal edges, or
automatically advance the project.

## Frozen measurement pipeline

Every individual reference replication uses:

- two independently generated standard-normal vectors;
- 1,000 evaluation rows;
- distance correlation;
- 199 permutations;
- the existing empirical permutation p-value formula.

Reference replications do not invoke fixtures, residualization, cross-fitting,
or a fitted adjustment model. The generated data are independent by design.

## Calibration half

Generate 100 independent calibration batches. Each batch contains 10
independent reference replications, for 1,000 reference pairs total.

For every batch, retain the ten observed dCor values, ten permutation
p-values, all ten permutation arrays, identity-derived seeds, warnings,
exceptions, elapsed runtime, and exact configuration.

A batch satisfies the p-value guard when at most 2 of its 10 p-values are at
or below 0.05. If fewer than 90 of the 100 calibration batches satisfy this
guard, the calibration half is `STOP`: no dCor boundary can make 90 of 100
batches satisfy the complete null-like rule without changing the p-value rule.

Otherwise, select the practical-null boundary as the smallest observed batch
median dCor among p-value-guard-passing batches for which at least 90 of all
100 calibration batches satisfy both conditions:

1. the batch satisfies the p-value guard; and
2. its median dCor is at or below the selected boundary.

The comparison is inclusive (`<=`) so the rank-based selected value is exactly
reproducible. The selected boundary, rank, qualifying batch identities, and
selection algorithm are written to the calibration manifest and memo. The
boundary is frozen before the independent confirmation half begins.

## Independent confirmation half

Generate a separate 100 independent batches of 10 reference replications,
again totaling 1,000 pairs. Use a distinct domain-separated seed namespace and
a new immutable output directory. It must not reuse calibration data, seeds,
or a recalculated boundary.

Apply the frozen complete null-like rule to every confirmation batch. The
confirmation checks:

- at least 85 of 100 batches are null-like; and
- no more than 67 of all 1,000 individual p-values are at or below 0.05.

The 85/100 limit tolerates ordinary confirmation-sample variation around the
90% target: if the true batch null-like rate is 90%, it has approximately a
96% probability of meeting this acceptance limit. The 67/1,000 p-value limit
is the 99th percentile of `Binomial(n=1000, p=0.05)` and guards against
anti-conservative permutation p-values.

Terminal outcomes are evaluated in this order:

1. `STOP`: any exception, malformed or incomplete required record matrix,
   calibration p-value-guard failure, or more than 67 of 1,000 confirmation
   p-values at or below 0.05;
2. `NARROW`: fewer than 85 of 100 confirmation batches are null-like;
3. `PASS`: every required record is complete and both confirmation checks pass.

`PASS` confirms only that this practical-null rule has the target batch-level
behavior on fresh known-independent standard-normal data under this frozen
measurement pipeline.

## Reproducibility and evidence

The two halves use distinct, named seed namespaces:

- `batch-null-calibration` for calibration; and
- `batch-null-confirmation` for confirmation.

Every output directory is initially empty and immutable after execution. Each
manifest records the run ID, source revision, environment, all frozen numeric
settings, seed namespace, record count, selection or confirmation counts,
artifact paths, and terminal outcome. Nullable integer seeds are serialized
without floating-point coercion.

The confirmation manifest pins the calibration manifest and records by
relative path and SHA-256 hash. It copies the selected boundary and selection
metadata rather than recomputing them. Memos state clearly that no F1--F8 run,
threshold change beyond the frozen calibration selection, estimator change, or
package decision occurred automatically.

## Verification and governance

Implementation must test:

- exactly 100 batches of 10 records in each half;
- p-value-guard `STOP` before boundary selection;
- inclusive, rank-based smallest-boundary selection with exact tie behavior;
- boundary immutability and calibration-manifest hash verification;
- the 85/100 and 67/1,000 independent-confirmation limits and terminal
  precedence;
- new seed namespaces and their non-overlap;
- complete per-run/per-batch artifact retention, exact seed round trips, and
  nonempty-directory refusal;
- absence of any fixture or residualization call from both reference halves;
- report/memo governance language and prohibition of F1--F8 execution.

Before each substantive half, the complete test suite and lint check must pass.
Source code/configuration changes are committed before each evidence commit.
The calibration half is reviewed before the confirmation half executes. The
confirmation evidence is reviewed independently after completion.

The final memo must end with:

> Owner decision required; this result does not authorize estimator redesign,
> a new simulation family, or package work.

No result from this protocol automatically launches a fixture validation,
threshold revision, package implementation, or additional simulation.
