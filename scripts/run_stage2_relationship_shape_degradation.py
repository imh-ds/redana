"""Run the Stage II round 2 relationship-shape degradation benchmark.

outline/plan.md section 6, scoped to exactly one of its remaining named
degradation dimensions this round: relationship shape, swept across four
levels (pure linear -> strong nonlinearity) at a fixed effect strength
(coefficient=0.7, Stage I's strong baseline). Not a Gate 0 study -- no
hash-pinned calibration, no per-replication artifact retention. Reuses
every Step 4 / Stage I / Stage II round 1 component unchanged except the
new `generate_stage2_shape_fixture` generator.
"""

from __future__ import annotations

from functools import partial

from redana.benchmark import ConditionResult, run_replicated_condition
from redana.network import NetworkConfig
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage2_shape_fixture

_N_REPS = 50
_N_ROWS = 1000
_PERMUTATIONS = 199
_ALPHA = 0.05
_BASE_SEED = 20260825
_COEFFICIENT = 0.7
_LEVELS = (
    ("pure_linear", 0.0),
    ("slight_curvature", 0.33),
    ("moderate_curvature", 0.67),
    ("strong_nonlinearity", 1.0),
)


def run() -> list[ConditionResult]:
    """Run all four relationship-shape conditions."""

    residual_config = PrototypeConfig()
    network_config = NetworkConfig()
    results: list[ConditionResult] = []

    for level_name, shape in _LEVELS:
        condition_name = f"stage2-shape-{level_name}"
        fixture_fn = partial(generate_stage2_shape_fixture, shape=shape, coefficient=_COEFFICIENT)
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
        results.append(result)

    return results


def main() -> int:
    results = run()
    print("== relationship-shape fixture across shape levels (coefficient=0.7) ==")
    for (level_name, shape), result in zip(_LEVELS, results, strict=True):
        summary = result.summary
        print(f"  -- {level_name} (shape={shape}) --")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
