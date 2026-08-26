"""Sample-size dependence, Stage B: does the effect-strength cliff shift with n?

Stage II round 1 found a sharp detectability cliff for the nonlinear
fixture between coefficient=0.10 and 0.20 at n=1,000. This crosses those
same three coefficient levels against three sample sizes to test
whether more data pushes the cliff toward weaker coefficients and less
data pushes it toward stronger coefficients, as basic statistical power
theory predicts.

Not a Gate 0 study, no new redana source: reuses
redana.benchmark.run_replicated_condition and
redana.scenarios.generate_stage1_nonlinear_fixture unchanged.
"""

from __future__ import annotations

from functools import partial

from redana.benchmark import ConditionResult, run_replicated_condition
from redana.network import NetworkConfig
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage1_nonlinear_fixture

_N_REPS = 50
_PERMUTATIONS = 199
_ALPHA = 0.05
_BASE_SEED = 20260825
_COEFFICIENT_LEVELS = (0.10, 0.15, 0.20)
_N_ROWS_LEVELS = (500, 1000, 2000)


def run() -> dict[tuple[float, int], ConditionResult]:
    """Run the nonlinear fixture across the coefficient x n_rows grid."""

    residual_config = PrototypeConfig()
    network_config = NetworkConfig()
    results: dict[tuple[float, int], ConditionResult] = {}

    for coefficient in _COEFFICIENT_LEVELS:
        for n_rows in _N_ROWS_LEVELS:
            condition_name = f"sample-size-b-{coefficient}-{n_rows}"
            fixture_fn = partial(generate_stage1_nonlinear_fixture, coefficient=coefficient)
            result = run_replicated_condition(
                fixture_fn,
                condition_name=condition_name,
                n_reps=_N_REPS,
                n_rows=n_rows,
                residual_config=residual_config,
                network_config=network_config,
                permutations=_PERMUTATIONS,
                alpha=_ALPHA,
                base_seed=_BASE_SEED,
            )
            results[(coefficient, n_rows)] = result

    return results


def main() -> int:
    results = run()
    print("== nonlinear fixture per-edge detection fraction, coefficient x n_rows grid ==")
    header = "coefficient".ljust(12) + "".join(f"n={n:<8}" for n in _N_ROWS_LEVELS)
    print(header)
    for coefficient in _COEFFICIENT_LEVELS:
        row = f"{coefficient:<12}"
        for n_rows in _N_ROWS_LEVELS:
            summary = results[(coefficient, n_rows)].summary
            fractions = list(summary.residual_per_edge_detection_fraction.values())
            mean_fraction = sum(fractions) / len(fractions)
            row += f"{mean_fraction:<10.3f}"
        print(row)

    print()
    print("== full detail per condition ==")
    for coefficient in _COEFFICIENT_LEVELS:
        for n_rows in _N_ROWS_LEVELS:
            summary = results[(coefficient, n_rows)].summary
            print(f"  -- coefficient={coefficient} n_rows={n_rows} --")
            print(
                f"    residual precision: mean={summary.residual_precision.mean:.3f} "
                f"median={summary.residual_precision.median:.3f}"
            )
            print(
                f"    residual recall:    mean={summary.residual_recall.mean:.3f} "
                f"median={summary.residual_recall.median:.3f}"
            )
            print(
                "    residual per-edge detection fraction: "
                f"{dict(sorted(summary.residual_per_edge_detection_fraction.items()))}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
