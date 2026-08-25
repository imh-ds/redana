"""Frozen synthetic scenarios for redana prototype validation."""

from __future__ import annotations

import numpy as np
import pandas as pd

_FIXTURE_COEFFICIENT = 0.7


def generate_step4_validation_frame(
    n_rows: int, seed: int
) -> tuple[pd.DataFrame, frozenset[tuple[str, str]], frozenset[tuple[str, str]]]:
    """Generate the frozen p=6 Step 4 first synthetic validation scenario.

    Two linear chain edges (X1-X2, X2-X3), one pure-nonlinear direct edge
    with zero linear covariance (X4-X5, reusing the F3-validated shape
    ``X5 = 0.7*(X4^2-1)+e5``), and one fully independent column (X6).
    """

    rng = np.random.default_rng(seed)
    e1, e2, e3, e4, e5, e6 = rng.standard_normal((6, n_rows))

    x1 = e1
    x2 = _FIXTURE_COEFFICIENT * x1 + e2
    x3 = _FIXTURE_COEFFICIENT * x2 + e3
    x4 = e4
    x5 = _FIXTURE_COEFFICIENT * (x4**2 - 1) + e5
    x6 = e6

    frame = pd.DataFrame({"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5, "X6": x6})
    true_linear_edges = frozenset({("X1", "X2"), ("X2", "X3")})
    true_nonlinear_edges = frozenset({("X4", "X5")})
    return frame, true_linear_edges, true_nonlinear_edges
