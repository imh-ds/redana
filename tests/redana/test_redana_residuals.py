"""Tests for the redana-promoted pair-specific cross-fitted residualization."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from redana.residuals import PrototypeConfig, cross_fitted_pair_residuals, predictor_columns
from research.gate0.config import Gate0Config, ComputationalProfile
from research.gate0.residuals import cross_fitted_pair_residuals as gate0_cross_fitted_pair_residuals


def _config() -> PrototypeConfig:
    return PrototypeConfig(n_splits=5, spline_knots=5, spline_degree=3, ridge_alpha=1.0)


def _synthetic_frame(rows: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = rng.standard_normal((rows, 4))
    return pd.DataFrame(data, columns=["X1", "X2", "X3", "X4"])


def test_predictor_columns_excludes_the_tested_pair() -> None:
    columns = ["X1", "X2", "X3", "X4"]
    assert predictor_columns(columns, "X1", "X3") == ("X2", "X4")


def test_residuals_are_held_out_and_approximately_mean_zero_for_independent_columns() -> None:
    frame = _synthetic_frame(300, seed=1)
    residuals = cross_fitted_pair_residuals(frame, "X1", "X2", _config(), seed=7)

    assert list(residuals.columns) == ["X1", "X2"]
    assert len(residuals) == 300
    assert residuals.notna().all().all()
    assert abs(residuals["X1"].mean()) < 0.2
    assert abs(residuals["X2"].mean()) < 0.2


def test_parity_with_gate0_original_on_identical_seeded_input() -> None:
    frame = _synthetic_frame(200, seed=3)
    gate0_config = Gate0Config(
        ComputationalProfile("parity", 200, 200, 1, 19),
        n_splits=5,
        spline_knots=5,
        spline_degree=3,
        ridge_alpha=1.0,
    )
    prototype_config = _config()

    gate0_residuals = gate0_cross_fitted_pair_residuals(frame, "X1", "X2", gate0_config, seed=11)
    redana_residuals = cross_fitted_pair_residuals(frame, "X1", "X2", prototype_config, seed=11)

    pd.testing.assert_frame_equal(gate0_residuals, redana_residuals)


def test_residuals_reject_mismatched_pair_columns() -> None:
    frame = _synthetic_frame(50, seed=5)
    with pytest.raises(KeyError):
        cross_fitted_pair_residuals(frame, "X1", "X9", _config(), seed=1)
