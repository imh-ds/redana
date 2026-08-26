"""Run the Stage II round 7 network-structure degradation benchmark.

outline/plan.md section 6, scoped to its seventh and last named
degradation dimension: network structure (chain -> hubs -> communities
-> redundant predictors). Unlike rounds 1-6, which swept a scalar
parameter across two shapes, this round tests four distinct topologies
each at a fixed coefficient=0.7, since network structure is categorical,
not a continuum. Not a Gate 0 study -- no hash-pinned calibration, no
per-replication artifact retention. Reuses every Step 4 / Stage I /
Stage II component unchanged; the `chain` condition reuses
`generate_stage1_linear_fixture` as-is, and `hub`/`community`/
`redundant_predictors` use the three new fixture generators.
"""

from __future__ import annotations

from functools import partial

from redana.benchmark import ConditionResult, run_replicated_condition
from redana.network import NetworkConfig
from redana.residuals import PrototypeConfig
from redana.scenarios import (
    generate_stage1_linear_fixture,
    generate_stage2_community_fixture,
    generate_stage2_hub_fixture,
    generate_stage2_redundant_predictors_fixture,
)

_N_REPS = 50
_N_ROWS = 1000
_PERMUTATIONS = 199
_ALPHA = 0.05
_BASE_SEED = 20260825
_COEFFICIENT = 0.7
_CONDITIONS = (
    ("chain", generate_stage1_linear_fixture),
    ("hub", generate_stage2_hub_fixture),
    ("community", generate_stage2_community_fixture),
    ("redundant_predictors", generate_stage2_redundant_predictors_fixture),
)


def run() -> list[ConditionResult]:
    """Run all four network-structure conditions."""

    residual_config = PrototypeConfig()
    network_config = NetworkConfig()
    results: list[ConditionResult] = []

    for condition_label, generator in _CONDITIONS:
        condition_name = f"stage2-network-structure-{condition_label}"
        fixture_fn = partial(generator, coefficient=_COEFFICIENT)
        result = run_replicated_condition(
            fixture_fn,
            condition_name=condition_name,
            n_reps=_N_REPS,
            n_rows=_N_ROWS,
            residual_config=residual_config,
            network_config=network_config,
            permutations=_PERMUTATIONS,
            alpha=_ALPHA,
            base_seed=_BASE_SEED,
        )
        results.append(result)

    return results


def _redundant_predictors_false_positive_rate(result: ConditionResult) -> float:
    flagged = sum(
        1
        for replication in result.replications
        if ("X2", "X3") in {tuple(sorted(edge)) for edge in replication.residual_edges}
    )
    return flagged / len(result.replications)


def main() -> int:
    results = run()
    print("== network structure across topologies (coefficient=0.7) ==")
    for (condition_label, _), result in zip(_CONDITIONS, results, strict=True):
        summary = result.summary
        print(f"  -- {condition_label} --")
        for label, incumbent, residual in (
            ("precision", summary.incumbent_precision, summary.residual_precision),
            ("recall", summary.incumbent_recall, summary.residual_recall),
            ("f1", summary.incumbent_f1, summary.residual_f1),
        ):
            print(
                f"    incumbent {label}: mean={incumbent.mean:.3f} median={incumbent.median:.3f}"
            )
            print(
                f"    residual  {label}: mean={residual.mean:.3f} median={residual.median:.3f}"
            )
        print(
            "    exact-match fraction: incumbent="
            f"{summary.incumbent_exact_match_fraction:.3f} residual="
            f"{summary.residual_exact_match_fraction:.3f}"
        )
        print(
            "    residual per-edge detection fraction: "
            f"{dict(sorted(summary.residual_per_edge_detection_fraction.items()))}"
        )
        if condition_label == "redundant_predictors":
            rate = _redundant_predictors_false_positive_rate(result)
            print(f"    residual (X2,X3) false-positive rate: {rate:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
