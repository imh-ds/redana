"""Combine shard JSON outputs from run_stage3_fdrcal_shard.py into a
single results table, and explicitly evaluate the predeclared
calibration decision rule per
docs/superpowers/specs/2026-08-27-stage3-fdr-calibration-charter.md:

Decision 2 (global null): passes if the pooled proportion of
replications (across all three n_rows) with at least one BH-FDR
rejection is <=0.12.

Decision 3 (mixed signal): passes if the mean empirical false discovery
proportion at n_rows=500 is <=0.10.

Decision 4: a fail on either condition invalidates the fair matched
comparison's n=500 PASS as usable evidence, pending its own fix -- it
does not retroactively change that PASS's own correctly-computed result.

Usage: point this at a directory containing all downloaded shard
artifacts (searches recursively).
"""

from __future__ import annotations

import argparse
import glob
import json

_NULL_N_ROWS_LEVELS = (200, 350, 500)
_MIXED_N_ROWS = 500
_SHARDS_PER_NULL_N_ROWS = 10
_SHARDS_PER_MIXED = 10
_NULL_THRESHOLD = 0.12
_MIXED_THRESHOLD = 0.10


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shard_dir")
    args = parser.parse_args()

    shards = []
    for path in glob.glob(f"{args.shard_dir}/**/*.json", recursive=True):
        with open(path) as f:
            shards.append(json.load(f))

    expected = len(_NULL_N_ROWS_LEVELS) * _SHARDS_PER_NULL_N_ROWS + _SHARDS_PER_MIXED
    if len(shards) != expected:
        print(f"WARNING: expected {expected} shards, found {len(shards)}")

    null_reps: list[dict] = []
    mixed_reps: list[dict] = []
    for shard in shards:
        if shard["condition"] == "null":
            null_reps.extend(shard["reps"])
        else:
            mixed_reps.extend(shard["reps"])

    results: dict = {}

    if null_reps:
        pooled_rejection_rate = sum(r["any_rejection"] for r in null_reps) / len(null_reps)
        null_decision = "PASS" if pooled_rejection_rate <= _NULL_THRESHOLD else "FAIL"
        results["global_null"] = {
            "n_reps": len(null_reps),
            "pooled_any_rejection_rate": pooled_rejection_rate,
            "threshold": _NULL_THRESHOLD,
            "decision": null_decision,
        }
        print(
            f"global_null (n_reps={len(null_reps)}): {null_decision} "
            f"(pooled any-rejection rate={pooled_rejection_rate:.3f}, threshold<={_NULL_THRESHOLD})"
        )
    else:
        print("WARNING: no null-condition reps found")

    if mixed_reps:
        mean_fdp = sum(r["false_discovery_proportion"] for r in mixed_reps) / len(mixed_reps)
        mixed_decision = "PASS" if mean_fdp <= _MIXED_THRESHOLD else "FAIL"
        results["mixed_signal"] = {
            "n_reps": len(mixed_reps),
            "n_rows": _MIXED_N_ROWS,
            "mean_false_discovery_proportion": mean_fdp,
            "threshold": _MIXED_THRESHOLD,
            "decision": mixed_decision,
        }
        print(
            f"mixed_signal n_rows={_MIXED_N_ROWS} (n_reps={len(mixed_reps)}): {mixed_decision} "
            f"(mean FDP={mean_fdp:.3f}, threshold<={_MIXED_THRESHOLD})"
        )
    else:
        print("WARNING: no mixed-condition reps found")

    if "global_null" in results and "mixed_signal" in results:
        both_pass = (
            results["global_null"]["decision"] == "PASS"
            and results["mixed_signal"]["decision"] == "PASS"
        )
        consequence = (
            "n=500 PASS remains usable evidence (both calibration conditions passed)."
            if both_pass
            else "n=500 PASS is INVALIDATED as usable evidence pending its own fix "
            "(at least one calibration condition failed) -- per charter Decision 4, "
            "this does not retroactively change the fair-comparison result itself."
        )
        results["consequence"] = consequence
        print(f"\nDecision 4 consequence: {consequence}")

    with open("scripts/stage3_fdrcal_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
