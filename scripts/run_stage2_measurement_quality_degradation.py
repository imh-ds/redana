"""Run the Stage II round 6 measurement-quality degradation benchmark.

outline/plan.md section 6, scoped to exactly one of its remaining named
degradation dimensions this round: measurement quality (perfect ->
modest -> substantial measurement error), swept across three levels on
Stage I's two existing fixture shapes at a fixed effect strength
(coefficient=0.7). Not a Gate 0 study -- no hash-pinned calibration, no
per-replication artifact retention. Reuses every Step 4 / Stage I /
Stage II component unchanged except the new `measurement_error`
parameter on the two Stage I fixture generators.
"""

from __future__ import annotations

from functools import partial

from redana.benchmark import ConditionResult, run_replicated_condition
from redana.network import NetworkConfig
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage1_linear_fixture, generate_stage1_nonlinear_fixture

_N_REPS = 50
_N_ROWS = 1000
_PERMUTATIONS = 199
_ALPHA = 0.05
_BASE_SEED = 20260825
_COEFFICIENT = 0.7
_LEVELS = (("perfect", 0.0), ("modest", 0.25), ("substantial", 1.0))


def run() -> dict[str, list[ConditionResult]]:
    """Run all six (shape x measurement-error level) conditions, grouped by shape."""

    residual_config = PrototypeConfig()
    network_config = NetworkConfig()
    results: dict[str, list[ConditionResult]] = {"linear": [], "nonlinear": []}

    for shape_name, generator in (
        ("linear", generate_stage1_linear_fixture),
        ("nonlinear", generate_stage1_nonlinear_fixture),
    ):
        for level_name, measurement_error in _LEVELS:
            condition_name = f"stage2-measurement-quality-{shape_name}-{level_name}"
            fixture_fn = partial(
                generator, coefficient=_COEFFICIENT, measurement_error=measurement_error
            )
            result = run_replicated_condition(
                fixture_fn,
                condition_name=condition_name,
                n_reps=_N_REPS,
                n_rows=_N_ROWS,
                residual_config=residual_config,
                network_config=network_config,
                permutations=_PERMUTATIONS,
                alpha=_ALPHA,
                base_seed=_BASE_SEED,
            )
            results[shape_name].append(result)

    return results


def _print_shape(shape_name: str, conditions: list[ConditionResult]) -> None:
    print(f"== {shape_name} fixture across measurement-error levels (coefficient=0.7) ==")
    for (level_name, measurement_error), result in zip(_LEVELS, conditions, strict=True):
        summary = result.summary
        print(f"  -- {level_name} (measurement_error={measurement_error}) --")
        for label, incumbent, residual in (
            ("precision", summary.incumbent_precision, summary.residual_precision),
            ("recall", summary.incumbent_recall, summary.residual_recall),
            ("f1", summary.incumbent_f1, summary.residual_f1),
        ):
            print(
                f"    incumbent {label}: mean={incumbent.mean:.3f} median={incumbent.median:.3f}"
            )
            print(
                f"    residual  {label}: mean={residual.mean:.3f} median={residual.median:.3f}"
            )
        print(
            "    exact-match fraction: incumbent="
            f"{summary.incumbent_exact_match_fraction:.3f} residual="
            f"{summary.residual_exact_match_fraction:.3f}"
        )
        print(
            "    residual per-edge detection fraction: "
            f"{dict(sorted(summary.residual_per_edge_detection_fraction.items()))}"
        )


def main() -> int:
    results = run()
    _print_shape("linear", results["linear"])
    _print_shape("nonlinear", results["nonlinear"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
