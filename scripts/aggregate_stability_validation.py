"""Combine shard JSON outputs from run_stability_validation_shard.py into the same
summary run_stability_validation.py prints when run serially.

Usage: point this at a directory containing all downloaded shard artifacts (the
GitHub Actions aggregation job downloads each shard's uploaded result.json into
its own subdirectory; this script searches recursively so that layout works
without extra flattening).
"""

from __future__ import annotations

import argparse
import glob
import json

from redana.stability import classify_stability_tier

_CONFIGURATIONS = (("well_powered", 0.7), ("marginal", 0.15))
_TRUE_EDGE_KEYS = ("X1,X2", "X3,X4")
_INCIDENTAL_KEY = "X5,X6"
_N_REPS = 50


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shard_dir")
    args = parser.parse_args()

    shards = []
    for path in glob.glob(f"{args.shard_dir}/**/*.json", recursive=True):
        with open(path) as f:
            shards.append(json.load(f))

    for label, coefficient in _CONFIGURATIONS:
        condition_name = f"stability-validation-{label}"
        print(f"== {label} (coefficient={coefficient}, n_rows=1000) ==")

        actual_shards = [
            s for s in shards if s["mode"] == "actual" and s["condition_name"] == condition_name
        ]
        detected_by_edge: dict[str, list[bool]] = {key: [] for key in _TRUE_EDGE_KEYS}
        for shard in actual_shards:
            for key, values in shard["detected"].items():
                detected_by_edge[key].extend(values)

        total_reps = len(detected_by_edge[_TRUE_EDGE_KEYS[0]])
        if total_reps != _N_REPS:
            print(f"  WARNING: expected {_N_REPS} actual-replication reps, found {total_reps}")

        detection_fraction = {
            key: (sum(values) / len(values) if values else None)
            for key, values in detected_by_edge.items()
        }
        print(
            f"  actual replication ({total_reps} datasets), "
            f"per-edge detection fraction: {detection_fraction}"
        )

        bootstrap_shards = sorted(
            (
                s
                for s in shards
                if s["mode"] == "bootstrap" and s["condition_name"] == condition_name
            ),
            key=lambda s: s["dataset_index"],
        )

        if not bootstrap_shards:
            print(f"  WARNING: no bootstrap shards found for {condition_name} -- skipping stability section")
            continue

        for key in _TRUE_EDGE_KEYS:
            values = [s["stability"][key] for s in bootstrap_shards]
            tiers = [classify_stability_tier(v) for v in values]
            print(f"  true edge {key}: mean bootstrap stability={_mean(values):.3f}")
            print(f"    per-dataset stability values: {[round(v, 3) for v in values]}")
            print(
                f"    tier distribution: core={tiers.count('core')} "
                f"provisional={tiers.count('provisional')} background={tiers.count('background')}"
            )

        incidental_values = [s["stability"][_INCIDENTAL_KEY] for s in bootstrap_shards]
        print(
            f"  incidental non-edge {_INCIDENTAL_KEY}: "
            f"mean bootstrap stability={_mean(incidental_values):.3f}"
        )
        print(f"    per-dataset stability values: {[round(v, 3) for v in incidental_values]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
