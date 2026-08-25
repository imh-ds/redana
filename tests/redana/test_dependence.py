"""Tests for the redana-promoted permutation distance-correlation statistic."""

from __future__ import annotations

import numpy as np
import pytest

from redana.dependence import permutation_distance_correlation
from research.gate0.metrics import permutation_distance_correlation as gate0_permutation_distance_correlation


def test_p_value_is_in_valid_range_and_null_array_has_requested_length() -> None:
    rng = np.random.default_rng(1)
    left = rng.standard_normal(200)
    right = rng.standard_normal(200)

    result = permutation_distance_correlation(left, right, permutations=49, seed=3)

    assert 0.0 < result.p_value <= 1.0
    assert result.null_statistics.shape == (49,)


def test_independent_input_yields_a_large_p_value_and_dependent_input_a_small_one() -> None:
    rng = np.random.default_rng(2)
    n = 500
    left = rng.standard_normal(n)
    independent_right = rng.standard_normal(n)
    dependent_right = 0.9 * left + 0.1 * rng.standard_normal(n)

    independent_result = permutation_distance_correlation(left, independent_right, 99, seed=5)
    dependent_result = permutation_distance_correlation(left, dependent_right, 99, seed=5)

    assert independent_result.p_value > 0.1
    assert dependent_result.p_value <= 0.05


def test_rejects_mismatched_or_multidimensional_input() -> None:
    with pytest.raises(ValueError, match="one-dimensional"):
        permutation_distance_correlation(np.zeros((5, 2)), np.zeros((5, 2)), 9, seed=1)
    with pytest.raises(ValueError, match="same shape"):
        permutation_distance_correlation(np.zeros(5), np.zeros(6), 9, seed=1)
    with pytest.raises(ValueError, match="non-negative"):
        permutation_distance_correlation(np.zeros(5), np.zeros(5), -1, seed=1)


def test_parity_with_gate0_original_on_identical_seeded_input() -> None:
    rng = np.random.default_rng(9)
    left = rng.standard_normal(150)
    right = rng.standard_normal(150)

    gate0_result = gate0_permutation_distance_correlation(left, right, 29, seed=17)
    redana_result = permutation_distance_correlation(left, right, 29, seed=17)

    assert redana_result.observed == gate0_result.observed
    assert redana_result.p_value == gate0_result.p_value
    assert np.array_equal(redana_result.null_statistics, gate0_result.null_statistics)
