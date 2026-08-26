"""Tests for the Stage II measurement-error parameter on the Stage I fixtures."""

from __future__ import annotations

import pandas as pd

from redana.scenarios import generate_stage1_linear_fixture, generate_stage1_nonlinear_fixture


def test_default_measurement_error_preserves_stage1_linear_behavior() -> None:
    default_frame, default_edges = generate_stage1_linear_fixture(300, seed=1, coefficient=0.7)
    explicit_frame, explicit_edges = generate_stage1_linear_fixture(
        300, seed=1, coefficient=0.7, measurement_error=0.0
    )

    pd.testing.assert_frame_equal(default_frame, explicit_frame)
    assert default_edges == explicit_edges


def test_default_measurement_error_preserves_stage1_nonlinear_behavior() -> None:
    default_frame, default_edges = generate_stage1_nonlinear_fixture(300, seed=1, coefficient=0.7)
    explicit_frame, explicit_edges = generate_stage1_nonlinear_fixture(
        300, seed=1, coefficient=0.7, measurement_error=0.0
    )

    pd.testing.assert_frame_equal(default_frame, explicit_frame)
    assert default_edges == explicit_edges


def test_measurement_error_increases_every_columns_variance() -> None:
    perfect_frame, _ = generate_stage1_linear_fixture(
        5000, seed=2, coefficient=0.7, measurement_error=0.0
    )
    noisy_frame, _ = generate_stage1_linear_fixture(
        5000, seed=2, coefficient=0.7, measurement_error=1.0
    )

    for column in ("X1", "X2", "X3", "X4", "X5", "X6"):
        assert noisy_frame[column].var() > perfect_frame[column].var()


def test_true_edges_are_unchanged_across_measurement_error_values() -> None:
    for measurement_error in (0.0, 0.25, 1.0):
        _, edges = generate_stage1_linear_fixture(300, seed=3, measurement_error=measurement_error)
        assert edges == frozenset({("X1", "X2"), ("X2", "X3")})

        _, nl_edges = generate_stage1_nonlinear_fixture(
            300, seed=3, measurement_error=measurement_error
        )
        assert nl_edges == frozenset({("X1", "X2"), ("X3", "X4")})


def test_measurement_error_does_not_reintroduce_linear_covariance_in_the_nonlinear_fixture() -> (
    None
):
    """Regression guard against a round-4-style confound: independent, zero-mean
    measurement noise added to already-realized columns cannot shift a conditional
    mean, so the nonlinear fixture's near-zero population covariance must be
    preserved regardless of measurement_error strength.
    """

    for measurement_error in (0.0, 0.25, 1.0):
        frame, _ = generate_stage1_nonlinear_fixture(
            50000, seed=4, coefficient=0.7, measurement_error=measurement_error
        )
        assert abs(frame["X1"].corr(frame["X2"])) < 0.05
        assert abs(frame["X3"].corr(frame["X4"])) < 0.05


def test_measurement_error_is_deterministic_given_the_same_seed() -> None:
    first, _ = generate_stage1_linear_fixture(300, seed=5, measurement_error=0.5)
    second, _ = generate_stage1_linear_fixture(300, seed=5, measurement_error=0.5)
    pd.testing.assert_frame_equal(first, second)
