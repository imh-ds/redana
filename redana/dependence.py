"""Permutation-based distance-correlation statistic for the redana prototype.

Promoted by verified copy from ``research/gate0/metrics.py`` (see
``tests/redana/test_dependence.py`` for the parity test against the
original). This module does not import from ``research.gate0``, since
that tree is disposable Gate 0 research code and this package is meant
to be reused.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import dcor
import numpy as np


@dataclass(frozen=True)
class PermutationResult:
    """Observed distance correlation and its permutation reference distribution."""

    observed: float
    null_statistics: np.ndarray
    p_value: float


def derive_seed(*parts: str | int) -> int:
    """Derive a stable unsigned 64-bit seed from an identity tuple."""

    identity = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(identity).digest()[:8], byteorder="big", signed=False)


def permutation_distance_correlation(
    left: np.ndarray, right: np.ndarray, permutations: int, seed: int
) -> PermutationResult:
    """Compute distance correlation against seeded permutations of ``right``."""

    left_array = np.asarray(left, dtype=float)
    right_array = np.asarray(right, dtype=float)
    if left_array.ndim != 1 or right_array.ndim != 1:
        raise ValueError("left and right must be one-dimensional arrays")
    if left_array.shape != right_array.shape:
        raise ValueError("left and right must have the same shape")
    if permutations < 0:
        raise ValueError("permutations must be non-negative")

    observed = float(dcor.distance_correlation(left_array, right_array))
    null_statistics = np.empty(permutations, dtype=float)
    for index in range(permutations):
        child_seed = derive_seed("permutation", seed, index)
        permutation = np.random.default_rng(child_seed).permutation(right_array)
        null_statistics[index] = dcor.distance_correlation(left_array, permutation)

    exceedances = np.count_nonzero(null_statistics >= observed)
    p_value = float((1 + exceedances) / (permutations + 1))
    return PermutationResult(observed, null_statistics, p_value)
