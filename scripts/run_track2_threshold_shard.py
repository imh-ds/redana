"""One shard of the threshold-justification bracketing grid: one
(n_rows, coefficient, arm) cell, 50 reps, written as JSON.

Per docs/superpowers/specs/2026-08-26-track2-threshold-justification-charter.md
and docs/superpowers/plans/2026-08-26-track2-threshold-justification.md
Task 1. Brackets the strong-coefficient crossover between the known
safe point (n_rows=100) and the known costly point (n_rows=300) at
25-row resolution, plus a coefficient=0.20 sanity check at the same
points.
"""

from __future__ import annotations

import argparse
import json
from functools import partial

from redana.benchmark import run_replicated_condition
from redana.network import NetworkConfig
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage1_nonlinear_fixture

_N_REPS = 50
_PERMUTATIONS = 199
_BASE_SEED = 20260825
_ARMS = {
    "sensitive": {"n_splits": 2, "alpha": 0.15},
    "normal": {"n_splits": 5, "alpha": 0.05},
}


def run_cell(arm_name: str, n_rows: int, coefficient: float) -> dict:
    arm = _ARMS[arm_name]
    fixture_fn = partial(generate_stage1_nonlinear_fixture, coefficient=coefficient)
    condition_name = f"track2-threshold-{arm_name}-n{n_rows}-c{coefficient}"
    result = run_replicated_condition(
        fixture_fn,
        condition_name=condition_name,
        n_reps=_N_REPS,
        n_rows=n_rows,
        residual_config=PrototypeConfig(n_splits=arm["n_splits"]),
        network_config=NetworkConfig(),
        permutations=_PERMUTATIONS,
        alpha=arm["alpha"],
        base_seed=_BASE_SEED,
    )
    detection_values = list(result.summary.residual_per_edge_detection_fraction.values())
    mean_detection = sum(detection_values) / len(detection_values)
    return {
        "arm": arm_name,
        "n_rows": n_rows,
        "coefficient": coefficient,
        "detection": mean_detection,
        "precision": result.summary.residual_precision.mean,
        "recall": result.summary.residual_recall.mean,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=["sensitive", "normal"], required=True)
    parser.add_argument("--n-rows", type=int, required=True)
    parser.add_argument("--coefficient", type=float, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    result = run_cell(args.arm, args.n_rows, args.coefficient)

    with open(args.out, "w") as f:
        json.dump(result, f)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
