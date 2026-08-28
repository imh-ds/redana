"""One shard of the full-family BH-FDR calibration study: one
(condition, n_rows, rep-chunk) cell, 5 reps, written as JSON.

Per docs/superpowers/plans/2026-08-27-stage3-fdr-calibration.md Task 3.
Validates redana.fdr.benjamini_hochberg's empirical false discovery
control at m=66 simultaneous pairs, permutations=1999 -- the exact scale
the fair matched comparison's n=500 PASS depends on, and which has never
been directly tested. Residual-layer only, no incumbent fit.

Two conditions:
  null  -- 12 fully mutually-independent Gaussian columns (no true edges
           at all). Every possible rejection is, by construction, false.
  mixed -- generate_stage3_hybrid_fixture at n_rows=500, using
           redana.scenarios.stage3_hybrid_scoring_true_edges for the
           false-discovery bookkeeping.
"""

from __future__ import annotations

import argparse
import json
from itertools import combinations

import numpy as np
import pandas as pd

from redana.dependence import derive_seed, permutation_distance_correlation
from redana.fdr import benjamini_hochberg
from redana.residuals import PrototypeConfig, cross_fitted_pair_residuals
from redana.scenarios import generate_stage3_hybrid_fixture, stage3_hybrid_scoring_true_edges

_REPS_PER_SHARD = 5
_PERMUTATIONS = 1999
_ALPHA = 0.05
_BASE_SEED = 20260827
_CONDITIONS = ("null", "mixed")


def _canonical(edges) -> set[tuple[str, str]]:
    return {tuple(sorted(edge)) for edge in edges}


def _generate_null_frame(n_rows: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    columns = [f"X{i}" for i in range(1, 13)]
    data = rng.standard_normal((n_rows, len(columns)))
    return pd.DataFrame(data, columns=columns)


def run_replication(condition: str, n_rows: int, rep_index: int) -> dict:
    condition_name = f"stage3-fdrcal-{condition}-n{n_rows}"
    seed = derive_seed("stage3-fdrcal", condition_name, rep_index, _BASE_SEED)

    if condition == "null":
        frame = _generate_null_frame(n_rows, seed)
        scoring_true_edges: set[tuple[str, str]] = set()
    else:
        frame, true_linear, true_nonlinear = generate_stage3_hybrid_fixture(n_rows, seed)
        scoring_true_edges = _canonical(stage3_hybrid_scoring_true_edges(true_linear, true_nonlinear))

    pairs = [tuple(sorted(pair)) for pair in combinations(frame.columns, 2)]
    p_values: list[float] = []
    for left, right in pairs:
        residual_seed = derive_seed("redana-prototype", seed, left, right, "residual") % (2**32)
        permutation_seed = derive_seed("redana-prototype", seed, left, right, "permutation")
        residuals = cross_fitted_pair_residuals(frame, left, right, PrototypeConfig(), residual_seed)
        result = permutation_distance_correlation(
            residuals[left].to_numpy(), residuals[right].to_numpy(), _PERMUTATIONS, permutation_seed
        )
        p_values.append(result.p_value)

    significant = benjamini_hochberg(p_values, _ALPHA)
    rejected_pairs = {pair for pair, sig in zip(pairs, significant, strict=True) if sig}
    n_rejections = len(rejected_pairs)
    false_rejections = len(rejected_pairs - scoring_true_edges)
    false_discovery_proportion = (false_rejections / n_rejections) if n_rejections else 0.0

    return {
        "condition": condition,
        "n_rows": n_rows,
        "rep_index": rep_index,
        "n_rejections": n_rejections,
        "any_rejection": n_rejections > 0,
        "false_rejections": false_rejections,
        "false_discovery_proportion": false_discovery_proportion,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", choices=_CONDITIONS, required=True)
    parser.add_argument("--n-rows", type=int, required=True)
    parser.add_argument("--rep-chunk", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rep_start = args.rep_chunk * _REPS_PER_SHARD
    reps = [
        run_replication(args.condition, args.n_rows, rep_index)
        for rep_index in range(rep_start, rep_start + _REPS_PER_SHARD)
    ]

    with open(args.out, "w") as f:
        json.dump(
            {
                "condition": args.condition,
                "n_rows": args.n_rows,
                "rep_chunk": args.rep_chunk,
                "reps": reps,
            },
            f,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
