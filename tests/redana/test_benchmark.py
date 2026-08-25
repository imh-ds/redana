"""Tests for the Stage I replicated benchmark runner and aggregation."""

from __future__ import annotations

import pandas as pd
import pytest

from redana.benchmark import ReplicationScore, _aggregate, run_replicated_condition
from redana.network import NetworkConfig
from redana.residuals import PrototypeConfig
from redana.scoring import score_edges


def _fake_fixture(n_rows: int, seed: int) -> tuple[pd.DataFrame, frozenset[tuple[str, str]]]:
    import numpy as np

    rng = np.random.default_rng(seed)
    frame = pd.DataFrame(rng.standard_normal((n_rows, 4)), columns=["X1", "X2", "X3", "X4"])
    return frame, frozenset({("X1", "X2")})


def test_runner_calls_the_fixture_function_n_reps_times_with_distinct_seeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[int, int]] = []
    original = _fake_fixture

    def spy(n_rows: int, seed: int) -> tuple[pd.DataFrame, frozenset[tuple[str, str]]]:
        calls.append((n_rows, seed))
        return original(n_rows, seed)

    result = run_replicated_condition(
        spy,
        condition_name="unit",
        n_reps=3,
        n_rows=80,
        residual_config=PrototypeConfig(n_splits=3, spline_knots=3, spline_degree=2),
        network_config=NetworkConfig(alphas=(0.1, 0.3)),
        permutations=9,
        alpha=0.05,
        base_seed=1,
    )

    assert len(calls) == 3
    assert len({seed for _, seed in calls}) == 3  # every seed distinct
    assert all(n_rows == 80 for n_rows, _ in calls)
    assert len(result.replications) == 3
    assert result.condition_name == "unit"


def test_runner_is_deterministic_across_reruns() -> None:
    kwargs = dict(
        condition_name="unit",
        n_reps=3,
        n_rows=80,
        residual_config=PrototypeConfig(n_splits=3, spline_knots=3, spline_degree=2),
        network_config=NetworkConfig(alphas=(0.1, 0.3)),
        permutations=9,
        alpha=0.05,
        base_seed=5,
    )

    first = run_replicated_condition(_fake_fixture, **kwargs)
    second = run_replicated_condition(_fake_fixture, **kwargs)

    first_precisions = [r.residual.precision for r in first.replications]
    second_precisions = [r.residual.precision for r in second.replications]
    assert first_precisions == second_precisions


def test_aggregate_computes_summary_statistics_from_hand_constructed_scores() -> None:
    true_edges = frozenset({("X1", "X2"), ("X3", "X4")})

    replications = [
        ReplicationScore(
            replication=0,
            true_edges=true_edges,
            incumbent=score_edges(set(true_edges), {("X1", "X2")}),
            residual=score_edges(set(true_edges), {("X1", "X2"), ("X3", "X4")}),
            residual_edges=frozenset({("X1", "X2"), ("X3", "X4")}),
        ),
        ReplicationScore(
            replication=1,
            true_edges=true_edges,
            incumbent=score_edges(set(true_edges), set()),
            residual=score_edges(set(true_edges), {("X1", "X2")}),
            residual_edges=frozenset({("X1", "X2")}),
        ),
    ]

    summary = _aggregate(replications)

    # incumbent precision across the two reps: [1.0, 0.0] -> mean 0.5
    assert summary.incumbent_precision.mean == pytest.approx(0.5)
    assert summary.incumbent_precision.minimum == pytest.approx(0.0)
    assert summary.incumbent_precision.maximum == pytest.approx(1.0)
    # residual recall across the two reps: [1.0, 0.5] -> mean 0.75
    assert summary.residual_recall.mean == pytest.approx(0.75)
    # exact match: incumbent never matched both edges; residual matched once (rep 0)
    assert summary.incumbent_exact_match_fraction == pytest.approx(0.0)
    assert summary.residual_exact_match_fraction == pytest.approx(0.5)
    # per-edge detection: (X1,X2) detected in both reps, (X3,X4) only in rep 0
    assert summary.residual_per_edge_detection_fraction[("X1", "X2")] == pytest.approx(1.0)
    assert summary.residual_per_edge_detection_fraction[("X3", "X4")] == pytest.approx(0.5)


def test_aggregate_rejects_empty_replication_list() -> None:
    with pytest.raises(ValueError, match="at least one"):
        _aggregate([])
