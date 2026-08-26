"""One shard of the Track 2 gap-narrowing study: one (n_rows, coefficient, arm)
cell, 50 reps, written as JSON.

Per docs/superpowers/specs/2026-08-26-track2-gap-narrowing-addendum.md.
Both arms are already fixed (not tuned here) -- this script only
evaluates them at new points in the untested n_rows=200-to-1,000 gap, via
a GitHub Actions matrix job per cell/arm, mirroring the sharding pattern
from docs/evidence/stability-validation-20260826.md's compute note.
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
    "selected": {"n_splits": 2, "alpha": 0.15},
    "control": {"n_splits": 5, "alpha": 0.05},
}


def run_cell(arm_name: str, n_rows: int, coefficient: float) -> dict:
    arm = _ARMS[arm_name]
    fixture_fn = partial(generate_stage1_nonlinear_fixture, coefficient=coefficient)
    condition_name = f"track2-gap-{arm_name}-n{n_rows}-c{coefficient}"
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
    parser.add_argument("--arm", choices=["selected", "control"], required=True)
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
