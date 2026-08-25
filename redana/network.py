"""Frozen EBIC-selected graphical-lasso incumbent linear network.

Native-Python stand-in for the psychometric-network literature's
EBICglasso (``qgraph::EBICglasso`` in R), avoiding an R dependency per
``docs/superpowers/specs/2026-08-25-step4-minimal-prototype-charter.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.covariance import graphical_lasso

_DEFAULT_ALPHAS = tuple(np.logspace(-2, 0, 15))


@dataclass(frozen=True)
class NetworkConfig:
    """Frozen settings for the EBIC-selected incumbent network."""

    alphas: tuple[float, ...] = field(default_factory=lambda: _DEFAULT_ALPHAS)
    gamma: float = 0.5


@dataclass(frozen=True)
class IncumbentNetworkResult:
    """The selected incumbent network's precision matrix and derived edges."""

    precision_matrix: pd.DataFrame
    partial_correlation: pd.DataFrame
    edges: frozenset[tuple[str, str]]
    selected_alpha: float
    selected_ebic: float


def fit_incumbent_network(frame: pd.DataFrame, config: NetworkConfig) -> IncumbentNetworkResult:
    """Select and fit the minimum-EBIC graphical-lasso network for ``frame``."""

    columns = list(frame.columns)
    standardized = (frame - frame.mean()) / frame.std(ddof=0)
    empirical_covariance = standardized.cov(ddof=0).to_numpy()
    n_rows = len(standardized)
    n_columns = len(columns)

    best_ebic: float | None = None
    best_alpha: float | None = None
    best_precision: np.ndarray | None = None
    for alpha in config.alphas:
        _, precision = graphical_lasso(empirical_covariance, alpha=alpha)
        ebic = _extended_bayesian_information_criterion(
            empirical_covariance, precision, n_rows, n_columns, config.gamma
        )
        if best_ebic is None or ebic < best_ebic:
            best_ebic, best_alpha, best_precision = ebic, alpha, precision

    precision_frame = pd.DataFrame(best_precision, index=columns, columns=columns)
    partial_correlation = _partial_correlation(precision_frame)
    edges = _nonzero_edges(partial_correlation)

    return IncumbentNetworkResult(
        precision_matrix=precision_frame,
        partial_correlation=partial_correlation,
        edges=edges,
        selected_alpha=float(best_alpha),
        selected_ebic=float(best_ebic),
    )


def _extended_bayesian_information_criterion(
    empirical_covariance: np.ndarray,
    precision: np.ndarray,
    n_rows: int,
    n_columns: int,
    gamma: float,
) -> float:
    sign, log_determinant = np.linalg.slogdet(precision)
    if sign <= 0:
        return float("inf")
    log_likelihood = 0.5 * n_rows * (
        log_determinant - np.trace(empirical_covariance @ precision)
    )
    edge_count = (np.count_nonzero(precision) - n_columns) // 2
    return (
        -2.0 * log_likelihood
        + edge_count * np.log(n_rows)
        + 4.0 * edge_count * gamma * np.log(n_columns)
    )


def _partial_correlation(precision_frame: pd.DataFrame) -> pd.DataFrame:
    diagonal = np.sqrt(np.diag(precision_frame.to_numpy()))
    outer = np.outer(diagonal, diagonal)
    partial = -precision_frame.to_numpy() / outer
    np.fill_diagonal(partial, 0.0)
    return pd.DataFrame(partial, index=precision_frame.index, columns=precision_frame.columns)


def _nonzero_edges(partial_correlation: pd.DataFrame) -> frozenset[tuple[str, str]]:
    columns = list(partial_correlation.columns)
    edges: set[tuple[str, str]] = set()
    for i, left in enumerate(columns):
        for right in columns[i + 1 :]:
            if abs(partial_correlation.loc[left, right]) > 1e-8:
                edges.add((left, right))
    return frozenset(edges)
