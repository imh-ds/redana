"""Bootstrap edge stability and stability-tier classification.

Implements ``outline/plan.md`` section 13's researcher-facing stability
signal and section 14's validation of bootstrap stability as a proxy for
actual between-dataset replication probability, scoped per
``docs/superpowers/specs/2026-08-26-stability-reporting-charter.md``
(Track 1): the statistical machinery only, no visualization.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd

from redana.dependence import derive_seed
from redana.network import NetworkConfig
from redana.prototype import run_prototype
from redana.residuals import PrototypeConfig

_FREQUENT_THRESHOLD = 0.75
_INTERMITTENT_THRESHOLD = 0.40

STABILITY_DISCLOSURE_CAVEAT = (
    "Bootstrap selection frequency reflects robustness to resampling this dataset. "
    "It is not an estimate of independent-study replication probability."
)
"""Attach this verbatim wherever a stability tier is shown to a researcher.

docs/evidence/stability-validation-20260826.md found that at a marginal effect
size, mean bootstrap stability (a within-dataset resampling statistic) landed
far above the actual between-dataset replication rate -- most datasets
classified "frequently_selected" despite only ~1-in-3 true replication. The
tier labels below were chosen, and this caveat added, specifically so neither
implies a claim about independent-study replication that bootstrap stability
cannot support. See docs/superpowers/specs/2026-08-26-stability-tier-relabeling-addendum.md.
"""


def bootstrap_edge_stability(
    frame: pd.DataFrame,
    residual_config: PrototypeConfig,
    network_config: NetworkConfig,
    permutations: int,
    alpha: float,
    seed: int,
    n_bootstrap: int,
) -> dict[tuple[str, str], float]:
    """Resample ``frame`` with replacement ``n_bootstrap`` times, rerunning the full
    prototype each time, and return each pair's fraction of resamples in which it
    was selected as a residual edge.
    """

    rng = np.random.default_rng(seed)
    n_rows = len(frame)
    columns = list(frame.columns)
    all_pairs = list(combinations(columns, 2))
    counts = dict.fromkeys(all_pairs, 0)

    for resample_index in range(n_bootstrap):
        row_indices = rng.integers(0, n_rows, size=n_rows)
        resampled_frame = frame.iloc[row_indices].reset_index(drop=True)
        resample_seed = derive_seed("bootstrap-edge-stability", seed, resample_index) % (2**32)
        result = run_prototype(
            resampled_frame, residual_config, network_config, permutations, alpha, resample_seed
        )
        for edge in result.residual_edges:
            pair = tuple(sorted(edge))
            counts[pair] += 1

    return {pair: count / n_bootstrap for pair, count in counts.items()}


def classify_stability_tier(stability: float) -> str:
    """Classify a bootstrap stability value into ``"frequently_selected"``,
    ``"intermittently_selected"``, or ``"rarely_selected"``, per the charter's
    approved thresholds (unchanged) and its tier-relabeling addendum (labels
    only, not thresholds). These labels describe selection frequency under
    resampling of one dataset -- see ``STABILITY_DISCLOSURE_CAVEAT`` for why
    they intentionally avoid implying anything about independent-study
    replication.
    """

    if not 0.0 <= stability <= 1.0:
        raise ValueError(f"stability must be in [0, 1], got {stability!r}")

    if stability >= _FREQUENT_THRESHOLD:
        return "frequently_selected"
    if stability >= _INTERMITTENT_THRESHOLD:
        return "intermittently_selected"
    return "rarely_selected"
