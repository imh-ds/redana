"""Tests for the Stage II round 2 relationship-shape fixture."""

from __future__ import annotations

import pandas as pd

from redana.scenarios import generate_stage1_nonlinear_fixture, generate_stage2_shape_fixture


def test_true_edges_are_unchanged_across_shape_values() -> None:
    _, edges_linear = generate_stage2_shape_fixture(300, seed=1, shape=0.0)
    _, edges_slight = generate_stage2_shape_fixture(300, seed=1, shape=0.33)
    _, edges_moderate = generate_stage2_shape_fixture(300, seed=1, shape=0.67)
    _, edges_nonlinear = generate_stage2_shape_fixture(300, seed=1, shape=1.0)

    expected = frozenset({("X1", "X2"), ("X3", "X4")})
    assert edges_linear == edges_slight == edges_moderate == edges_nonlinear == expected


def test_shape_zero_is_pure_linear() -> None:
    frame, _ = generate_stage2_shape_fixture(5000, seed=2, shape=0.0, coefficient=0.7)

    # at shape=0 the quadratic term drops out entirely: X2 = 0.7*X1 + e2
    correlation = frame["X1"].corr(frame["X2"])
    # population correlation for X2 = 0.7*X1 + e2 with X1, e2 ~ N(0,1) is
    # 0.7 / sqrt(0.7^2 + 1) ~= 0.573
    assert abs(correlation - 0.573) < 0.02


def test_shape_one_matches_stage1_nonlinear_fixture_exactly() -> None:
    shape_frame, shape_edges = generate_stage2_shape_fixture(
        300, seed=3, shape=1.0, coefficient=0.7
    )
    stage1_frame, stage1_edges = generate_stage1_nonlinear_fixture(300, seed=3, coefficient=0.7)

    pd.testing.assert_frame_equal(shape_frame, stage1_frame)
    assert shape_edges == stage1_edges


def test_intermediate_shape_differs_from_both_endpoints() -> None:
    linear_frame, _ = generate_stage2_shape_fixture(300, seed=4, shape=0.0)
    nonlinear_frame, _ = generate_stage2_shape_fixture(300, seed=4, shape=1.0)
    intermediate_frame, _ = generate_stage2_shape_fixture(300, seed=4, shape=0.33)

    assert not intermediate_frame["X2"].equals(linear_frame["X2"])
    assert not intermediate_frame["X2"].equals(nonlinear_frame["X2"])
