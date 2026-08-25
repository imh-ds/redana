"""Tests for the Stage II effect-strength coefficient on the Stage I fixtures."""

from __future__ import annotations

import pandas as pd

from redana.scenarios import generate_stage1_linear_fixture, generate_stage1_nonlinear_fixture


def test_default_coefficient_preserves_stage1_linear_behavior() -> None:
    default_frame, default_edges = generate_stage1_linear_fixture(300, seed=1)
    explicit_frame, explicit_edges = generate_stage1_linear_fixture(300, seed=1, coefficient=0.7)

    pd.testing.assert_frame_equal(default_frame, explicit_frame)
    assert default_edges == explicit_edges


def test_default_coefficient_preserves_stage1_nonlinear_behavior() -> None:
    default_frame, default_edges = generate_stage1_nonlinear_fixture(300, seed=1)
    explicit_frame, explicit_edges = generate_stage1_nonlinear_fixture(
        300, seed=1, coefficient=0.7
    )

    pd.testing.assert_frame_equal(default_frame, explicit_frame)
    assert default_edges == explicit_edges


def test_smaller_linear_coefficient_shrinks_the_true_edge_correlation() -> None:
    strong_frame, _ = generate_stage1_linear_fixture(5000, seed=2, coefficient=0.7)
    weak_frame, _ = generate_stage1_linear_fixture(5000, seed=2, coefficient=0.2)

    strong_correlation = abs(strong_frame["X1"].corr(strong_frame["X2"]))
    weak_correlation = abs(weak_frame["X1"].corr(weak_frame["X2"]))
    assert weak_correlation < strong_correlation


def test_true_edges_are_unchanged_across_coefficient_values() -> None:
    _, strong_edges = generate_stage1_linear_fixture(300, seed=3, coefficient=0.7)
    _, weak_edges = generate_stage1_linear_fixture(300, seed=3, coefficient=0.2)
    assert strong_edges == weak_edges == frozenset({("X1", "X2"), ("X2", "X3")})

    _, strong_nl_edges = generate_stage1_nonlinear_fixture(300, seed=3, coefficient=0.7)
    _, weak_nl_edges = generate_stage1_nonlinear_fixture(300, seed=3, coefficient=0.2)
    assert strong_nl_edges == weak_nl_edges == frozenset({("X1", "X2"), ("X3", "X4")})


def test_zero_coefficient_removes_the_nonlinear_dependence() -> None:
    frame, _ = generate_stage1_nonlinear_fixture(5000, seed=4, coefficient=0.0)

    # with coefficient 0, X2 = e2 and X4 = e4, independent of X1 and X3
    from redana.dependence import permutation_distance_correlation

    result = permutation_distance_correlation(
        frame["X1"].to_numpy(), frame["X2"].to_numpy(), permutations=49, seed=9
    )
    assert result.p_value >= 0.1
