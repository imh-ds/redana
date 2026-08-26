"""One shard of the stability validation study.

Computes either a chunk of actual-replication reps or one bootstrap dataset's
stability, for one configuration, and writes the result as JSON. This lets a
GitHub Actions matrix job run each shard independently (each keeping
n_bootstrap=100, per docs/superpowers/specs/2026-08-26-stability-reporting-charter.md
Decision 1) instead of one long serial process, then
scripts/aggregate_stability_validation.py combines all shard outputs into the
same summary scripts/run_stability_validation.py prints.

Seed derivation is identical to run_stability_validation.py and
redana.benchmark.run_replicated_condition, so a given (config_label, index)
shard produces exactly the same dataset regardless of whether it runs here,
in the serial script, or as an isolated GitHub Actions job -- sharding does
not change what gets computed, only how the work is distributed.
"""

from __future__ import annotations

import argparse
import json

from redana.dependence import derive_seed
from redana.network import NetworkConfig
from redana.prototype import run_prototype
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage1_nonlinear_fixture
from redana.stability import bootstrap_edge_stability

_N_ROWS = 1000
_PERMUTATIONS = 199
_ALPHA = 0.05
_BASE_SEED = 20260825
_N_BOOTSTRAP = 100
_TRUE_EDGES = frozenset({("X1", "X2"), ("X3", "X4")})


def _edge_key(edge: tuple[str, str]) -> str:
    return ",".join(edge)


def run_actual_chunk(condition_name: str, coefficient: float, rep_indices: list[int]) -> dict:
    residual_config = PrototypeConfig()
    network_config = NetworkConfig()
    detected: dict[str, list[bool]] = {_edge_key(edge): [] for edge in _TRUE_EDGES}

    for index in rep_indices:
        seed = derive_seed("stage1", condition_name, index, _BASE_SEED)
        frame, _ = generate_stage1_nonlinear_fixture(_N_ROWS, seed, coefficient=coefficient)
        result = run_prototype(frame, residual_config, network_config, _PERMUTATIONS, _ALPHA, seed)
        found = {tuple(sorted(edge)) for edge in result.residual_edges}
        for edge in _TRUE_EDGES:
            detected[_edge_key(edge)].append(tuple(sorted(edge)) in found)

    return {
        "mode": "actual",
        "condition_name": condition_name,
        "rep_indices": rep_indices,
        "detected": detected,
    }


def run_bootstrap_dataset(condition_name: str, coefficient: float, dataset_index: int) -> dict:
    residual_config = PrototypeConfig()
    network_config = NetworkConfig()
    dataset_seed = derive_seed("stage1", condition_name, dataset_index, _BASE_SEED)
    frame, _ = generate_stage1_nonlinear_fixture(_N_ROWS, dataset_seed, coefficient=coefficient)
    stability = bootstrap_edge_stability(
        frame,
        residual_config,
        network_config,
        permutations=_PERMUTATIONS,
        alpha=_ALPHA,
        seed=dataset_seed,
        n_bootstrap=_N_BOOTSTRAP,
    )
    return {
        "mode": "bootstrap",
        "condition_name": condition_name,
        "dataset_index": dataset_index,
        "stability": {_edge_key(pair): value for pair, value in stability.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["actual", "bootstrap"], required=True)
    parser.add_argument("--config-label", required=True)
    parser.add_argument("--coefficient", type=float, required=True)
    parser.add_argument("--rep-start", type=int, default=0)
    parser.add_argument("--rep-count", type=int, default=0)
    parser.add_argument("--dataset-index", type=int, default=0)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    condition_name = f"stability-validation-{args.config_label}"

    if args.mode == "actual":
        rep_indices = list(range(args.rep_start, args.rep_start + args.rep_count))
        result = run_actual_chunk(condition_name, args.coefficient, rep_indices)
    else:
        result = run_bootstrap_dataset(condition_name, args.coefficient, args.dataset_index)

    with open(args.out, "w") as f:
        json.dump(result, f)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
