# Gate 0 evidence memo

Run ID: gate0-20260820-001
Overall status: **NARROW**
Selected profile: full

Estimand: Residual dependence remaining after adjustment for the other observed variables under the specified model.

## Frozen configuration required by the specification

| Setting | Value |
| --- | --- |
| Source rows | 50000 |
| Evaluation rows | 1000 |
| Replications | 10 |
| Permutations | 199 |
| Cross-fitting folds | 5 |
| Adjustment set | all observed variables except both pair endpoints |
| Residuals | pair-specific out-of-sample predictions |
| Spline knots | 5 |
| Spline degree | 3 |
| Spline knot strategy | quantile |
| Spline include bias | False |
| Feature scaler | StandardScaler |
| Ridge alpha | 1.0 |
| Dependence statistic | distance correlation |
| Permutation reference | permute one residual vector |
| Fixture coefficient | 0.7 |
| Linear relationship | 0.7x |
| Quadratic relationship | 0.7(x^2 - 1) |
| Exogenous noise | independent standard Gaussian; mean 0.0; standard deviation 1.0 |
| Source revision | 126cf73fe8467e2c9041b6603037b0154627b743 |

Dependency versions:

- python: 3.12.13
- numpy: 2.5.2
- pandas: 3.0.5
- scikit-learn: 1.9.0
- dcor: 0.7
- matplotlib: 3.11.1

## Exact fixture equations and evaluation pairs

| Fixture | Generating equation | Target pair | Null-control pair | Expected target | Expected control |
| --- | --- | --- | --- | --- | --- |
| F1 | X1=e1; X2=e2; X3=e3; X4=e4; X5=e5; X6=e6 | X1, X2 | X4, X5 | null-like | null-like |
| F2 | X1=e1; X2=0.7*X1+e2; X3=e3; X4=e4; X5=e5; X6=e6 | X1, X2 | X4, X5 | non-null | null-like |
| F3 | X1=e1; X2=0.7*(X1**2-1)+e2; X3=e3; X4=e4; X5=e5; X6=e6 | X1, X2 | X4, X5 | non-null | null-like |
| F4 | X1=e1; X2=0.7*X1+e2; X3=0.7*X2+e3; X4=e4; X5=e5; X6=e6 | X1, X3 | X4, X5 | null-like | null-like |
| F5 | X3=e3; X1=0.7*(X3**2-1)+e1; X2=0.7*(X3**2-1)+e2; X4=e4; X5=e5; X6=e6 | X1, X2 | X4, X5 | null-like | null-like |
| F6 | X1=e1; X2=0.7*(X1**2-1)+e2; X3=0.7*X2+e3; X4=e4; X5=e5; X6=e6 | X1, X3 | X4, X5 | null-like | null-like |
| F7 | X1=e1; X2=e2; X3=0.7*X1+0.7*X2+e3; X4=e4; X5=e5; X6=e6 | X1, X2 | X4, X5 | non-null | null-like |
| F8 | X1=e1; X3=0.7*X1+e3; X2=0.7*X1+0.7*X3+e2; X4=e4; X5=e5; X6=e6 | X1, X2 | X4, X5 | non-null | null-like |

Post-generation standardization: Each X1-X6 column is centered by its generated sample mean and scaled by its generated population standard deviation (ddof=0).

Seed derivation: SHA-256 of UTF-8 text formed by joining identity parts with '|'; the first eight digest bytes are interpreted as an unsigned big-endian integer.
Seed derivation is identity-based and independent of execution order.
Shared fixture dataset (`fixture-dataset`): `gate0 | fixture_id | replication | fixture | dataset`; pair identity is not included; fixture generation rehashes `fixture | fixture_id | seed`.
Pair-role residual (`pair-role-residual`): `gate0 | fixture_id | replication | pair_role | residual`; KFold receives the identity seed modulo `2**32`.
Pair-role evaluation (`pair-role-evaluation`): `gate0 | fixture_id | replication | pair_role | evaluation`.
Pair-role permutation (`pair-role-permutation`): `gate0 | fixture_id | replication | pair_role | permutation`; each permutation child rehashes `permutation | permutation_seed | permutation_index`.

Empirical permutation p-value: `(1 + count(null >= observed)) / (B + 1)`

## Pair and fixture gate thresholds

- null-like: At most 2 of 10 p-values <= 0.05 and median observed distance correlation < 0.05.
- non-null: At least 8 of 10 p-values <= 0.01 and median observed distance correlation >= 0.10.
- ambiguous: Any other result.
- PASS: Every target matches its expected class and every null-control pair is null-like.
- STOP: Any expected target-class mismatch (including the F7 collider target), any non-null control, any exception, or any malformed or incomplete matrix.
- NARROW: Any remaining ambiguity.

## Fixture classifications

| Fixture | Pair | Expected | Observed |
| --- | --- | --- | --- |
| F1 | null_control | null-like | ambiguous |
| F1 | target | null-like | null-like |
| F2 | null_control | null-like | null-like |
| F2 | target | non-null | non-null |
| F3 | null_control | null-like | ambiguous |
| F3 | target | non-null | non-null |
| F4 | null_control | null-like | ambiguous |
| F4 | target | null-like | ambiguous |
| F5 | null_control | null-like | ambiguous |
| F5 | target | null-like | ambiguous |
| F6 | null_control | null-like | ambiguous |
| F6 | target | null-like | ambiguous |
| F7 | null_control | null-like | ambiguous |
| F7 | target | non-null | non-null |
| F8 | null_control | null-like | null-like |
| F8 | target | non-null | non-null |

## Raw-statistic summary

| Fixture | Pair | Median observed | Median p-value |
| --- | --- | ---: | ---: |
| F1 | null_control | 0.0531 | 0.4725 |
| F1 | target | 0.0489 | 0.6750 |
| F2 | null_control | 0.0492 | 0.6550 |
| F2 | target | 0.5077 | 0.0050 |
| F3 | null_control | 0.0563 | 0.3900 |
| F3 | target | 0.3288 | 0.0050 |
| F4 | null_control | 0.0530 | 0.4825 |
| F4 | target | 0.0607 | 0.2850 |
| F5 | null_control | 0.0502 | 0.6775 |
| F5 | target | 0.0528 | 0.4800 |
| F6 | null_control | 0.0531 | 0.5125 |
| F6 | target | 0.0536 | 0.4650 |
| F7 | null_control | 0.0506 | 0.6325 |
| F7 | target | 0.3093 | 0.0050 |
| F8 | null_control | 0.0428 | 0.8900 |
| F8 | target | 0.4516 | 0.0050 |

## Exceptions

- None

## Warnings

- None

## Illustrative residual scatterplots

Each residual scatterplot shows one representative replication only and is illustrative rather than confirmatory evidence.

## F7 collider interpretation

For F7, an expected non-null result is induced conditional dependence—not a direct causal relationship. Conditioning on the collider X3 can make the otherwise independent X1 and X2 residuals dependent.

Owner decision required; this result does not authorize estimator redesign, a new simulation family, or package work.
