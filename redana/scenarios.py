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


def generate_stage1_linear_fixture(
    n_rows: int, seed: int, coefficient: float = _FIXTURE_COEFFICIENT
) -> tuple[pd.DataFrame, frozenset[tuple[str, str]]]:
    """Generate the Stage I linear fixture: a linear chain plus three independent columns.

    ``outline/plan.md`` section 5's "linear fixture": the incumbent
    should recover the structure well, and the residual layer should add
    approximately nothing beyond it. ``coefficient`` defaults to Stage
    I's exact strength (``0.7``); Stage II round 1
    (``docs/superpowers/specs/2026-08-25-stage2-effect-strength-degradation-design.md``)
    sweeps it to study effect-strength degradation.
    """

    rng = np.random.default_rng(seed)
    e1, e2, e3, e4, e5, e6 = rng.standard_normal((6, n_rows))

    x1 = e1
    x2 = coefficient * x1 + e2
    x3 = coefficient * x2 + e3
    x4, x5, x6 = e4, e5, e6

    frame = pd.DataFrame({"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5, "X6": x6})
    true_edges = frozenset({("X1", "X2"), ("X2", "X3")})
    return frame, true_edges


def generate_stage1_nonlinear_fixture(
    n_rows: int, seed: int, coefficient: float = _FIXTURE_COEFFICIENT
) -> tuple[pd.DataFrame, frozenset[tuple[str, str]]]:
    """Generate the Stage I pure nonlinear fixture: two independent quadratic pairs.

    ``outline/plan.md`` section 5's "pure nonlinear fixture": the
    incumbent may miss this nonlinear-only structure, while the residual
    layer should detect a useful proportion of it. Reuses the
    F3/Step4-validated shape (``coefficient*(Z^2-1)``), which has exactly
    zero linear covariance with its source in population regardless of
    ``coefficient``. ``coefficient`` defaults to Stage I's exact strength
    (``0.7``); Stage II round 1 sweeps it to study effect-strength
    degradation.
    """

    rng = np.random.default_rng(seed)
    e1, e2, e3, e4, e5, e6 = rng.standard_normal((6, n_rows))

    x1 = e1
    x2 = coefficient * (x1**2 - 1) + e2
    x3 = e3
    x4 = coefficient * (x3**2 - 1) + e4
    x5, x6 = e5, e6

    frame = pd.DataFrame({"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5, "X6": x6})
    true_edges = frozenset({("X1", "X2"), ("X3", "X4")})
    return frame, true_edges
