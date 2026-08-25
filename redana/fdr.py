"""Benjamini-Hochberg false discovery rate multiplicity control."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def benjamini_hochberg(p_values: Sequence[float], alpha: float) -> np.ndarray:
    """Return a boolean significance mask via the standard BH step-up procedure."""

    values = np.asarray(p_values, dtype=float)
    count = values.shape[0]
    significant = np.zeros(count, dtype=bool)
    if count == 0:
        return significant

    order = np.argsort(values, kind="stable")
    sorted_values = values[order]
    ranks = np.arange(1, count + 1)
    thresholds = (ranks / count) * alpha
    eligible = sorted_values <= thresholds
    if not eligible.any():
        return significant

    cutoff_rank = np.max(np.flatnonzero(eligible))
    cutoff_value = sorted_values[cutoff_rank]
    significant[values <= cutoff_value] = True
    return significant
