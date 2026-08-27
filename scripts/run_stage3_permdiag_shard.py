"""One shard of the permutation-resolution diagnostic: one (config, n_rows,
rep-chunk) cell, 5 reps, written as JSON.

Per docs/superpowers/plans/2026-08-27-stage3-permutation-resolution-diagnostic.md
Task 1. Resolves two confounds independent peer review identified in
docs/evidence/stage3-peer-review-prompt-adjustment-set-floor-20260827.md:
(1) with permutations=199, the achievable p-value floor (1/200=0.005) is
coarser than BH-FDR's rank-1 threshold at m=66 (0.05/66~=0.000758), making
discovery mechanically require 7+ simultaneous ties at the floor,
independent of true signal strength; (2) the earlier "drop X5" comparison
confounded removing X5 as an over-adjustment proxy with shrinking the BH
test family from 66 to 55 pairs.

No incumbent network fit this round -- residual-layer diagnostic only.
Three configs, differing only in which columns cross_fitted_pair_residuals
sees per pair (never by editing redana.residuals itself):
  A          -- X5 dropped entirely. 11 nodes, m=55.
  B_baseline -- full 12-node frame, standard adjustment (current default
                behavior). m=66.
  B_targeted -- full 12-node frame, m=66 (X5 stays a tested variable), but
                excluded from every *other* pair's adjustment set --
                isolates the proxy-suppression mechanism without changing
                family size.
"""

from __future__ import annotations

import argparse
import json
from itertools import combinations

from redana.dependence import derive_seed, permutation_distance_correlation
from redana.fdr import benjamini_hochberg
from redana.residuals import PrototypeConfig, cross_fitted_pair_residuals
from redana.scenarios import generate_stage3_hybrid_fixture

_REPS_PER_SHARD = 5
_PERMUTATIONS = 1999
_ALPHA = 0.05
_BASE_SEED = 20260827
_CONFIGS = ("A", "B_baseline", "B_targeted")
_TRUE_NONLINEAR_EDGES = frozenset(
    {tuple(sorted(e)) for e in (("X1", "X4"), ("X7", "X10"), ("X1", "X12"))}
)


def _pair_universe(config: str, frame_columns: list[str]) -> list[tuple[str, str]]:
    if config == "A":
        columns = [c for c in frame_columns if c != "X5"]
    else:
        columns = list(frame_columns)
    return [tuple(sorted(pair)) for pair in combinations(columns, 2)]


def _adjustment_frame(config: str, frame, left: str, right: str):
    if config == "A":
        return frame.drop(columns=["X5"])
    if config == "B_baseline":
        return frame
    if config == "B_targeted":
        if "X5" in (left, right):
            return frame
        return frame.drop(columns=["X5"])
    raise ValueError(f"unknown config {config!r}")


def run_replication(config: str, n_rows: int, rep_index: int) -> dict:
    condition_name = f"stage3-permdiag-{config}-n{n_rows}"
    seed = derive_seed("stage3-permdiag", condition_name, rep_index, _BASE_SEED)
    frame, _, _ = generate_stage3_hybrid_fixture(n_rows, seed)

    pairs = _pair_universe(config, list(frame.columns))
    p_values: list[float] = []
    for left, right in pairs:
        adjustment_frame = _adjustment_frame(config, frame, left, right)
        residual_seed = derive_seed("redana-prototype", seed, left, right, "residual") % (2**32)
        permutation_seed = derive_seed("redana-prototype", seed, left, right, "permutation")
        residuals = cross_fitted_pair_residuals(
            adjustment_frame, left, right, PrototypeConfig(), residual_seed
        )
        result = permutation_distance_correlation(
            residuals[left].to_numpy(), residuals[right].to_numpy(), _PERMUTATIONS, permutation_seed
        )
        p_values.append(result.p_value)

    full_family_significant = benjamini_hochberg(p_values, _ALPHA)
    pair_p_value = dict(zip(pairs, p_values, strict=True))
    pair_significant = dict(zip(pairs, full_family_significant.tolist(), strict=True))

    oracle_pairs = [p for p in pairs if p in _TRUE_NONLINEAR_EDGES]
    oracle_p_values = [pair_p_value[p] for p in oracle_pairs]
    oracle_significant = (
        dict(
            zip(
                oracle_pairs,
                benjamini_hochberg(oracle_p_values, _ALPHA).tolist(),
                strict=True,
            )
        )
        if oracle_pairs
        else {}
    )

    nonlinear_edges_present = [p for p in pairs if p in _TRUE_NONLINEAR_EDGES]
    edge_results = {
        f"{p[0]}-{p[1]}": {
            "p_value": pair_p_value[p],
            "raw_significant": pair_p_value[p] < _ALPHA,
            "full_family_bh_significant": pair_significant[p],
            "oracle_bh_significant": oracle_significant.get(p),
        }
        for p in nonlinear_edges_present
    }

    return {
        "config": config,
        "n_rows": n_rows,
        "rep_index": rep_index,
        "m": len(pairs),
        "full_family_bh_rejections": int(sum(full_family_significant)),
        "min_p_value": min(p_values) if p_values else None,
        "nonlinear_edges": edge_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", choices=_CONFIGS, required=True)
    parser.add_argument("--n-rows", type=int, required=True)
    parser.add_argument("--rep-chunk", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rep_start = args.rep_chunk * _REPS_PER_SHARD
    reps = [
        run_replication(args.config, args.n_rows, rep_index)
        for rep_index in range(rep_start, rep_start + _REPS_PER_SHARD)
    ]

    with open(args.out, "w") as f:
        json.dump(
            {"config": args.config, "n_rows": args.n_rows, "rep_chunk": args.rep_chunk, "reps": reps},
            f,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
