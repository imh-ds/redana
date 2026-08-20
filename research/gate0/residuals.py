"""Cross-fitted, pair-specific residualization for Gate 0 tests."""

from collections.abc import Sequence

import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler

from research.gate0.config import Gate0Config


def predictor_columns(columns: Sequence[str], left: str, right: str) -> tuple[str, ...]:
    """Return the adjustment variables excluding both tested endpoints."""

    return tuple(column for column in columns if column not in {left, right})


def _adjustment_pipeline(config: Gate0Config) -> Pipeline:
    """Build the frozen preprocessing and regression pipeline for one fold."""

    return Pipeline(
        [
            (
                "spline",
                SplineTransformer(
                    n_knots=config.spline_knots,
                    degree=config.spline_degree,
                    include_bias=False,
                    knots="quantile",
                ),
            ),
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=config.ridge_alpha)),
        ]
    )


def cross_fitted_pair_residuals(
    frame: pd.DataFrame, left: str, right: str, config: Gate0Config, seed: int
) -> pd.DataFrame:
    """Return held-out residuals for a pair after pair-specific adjustment."""

    predictors = predictor_columns(frame.columns, left, right)
    design = frame.loc[:, predictors]
    splitter = KFold(n_splits=config.n_splits, shuffle=True, random_state=seed)
    residuals = pd.DataFrame(index=frame.index, columns=[left, right], dtype=float)

    for endpoint in (left, right):
        observed = frame[endpoint]
        for train_rows, test_rows in splitter.split(design):
            model = _adjustment_pipeline(config)
            model.fit(design.iloc[train_rows], observed.iloc[train_rows])
            held_out_prediction = model.predict(design.iloc[test_rows])
            residuals.iloc[test_rows, residuals.columns.get_loc(endpoint)] = (
                observed.iloc[test_rows] - held_out_prediction
            ).to_numpy()

    return residuals
