"""Establish ground truth for the previously-untested (n=100, coefficient=0.7) cell.

Per docs/superpowers/plans/2026-08-26-track2-adaptive-selection.md
Task 1. Every prior Track 2 study tested coefficient=0.7 (well-powered)
only at n_rows in {300, 500, 700, 1000}, and coefficient in {0.15, 0.20}
(weak) at n_rows in {100, 200, 300, 500, 700} -- n_rows=100 with
coefficient=0.7 specifically was never run. This script fills that gap
with the same 50-rep-per-arm methodology used throughout Track 2, so the
adaptive-selection study (Task 3) has a real ground-truth answer to score
against at this cell rather than an extrapolated guess.
"""

from __future__ import annotations

from functools import partial

from redana.benchmark import run_replicated_condition
from redana.network import NetworkConfig
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage1_nonlinear_fixture

_N_ROWS = 100
_COEFFICIENT = 0.7
_ARMS = {
    "sensitive": {"n_splits": 2, "alpha": 0.15},
    "normal": {"n_splits": 5, "alpha": 0.05},
}
_N_REPS = 50
_PERMUTATIONS = 199
_BASE_SEED = 20260825
_DETECTION_BAR = 0.15
_PRECISION_FLOOR_DROP = 0.10


def run_arm(arm_name: str) -> dict:
    arm = _ARMS[arm_name]
    fixture_fn = partial(generate_stage1_nonlinear_fixture, coefficient=_COEFFICIENT)
    condition_name = f"adaptive-groundtruth-{arm_name}-n{_N_ROWS}-c{_COEFFICIENT}"
    result = run_replicated_condition(
        fixture_fn,
        condition_name=condition_name,
        n_reps=_N_REPS,
        n_rows=_N_ROWS,
        residual_config=PrototypeConfig(n_splits=arm["n_splits"]),
        network_config=NetworkConfig(),
        permutations=_PERMUTATIONS,
        alpha=arm["alpha"],
        base_seed=_BASE_SEED,
    )
    detection_values = list(result.summary.residual_per_edge_detection_fraction.values())
    mean_detection = sum(detection_values) / len(detection_values)
    return {
        "detection": mean_detection,
        "precision": result.summary.residual_precision.mean,
        "recall": result.summary.residual_recall.mean,
    }


def main() -> int:
    sensitive = run_arm("sensitive")
    normal = run_arm("normal")

    detection_improvement = sensitive["detection"] - normal["detection"]
    precision_delta = sensitive["precision"] - normal["precision"]
    sensitive_wins = (
        detection_improvement >= _DETECTION_BAR and precision_delta >= -_PRECISION_FLOOR_DROP
    )

    print(f"n_rows={_N_ROWS} coefficient={_COEFFICIENT}")
    print(f"  sensitive: detection={sensitive['detection']:.3f} precision={sensitive['precision']:.3f} recall={sensitive['recall']:.3f}")
    print(f"  normal:    detection={normal['detection']:.3f} precision={normal['precision']:.3f} recall={normal['recall']:.3f}")
    print(f"  detection improvement (sensitive - normal): {detection_improvement:+.3f}")
    print(f"  precision delta (sensitive - normal): {precision_delta:+.3f}")
    print(f"  objectively better (by Track 2's own +{_DETECTION_BAR}/-{_PRECISION_FLOOR_DROP} bar): "
          f"{'sensitive' if sensitive_wins else 'normal'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
