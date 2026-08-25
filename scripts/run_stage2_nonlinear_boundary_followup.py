"""Narrow in on the nonlinear detectability boundary below coefficient=0.2.

Follow-up to docs/evidence/stage2-effect-strength-degradation-20260825.md,
which found the residual layer's per-edge detection on the pure
nonlinear fixture held at 100% for coefficient in {0.7, 0.4} and dropped
to 84% at coefficient=0.2, without pinning down where detection actually
starts to fail. This script re-runs the nonlinear fixture only, at
0.2 (rerun as an anchor point) plus three additional, weaker levels
(0.15, 0.1, 0.05).

Not a new Stage II dimension, not a Gate 0 study, no new redana source:
this reuses redana.benchmark.run_replicated_condition and
redana.scenarios.generate_stage1_nonlinear_fixture exactly as built for
Stage II round 1.
"""

from __future__ import annotations

from functools import partial

from redana.benchmark import ConditionResult, run_replicated_condition
from redana.network import NetworkConfig
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage1_nonlinear_fixture

_N_REPS = 50
_N_ROWS = 1000
_PERMUTATIONS = 199
_ALPHA = 0.05
_BASE_SEED = 20260825
_LEVELS = (("0.20", 0.20), ("0.15", 0.15), ("0.10", 0.10), ("0.05", 0.05))


def run() -> list[ConditionResult]:
    """Run the nonlinear fixture at each of the four boundary-narrowing levels."""

    residual_config = PrototypeConfig()
    network_config = NetworkConfig()
    results: list[ConditionResult] = []

    for level_name, coefficient in _LEVELS:
        condition_name = f"stage2-nonlinear-boundary-{level_name}"
        fixture_fn = partial(generate_stage1_nonlinear_fixture, coefficient=coefficient)
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
    print("== nonlinear fixture, narrowing the detectability boundary ==")
    for (level_name, coefficient), result in zip(_LEVELS, results, strict=True):
        summary = result.summary
        print(f"  -- coefficient={level_name} --")
        print(
            f"    residual precision: mean={summary.residual_precision.mean:.3f} "
            f"median={summary.residual_precision.median:.3f}"
        )
        print(
            f"    residual recall:    mean={summary.residual_recall.mean:.3f} "
            f"median={summary.residual_recall.median:.3f}"
        )
        print(f"    residual exact-match fraction: {summary.residual_exact_match_fraction:.3f}")
        print(
            "    residual per-edge detection fraction: "
            f"{dict(sorted(summary.residual_per_edge_detection_fraction.items()))}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
