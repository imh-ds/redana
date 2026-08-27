"""Combine shard JSON outputs from run_stage3_permdiag_shard.py into a
single results table.

Usage: point this at a directory containing all downloaded shard artifacts
(searches recursively, matching scripts/aggregate_stability_validation.py's
layout handling).
"""

from __future__ import annotations

import argparse
import glob
import json

_CONFIGS = ("A", "B_baseline", "B_targeted")
_N_ROWS_LEVELS = (200, 350, 500)
_SHARDS_PER_CELL = 10
_NONLINEAR_EDGE_KEYS = ("X1-X4", "X10-X7", "X1-X12")


def _rate(values: list[bool]) -> float:
    return sum(values) / len(values) if values else float("nan")


def _summarize(reps: list[dict]) -> dict:
    per_edge = {}
    for key in _NONLINEAR_EDGE_KEYS:
        present = [r["nonlinear_edges"][key] for r in reps if key in r["nonlinear_edges"]]
        if not present:
            continue
        oracle_values = [e["oracle_bh_significant"] for e in present if e["oracle_bh_significant"] is not None]
        per_edge[key] = {
            "n_reps_present": len(present),
            "raw_power": _rate([e["raw_significant"] for e in present]),
            "full_family_bh_power": _rate([e["full_family_bh_significant"] for e in present]),
            "oracle_bh_power": _rate(oracle_values) if oracle_values else None,
        }

    return {
        "n_reps": len(reps),
        "m": reps[0]["m"] if reps else None,
        "mean_full_family_bh_rejections": (
            sum(r["full_family_bh_rejections"] for r in reps) / len(reps) if reps else None
        ),
        "mean_min_p_value": (
            sum(r["min_p_value"] for r in reps) / len(reps) if reps else None
        ),
        "nonlinear_edges": per_edge,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shard_dir")
    args = parser.parse_args()

    shards = []
    for path in glob.glob(f"{args.shard_dir}/**/*.json", recursive=True):
        with open(path) as f:
            shards.append(json.load(f))

    expected = len(_CONFIGS) * len(_N_ROWS_LEVELS) * _SHARDS_PER_CELL
    if len(shards) != expected:
        print(f"WARNING: expected {expected} shards, found {len(shards)}")

    reps_by_cell: dict[tuple[str, int], list[dict]] = {
        (config, n_rows): [] for config in _CONFIGS for n_rows in _N_ROWS_LEVELS
    }
    for shard in shards:
        key = (shard["config"], shard["n_rows"])
        reps_by_cell.setdefault(key, []).extend(shard["reps"])

    results = {"cells": []}
    for config in _CONFIGS:
        for n_rows in _N_ROWS_LEVELS:
            reps = reps_by_cell.get((config, n_rows), [])
            if not reps:
                print(f"WARNING: no reps found for config={config} n_rows={n_rows}")
                continue
            summary = _summarize(reps)
            results["cells"].append({"config": config, "n_rows": n_rows, "summary": summary})
            print(f"config={config} n_rows={n_rows} (m={summary['m']}, n_reps={summary['n_reps']}):")
            for key, edge_summary in summary["nonlinear_edges"].items():
                print(
                    f"  {key}: raw_power={edge_summary['raw_power']:.3f} "
                    f"full_family_bh_power={edge_summary['full_family_bh_power']:.3f} "
                    f"oracle_bh_power={edge_summary['oracle_bh_power']}"
                )

    with open("scripts/stage3_permdiag_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
