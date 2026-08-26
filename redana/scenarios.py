"""Frozen synthetic scenarios for redana prototype validation."""

from __future__ import annotations

import numpy as np
import pandas as pd

_FIXTURE_COEFFICIENT = 0.7
_VALID_DISTRIBUTIONS = frozenset({"gaussian", "skewed", "heavy_tailed"})


def _draw_errors(
    rng: np.random.Generator, n_rows: int, distribution: str
) -> tuple[np.ndarray, ...]:
    """Draw six standardized (mean 0, variance 1) error columns.

    ``distribution`` selects the shape: ``"gaussian"`` (standard normal),
    ``"skewed"`` (centered/scaled chi-squared, df=3, positive skew), or
    ``"heavy_tailed"`` (scaled Student's t, df=3, heavier tails than
    Gaussian). All three are standardized to the same mean and variance
    so only distributional shape varies, matching
    ``outline/plan.md`` section 6's "Gaussian -> skewed -> heavy-tailed"
    dimension.
    """

    if distribution not in _VALID_DISTRIBUTIONS:
        raise ValueError(
            f"unknown distribution {distribution!r}; expected one of {sorted(_VALID_DISTRIBUTIONS)}"
        )

    if distribution == "gaussian":
        draws = rng.standard_normal((6, n_rows))
    elif distribution == "skewed":
        draws = (rng.chisquare(df=3, size=(6, n_rows)) - 3) / np.sqrt(6)
    else:
        draws = rng.standard_t(df=3, size=(6, n_rows)) / np.sqrt(3)

    return tuple(draws)


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
    n_rows: int,
    seed: int,
    coefficient: float = _FIXTURE_COEFFICIENT,
    noise_scale: float = 1.0,
    distribution: str = "gaussian",
    heteroskedasticity: float = 0.0,
) -> tuple[pd.DataFrame, frozenset[tuple[str, str]]]:
    """Generate the Stage I linear fixture: a linear chain plus three independent columns.

    ``outline/plan.md`` section 5's "linear fixture": the incumbent
    should recover the structure well, and the residual layer should add
    approximately nothing beyond it. ``coefficient`` defaults to Stage
    I's exact strength (``0.7``); Stage II round 1
    (``docs/superpowers/specs/2026-08-25-stage2-effect-strength-degradation-design.md``)
    sweeps it to study effect-strength degradation. ``noise_scale``
    defaults to ``1.0`` (Stage I's exact residual noise magnitude);
    Stage II round 3
    (``docs/superpowers/specs/2026-08-25-stage2-noise-degradation-design.md``)
    sweeps it to study noise degradation, scaling only each downstream
    variable's own residual noise term, not the source variables' noise.
    ``distribution`` defaults to ``"gaussian"`` (Stage I's exact error
    shape); Stage II round 4
    (``docs/superpowers/specs/2026-08-25-stage2-distribution-degradation-design.md``)
    sweeps it to study distribution degradation. ``heteroskedasticity``
    defaults to ``0.0`` (Stage I's exact constant-variance noise); Stage
    II round 5
    (``docs/superpowers/specs/2026-08-25-stage2-residual-variance-degradation-design.md``)
    sweeps it to study residual-variance degradation, scaling each
    downstream variable's own residual noise standard deviation by
    ``1 + heteroskedasticity * abs(source)``, never touching a source
    variable's own draw.
    """

    rng = np.random.default_rng(seed)
    e1, e2, e3, e4, e5, e6 = _draw_errors(rng, n_rows, distribution)

    x1 = e1
    x2 = coefficient * x1 + noise_scale * (1 + heteroskedasticity * np.abs(x1)) * e2
    x3 = coefficient * x2 + noise_scale * (1 + heteroskedasticity * np.abs(x2)) * e3
    x4, x5, x6 = e4, e5, e6

    frame = pd.DataFrame({"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5, "X6": x6})
    true_edges = frozenset({("X1", "X2"), ("X2", "X3")})
    return frame, true_edges


def generate_stage2_shape_fixture(
    n_rows: int, seed: int, shape: float, coefficient: float = _FIXTURE_COEFFICIENT
) -> tuple[pd.DataFrame, frozenset[tuple[str, str]]]:
    """Generate the Stage II round 2 relationship-shape fixture: two independent pairs
    blending a linear term and a centered quadratic term.

    ``outline/plan.md`` section 6's "relationship shape" dimension: "pure
    linear -> slight curvature -> moderate curvature -> strong
    nonlinearity." ``shape`` blends the two terms linearly (``0.0`` is
    pure linear, ``1.0`` is pure quadratic, reproducing
    ``generate_stage1_nonlinear_fixture`` exactly at the same
    ``coefficient``). ``coefficient`` defaults to Stage I's strong
    baseline (``0.7``) and is held fixed by Stage II round 2
    (``docs/superpowers/specs/2026-08-25-stage2-relationship-shape-degradation-design.md``),
    which sweeps ``shape`` instead.
    """

    rng = np.random.default_rng(seed)
    e1, e2, e3, e4, e5, e6 = rng.standard_normal((6, n_rows))

    x1 = e1
    x2 = coefficient * ((1 - shape) * x1 + shape * (x1**2 - 1)) + e2
    x3 = e3
    x4 = coefficient * ((1 - shape) * x3 + shape * (x3**2 - 1)) + e4
    x5, x6 = e5, e6

    frame = pd.DataFrame({"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5, "X6": x6})
    true_edges = frozenset({("X1", "X2"), ("X3", "X4")})
    return frame, true_edges


def generate_stage1_nonlinear_fixture(
    n_rows: int,
    seed: int,
    coefficient: float = _FIXTURE_COEFFICIENT,
    noise_scale: float = 1.0,
    distribution: str = "gaussian",
    heteroskedasticity: float = 0.0,
) -> tuple[pd.DataFrame, frozenset[tuple[str, str]]]:
    """Generate the Stage I pure nonlinear fixture: two independent quadratic pairs.

    ``outline/plan.md`` section 5's "pure nonlinear fixture": the
    incumbent may miss this nonlinear-only structure, while the residual
    layer should detect a useful proportion of it. Reuses the
    F3/Step4-validated shape (``coefficient*(Z^2-1)``), which has exactly
    zero linear covariance with its source in population regardless of
    ``coefficient``. ``coefficient`` defaults to Stage I's exact strength
    (``0.7``); Stage II round 1 sweeps it to study effect-strength
    degradation. ``noise_scale`` defaults to ``1.0`` (Stage I's exact
    residual noise magnitude); Stage II round 3 sweeps it to study noise
    degradation, scaling only each downstream variable's own residual
    noise term, not the source variables' noise. ``distribution``
    defaults to ``"gaussian"`` (Stage I's exact error shape); Stage II
    round 4 sweeps it to study distribution degradation.
    ``heteroskedasticity`` defaults to ``0.0`` (Stage I's exact
    constant-variance noise); Stage II round 5 sweeps it to study
    residual-variance degradation, scaling each downstream variable's own
    residual noise standard deviation by ``1 + heteroskedasticity *
    abs(source)``, never touching a source variable's own draw.
    """

    rng = np.random.default_rng(seed)
    e1, e2, e3, e4, e5, e6 = _draw_errors(rng, n_rows, distribution)

    x1 = e1
    x2 = coefficient * (x1**2 - 1) + noise_scale * (1 + heteroskedasticity * np.abs(x1)) * e2
    x3 = e3
    x4 = coefficient * (x3**2 - 1) + noise_scale * (1 + heteroskedasticity * np.abs(x3)) * e4
    x5, x6 = e5, e6

    frame = pd.DataFrame({"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5, "X6": x6})
    true_edges = frozenset({("X1", "X2"), ("X3", "X4")})
    return frame, true_edges
