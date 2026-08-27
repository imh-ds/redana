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


def _apply_measurement_error(
    columns: dict[str, np.ndarray], rng: np.random.Generator, measurement_error: float
) -> dict[str, np.ndarray]:
    """Add independent Gaussian measurement noise to each already-realized column.

    ``measurement_error`` is a noise-to-signal variance ratio relative to
    each column's own realized sample standard deviation, equivalently
    reliability ``1 / (1 + measurement_error)``. At ``0.0`` the columns
    are returned numerically unchanged, since ``sqrt(0) == 0``. Always
    Gaussian, independent of the ``distribution`` parameter, since
    measurement error is conventionally modeled as instrument noise
    distinct from the structural error terms.
    """

    n_rows = next(iter(columns.values())).shape[0]
    noise = rng.standard_normal((len(columns), n_rows))
    scale = np.sqrt(measurement_error)
    return {
        name: column + scale * column.std() * noise_row
        for (name, column), noise_row in zip(columns.items(), noise, strict=True)
    }


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
    measurement_error: float = 0.0,
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
    variable's own draw. ``measurement_error`` defaults to ``0.0``
    (Stage I's exact perfect measurement); Stage II round 6
    (``docs/superpowers/specs/2026-08-25-stage2-measurement-quality-degradation-design.md``)
    sweeps it to study measurement-quality degradation, adding
    independent Gaussian noise to every already-realized column.
    """

    rng = np.random.default_rng(seed)
    e1, e2, e3, e4, e5, e6 = _draw_errors(rng, n_rows, distribution)

    x1 = e1
    x2 = coefficient * x1 + noise_scale * (1 + heteroskedasticity * np.abs(x1)) * e2
    x3 = coefficient * x2 + noise_scale * (1 + heteroskedasticity * np.abs(x2)) * e3
    x4, x5, x6 = e4, e5, e6

    columns = _apply_measurement_error(
        {"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5, "X6": x6}, rng, measurement_error
    )
    frame = pd.DataFrame(columns)
    true_edges = frozenset({("X1", "X2"), ("X2", "X3")})
    return frame, true_edges


def generate_stage2_hub_fixture(
    n_rows: int, seed: int, coefficient: float = _FIXTURE_COEFFICIENT
) -> tuple[pd.DataFrame, frozenset[tuple[str, str]]]:
    """Generate the Stage II round 7 hub fixture: one central variable with three spokes.

    ``outline/plan.md`` section 6's "network structure" dimension:
    "chain -> hubs -> communities -> redundant predictors." ``X1`` is the
    hub, directly driving ``X2``, ``X3``, and ``X4`` (degree 3), versus
    the chain fixture's maximum node degree of 2.
    """

    rng = np.random.default_rng(seed)
    e1, e2, e3, e4, e5, e6 = rng.standard_normal((6, n_rows))

    x1 = e1
    x2 = coefficient * x1 + e2
    x3 = coefficient * x1 + e3
    x4 = coefficient * x1 + e4
    x5, x6 = e5, e6

    frame = pd.DataFrame({"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5, "X6": x6})
    true_edges = frozenset({("X1", "X2"), ("X1", "X3"), ("X1", "X4")})
    return frame, true_edges


def generate_stage2_community_fixture(
    n_rows: int, seed: int, coefficient: float = _FIXTURE_COEFFICIENT
) -> tuple[pd.DataFrame, frozenset[tuple[str, str]]]:
    """Generate the Stage II round 7 community fixture: two disjoint three-node chains.

    ``outline/plan.md`` section 6's "network structure" dimension. Unlike
    the chain fixture (one chain plus three independent columns), this
    fixture has *two* independent structural clusters, each with the
    same already-validated chain topology.
    """

    rng = np.random.default_rng(seed)
    e1, e2, e3, e4, e5, e6 = rng.standard_normal((6, n_rows))

    x1 = e1
    x2 = coefficient * x1 + e2
    x3 = coefficient * x2 + e3
    x4 = e4
    x5 = coefficient * x4 + e5
    x6 = coefficient * x5 + e6

    frame = pd.DataFrame({"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5, "X6": x6})
    true_edges = frozenset({("X1", "X2"), ("X2", "X3"), ("X4", "X5"), ("X5", "X6")})
    return frame, true_edges


def generate_stage2_redundant_predictors_fixture(
    n_rows: int,
    seed: int,
    coefficient: float = _FIXTURE_COEFFICIENT,
    redundancy: float = 0.9,
) -> tuple[pd.DataFrame, frozenset[tuple[str, str]]]:
    """Generate the Stage II round 7 redundant-predictors fixture.

    ``outline/plan.md`` section 6's "network structure" dimension. ``X2``
    is a near-collinear ("redundant") copy of ``X1`` (correlation
    ``redundancy``), but only ``X1`` is a true direct cause of ``X3``.
    Detecting ``(X2, X3)`` would be a false positive driven by
    collinearity, not a real direct effect -- the central question this
    fixture tests.
    """

    rng = np.random.default_rng(seed)
    e1, e2, e3, e4, e5, e6 = rng.standard_normal((6, n_rows))

    x1 = e1
    x2 = redundancy * x1 + np.sqrt(1 - redundancy**2) * e2
    x3 = coefficient * x1 + e3
    x4, x5, x6 = e4, e5, e6

    frame = pd.DataFrame({"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5, "X6": x6})
    true_edges = frozenset({("X1", "X3")})
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


def generate_stage3_hybrid_fixture(
    n_rows: int,
    seed: int,
    strong_coefficient: float = 0.7,
    moderate_coefficient: float = 0.4,
    weak_coefficient: float = 0.25,
    redundancy: float = 0.85,
) -> tuple[pd.DataFrame, frozenset[tuple[str, str]], frozenset[tuple[str, str]]]:
    """Generate the Stage III round 1 hybrid fixture: two hub communities,
    mixed edge types, heterogeneous strength, a redundant pair, and isolated nodes.

    Per
    ``docs/superpowers/specs/2026-08-27-stage3-hybrid-benchmark-round1-charter.md``
    decision 1: 12 nodes, reusing ``generate_stage2_hub_fixture``'s
    degree-3 hub/spoke shape twice (community A: ``X1`` hub with spokes
    ``X2``-``X4``; community B: ``X7`` hub with spokes ``X8``-``X10``),
    joined by one weak nonlinear bridge edge (``X1``-``X12``) crossing
    between the two communities. Each community's spokes span round 1's
    strong/moderate strength zones and include one nonlinear spoke
    (reusing the F3-validated ``coefficient*(Z^2-1)`` shape), so true
    edges are a linear majority (4 linear, 3 nonlinear) rather than one
    fixed relationship family. ``X5`` is a redundant/collinear copy of
    ``X1`` (correlation ``redundancy``, reusing
    ``generate_stage2_redundant_predictors_fixture``'s pattern) with no
    true edge of its own -- a direct false-positive-under-collinearity
    test. ``X6`` and ``X11`` carry no true edges at all, to observe
    false-positive behavior under realistic sparsity.
    """

    rng = np.random.default_rng(seed)
    e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12 = rng.standard_normal((12, n_rows))

    x1 = e1
    x2 = strong_coefficient * x1 + e2
    x3 = moderate_coefficient * x1 + e3
    x4 = moderate_coefficient * (x1**2 - 1) + e4
    x5 = redundancy * x1 + np.sqrt(1 - redundancy**2) * e5
    x6 = e6

    x7 = e7
    x8 = strong_coefficient * x7 + e8
    x9 = moderate_coefficient * x7 + e9
    x10 = moderate_coefficient * (x7**2 - 1) + e10
    x11 = e11
    x12 = weak_coefficient * (x1**2 - 1) + e12

    frame = pd.DataFrame(
        {
            "X1": x1,
            "X2": x2,
            "X3": x3,
            "X4": x4,
            "X5": x5,
            "X6": x6,
            "X7": x7,
            "X8": x8,
            "X9": x9,
            "X10": x10,
            "X11": x11,
            "X12": x12,
        }
    )
    true_linear_edges = frozenset({("X1", "X2"), ("X1", "X3"), ("X7", "X8"), ("X7", "X9")})
    true_nonlinear_edges = frozenset({("X1", "X4"), ("X7", "X10"), ("X1", "X12")})
    return frame, true_linear_edges, true_nonlinear_edges


def stage3_hybrid_known_real_extra_edges() -> frozenset[tuple[str, str]]:
    """Return the Stage III hybrid fixture's known-real edges outside the designed true-edge set.

    ``X5 = redundancy*X1 + noise`` (see ``generate_stage3_hybrid_fixture``)
    is mechanistically the same kind of constructed relationship as
    ``X2 = strong_coefficient*X1 + noise`` -- a true edge in that
    fixture -- just a different coefficient. There is no principled
    statistical basis for treating one as real and the other as a false
    positive when both were built identically; ``(X1, X5)`` was
    deliberately excluded from the *designed* true-edge set (it exists to
    test false-positive robustness under collinearity, not as a direct
    structural edge), but it is real for scoring purposes -- flagging it
    is correct detection, not a false positive. See
    ``docs/evidence/stage3-permutation-resolution-diagnostic-20260827.md``
    for the original correction this formalizes.
    """

    return frozenset({("X1", "X5")})


def stage3_hybrid_scoring_true_edges(
    true_linear_edges: frozenset[tuple[str, str]],
    true_nonlinear_edges: frozenset[tuple[str, str]],
) -> frozenset[tuple[str, str]]:
    """Return the Stage III hybrid fixture's true-edge set used for scoring false positives.

    Distinct from the *designed* true-edge set
    (``generate_stage3_hybrid_fixture``'s own return values, used for the
    recovery metric, which is specifically about the deliberately-
    constructed structural edges): this adds
    ``stage3_hybrid_known_real_extra_edges``, so that a real relationship
    excluded from the design for other reasons is never counted as a
    false positive.
    """

    return true_linear_edges | true_nonlinear_edges | stage3_hybrid_known_real_extra_edges()


def generate_stage1_nonlinear_fixture(
    n_rows: int,
    seed: int,
    coefficient: float = _FIXTURE_COEFFICIENT,
    noise_scale: float = 1.0,
    distribution: str = "gaussian",
    heteroskedasticity: float = 0.0,
    measurement_error: float = 0.0,
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
    ``measurement_error`` defaults to ``0.0`` (Stage I's exact perfect
    measurement); Stage II round 6 sweeps it to study measurement-
    quality degradation, adding independent Gaussian noise to every
    already-realized column.
    """

    rng = np.random.default_rng(seed)
    e1, e2, e3, e4, e5, e6 = _draw_errors(rng, n_rows, distribution)

    x1 = e1
    x2 = coefficient * (x1**2 - 1) + noise_scale * (1 + heteroskedasticity * np.abs(x1)) * e2
    x3 = e3
    x4 = coefficient * (x3**2 - 1) + noise_scale * (1 + heteroskedasticity * np.abs(x3)) * e4
    x5, x6 = e5, e6

    columns = _apply_measurement_error(
        {"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5, "X6": x6}, rng, measurement_error
    )
    frame = pd.DataFrame(columns)
    true_edges = frozenset({("X1", "X2"), ("X3", "X4")})
    return frame, true_edges
