import numpy as np
import pandas as pd

from research.gate0.config import SMOKE_PROFILE, Gate0Config
from research.gate0 import residuals as residuals_module
from research.gate0.residuals import (
    cross_fitted_pair_quadratic_residuals,
    cross_fitted_pair_residuals,
    predictor_columns,
    quadratic_adjustment_features,
)


def test_endpoints_are_excluded_from_both_adjustment_designs() -> None:
    assert predictor_columns(("X1", "X2", "X3", "X4"), "X1", "X2") == ("X3", "X4")


def test_cross_fitted_residuals_have_one_value_per_input_row() -> None:
    rng = np.random.default_rng(2)
    frame = pd.DataFrame(rng.normal(size=(100, 6)), columns=[f"X{i}" for i in range(1, 7)])

    residuals = cross_fitted_pair_residuals(frame, "X1", "X2", Gate0Config(SMOKE_PROFILE), seed=4)

    assert residuals.shape == (100, 2)
    assert residuals.columns.tolist() == ["X1", "X2"]
    assert residuals.notna().all().all()


def test_quadratic_adjustment_features_keep_raw_then_square_per_column() -> None:
    design = pd.DataFrame({"X3": [2.0, -1.0], "X4": [3.0, 4.0]})

    actual = quadratic_adjustment_features(design)

    assert list(actual.columns) == ["X3", "X3_squared", "X4", "X4_squared"]
    assert actual.to_dict("list") == {
        "X3": [2.0, -1.0],
        "X3_squared": [4.0, 1.0],
        "X4": [3.0, 4.0],
        "X4_squared": [9.0, 16.0],
    }


def test_quadratic_residuals_use_five_fitted_ridge_models_without_splines(
    monkeypatch,
) -> None:
    frame = pd.DataFrame(
        {
            "X1": np.arange(10, dtype=float),
            "X2": np.arange(10, dtype=float) * 2,
            "X3": np.linspace(-1, 1, 10),
        },
        index=np.arange(100, 110),
    )
    fit_calls = []

    class FakePipeline:
        def fit(self, design, observed):
            fit_calls.append((design.copy(), observed.copy()))
            self.mean = observed.mean()
            return self

        def predict(self, design):
            return np.full(len(design), self.mean)

    monkeypatch.setattr(residuals_module, "_quadratic_adjustment_pipeline", lambda config: FakePipeline())

    def fail_if_spline_constructed(*args, **kwargs):
        raise AssertionError("quadratic residualization must not construct a spline")

    monkeypatch.setattr(residuals_module, "SplineTransformer", fail_if_spline_constructed)

    actual = cross_fitted_pair_quadratic_residuals(
        frame, "X1", "X2", Gate0Config(SMOKE_PROFILE), seed=4
    )

    assert len(fit_calls) == 10
    assert actual.index.equals(frame.index)
    assert actual.columns.tolist() == ["X1", "X2"]
    assert np.isfinite(actual.to_numpy()).all()
