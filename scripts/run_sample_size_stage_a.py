"""Sample-size dependence, Stage A: does sample size matter at all?

outline/plan.md section 1 scopes this project to n >= 200 for nonlinear
inference, and section 10 tracks "behavior as n/p changes" -- but every
study so far (Gate 0 through Stage II round 7) has used a single fixed
n=1,000. This holds the effect strength fixed at Stage I's strong
baseline (coefficient=0.7, near-ceiling detection at n=1,000 in every
prior round) and sweeps only n_rows, to see whether sample size matters
at all when the signal itself is not the limiting factor, and to check
for outright breakage below plan.md's stated n>=200 floor.

Not a Gate 0 study, no new redana source: reuses
redana.benchmark.run_replicated_condition and
redana.scenarios.generate_stage1_nonlinear_fixture unchanged.
"""

from __future__ import annotations

from functools import partial

from redana.benchmark import ConditionResult, run_replicated_condition
from redana.network import NetworkConfig
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage1_nonlinear_fixture

_N_REPS = 50
_PERMUTATIONS = 199
_ALPHA = 0.05
_BASE_SEED = 20260825
_COEFFICIENT = 0.7
_N_ROWS_LEVELS = (100, 200, 500, 1000, 2000)


def run() -> list[ConditionResult]:
    """Run the nonlinear fixture at coefficient=0.7 across five sample sizes."""

    residual_config = PrototypeConfig()
    network_config = NetworkConfig()
    results: list[ConditionResult] = []

    for n_rows in _N_ROWS_LEVELS:
        condition_name = f"sample-size-a-{n_rows}"
        fixture_fn = partial(generate_stage1_nonlinear_fixture, coefficient=_COEFFICIENT)
        result = run_replicated_condition(
            fixture_fn,
            condition_name=condition_name,
            n_reps=_N_REPS,
            n_rows=n_rows,
            residual_config=residual_config,
            network_config=network_config,
            permutations=_PERMUTATIONS,
            alpha=_ALPHA,
            base_seed=_BASE_SEED,
        )
        results.append(result)

    return results


def main() -> int:
    results = run()
    print("== nonlinear fixture (coefficient=0.7) across sample sizes ==")
    for n_rows, result in zip(_N_ROWS_LEVELS, results, strict=True):
        summary = result.summary
        print(f"  -- n_rows={n_rows} --")
        print(
            f"    residual precision: mean={summary.residual_precision.mean:.3f} "
            f"median={summary.residual_precision.median:.3f}"
        )
        print(
            f"    residual recall:    mean={summary.residual_recall.mean:.3f} "
            f"median={summary.residual_recall.median:.3f}"
        )
        print(f"    residual exact-match fraction: {summary.residual_exact_match_fraction:.3f}")
        print(
            "    residual per-edge detection fraction: "
            f"{dict(sorted(summary.residual_per_edge_detection_fraction.items()))}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
