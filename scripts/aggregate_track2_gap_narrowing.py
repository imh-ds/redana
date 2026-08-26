"""Combine shard JSON outputs from run_track2_gap_narrowing_shard.py into a
single results table.

Usage: point this at a directory containing all downloaded shard
artifacts (searches recursively, matching
scripts/aggregate_stability_validation.py's layout handling).
"""

from __future__ import annotations

import argparse
import glob
import json

_N_ROWS_LEVELS = (300, 500, 700)
_COEFFICIENT_LEVELS = (0.15, 0.20, 0.7)


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
    for n_rows in _N_ROWS_LEVELS:
        for coefficient in _COEFFICIENT_LEVELS:
            selected = by_key.get(("selected", n_rows, coefficient))
            control = by_key.get(("control", n_rows, coefficient))
            if selected is None or control is None:
                print(f"WARNING: missing shard(s) for n_rows={n_rows} coefficient={coefficient}")
                continue

            detection_improvement = selected["detection"] - control["detection"]
            precision_delta = selected["precision"] - control["precision"]
            cell = {
                "n_rows": n_rows,
                "coefficient": coefficient,
                "selected": selected,
                "control": control,
                "detection_improvement": detection_improvement,
                "precision_delta": precision_delta,
            }
            results["cells"].append(cell)
            print(
                f"n_rows={n_rows} coefficient={coefficient}: "
                f"selected(detection={selected['detection']:.3f}, precision={selected['precision']:.3f}) "
                f"control(detection={control['detection']:.3f}, precision={control['precision']:.3f}) "
                f"detection_improvement={detection_improvement:+.3f} precision_delta={precision_delta:+.3f}"
            )

    with open("scripts/track2_gap_narrowing_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
