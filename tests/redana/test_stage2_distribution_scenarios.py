"""Tests for the Stage II distribution parameter on the Stage I fixtures."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from redana.scenarios import generate_stage1_linear_fixture, generate_stage1_nonlinear_fixture


def test_default_distribution_preserves_stage1_linear_behavior() -> None:
    default_frame, default_edges = generate_stage1_linear_fixture(300, seed=1, coefficient=0.7)
    explicit_frame, explicit_edges = generate_stage1_linear_fixture(
        300, seed=1, coefficient=0.7, distribution="gaussian"
    )

    pd.testing.assert_frame_equal(default_frame, explicit_frame)
    assert default_edges == explicit_edges


def test_default_distribution_preserves_stage1_nonlinear_behavior() -> None:
    default_frame, default_edges = generate_stage1_nonlinear_fixture(300, seed=1, coefficient=0.7)
    explicit_frame, explicit_edges = generate_stage1_nonlinear_fixture(
        300, seed=1, coefficient=0.7, distribution="gaussian"
    )

    pd.testing.assert_frame_equal(default_frame, explicit_frame)
    assert default_edges == explicit_edges


@pytest.mark.parametrize("distribution", ["gaussian", "skewed", "heavy_tailed"])
def test_error_terms_are_standardized(distribution: str) -> None:
    frame, _ = generate_stage1_linear_fixture(
        20000, seed=2, coefficient=0.0, noise_scale=1.0, distribution=distribution
    )
    # coefficient=0.0 makes X4, X5, X6 pure error draws. heavy_tailed
    # (Student's t, df=3) has infinite theoretical kurtosis, so its
    # sample variance is inherently unstable even at large n -- this is
    # an expected statistical property of the distribution, not
    # evidence of a bug, so it gets a much looser tolerance than the
    # other two distributions' well-behaved sample variances.
    variance_tolerance = 1.5 if distribution == "heavy_tailed" else 0.1
    for column in ("X4", "X5", "X6"):
        assert abs(frame[column].mean()) < 0.05
        assert abs(frame[column].var() - 1.0) < variance_tolerance


def test_skewed_distribution_has_positive_skewness() -> None:
    frame, _ = generate_stage1_linear_fixture(
        20000, seed=3, coefficient=0.0, distribution="skewed"
    )
    gaussian_frame, _ = generate_stage1_linear_fixture(
        20000, seed=3, coefficient=0.0, distribution="gaussian"
    )

    skewed_skewness = frame["X4"].skew()
    gaussian_skewness = gaussian_frame["X4"].skew()
    assert skewed_skewness > 0.5
    assert abs(gaussian_skewness) < 0.2


def test_true_edges_are_unchanged_across_distributions() -> None:
    for distribution in ("gaussian", "skewed", "heavy_tailed"):
        _, edges = generate_stage1_linear_fixture(300, seed=4, distribution=distribution)
        assert edges == frozenset({("X1", "X2"), ("X2", "X3")})

        _, nl_edges = generate_stage1_nonlinear_fixture(300, seed=4, distribution=distribution)
        assert nl_edges == frozenset({("X1", "X2"), ("X3", "X4")})


def test_invalid_distribution_raises() -> None:
    with pytest.raises(ValueError, match="distribution"):
        generate_stage1_linear_fixture(300, seed=5, distribution="uniform")

    with pytest.raises(ValueError, match="distribution"):
        generate_stage1_nonlinear_fixture(300, seed=5, distribution="uniform")


def test_distribution_is_deterministic_given_the_same_seed() -> None:
    first, _ = generate_stage1_linear_fixture(300, seed=6, distribution="heavy_tailed")
    second, _ = generate_stage1_linear_fixture(300, seed=6, distribution="heavy_tailed")
    pd.testing.assert_frame_equal(first, second)


def test_heavy_tailed_and_skewed_differ_from_gaussian() -> None:
    gaussian, _ = generate_stage1_linear_fixture(300, seed=7, distribution="gaussian")
    skewed, _ = generate_stage1_linear_fixture(300, seed=7, distribution="skewed")
    heavy_tailed, _ = generate_stage1_linear_fixture(300, seed=7, distribution="heavy_tailed")

    assert not np.allclose(gaussian["X4"].to_numpy(), skewed["X4"].to_numpy())
    assert not np.allclose(gaussian["X4"].to_numpy(), heavy_tailed["X4"].to_numpy())
