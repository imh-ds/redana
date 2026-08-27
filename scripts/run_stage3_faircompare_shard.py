"""One shard of the fair matched incumbent-vs-redana comparison: one
(n_rows, rep-chunk) cell, 5 reps, written as JSON.

Per docs/superpowers/plans/2026-08-27-stage3-fair-matched-comparison.md
Task 1. Runs the current, actually-deployable redana workflow (default
adjustment behavior, permutations=1999 -- the one confirmed-safe fix from
the permutation-resolution diagnostic; no proxy exclusion, no clustering)
paired against the incumbent on the identical dataset via
redana.prototype.run_prototype, which fits both on the same frame
internally. This directly answers the gap prior rounds left open: no
study before this one reran the incumbent under the same, current
conditions as redana's fixed measurement setup.

Corrected 2026-08-27. The original version's FAIL-at-all-three-`n_rows`
result was reported to the project owner as a firm, predeclared stop
signal; independent peer review caught the scoring error described below
only afterward, on a later review pass. The original cost metric
(``len(residual_edges - true_edges)``) did not match the charter's own
definition ("spurious annotations the residual layer adds *beyond the
incumbent's own false positives*") -- it counted every residual edge
outside the declared true-edge set, including ones the incumbent already
flags, and it treated (X1, X5) as a false edge despite the
permutation-resolution diagnostic's correction that X1-X5 is a real,
constructed relationship (X5 = 0.85*X1 + noise), not a false positive.
Both are fixed here: (X1, X5) is now treated as real for scoring
purposes (affecting incumbent precision/recall too, for consistency),
and the cost metric now only counts residual false positives the
incumbent did not already flag.

Refactored 2026-08-27, per independent peer review's further
refinements: the local ``(X1, X5)`` patch is replaced with
``redana.scenarios.stage3_hybrid_scoring_true_edges`` (a single, shared,
documented definition, so future scripts can't reintroduce the same
scoring bug by hand-rolling their own patch), and a second cost metric
is now reported alongside the existing one. ``residual_spurious_count``
(unchanged, the metric the fair-comparison decision rule actually uses)
answers "how many false edges does the *combined* incumbent+redana
network gain from adding redana" -- the metric appropriate for a
combined-workflow claim. The new ``residual_total_false_positive_count``
answers a different, also-real question: "how many false annotations
does the residual layer produce in total," including ones already
present in the incumbent's own output -- closer to what a researcher
might care about if a residual annotation changes how they read an
existing incumbent edge, even when it doesn't add a *new* edge to the
combined network. Reporting both, clearly labeled, avoids the ambiguity
of collapsing them into one "spurious annotations" number.
"""

from __future__ import annotations

import argparse
import json

from redana.dependence import derive_seed
from redana.network import NetworkConfig
from redana.prototype import run_prototype
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage3_hybrid_fixture, stage3_hybrid_scoring_true_edges
from redana.scoring import score_edges

_REPS_PER_SHARD = 5
_PERMUTATIONS = 1999
_ALPHA = 0.05
_BASE_SEED = 20260827
_TARGET_EDGES = {
    "X1-X4": ("X1", "X4"),
    "X10-X7": ("X10", "X7"),
    "X1-X12": ("X1", "X12"),
}


def _canonical(edges) -> set[tuple[str, str]]:
    return {tuple(sorted(edge)) for edge in edges}


def run_replication(n_rows: int, rep_index: int) -> dict:
    condition_name = f"stage3-faircompare-n{n_rows}"
    seed = derive_seed("stage3-faircompare", condition_name, rep_index, _BASE_SEED)
    frame, true_linear, true_nonlinear = generate_stage3_hybrid_fixture(n_rows, seed)
    scoring_true_edges = _canonical(stage3_hybrid_scoring_true_edges(true_linear, true_nonlinear))

    result = run_prototype(frame, PrototypeConfig(), NetworkConfig(), _PERMUTATIONS, _ALPHA, seed)
    incumbent_edges = _canonical(result.incumbent.edges)
    residual_edges = _canonical(result.residual_edges)

    incumbent_score = score_edges(scoring_true_edges, incumbent_edges)
    incumbent_false_positives = incumbent_edges - scoring_true_edges
    residual_false_positives = residual_edges - scoring_true_edges
    residual_spurious_count = len(residual_false_positives - incumbent_false_positives)
    residual_total_false_positive_count = len(residual_false_positives)

    target_results = {}
    for key, edge in _TARGET_EDGES.items():
        canonical_edge = tuple(sorted(edge))
        missed_by_incumbent = canonical_edge not in incumbent_edges
        recovered_by_residual = missed_by_incumbent and canonical_edge in residual_edges
        target_results[key] = {
            "missed_by_incumbent": missed_by_incumbent,
            "recovered_by_residual": recovered_by_residual,
        }

    return {
        "n_rows": n_rows,
        "rep_index": rep_index,
        "incumbent_precision": incumbent_score.precision,
        "incumbent_recall": incumbent_score.recall,
        "incumbent_f1": incumbent_score.f1,
        "residual_spurious_count": residual_spurious_count,
        "residual_total_false_positive_count": residual_total_false_positive_count,
        "target_edges": target_results,
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
