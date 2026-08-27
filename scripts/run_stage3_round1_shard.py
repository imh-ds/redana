"""One shard of the Stage III round 1 hybrid benchmark: one (n_rows, rep-chunk)
cell, 10 reps, written as JSON.

Per docs/superpowers/plans/2026-08-27-stage3-hybrid-benchmark-round1.md
Task 3. Runs both the incumbent linear network and the residual-dependence
prototype on the same datasets, computing protocol A (native-workflow
score_edges), the primary project-specific metric (recovery among
incumbent-missed true edges, spurious annotations among non-true pairs),
and protocol B (AUPRC + matched-FPR precision, via redana.fairness) for
both methods. Uses the project's existing default settings unchanged, per
the charter's explicit scope note -- redana.defaults.recommended_settings
is not applied here even at n_rows=200.
"""

from __future__ import annotations

import argparse
import json
from itertools import combinations

from redana.dependence import derive_seed
from redana.fairness import average_precision, precision_at_matched_fpr
from redana.network import NetworkConfig
from redana.prototype import run_prototype
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage3_hybrid_fixture
from redana.scoring import score_edges

_REPS_PER_SHARD = 10
_PERMUTATIONS = 199
_ALPHA = 0.05
_BASE_SEED = 20260827
_TARGET_FPR = 0.1
_REDUNDANT_PAIR = tuple(sorted(("X1", "X5")))
_ISOLATED_NODES = {"X6", "X11"}


def _canonical(edges) -> set[tuple[str, str]]:
    return {tuple(sorted(edge)) for edge in edges}


def _touches_isolated(edge: tuple[str, str]) -> bool:
    return bool(set(edge) & _ISOLATED_NODES)


def run_replication(n_rows: int, rep_index: int) -> dict:
    condition_name = f"stage3-round1-n{n_rows}"
    seed = derive_seed("stage3", condition_name, rep_index, _BASE_SEED)
    frame, true_linear_edges, true_nonlinear_edges = generate_stage3_hybrid_fixture(n_rows, seed)
    true_edges = _canonical(true_linear_edges | true_nonlinear_edges)

    residual_config = PrototypeConfig()
    network_config = NetworkConfig()
    result = run_prototype(frame, residual_config, network_config, _PERMUTATIONS, _ALPHA, seed)

    incumbent_edges = _canonical(result.incumbent.edges)
    residual_edges = _canonical(result.residual_edges)

    incumbent_score = score_edges(true_edges, incumbent_edges)
    residual_score = score_edges(true_edges, residual_edges)

    missed_by_incumbent = true_edges - incumbent_edges
    recovered_by_residual = missed_by_incumbent & residual_edges
    recovery_rate = (
        len(recovered_by_residual) / len(missed_by_incumbent) if missed_by_incumbent else None
    )
    residual_spurious = residual_edges - true_edges

    columns = list(frame.columns)
    all_pairs = {tuple(sorted(pair)) for pair in combinations(columns, 2)}
    incumbent_scores = {
        pair: abs(result.incumbent.partial_correlation.loc[pair[0], pair[1]])
        for pair in all_pairs
    }
    residual_scores = {
        tuple(sorted((stat.left, stat.right))): stat.p_value for stat in result.pair_statistics
    }

    incumbent_auprc = average_precision(
        incumbent_scores, true_edges, higher_is_more_significant=True
    )
    residual_auprc = average_precision(
        residual_scores, true_edges, higher_is_more_significant=False
    )
    incumbent_precision_at_fpr = precision_at_matched_fpr(
        incumbent_scores, true_edges, all_pairs, _TARGET_FPR, higher_is_more_significant=True
    )
    residual_precision_at_fpr = precision_at_matched_fpr(
        residual_scores, true_edges, all_pairs, _TARGET_FPR, higher_is_more_significant=False
    )

    return {
        "n_rows": n_rows,
        "rep_index": rep_index,
        "incumbent_precision": incumbent_score.precision,
        "incumbent_recall": incumbent_score.recall,
        "incumbent_f1": incumbent_score.f1,
        "residual_precision": residual_score.precision,
        "residual_recall": residual_score.recall,
        "residual_f1": residual_score.f1,
        "missed_by_incumbent_count": len(missed_by_incumbent),
        "recovered_by_residual_count": len(recovered_by_residual),
        "recovery_rate": recovery_rate,
        "residual_spurious_count": len(residual_spurious),
        "incumbent_auprc": incumbent_auprc,
        "residual_auprc": residual_auprc,
        "incumbent_precision_at_matched_fpr": incumbent_precision_at_fpr,
        "residual_precision_at_matched_fpr": residual_precision_at_fpr,
        "redundant_pair_flagged_incumbent": _REDUNDANT_PAIR in incumbent_edges,
        "redundant_pair_flagged_residual": _REDUNDANT_PAIR in residual_edges,
        "isolated_false_positives_incumbent": sum(
            1 for e in incumbent_edges if _touches_isolated(e)
        ),
        "isolated_false_positives_residual": sum(
            1 for e in residual_edges if _touches_isolated(e)
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-rows", type=int, required=True)
    parser.add_argument("--rep-chunk", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rep_start = args.rep_chunk * _REPS_PER_SHARD
    reps = [
        run_replication(args.n_rows, rep_index)
        for rep_index in range(rep_start, rep_start + _REPS_PER_SHARD)
    ]

    with open(args.out, "w") as f:
        json.dump({"n_rows": args.n_rows, "rep_chunk": args.rep_chunk, "reps": reps}, f)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
