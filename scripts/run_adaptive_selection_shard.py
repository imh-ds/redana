"""One shard of the adaptive-selection evaluation: one (n_rows, coefficient)
cell, 30 reps of the held-out-consistency arbiter plus the three
deterministic baseline picks, written as JSON.

Per docs/superpowers/specs/2026-08-26-track2-adaptive-selection-charter.md
and docs/superpowers/plans/2026-08-26-track2-adaptive-selection.md
Task 3. Ground truth per cell is either already published
(docs/evidence/track2-low-n-power-levers-20260826.md,
docs/evidence/track2-gap-narrowing-20260826.md) or, for the previously-
untested (n_rows=100, coefficient=0.7) cell, established fresh in Task 1
(scripts/run_adaptive_selection_ground_truth.py,
scripts/adaptive_selection_ground_truth_n100_c0.7.json).
"""

from __future__ import annotations

import argparse
import json

from redana.arbiter import select_configuration
from redana.dependence import derive_seed
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage1_nonlinear_fixture

_N_REPS = 30
_PERMUTATIONS = 199
_BASE_SEED = 20260825
_CANDIDATES = {
    "normal": (PrototypeConfig(n_splits=5), 0.05),
    "sensitive": (PrototypeConfig(n_splits=2), 0.15),
}
_STATIC_RULE_THRESHOLD = 200

# (n_rows, coefficient) -> objectively-better configuration, per already-
# published evidence notes (see module docstring) plus this study's own
# Task 1 for the one cell that was previously untested.
_GROUND_TRUTH = {
    (100, 0.15): "sensitive",
    (100, 0.7): "sensitive",
    (300, 0.15): "sensitive",
    (300, 0.7): "normal",
    (500, 0.15): "sensitive",
    (500, 0.7): "normal",
}


def static_rule_pick(n_rows: int) -> str:
    return "sensitive" if n_rows <= _STATIC_RULE_THRESHOLD else "normal"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-rows", type=int, required=True)
    parser.add_argument("--coefficient", type=float, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    n_rows = args.n_rows
    coefficient = args.coefficient
    ground_truth = _GROUND_TRUTH[(n_rows, coefficient)]
    condition_name = f"adaptive-selection-n{n_rows}-c{coefficient}"

    arbiter_picks = []
    for index in range(_N_REPS):
        seed = derive_seed("stage1", condition_name, index, _BASE_SEED)
        frame, _ = generate_stage1_nonlinear_fixture(n_rows, seed, coefficient=coefficient)
        result = select_configuration(frame, _CANDIDATES, permutations=_PERMUTATIONS, seed=seed)
        arbiter_picks.append(result.selected)

    output = {
        "n_rows": n_rows,
        "coefficient": coefficient,
        "ground_truth": ground_truth,
        "always_sensitive_pick": "sensitive",
        "always_normal_pick": "normal",
        "static_rule_pick": static_rule_pick(n_rows),
        "arbiter_picks": arbiter_picks,
    }

    with open(args.out, "w") as f:
        json.dump(output, f)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
