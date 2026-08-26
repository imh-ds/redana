"""Combine shard JSON outputs from run_adaptive_selection_shard.py into a
per-cell, per-method accuracy table.

Usage: point this at a directory containing all downloaded shard
artifacts (searches recursively, matching the pattern used by
scripts/aggregate_stability_validation.py and
scripts/aggregate_track2_gap_narrowing.py).
"""

from __future__ import annotations

import argparse
import glob
import json

_N_ROWS_LEVELS = (100, 300, 500)
_COEFFICIENT_LEVELS = (0.15, 0.7)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shard_dir")
    args = parser.parse_args()

    shards = []
    for path in glob.glob(f"{args.shard_dir}/**/*.json", recursive=True):
        with open(path) as f:
            shards.append(json.load(f))

    by_cell = {(s["n_rows"], s["coefficient"]): s for s in shards}

    expected = len(_N_ROWS_LEVELS) * len(_COEFFICIENT_LEVELS)
    if len(shards) != expected:
        print(f"WARNING: expected {expected} shards, found {len(shards)}")

    results = {"cells": []}
    for n_rows in _N_ROWS_LEVELS:
        for coefficient in _COEFFICIENT_LEVELS:
            shard = by_cell.get((n_rows, coefficient))
            if shard is None:
                print(f"WARNING: missing shard for n_rows={n_rows} coefficient={coefficient}")
                continue

            ground_truth = shard["ground_truth"]
            arbiter_accuracy = sum(
                1 for pick in shard["arbiter_picks"] if pick == ground_truth
            ) / len(shard["arbiter_picks"])
            always_sensitive_accuracy = 1.0 if shard["always_sensitive_pick"] == ground_truth else 0.0
            always_normal_accuracy = 1.0 if shard["always_normal_pick"] == ground_truth else 0.0
            static_rule_accuracy = 1.0 if shard["static_rule_pick"] == ground_truth else 0.0

            cell = {
                "n_rows": n_rows,
                "coefficient": coefficient,
                "ground_truth": ground_truth,
                "arbiter_accuracy": arbiter_accuracy,
                "always_sensitive_accuracy": always_sensitive_accuracy,
                "always_normal_accuracy": always_normal_accuracy,
                "static_rule_accuracy": static_rule_accuracy,
            }
            results["cells"].append(cell)
            print(
                f"n_rows={n_rows} coefficient={coefficient} ground_truth={ground_truth}: "
                f"arbiter={arbiter_accuracy:.3f} always_sensitive={always_sensitive_accuracy:.1f} "
                f"always_normal={always_normal_accuracy:.1f} static_rule={static_rule_accuracy:.1f}"
            )

    if results["cells"]:
        mean_arbiter = sum(c["arbiter_accuracy"] for c in results["cells"]) / len(results["cells"])
        mean_static_rule = sum(c["static_rule_accuracy"] for c in results["cells"]) / len(
            results["cells"]
        )
        print(f"\nmean arbiter accuracy: {mean_arbiter:.3f}")
        print(f"mean static-rule accuracy: {mean_static_rule:.3f}")
        print(f"mean improvement (arbiter - static rule): {mean_arbiter - mean_static_rule:+.3f}")

    with open("scripts/adaptive_selection_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
