"""Combine shard JSON outputs from run_track2_threshold_shard.py into a
classification table and the resulting threshold recommendation.

Usage: point this at a directory containing all downloaded shard
artifacts (searches recursively, matching this project's established
aggregation-script pattern).
"""

from __future__ import annotations

import argparse
import glob
import json

_N_ROWS_LEVELS = (125, 150, 175, 200, 225, 250, 275)
_COEFFICIENT_LEVELS = (0.20, 0.7)
_DETECTION_GAIN_FLOOR = 0.05
_PRECISION_LOSS_FLOOR = -0.05


def classify(detection_improvement: float, precision_delta: float) -> str:
    if detection_improvement < _DETECTION_GAIN_FLOOR and precision_delta <= _PRECISION_LOSS_FLOOR:
        return "cost_present"
    return "safe"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shard_dir")
    args = parser.parse_args()

    shards = []
    for path in glob.glob(f"{args.shard_dir}/**/*.json", recursive=True):
        with open(path) as f:
            shards.append(json.load(f))

    by_key = {(s["arm"], s["n_rows"], s["coefficient"]): s for s in shards}

    expected = len(_N_ROWS_LEVELS) * len(_COEFFICIENT_LEVELS) * 2
    if len(shards) != expected:
        print(f"WARNING: expected {expected} shards, found {len(shards)}")

    results = {"cells": []}
    for coefficient in _COEFFICIENT_LEVELS:
        print(f"== coefficient={coefficient} ==")
        for n_rows in _N_ROWS_LEVELS:
            sensitive = by_key.get(("sensitive", n_rows, coefficient))
            normal = by_key.get(("normal", n_rows, coefficient))
            if sensitive is None or normal is None:
                print(f"  WARNING: missing shard(s) for n_rows={n_rows}")
                continue

            detection_improvement = sensitive["detection"] - normal["detection"]
            precision_delta = sensitive["precision"] - normal["precision"]
            classification = classify(detection_improvement, precision_delta)

            cell = {
                "n_rows": n_rows,
                "coefficient": coefficient,
                "sensitive": sensitive,
                "normal": normal,
                "detection_improvement": detection_improvement,
                "precision_delta": precision_delta,
                "classification": classification,
            }
            results["cells"].append(cell)
            print(
                f"  n_rows={n_rows}: sensitive(detection={sensitive['detection']:.3f}, "
                f"precision={sensitive['precision']:.3f}) normal(detection={normal['detection']:.3f}, "
                f"precision={normal['precision']:.3f}) "
                f"detection_improvement={detection_improvement:+.3f} "
                f"precision_delta={precision_delta:+.3f} -> {classification}"
            )

    strong_cells = [c for c in results["cells"] if c["coefficient"] == 0.7]
    safe_strong_n_rows = [c["n_rows"] for c in strong_cells if c["classification"] == "safe"]
    recommended_threshold = max(safe_strong_n_rows) if safe_strong_n_rows else None
    results["recommended_threshold"] = recommended_threshold

    print(f"\nSafe n_rows at coefficient=0.7: {sorted(safe_strong_n_rows)}")
    print(f"Recommended threshold (largest safe n_rows at coefficient=0.7): {recommended_threshold}")

    weak_cells = [c for c in results["cells"] if c["coefficient"] == 0.20]
    weak_cost_cells = [c for c in weak_cells if c["classification"] == "cost_present"]
    if weak_cost_cells:
        print(
            f"\nWARNING: coefficient=0.20 sanity check found cost at n_rows="
            f"{[c['n_rows'] for c in weak_cost_cells]} -- this contradicts prior evidence and "
            f"needs attention before updating the threshold."
        )
    else:
        print("\ncoefficient=0.20 sanity check: all points classified 'safe', as expected.")

    with open("scripts/track2_threshold_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
