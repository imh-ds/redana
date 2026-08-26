"""Tests for the Stage II noise-scale parameter on the Stage I fixtures."""

from __future__ import annotations

import pandas as pd

from redana.scenarios import generate_stage1_linear_fixture, generate_stage1_nonlinear_fixture


def test_default_noise_scale_preserves_stage1_linear_behavior() -> None:
    default_frame, default_edges = generate_stage1_linear_fixture(300, seed=1, coefficient=0.7)
    explicit_frame, explicit_edges = generate_stage1_linear_fixture(
        300, seed=1, coefficient=0.7, noise_scale=1.0
    )

    pd.testing.assert_frame_equal(default_frame, explicit_frame)
    assert default_edges == explicit_edges


def test_default_noise_scale_preserves_stage1_nonlinear_behavior() -> None:
    default_frame, default_edges = generate_stage1_nonlinear_fixture(300, seed=1, coefficient=0.7)
    explicit_frame, explicit_edges = generate_stage1_nonlinear_fixture(
        300, seed=1, coefficient=0.7, noise_scale=1.0
    )

    pd.testing.assert_frame_equal(default_frame, explicit_frame)
    assert default_edges == explicit_edges


def test_smaller_noise_scale_increases_the_linear_correlation() -> None:
    low_noise_frame, _ = generate_stage1_linear_fixture(
        5000, seed=2, coefficient=0.7, noise_scale=0.5
    )
    baseline_frame, _ = generate_stage1_linear_fixture(
        5000, seed=2, coefficient=0.7, noise_scale=1.0
    )
    high_noise_frame, _ = generate_stage1_linear_fixture(
        5000, seed=2, coefficient=0.7, noise_scale=2.0
    )

    low_correlation = abs(low_noise_frame["X1"].corr(low_noise_frame["X2"]))
    baseline_correlation = abs(baseline_frame["X1"].corr(baseline_frame["X2"]))
    high_correlation = abs(high_noise_frame["X1"].corr(high_noise_frame["X2"]))
    assert low_correlation > baseline_correlation > high_correlation


def test_true_edges_are_unchanged_across_noise_scale_values() -> None:
    _, low_edges = generate_stage1_linear_fixture(300, seed=3, coefficient=0.7, noise_scale=0.5)
    _, high_edges = generate_stage1_linear_fixture(300, seed=3, coefficient=0.7, noise_scale=2.0)
    assert low_edges == high_edges == frozenset({("X1", "X2"), ("X2", "X3")})

    _, low_nl_edges = generate_stage1_nonlinear_fixture(
        300, seed=3, coefficient=0.7, noise_scale=0.5
    )
    _, high_nl_edges = generate_stage1_nonlinear_fixture(
        300, seed=3, coefficient=0.7, noise_scale=2.0
    )
    assert low_nl_edges == high_nl_edges == frozenset({("X1", "X2"), ("X3", "X4")})


def test_noise_scale_does_not_change_source_variable_variance() -> None:
    low_noise_frame, _ = generate_stage1_linear_fixture(
        5000, seed=4, coefficient=0.7, noise_scale=0.5
    )
    high_noise_frame, _ = generate_stage1_linear_fixture(
        5000, seed=4, coefficient=0.7, noise_scale=2.0
    )

    # X1 is the source variable and is drawn independently of noise_scale,
    # so it must be identical across both frames given the same seed.
    pd.testing.assert_series_equal(low_noise_frame["X1"], high_noise_frame["X1"])
