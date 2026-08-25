"""Replicated benchmark runner and aggregation for Stage I mechanistic tests."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from redana.dependence import derive_seed
from redana.network import IncumbentNetworkResult, NetworkConfig, fit_incumbent_network
from redana.prototype import run_prototype
from redana.residuals import PrototypeConfig
from redana.scoring import EdgeScore, score_edges

FixtureFunction = Callable[[int, int], tuple[pd.DataFrame, frozenset[tuple[str, str]]]]


@dataclass(frozen=True)
class ReplicationScore:
    """One replication's true edges and both mechanisms' scores against them."""

    replication: int
    true_edges: frozenset[tuple[str, str]]
    incumbent: EdgeScore
    residual: EdgeScore
    residual_edges: frozenset[tuple[str, str]]


@dataclass(frozen=True)
class MetricSummary:
    """Distribution summary for one metric across replications."""

    mean: float
    median: float
    minimum: float
    maximum: float


@dataclass(frozen=True)
class ConditionSummary:
    """Aggregate Stage I results for one fixture condition."""

    incumbent_precision: MetricSummary
    incumbent_recall: MetricSummary
    incumbent_f1: MetricSummary
    residual_precision: MetricSummary
    residual_recall: MetricSummary
    residual_f1: MetricSummary
    incumbent_exact_match_fraction: float
    residual_exact_match_fraction: float
    residual_per_edge_detection_fraction: dict[tuple[str, str], float]


@dataclass(frozen=True)
class ConditionResult:
    """One fixture condition's per-replication results and aggregate summary."""

    condition_name: str
    replications: tuple[ReplicationScore, ...]
    summary: ConditionSummary


def run_replicated_condition(
    fixture_fn: FixtureFunction,
    condition_name: str,
    n_reps: int,
    n_rows: int,
    residual_config: PrototypeConfig,
    network_config: NetworkConfig,
    permutations: int,
    alpha: float,
    base_seed: int,
) -> ConditionResult:
    """Run ``fixture_fn`` and the prototype ``n_reps`` times and aggregate the scores."""

    replications: list[ReplicationScore] = []
    for index in range(n_reps):
        seed = derive_seed("stage1", condition_name, index, base_seed)
        frame, true_edges = fixture_fn(n_rows, seed)
        incumbent_result: IncumbentNetworkResult = fit_incumbent_network(frame, network_config)
        prototype_result = run_prototype(
            frame, residual_config, network_config, permutations, alpha, seed
        )
        incumbent_score = score_edges(set(true_edges), set(incumbent_result.edges))
        residual_score = score_edges(set(true_edges), set(prototype_result.residual_edges))
        replications.append(
            ReplicationScore(
                replication=index,
                true_edges=true_edges,
                incumbent=incumbent_score,
                residual=residual_score,
                residual_edges=prototype_result.residual_edges,
            )
        )

    return ConditionResult(
        condition_name=condition_name,
        replications=tuple(replications),
        summary=_aggregate(replications),
    )


def _metric_summary(values: list[float]) -> MetricSummary:
    array = np.asarray(values, dtype=float)
    return MetricSummary(
        mean=float(np.mean(array)),
        median=float(np.median(array)),
        minimum=float(np.min(array)),
        maximum=float(np.max(array)),
    )


def _aggregate(replications: list[ReplicationScore]) -> ConditionSummary:
    if not replications:
        raise ValueError("aggregation requires at least one replication")

    incumbent_precision = _metric_summary([r.incumbent.precision for r in replications])
    incumbent_recall = _metric_summary([r.incumbent.recall for r in replications])
    incumbent_f1 = _metric_summary([r.incumbent.f1 for r in replications])
    residual_precision = _metric_summary([r.residual.precision for r in replications])
    residual_recall = _metric_summary([r.residual.recall for r in replications])
    residual_f1 = _metric_summary([r.residual.f1 for r in replications])

    incumbent_exact_match_fraction = sum(
        1 for r in replications if r.incumbent.false_positive_count == 0
        and r.incumbent.false_negative_count == 0
    ) / len(replications)
    residual_exact_match_fraction = sum(
        1 for r in replications if r.residual.false_positive_count == 0
        and r.residual.false_negative_count == 0
    ) / len(replications)

    all_true_edges: set[tuple[str, str]] = set()
    for r in replications:
        all_true_edges |= {tuple(sorted(edge)) for edge in r.true_edges}
    per_edge_detection: dict[tuple[str, str], float] = {}
    for edge in all_true_edges:
        eligible = [r for r in replications if edge in {tuple(sorted(e)) for e in r.true_edges}]
        detected = [
            r for r in eligible if edge in {tuple(sorted(e)) for e in r.residual_edges}
        ]
        per_edge_detection[edge] = len(detected) / len(eligible) if eligible else 0.0

    return ConditionSummary(
        incumbent_precision=incumbent_precision,
        incumbent_recall=incumbent_recall,
        incumbent_f1=incumbent_f1,
        residual_precision=residual_precision,
        residual_recall=residual_recall,
        residual_f1=residual_f1,
        incumbent_exact_match_fraction=incumbent_exact_match_fraction,
        residual_exact_match_fraction=residual_exact_match_fraction,
        residual_per_edge_detection_fraction=per_edge_detection,
    )
