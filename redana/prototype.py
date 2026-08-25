"""Prototype orchestration: ties residualization, dCor, FDR, and the incumbent network together."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import pandas as pd

from redana.dependence import derive_seed, permutation_distance_correlation
from redana.fdr import benjamini_hochberg
from redana.network import IncumbentNetworkResult, NetworkConfig, fit_incumbent_network
from redana.residuals import PrototypeConfig, cross_fitted_pair_residuals


@dataclass(frozen=True)
class PairStatistic:
    """One tested pair's residual dependence statistic and significance."""

    left: str
    right: str
    observed_statistic: float
    p_value: float
    significant: bool


@dataclass(frozen=True)
class PrototypeResult:
    """The incumbent network and the BH-FDR-controlled residual layer for one dataset."""

    incumbent: IncumbentNetworkResult
    incumbent_edges: frozenset[tuple[str, str]]
    residual_edges: frozenset[tuple[str, str]]
    pair_statistics: tuple[PairStatistic, ...]


def run_prototype(
    frame: pd.DataFrame,
    residual_config: PrototypeConfig,
    network_config: NetworkConfig,
    permutations: int,
    alpha: float,
    seed: int,
) -> PrototypeResult:
    """Run the incumbent network and the residual-dependence layer on ``frame``."""

    incumbent = fit_incumbent_network(frame, network_config)

    columns = list(frame.columns)
    pairs = list(combinations(columns, 2))
    observed_statistics: list[float] = []
    p_values: list[float] = []
    for left, right in pairs:
        residual_seed = derive_seed("redana-prototype", seed, left, right, "residual")
        permutation_seed = derive_seed("redana-prototype", seed, left, right, "permutation")
        residuals = cross_fitted_pair_residuals(
            frame, left, right, residual_config, residual_seed % (2**32)
        )
        result = permutation_distance_correlation(
            residuals[left].to_numpy(), residuals[right].to_numpy(), permutations, permutation_seed
        )
        observed_statistics.append(result.observed)
        p_values.append(result.p_value)

    significance = benjamini_hochberg(p_values, alpha)
    pair_statistics = tuple(
        PairStatistic(left, right, observed_statistics[index], p_values[index], bool(significance[index]))
        for index, (left, right) in enumerate(pairs)
    )
    residual_edges = frozenset(
        (stat.left, stat.right) for stat in pair_statistics if stat.significant
    )

    return PrototypeResult(
        incumbent=incumbent,
        incumbent_edges=incumbent.edges,
        residual_edges=residual_edges,
        pair_statistics=pair_statistics,
    )
