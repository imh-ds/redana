"""Track 2 dev-matrix sweep: mechanically select a (n_splits, alpha) combination.

Per docs/superpowers/specs/2026-08-26-track2-low-n-power-charter.md
(Decisions 1-4) and docs/superpowers/plans/2026-08-26-track2-low-n-power-levers.md
Task 1. Tests two cheap, parameter-only levers on the existing pipeline --
redana.residuals.PrototypeConfig.n_splits and the FDR alpha threshold --
at the four (n_rows, coefficient) cells where prior evidence
(docs/evidence/sample-size-dependence-20260825.md) showed the sharpest
detection collapse.

This is a *dev* matrix only: its purpose is to mechanically pick one
winning combination via the fixed selection rule below, not to report a
result. Its own numbers are never the study's reported finding -- that
comes from scripts/run_track2_final_evaluation.py, run on fresh,
independently-seeded data using whatever combination this script selects.
This separation exists specifically to satisfy outline/plan.md section 18
rule 3 ("no tuning on the same simulation matrix used for final
evaluation").

Selection rule (fixed before this script runs, per Decision 4): among all
9 (n_splits, alpha) combinations -- including (5, 0.05), the current
default, which always participates as the control anchor -- restrict to
those whose mean residual precision (averaged across the 4 cells) is no
more than 10 percentage points below the control's mean precision. Among
those eligible combinations, pick the one with the largest mean per-edge
detection improvement over control (also averaged across the 4 cells).
Because the control combination is always eligible (a 0-point precision
drop against itself never exceeds the 10pp floor), this mechanism always
selects *some* combination; if nothing beats control, the selected
combination simply equals control, and that is itself the reportable
outcome ("no combination improved on the default here"), not a failure
requiring special-casing.
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
_N_SPLITS_CANDIDATES = (2, 3, 5)
_ALPHA_CANDIDATES = (0.05, 0.10, 0.15)
_CONTROL = (5, 0.05)
_N_REPS = 10
_PERMUTATIONS = 199
_BASE_SEED = 20260825
_PRECISION_FLOOR_DROP = 0.10


def _run_cell(n_rows: int, coefficient: float, n_splits: int, alpha: float) -> tuple[float, float]:
    """Return (mean per-edge detection fraction, mean residual precision) for one cell."""

    fixture_fn = partial(generate_stage1_nonlinear_fixture, coefficient=coefficient)
    condition_name = f"track2-dev-n{n_rows}-c{coefficient}-splits{n_splits}-alpha{alpha}"
    result = run_replicated_condition(
        fixture_fn,
        condition_name=condition_name,
        n_reps=_N_REPS,
        n_rows=n_rows,
        residual_config=PrototypeConfig(n_splits=n_splits),
        network_config=NetworkConfig(),
        permutations=_PERMUTATIONS,
        alpha=alpha,
        base_seed=_BASE_SEED,
    )
    detection_values = list(result.summary.residual_per_edge_detection_fraction.values())
    mean_detection = sum(detection_values) / len(detection_values)
    mean_precision = result.summary.residual_precision.mean
    return mean_detection, mean_precision


def run_dev_matrix() -> dict:
    """Run all 9 combinations across all 4 cells; return per-combination cell results
    plus each combination's cross-cell mean detection and mean precision.
    """

    combinations = sorted(set(product(_N_SPLITS_CANDIDATES, _ALPHA_CANDIDATES)) | {_CONTROL})
    per_combination: dict[str, dict] = {}

    for n_splits, alpha in combinations:
        cells = {}
        for n_rows, coefficient in product(_N_ROWS_LEVELS, _COEFFICIENT_LEVELS):
            detection, precision = _run_cell(n_rows, coefficient, n_splits, alpha)
            cells[f"n{n_rows}_c{coefficient}"] = {"detection": detection, "precision": precision}

        mean_detection = sum(c["detection"] for c in cells.values()) / len(cells)
        mean_precision = sum(c["precision"] for c in cells.values()) / len(cells)
        per_combination[f"splits{n_splits}_alpha{alpha}"] = {
            "n_splits": n_splits,
            "alpha": alpha,
            "cells": cells,
            "mean_detection": mean_detection,
            "mean_precision": mean_precision,
        }

    return per_combination


def select_combination(per_combination: dict) -> dict:
    """Apply the fixed selection rule and return the winning combination's entry."""

    control_key = f"splits{_CONTROL[0]}_alpha{_CONTROL[1]}"
    control_precision = per_combination[control_key]["mean_precision"]
    control_detection = per_combination[control_key]["mean_detection"]

    eligible = [
        entry
        for entry in per_combination.values()
        if entry["mean_precision"] >= control_precision - _PRECISION_FLOOR_DROP
    ]

    winner = max(eligible, key=lambda entry: entry["mean_detection"])
    winner = dict(winner)
    winner["detection_improvement_over_control"] = winner["mean_detection"] - control_detection
    winner["precision_delta_vs_control"] = winner["mean_precision"] - control_precision
    winner["matches_control"] = (winner["n_splits"], winner["alpha"]) == _CONTROL
    return winner


def main() -> int:
    per_combination = run_dev_matrix()
    winner = select_combination(per_combination)

    output = {"combinations": per_combination, "selected": winner}
    with open("scripts/track2_dev_matrix_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Selected combination: n_splits={winner['n_splits']}, alpha={winner['alpha']}")
    print(f"  mean detection: {winner['mean_detection']:.3f}")
    print(f"  mean precision: {winner['mean_precision']:.3f}")
    print(f"  detection improvement over control: {winner['detection_improvement_over_control']:+.3f}")
    print(f"  precision delta vs control: {winner['precision_delta_vs_control']:+.3f}")
    print(f"  matches control (5, 0.05): {winner['matches_control']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
