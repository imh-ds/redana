"""Tests for the Stage II network-structure fixtures: hub, community, redundant predictors."""

from __future__ import annotations

import pandas as pd

from redana.scenarios import (
    generate_stage2_community_fixture,
    generate_stage2_hub_fixture,
    generate_stage2_redundant_predictors_fixture,
)


def test_hub_fixture_has_correct_shape_and_true_edges() -> None:
    frame, edges = generate_stage2_hub_fixture(1000, seed=1)
    assert frame.shape == (1000, 6)
    assert list(frame.columns) == ["X1", "X2", "X3", "X4", "X5", "X6"]
    assert edges == frozenset({("X1", "X2"), ("X1", "X3"), ("X1", "X4")})


def test_hub_fixture_is_deterministic_given_the_same_seed() -> None:
    first, _ = generate_stage2_hub_fixture(300, seed=2)
    second, _ = generate_stage2_hub_fixture(300, seed=2)
    pd.testing.assert_frame_equal(first, second)


def test_hub_fixture_differs_across_seeds() -> None:
    first, _ = generate_stage2_hub_fixture(300, seed=2)
    second, _ = generate_stage2_hub_fixture(300, seed=3)
    assert not first["X2"].equals(second["X2"])


def test_community_fixture_has_correct_shape_and_true_edges() -> None:
    frame, edges = generate_stage2_community_fixture(1000, seed=1)
    assert frame.shape == (1000, 6)
    assert edges == frozenset({("X1", "X2"), ("X2", "X3"), ("X4", "X5"), ("X5", "X6")})


def test_community_fixture_is_deterministic_given_the_same_seed() -> None:
    first, _ = generate_stage2_community_fixture(300, seed=2)
    second, _ = generate_stage2_community_fixture(300, seed=2)
    pd.testing.assert_frame_equal(first, second)


def test_community_fixture_differs_across_seeds() -> None:
    first, _ = generate_stage2_community_fixture(300, seed=2)
    second, _ = generate_stage2_community_fixture(300, seed=3)
    assert not first["X5"].equals(second["X5"])


def test_redundant_predictors_fixture_has_correct_shape_and_true_edges() -> None:
    frame, edges = generate_stage2_redundant_predictors_fixture(1000, seed=1)
    assert frame.shape == (1000, 6)
    assert edges == frozenset({("X1", "X3")})
    assert ("X1", "X2") not in edges
    assert ("X2", "X3") not in edges


def test_redundant_predictors_fixture_is_deterministic_given_the_same_seed() -> None:
    first, _ = generate_stage2_redundant_predictors_fixture(300, seed=2)
    second, _ = generate_stage2_redundant_predictors_fixture(300, seed=2)
    pd.testing.assert_frame_equal(first, second)


def test_redundant_predictors_fixture_differs_across_seeds() -> None:
    first, _ = generate_stage2_redundant_predictors_fixture(300, seed=2)
    second, _ = generate_stage2_redundant_predictors_fixture(300, seed=3)
    assert not first["X1"].equals(second["X1"])


def test_redundant_predictors_x1_x2_are_highly_correlated() -> None:
    frame, _ = generate_stage2_redundant_predictors_fixture(5000, seed=4)
    x1_x2_correlation = abs(frame["X1"].corr(frame["X2"]))
    assert x1_x2_correlation > 0.8


def test_redundant_predictors_x2_x3_correlation_is_weaker_than_x1_x3() -> None:
    frame, _ = generate_stage2_redundant_predictors_fixture(5000, seed=4)
    x1_x3_correlation = abs(frame["X1"].corr(frame["X3"]))
    x2_x3_correlation = abs(frame["X2"].corr(frame["X3"]))
    assert x2_x3_correlation < x1_x3_correlation
