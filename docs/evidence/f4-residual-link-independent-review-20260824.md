# Independent review: F4 residual-link alternative

Independent LLM review: **PASS supported**. The reviewer audited worktree commit `cd66663273e0cea2f7cab7b0c0026a1b81905f8e` read-only and reported no evidence, provenance, or scope blocker.

## Verified evidence

- 1,000 `(batch, replication)` records covering 0--99 x 0--9.
- 1,000 finite 1,000-row `X1`/`X3` residual samples and 1,000 finite 199-value permutation-null arrays.
- Matching records and runner-input SHA-256 values, pinned raw-calibration and reviewed F4-null provenance, correct DGP/pair/phase/namespace/run ID/seeds, 100 detected batches, and no warnings or exceptions.
- Detection recomputed from retained records rather than accepted from the memo/report.

## Interpretation and caveat

The supported claim is narrow: the frozen 1,000-row workflow detected this one deliberately clear, matched linear residual-link alternative after the reviewed F4 linear residual-null passed. It does not establish general power, nonlinear robustness, conditional-independence testing, network recovery, causal discovery, real-data validity, or package readiness.

The reviewer could not run dcor-dependent pytest in its own environment. It verified retained artifacts and recomputed core quantities directly instead. This is an environment limitation, not an evidence defect; project-focused tests and Ruff had already passed in the project environment.

## Governance

The review made no repository changes and does not authorize automatic recalibration, a new simulation family, or package work.
