"""Tests for the Stage II heteroskedasticity parameter on the Stage I fixtures."""

from __future__ import annotations

import numpy as np
import pandas as pd

from redana.scenarios import generate_stage1_linear_fixture, generate_stage1_nonlinear_fixture


def test_default_heteroskedasticity_preserves_stage1_linear_behavior() -> None:
    default_frame, default_edges = generate_stage1_linear_fixture(300, seed=1, coefficient=0.7)
    explicit_frame, explicit_edges = generate_stage1_linear_fixture(
        300, seed=1, coefficient=0.7, heteroskedasticity=0.0
    )

    pd.testing.assert_frame_equal(default_frame, explicit_frame)
    assert default_edges == explicit_edges


def test_default_heteroskedasticity_preserves_stage1_nonlinear_behavior() -> None:
    default_frame, default_edges = generate_stage1_nonlinear_fixture(300, seed=1, coefficient=0.7)
    explicit_frame, explicit_edges = generate_stage1_nonlinear_fixture(
        300, seed=1, coefficient=0.7, heteroskedasticity=0.0
    )

    pd.testing.assert_frame_equal(default_frame, explicit_frame)
    assert default_edges == explicit_edges


def test_heteroskedasticity_widens_conditional_variance_for_large_source_values() -> None:
    frame, _ = generate_stage1_linear_fixture(
        20000, seed=2, coefficient=0.7, heteroskedasticity=1.0
    )
    residual = frame["X2"] - 0.7 * frame["X1"]

    low_decile = frame["X1"].abs() <= frame["X1"].abs().quantile(0.1)
    high_decile = frame["X1"].abs() >= frame["X1"].abs().quantile(0.9)

    low_variance = residual[low_decile].var()
    high_variance = residual[high_decile].var()
    assert high_variance > low_variance


def test_true_edges_are_unchanged_across_heteroskedasticity_values() -> None:
    for het in (0.0, 0.5, 1.0):
        _, edges = generate_stage1_linear_fixture(300, seed=3, heteroskedasticity=het)
        assert edges == frozenset({("X1", "X2"), ("X2", "X3")})

        _, nl_edges = generate_stage1_nonlinear_fixture(300, seed=3, heteroskedasticity=het)
        assert nl_edges == frozenset({("X1", "X2"), ("X3", "X4")})


def test_heteroskedasticity_does_not_reintroduce_linear_covariance_in_the_nonlinear_fixture() -> (
    None
):
    """Regression guard against a round-4-style confound: unlike round 4's skewed
    source distribution (which shifted the source's conditional mean relationship
    and broke the nonlinear fixture's zero-covariance guarantee), heteroskedasticity
    only scales the noise term's *conditional variance*, not its conditional mean,
    so the nonlinear fixture's near-zero population covariance must be preserved
    regardless of heteroskedasticity strength. (The linear fixture's correlation is
    *expected* to shrink as heteroskedasticity increases -- widening residual
    variance naturally weakens the observed correlation, the same effect
    ``noise_scale`` had in round 3 -- so no invariance is asserted there.)
    """

    for het in (0.0, 0.5, 1.0):
        frame, _ = generate_stage1_nonlinear_fixture(
            50000, seed=4, coefficient=0.7, heteroskedasticity=het
        )
        assert abs(frame["X1"].corr(frame["X2"])) < 0.05
        assert abs(frame["X3"].corr(frame["X4"])) < 0.05


def test_heteroskedasticity_is_deterministic_given_the_same_seed() -> None:
    first, _ = generate_stage1_linear_fixture(300, seed=5, heteroskedasticity=0.5)
    second, _ = generate_stage1_linear_fixture(300, seed=5, heteroskedasticity=0.5)
    pd.testing.assert_frame_equal(first, second)


def test_nonzero_heteroskedasticity_changes_the_frame() -> None:
    baseline, _ = generate_stage1_linear_fixture(300, seed=6, heteroskedasticity=0.0)
    hetero, _ = generate_stage1_linear_fixture(300, seed=6, heteroskedasticity=1.0)
    assert not np.allclose(baseline["X2"].to_numpy(), hetero["X2"].to_numpy())
