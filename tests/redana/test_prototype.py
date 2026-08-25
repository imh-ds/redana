"""Tests for the redana prototype orchestration entry point."""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
import pytest

from redana import prototype as prototype_module
from redana.network import IncumbentNetworkResult, NetworkConfig
from redana.prototype import run_prototype
from redana.residuals import PrototypeConfig


def _synthetic_frame(n: int, columns: list[str], seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame(rng.standard_normal((n, len(columns))), columns=columns)


def _small_configs() -> tuple[PrototypeConfig, NetworkConfig]:
    return PrototypeConfig(n_splits=3, spline_knots=3, spline_degree=2, ridge_alpha=1.0), (
        NetworkConfig(alphas=(0.1, 0.3, 0.5))
    )


def test_every_unordered_pair_is_tested_exactly_once() -> None:
    columns = ["X1", "X2", "X3", "X4"]
    frame = _synthetic_frame(150, columns, seed=1)
    residual_config, network_config = _small_configs()

    result = run_prototype(
        frame, residual_config, network_config, permutations=19, alpha=0.05, seed=7
    )

    expected_pairs = {tuple(sorted(pair)) for pair in combinations(columns, 2)}
    tested_pairs = {(stat.left, stat.right) for stat in result.pair_statistics}
    assert tested_pairs == expected_pairs
    assert len(result.pair_statistics) == len(expected_pairs)


def test_rerunning_with_the_same_seed_is_deterministic() -> None:
    columns = ["X1", "X2", "X3", "X4"]
    frame = _synthetic_frame(150, columns, seed=2)
    residual_config, network_config = _small_configs()

    first = run_prototype(
        frame, residual_config, network_config, permutations=19, alpha=0.05, seed=11
    )
    second = run_prototype(
        frame, residual_config, network_config, permutations=19, alpha=0.05, seed=11
    )

    first_stats = sorted(
        (s.left, s.right, s.observed_statistic, s.p_value) for s in first.pair_statistics
    )
    second_stats = sorted(
        (s.left, s.right, s.observed_statistic, s.p_value) for s in second.pair_statistics
    )
    assert first_stats == second_stats
    assert first.residual_edges == second.residual_edges
    assert first.incumbent_edges == second.incumbent_edges


def test_incumbent_and_residual_edge_sets_are_computed_independently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    columns = ["X1", "X2", "X3"]
    frame = _synthetic_frame(120, columns, seed=3)
    residual_config, network_config = _small_configs()

    fixed_incumbent = IncumbentNetworkResult(
        precision_matrix=pd.DataFrame(np.eye(3), index=columns, columns=columns),
        partial_correlation=pd.DataFrame(np.zeros((3, 3)), index=columns, columns=columns),
        edges=frozenset({("X1", "X2")}),
        selected_alpha=0.5,
        selected_ebic=0.0,
    )
    monkeypatch.setattr(
        prototype_module, "fit_incumbent_network", lambda *args, **kwargs: fixed_incumbent
    )

    result = run_prototype(
        frame, residual_config, network_config, permutations=19, alpha=0.05, seed=13
    )

    assert result.incumbent_edges == frozenset({("X1", "X2")})
    assert len(result.pair_statistics) == 3  # residual layer still ran on all pairs


def test_pair_statistics_carry_valid_probabilities() -> None:
    columns = ["X1", "X2", "X3"]
    frame = _synthetic_frame(120, columns, seed=4)
    residual_config, network_config = _small_configs()

    result = run_prototype(
        frame, residual_config, network_config, permutations=19, alpha=0.05, seed=17
    )

    for stat in result.pair_statistics:
        assert 0.0 < stat.p_value <= 1.0
        assert isinstance(stat.significant, (bool, np.bool_))
