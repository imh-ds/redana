"""Combine shard JSON outputs from run_stage3_round1_shard.py into a single
results table.

Usage: point this at a directory containing all downloaded shard artifacts
(searches recursively, matching scripts/aggregate_stability_validation.py's
layout handling).
"""

from __future__ import annotations

import argparse
import glob
import json

_N_ROWS_LEVELS = (200, 500, 1000)
_SHARDS_PER_N_ROWS = 5


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _summarize(reps: list[dict]) -> dict:
    recovery_rates = [r["recovery_rate"] for r in reps if r["recovery_rate"] is not None]
    return {
        "n_reps": len(reps),
        "incumbent_precision": _mean([r["incumbent_precision"] for r in reps]),
        "incumbent_recall": _mean([r["incumbent_recall"] for r in reps]),
        "incumbent_f1": _mean([r["incumbent_f1"] for r in reps]),
        "residual_precision": _mean([r["residual_precision"] for r in reps]),
        "residual_recall": _mean([r["residual_recall"] for r in reps]),
        "residual_f1": _mean([r["residual_f1"] for r in reps]),
        "mean_recovery_rate": _mean(recovery_rates) if recovery_rates else None,
        "recovery_rate_n_eligible_reps": len(recovery_rates),
        "mean_residual_spurious_count": _mean([r["residual_spurious_count"] for r in reps]),
        "incumbent_auprc": _mean([r["incumbent_auprc"] for r in reps]),
        "residual_auprc": _mean([r["residual_auprc"] for r in reps]),
        "incumbent_precision_at_matched_fpr": _mean(
            [r["incumbent_precision_at_matched_fpr"] for r in reps]
        ),
        "residual_precision_at_matched_fpr": _mean(
            [r["residual_precision_at_matched_fpr"] for r in reps]
        ),
        "redundant_pair_flag_rate_incumbent": _mean(
            [float(r["redundant_pair_flagged_incumbent"]) for r in reps]
        ),
        "redundant_pair_flag_rate_residual": _mean(
            [float(r["redundant_pair_flagged_residual"]) for r in reps]
        ),
        "mean_isolated_false_positives_incumbent": _mean(
            [r["isolated_false_positives_incumbent"] for r in reps]
        ),
        "mean_isolated_false_positives_residual": _mean(
            [r["isolated_false_positives_residual"] for r in reps]
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shard_dir")
    args = parser.parse_args()

    shards = []
    for path in glob.glob(f"{args.shard_dir}/**/*.json", recursive=True):
        with open(path) as f:
            shards.append(json.load(f))

    expected = len(_N_ROWS_LEVELS) * _SHARDS_PER_N_ROWS
    if len(shards) != expected:
        print(f"WARNING: expected {expected} shards, found {len(shards)}")

    reps_by_n_rows: dict[int, list[dict]] = {n: [] for n in _N_ROWS_LEVELS}
    for shard in shards:
        reps_by_n_rows.setdefault(shard["n_rows"], []).extend(shard["reps"])

    results = {"conditions": []}
    for n_rows in _N_ROWS_LEVELS:
        reps = reps_by_n_rows.get(n_rows, [])
        if not reps:
            print(f"WARNING: no reps found for n_rows={n_rows}")
            continue
        summary = _summarize(reps)
        results["conditions"].append({"n_rows": n_rows, "summary": summary})
        print(
            f"n_rows={n_rows} (n_reps={summary['n_reps']}): "
            f"incumbent(P={summary['incumbent_precision']:.3f}, R={summary['incumbent_recall']:.3f}) "
            f"residual(P={summary['residual_precision']:.3f}, R={summary['residual_recall']:.3f}) "
            f"recovery_of_incumbent_misses={summary['mean_recovery_rate']} "
            f"(n_eligible={summary['recovery_rate_n_eligible_reps']}) "
            f"mean_spurious={summary['mean_residual_spurious_count']:.3f} "
            f"AUPRC(incumbent={summary['incumbent_auprc']:.3f}, residual={summary['residual_auprc']:.3f}) "
            f"P@matchedFPR(incumbent={summary['incumbent_precision_at_matched_fpr']:.3f}, "
            f"residual={summary['residual_precision_at_matched_fpr']:.3f})"
        )

    with open("scripts/stage3_round1_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
