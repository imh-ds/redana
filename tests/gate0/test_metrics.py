import numpy as np

from research.gate0.metrics import permutation_distance_correlation


def test_permutation_result_is_reproducible_and_bounded() -> None:
    rng = np.random.default_rng(7)
    left = rng.normal(size=80)
    right = left + rng.normal(scale=0.1, size=80)
    result = permutation_distance_correlation(left, right, permutations=19, seed=3)
    repeat = permutation_distance_correlation(left, right, permutations=19, seed=3)
    assert result.observed == repeat.observed
    assert np.array_equal(result.null_statistics, repeat.null_statistics)
    assert 1 / 20 <= result.p_value <= 1


def test_dependent_pair_exceeds_its_permutation_median() -> None:
    rng = np.random.default_rng(11)
    left = rng.normal(size=120)
    result = permutation_distance_correlation(left, left**2, permutations=39, seed=5)
    assert result.observed > np.median(result.null_statistics)
