"""Validate bootstrap edge stability against actual between-dataset replication.

outline/plan.md section 14's central question: is bootstrap stability
(computable from a single real dataset) a trustworthy proxy for actual
replication probability (which a real researcher can never directly
observe, since they only ever have one dataset)? Per
docs/superpowers/specs/2026-08-26-stability-reporting-charter.md (Track
1), tests two charter-approved configurations at n=1,000: a well-powered
case (coefficient=0.7) and a marginal case near Stage II round 1's
already-characterized detectability cliff (coefficient=0.15).

For each configuration: (a) 50 independent datasets give the actual
replication rate, exactly as every prior Stage I/II round measured it;
(b) for the first 10 of those same 50 datasets (re-derived via the same
seed formula redana.benchmark.run_replicated_condition uses internally),
100-resample bootstrap stability is computed per pair. The 10-dataset
mean bootstrap stability is compared against the 50-dataset actual
replication rate.

Not a Gate 0 study, no new redana source beyond Tasks 1-2's stability
and detectability modules.
"""

from __future__ import annotations

from functools import partial

from redana.benchmark import ConditionResult, run_replicated_condition
from redana.dependence import derive_seed
from redana.network import NetworkConfig
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage1_nonlinear_fixture
from redana.stability import bootstrap_edge_stability, classify_stability_tier

_N_REPS = 50
_N_BOOTSTRAP_DATASETS = 10
_N_BOOTSTRAP = 100
_N_ROWS = 1000
_PERMUTATIONS = 199
_ALPHA = 0.05
_BASE_SEED = 20260825
_CONFIGURATIONS = (("well_powered", 0.7), ("marginal", 0.15))
_TRUE_EDGES = frozenset({("X1", "X2"), ("X3", "X4")})
_INCIDENTAL_PAIR = ("X5", "X6")


def run_actual_replication(condition_name: str, coefficient: float) -> ConditionResult:
    fixture_fn = partial(generate_stage1_nonlinear_fixture, coefficient=coefficient)
    return run_replicated_condition(
        fixture_fn,
        condition_name=condition_name,
        n_reps=_N_REPS,
        n_rows=_N_ROWS,
        residual_config=PrototypeConfig(),
        network_config=NetworkConfig(),
        permutations=_PERMUTATIONS,
        alpha=_ALPHA,
        base_seed=_BASE_SEED,
    )


def run_bootstrap_subset(condition_name: str, coefficient: float) -> list[dict[tuple[str, str], float]]:
    residual_config = PrototypeConfig()
    network_config = NetworkConfig()
    per_dataset_stability: list[dict[tuple[str, str], float]] = []

    for index in range(_N_BOOTSTRAP_DATASETS):
        dataset_seed = derive_seed("stage1", condition_name, index, _BASE_SEED)
        frame, _ = generate_stage1_nonlinear_fixture(_N_ROWS, dataset_seed, coefficient=coefficient)
        stability = bootstrap_edge_stability(
            frame,
            residual_config,
            network_config,
            permutations=_PERMUTATIONS,
            alpha=_ALPHA,
            seed=dataset_seed,
            n_bootstrap=_N_BOOTSTRAP,
        )
        per_dataset_stability.append(stability)

    return per_dataset_stability


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def main() -> int:
    for label, coefficient in _CONFIGURATIONS:
        condition_name = f"stability-validation-{label}"
        print(f"== {label} (coefficient={coefficient}, n_rows={_N_ROWS}) ==")

        actual = run_actual_replication(condition_name, coefficient)
        print(
            "  actual replication (50 datasets), per-edge detection fraction: "
            f"{dict(sorted(actual.summary.residual_per_edge_detection_fraction.items()))}"
        )

        bootstrap_datasets = run_bootstrap_subset(condition_name, coefficient)

        for edge in sorted(_TRUE_EDGES):
            values = [d[edge] for d in bootstrap_datasets]
            tiers = [classify_stability_tier(v) for v in values]
            print(f"  true edge {edge}: mean bootstrap stability={_mean(values):.3f}")
            print(f"    per-dataset stability values: {[round(v, 3) for v in values]}")
            print(
                f"    tier distribution: frequently_selected={tiers.count('frequently_selected')} "
                f"intermittently_selected={tiers.count('intermittently_selected')} "
                f"rarely_selected={tiers.count('rarely_selected')}"
            )

        incidental_values = [d[_INCIDENTAL_PAIR] for d in bootstrap_datasets]
        print(
            f"  incidental non-edge {_INCIDENTAL_PAIR}: "
            f"mean bootstrap stability={_mean(incidental_values):.3f}"
        )
        print(f"    per-dataset stability values: {[round(v, 3) for v in incidental_values]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
