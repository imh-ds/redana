# Step 4 multi-seed follow-up: are the incumbent's false positives stable?

This is a diagnostic follow-up to
`docs/evidence/step4-first-validation-scenario-20260825.md`, which found
the incumbent network selected two false-positive edges (`X3-X4`,
`X4-X5`) in one seeded run and explicitly flagged that a single run
cannot distinguish sampling noise from a systematic issue. It is **not**
a Gate 0 study, and it is **not** `outline/plan.md` Stage I/II/III
benchmarking: five seeds is not a replication design (`plan.md` §9 wants
50-100+ independent draws per condition for a decisive claim), and this
note draws no conclusion about general detection power or
false-positive rates. It only reports what happened across these five
specific seeds on the same frozen scenario.

## What ran

`scripts/run_step4_validation_scenario_multi_seed.py`: the identical
frozen `p=6` scenario and configuration from Task 6
(`redana/scenarios.py::generate_step4_validation_frame`, `n=5000`), run
across five seeds (`20260825, 1, 2, 3, 4`) -- the original Task 6 seed
plus four more.

## Results

| Seed | Incumbent edges (beyond the 2 true) | Incumbent precision | Residual edges (beyond the 3 true) | Residual precision | X4-X5 detected |
| --- | --- | --- | --- | --- | --- |
| 20260825 | `(X3,X4)`, `(X4,X5)` | 0.500 | -- | 1.000 | Yes |
| 1 | `(X1,X3)`, `(X2,X4)`, `(X2,X6)` | 0.400 | `(X2,X4)` | 0.750 | Yes |
| 2 | `(X1,X3)`, `(X1,X6)`, `(X4,X5)`, `(X4,X6)` | 0.333 | -- | 1.000 | Yes |
| 3 | none | 1.000 | -- | 1.000 | Yes |
| 4 | none | 1.000 | -- | 1.000 | Yes |

Recall was **1.000 for both mechanisms on every seed** -- neither the
incumbent nor the residual layer ever missed a true edge, linear or
nonlinear.

The nonlinear edge `(X4, X5)` -- zero linear covariance in population --
was correctly caught by the residual layer in **all five of five**
seeds.

## What this does and does not show

- **The incumbent's false positives are not fixed to specific pairs.**
  Across five seeds, the false-positive edges were entirely different
  each time (`X3-X4`/`X4-X5`; then `X1-X3`/`X2-X4`/`X2-X6`; then
  `X1-X3`/`X1-X6`/`X4-X5`/`X4-X6`; then none; then none). If there were a
  systematic bug -- for example, always spuriously connecting a specific
  pair regardless of data -- the same pair would recur. It did not. This
  pattern is consistent with the sampling-noise explanation offered in
  the first validation note, not with a defect in `redana/network.py`.
  Two of five seeds (3 and 4) had **zero** false positives.
- **The residual layer was cleaner but not perfect.** Four of five seeds
  had zero false positives; one seed (1) had one (`X2-X4`). With 15
  pairs tested and BH-FDR at `alpha=0.05` per run, an occasional false
  discovery is exactly what nominal FDR control predicts, not a
  surprise.
- **This is five seeds, not a calibrated claim.** It is enough to
  distinguish "the same pair recurs every time" (which would demand
  investigation) from "different pairs each time, occasionally none"
  (consistent with expected finite-sample noise). It is not enough to
  estimate an actual false-positive rate, and it does not attempt to.
  That estimation is exactly `outline/plan.md` Stage II's job (§6,
  controlled degradation across sample size and other dimensions), not
  a Step 4 diagnostic.

## Governance

This follow-up does not authorize Stage I/II/III benchmarking, changing
the frozen `NetworkConfig` grid or `gamma`, or any further automatic
work. It answers only the narrow question it was run to answer: the
first validation scenario's false positives look like ordinary
finite-sample noise rather than a systematic defect, based on five
seeds. Whether to move to Stage I benchmarking, characterize
false-positive rates more formally first, or pause here remains a
separate, later owner decision.
