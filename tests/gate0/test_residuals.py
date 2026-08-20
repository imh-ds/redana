import numpy as np
import pandas as pd

from research.gate0.config import SMOKE_PROFILE, Gate0Config
from research.gate0.residuals import cross_fitted_pair_residuals, predictor_columns


def test_endpoints_are_excluded_from_both_adjustment_designs() -> None:
    assert predictor_columns(("X1", "X2", "X3", "X4"), "X1", "X2") == ("X3", "X4")


def test_cross_fitted_residuals_have_one_value_per_input_row() -> None:
    rng = np.random.default_rng(2)
    frame = pd.DataFrame(rng.normal(size=(100, 6)), columns=[f"X{i}" for i in range(1, 7)])

    residuals = cross_fitted_pair_residuals(frame, "X1", "X2", Gate0Config(SMOKE_PROFILE), seed=4)

    assert residuals.shape == (100, 2)
    assert residuals.columns.tolist() == ["X1", "X2"]
    assert residuals.notna().all().all()
