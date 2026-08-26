"""Track 2 final evaluation: the selected combination vs. control, on fresh data.

Per docs/superpowers/specs/2026-08-26-track2-low-n-power-charter.md
(Decisions 1-4) and docs/superpowers/plans/2026-08-26-track2-low-n-power-levers.md
Task 2. Evaluates exactly one lever combination -- whatever
scripts/run_track2_dev_matrix.py selected (n_splits=2, alpha=0.15, from
scripts/track2_dev_matrix_results.json, committed in
4aa4192c "feat: add Track 2 dev-matrix sweep and selection") -- against
the current default (n_splits=5, alpha=0.05) as a control arm, at each of
the 4 target cells, using 50 reps per (cell, arm) -- matching every prior
round's replication count.

The selected combination is hardcoded here, not re-derived from the
dev-matrix script at runtime, to keep dev-matrix selection and final
evaluation as two cleanly separate steps: this script must not be able to
silently pick up a different selection if the dev matrix were ever rerun.

Condition names use a "track2-final-" prefix (distinct from the dev
matrix's "track2-dev-" prefix), so every seed here is independently drawn
from every dev-matrix seed -- this is fresh data, not a re-run of dev
data, per outline/plan.md section 18 rule 3.
"""

from __future__ import annotations

import json
from functools import partial
from itertools import product

from redana.benchmark import run_replicated_condition
from redana.network import NetworkConfig
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage1_nonlinear_fixture

_N_ROWS_LEVELS = (100, 200)
_COEFFICIENT_LEVELS = (0.15, 0.20)
_SELECTED = {"n_splits": 2, "alpha": 0.15}
_CONTROL = {"n_splits": 5, "alpha": 0.05}
_ARMS = {"selected": _SELECTED, "control": _CONTROL}
_N_REPS = 50
_PERMUTATIONS = 199
_BASE_SEED = 20260825
_DETECTION_BAR = 0.15
_PRECISION_FLOOR_DROP = 0.10


def _run_cell(arm_name: str, n_rows: int, coefficient: float) -> dict:
    arm = _ARMS[arm_name]
    fixture_fn = partial(generate_stage1_nonlinear_fixture, coefficient=coefficient)
    condition_name = f"track2-final-{arm_name}-n{n_rows}-c{coefficient}"
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
        "detection": mean_detection,
        "precision": result.summary.residual_precision.mean,
        "recall": result.summary.residual_recall.mean,
    }


def run_final_evaluation() -> dict:
    cells: dict[str, dict] = {}
    for n_rows, coefficient in product(_N_ROWS_LEVELS, _COEFFICIENT_LEVELS):
        cell_key = f"n{n_rows}_c{coefficient}"
        selected = _run_cell("selected", n_rows, coefficient)
        control = _run_cell("control", n_rows, coefficient)
        detection_improvement = selected["detection"] - control["detection"]
        precision_delta = selected["precision"] - control["precision"]
        cells[cell_key] = {
            "n_rows": n_rows,
            "coefficient": coefficient,
            "selected": selected,
            "control": control,
            "detection_improvement": detection_improvement,
            "precision_delta": precision_delta,
            "clears_bar": (
                detection_improvement >= _DETECTION_BAR
                and precision_delta >= -_PRECISION_FLOOR_DROP
            ),
        }
    return cells


def main() -> int:
    cells = run_final_evaluation()

    with open("scripts/track2_final_evaluation_results.json", "w") as f:
        json.dump(
            {"selected_arm": _SELECTED, "control_arm": _CONTROL, "cells": cells},
            f,
            indent=2,
        )

    print(f"Selected arm: {_SELECTED}  |  Control arm: {_CONTROL}")
    for cell_key, cell in cells.items():
        print(f"\n{cell_key}:")
        print(f"  selected: detection={cell['selected']['detection']:.3f} precision={cell['selected']['precision']:.3f}")
        print(f"  control:  detection={cell['control']['detection']:.3f} precision={cell['control']['precision']:.3f}")
        print(
            f"  detection improvement: {cell['detection_improvement']:+.3f}  "
            f"precision delta: {cell['precision_delta']:+.3f}  "
            f"clears bar (+{_DETECTION_BAR}/-{ _PRECISION_FLOOR_DROP}): {cell['clears_bar']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
