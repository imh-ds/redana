"""Tests for the Stage I clean mechanistic fixture generators."""

from __future__ import annotations

import pandas as pd

from redana.scenarios import generate_stage1_linear_fixture, generate_stage1_nonlinear_fixture


def test_linear_fixture_has_correct_shape_and_true_edges() -> None:
    frame, true_edges = generate_stage1_linear_fixture(500, seed=1)

    assert list(frame.columns) == ["X1", "X2", "X3", "X4", "X5", "X6"]
    assert len(frame) == 500
    assert true_edges == frozenset({("X1", "X2"), ("X2", "X3")})


def test_linear_fixture_is_deterministic_given_the_same_seed() -> None:
    first, _ = generate_stage1_linear_fixture(300, seed=7)
    second, _ = generate_stage1_linear_fixture(300, seed=7)

    pd.testing.assert_frame_equal(first, second)


def test_linear_fixture_differs_across_seeds() -> None:
    first, _ = generate_stage1_linear_fixture(300, seed=7)
    second, _ = generate_stage1_linear_fixture(300, seed=8)

    assert not first.equals(second)


def test_nonlinear_fixture_has_correct_shape_and_true_edges() -> None:
    frame, true_edges = generate_stage1_nonlinear_fixture(500, seed=1)

    assert list(frame.columns) == ["X1", "X2", "X3", "X4", "X5", "X6"]
    assert len(frame) == 500
    assert true_edges == frozenset({("X1", "X2"), ("X3", "X4")})


def test_nonlinear_fixture_is_deterministic_given_the_same_seed() -> None:
    first, _ = generate_stage1_nonlinear_fixture(300, seed=9)
    second, _ = generate_stage1_nonlinear_fixture(300, seed=9)

    pd.testing.assert_frame_equal(first, second)


def test_nonlinear_fixture_differs_across_seeds() -> None:
    first, _ = generate_stage1_nonlinear_fixture(300, seed=9)
    second, _ = generate_stage1_nonlinear_fixture(300, seed=10)

    assert not first.equals(second)


def test_nonlinear_fixture_pairs_have_near_zero_linear_covariance() -> None:
    frame, _ = generate_stage1_nonlinear_fixture(20000, seed=2)

    assert abs(frame["X1"].corr(frame["X2"])) < 0.05
    assert abs(frame["X3"].corr(frame["X4"])) < 0.05
