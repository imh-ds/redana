"""Combine shard JSON outputs from run_stage3_faircompare_shard.py into a
single results table, and explicitly evaluate the predeclared pass/fail
decision rule per docs/superpowers/specs/2026-08-27-stage3-fair-matched-comparison-charter.md
Decision 2: a sample size passes if recovery among incumbent-missed edges
reaches >=25% for at least one of (X1,X4) or (X10,X7), AND mean added
spurious annotations <=1.5 per replication.

Usage: point this at a directory containing all downloaded shard artifacts
(searches recursively, matching scripts/aggregate_stability_validation.py's
layout handling).
"""

from __future__ import annotations

import argparse
import glob
import json

_N_ROWS_LEVELS = (200, 350, 500)
_SHARDS_PER_N_ROWS = 10
_MODERATE_EDGES = ("X1-X4", "X10-X7")
_RECOVERY_THRESHOLD = 0.25
_SPURIOUS_THRESHOLD = 1.5


def _edge_recovery(reps: list[dict], key: str) -> dict:
    eligible = [r["target_edges"][key]["missed_by_incumbent"] for r in reps]
    recovered = [
        r["target_edges"][key]["recovered_by_residual"]
        for r in reps
        if r["target_edges"][key]["missed_by_incumbent"]
    ]
    n_eligible = sum(eligible)
    return {
        "n_eligible": n_eligible,
        "n_recovered": sum(recovered),
        "recovery_rate": (sum(recovered) / n_eligible) if n_eligible else None,
    }


def _summarize(reps: list[dict]) -> dict:
    mean_spurious = sum(r["residual_spurious_count"] for r in reps) / len(reps)
    edge_summaries = {key: _edge_recovery(reps, key) for key in _TARGET_KEYS}

    moderate_pass = any(
        edge_summaries[key]["recovery_rate"] is not None
        and edge_summaries[key]["recovery_rate"] >= _RECOVERY_THRESHOLD
        for key in _MODERATE_EDGES
    )
    spurious_pass = mean_spurious <= _SPURIOUS_THRESHOLD
    decision = "PASS" if (moderate_pass and spurious_pass) else "FAIL"

    return {
        "n_reps": len(reps),
        "incumbent_precision": sum(r["incumbent_precision"] for r in reps) / len(reps),
        "incumbent_recall": sum(r["incumbent_recall"] for r in reps) / len(reps),
        "incumbent_f1": sum(r["incumbent_f1"] for r in reps) / len(reps),
        "mean_spurious": mean_spurious,
        "edges": edge_summaries,
        "decision": decision,
        "decision_reasoning": {
            "moderate_edge_recovery_pass": moderate_pass,
            "spurious_cost_pass": spurious_pass,
            "recovery_threshold": _RECOVERY_THRESHOLD,
            "spurious_threshold": _SPURIOUS_THRESHOLD,
        },
    }


_TARGET_KEYS = ("X1-X4", "X10-X7", "X1-X12")


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

    results = {"cells": []}
    for n_rows in _N_ROWS_LEVELS:
        reps = reps_by_n_rows.get(n_rows, [])
        if not reps:
            print(f"WARNING: no reps found for n_rows={n_rows}")
            continue
        summary = _summarize(reps)
        results["cells"].append({"n_rows": n_rows, "summary": summary})

        print(f"n_rows={n_rows} (n_reps={summary['n_reps']}): {summary['decision']}")
        print(
            f"  incumbent(P={summary['incumbent_precision']:.3f}, "
            f"R={summary['incumbent_recall']:.3f}) mean_spurious={summary['mean_spurious']:.3f}"
        )
        for key in _TARGET_KEYS:
            edge = summary["edges"][key]
            rate = edge["recovery_rate"]
            rate_str = f"{rate:.3f}" if rate is not None else "n/a"
            print(
                f"  {key}: recovery_rate={rate_str} "
                f"(n_recovered={edge['n_recovered']}/{edge['n_eligible']} eligible)"
            )

    with open("scripts/stage3_faircompare_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
