"""Dependence metrics with reproducible seeded permutation references."""

from dataclasses import dataclass

import dcor
import numpy as np

from research.gate0.config import derive_seed


@dataclass(frozen=True)
class PermutationResult:
    """Observed distance correlation and its permutation reference distribution."""

    observed: float
    null_statistics: np.ndarray
    p_value: float


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
