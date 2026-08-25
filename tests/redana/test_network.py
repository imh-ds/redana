"""Tests for the redana frozen EBIC-selected incumbent linear network."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from redana.network import NetworkConfig, fit_incumbent_network


def _chain_precision(p: int, diagonal: float, off_diagonal: float) -> np.ndarray:
    theta = np.eye(p) * diagonal
    for i in range(p - 1):
        theta[i, i + 1] = off_diagonal
        theta[i + 1, i] = off_diagonal
    return theta


def _chain_frame(n: int, p: int, seed: int) -> tuple[pd.DataFrame, set[tuple[str, str]]]:
    theta = _chain_precision(p, diagonal=1.5, off_diagonal=0.4)
    covariance = np.linalg.inv(theta)
    rng = np.random.default_rng(seed)
    data = rng.multivariate_normal(np.zeros(p), covariance, size=n)
    columns = [f"X{i + 1}" for i in range(p)]
    frame = pd.DataFrame(data, columns=columns)
    true_edges = {(columns[i], columns[i + 1]) for i in range(p - 1)}
    return frame, true_edges


def test_recovers_a_known_sparse_chain_structure_at_a_large_sample() -> None:
    frame, true_edges = _chain_frame(n=3000, p=5, seed=1)

    result = fit_incumbent_network(frame, NetworkConfig())

    true_positives = result.edges & true_edges
    false_positives = result.edges - true_edges
    false_negatives = true_edges - result.edges
    precision = len(true_positives) / len(result.edges) if result.edges else 0.0
    recall = len(true_positives) / len(true_edges)

    assert precision >= 0.8
    assert recall >= 0.8
    assert len(false_positives) <= 1
    assert len(false_negatives) <= 1


def test_fully_independent_columns_select_a_near_empty_edge_set() -> None:
    rng = np.random.default_rng(2)
    frame = pd.DataFrame(rng.standard_normal((3000, 5)), columns=[f"X{i + 1}" for i in range(5)])

    result = fit_incumbent_network(frame, NetworkConfig())

    assert len(result.edges) <= 1


def test_edges_are_undirected_and_derived_from_nonzero_partial_correlation() -> None:
    frame, _ = _chain_frame(n=1000, p=4, seed=3)

    result = fit_incumbent_network(frame, NetworkConfig())

    assert result.edges, "expected the chain structure to yield at least one edge"
    for left, right in result.edges:
        assert (right, left) not in result.edges  # canonical, undirected pairs only
        partial_correlation = result.partial_correlation.loc[left, right]
        assert abs(partial_correlation) > 0


def test_network_config_defaults_are_frozen_and_fixed() -> None:
    first = NetworkConfig()
    second = NetworkConfig()

    assert first == second
    assert first.gamma == 0.5
    with pytest.raises(AttributeError):
        first.gamma = 0.9  # frozen dataclass rejects mutation
