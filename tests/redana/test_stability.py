"""Tests for bootstrap edge stability and stability-tier classification."""

from __future__ import annotations

import pytest

from redana.network import NetworkConfig
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage1_nonlinear_fixture
from redana.stability import bootstrap_edge_stability, classify_stability_tier


def test_bootstrap_edge_stability_covers_all_pairs() -> None:
    frame, _ = generate_stage1_nonlinear_fixture(300, seed=1, coefficient=0.7)
    stability = bootstrap_edge_stability(
        frame,
        PrototypeConfig(),
        NetworkConfig(),
        permutations=49,
        alpha=0.05,
        seed=10,
        n_bootstrap=10,
    )
    columns = list(frame.columns)
    expected_pairs = {
        (columns[i], columns[j]) for i in range(len(columns)) for j in range(i + 1, len(columns))
    }
    assert set(stability.keys()) == expected_pairs
    assert all(0.0 <= value <= 1.0 for value in stability.values())


def test_bootstrap_edge_stability_is_deterministic_given_the_same_seed() -> None:
    frame, _ = generate_stage1_nonlinear_fixture(300, seed=1, coefficient=0.7)
    first = bootstrap_edge_stability(
        frame, PrototypeConfig(), NetworkConfig(), permutations=49, alpha=0.05, seed=10, n_bootstrap=10
    )
    second = bootstrap_edge_stability(
        frame, PrototypeConfig(), NetworkConfig(), permutations=49, alpha=0.05, seed=10, n_bootstrap=10
    )
    assert first == second


def test_bootstrap_edge_stability_is_higher_for_true_edges() -> None:
    frame, true_edges = generate_stage1_nonlinear_fixture(300, seed=2, coefficient=0.7)
    stability = bootstrap_edge_stability(
        frame, PrototypeConfig(), NetworkConfig(), permutations=49, alpha=0.05, seed=11, n_bootstrap=10
    )
    true_edge_stability = [stability[edge] for edge in true_edges]
    unrelated_pair_stability = stability[("X5", "X6")]
    assert min(true_edge_stability) > unrelated_pair_stability


@pytest.mark.parametrize(
    "stability,expected_tier",
    [
        (1.0, "core"),
        (0.80, "core"),
        (0.75, "core"),
        (0.74999, "provisional"),
        (0.40, "provisional"),
        (0.399, "background"),
        (0.0, "background"),
    ],
)
def test_classify_stability_tier(stability: float, expected_tier: str) -> None:
    assert classify_stability_tier(stability) == expected_tier


@pytest.mark.parametrize("invalid_stability", [-0.1, 1.1])
def test_classify_stability_tier_rejects_out_of_range(invalid_stability: float) -> None:
    with pytest.raises(ValueError, match="stability"):
        classify_stability_tier(invalid_stability)
