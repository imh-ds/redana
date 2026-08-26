"""Tests for the held-out-consistency configuration arbiter."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from redana.arbiter import select_configuration
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage1_nonlinear_fixture

_CANDIDATES = {
    "normal": (PrototypeConfig(n_splits=5), 0.05),
    "sensitive": (PrototypeConfig(n_splits=2), 0.15),
}


def test_select_configuration_is_deterministic_given_the_same_seed() -> None:
    frame, _ = generate_stage1_nonlinear_fixture(500, seed=1, coefficient=0.7)
    first = select_configuration(frame, _CANDIDATES, permutations=199, seed=10)
    second = select_configuration(frame, _CANDIDATES, permutations=199, seed=10)
    assert first == second


def test_select_configuration_returns_a_valid_candidate_name() -> None:
    frame, _ = generate_stage1_nonlinear_fixture(500, seed=2, coefficient=0.7)
    result = select_configuration(frame, _CANDIDATES, permutations=199, seed=11)
    assert result.selected in _CANDIDATES
    assert set(result.consistency_scores) == set(_CANDIDATES)
    assert all(0.0 <= v <= 1.0 for v in result.consistency_scores.values())


def test_select_configuration_finds_high_consistency_for_a_strong_dependency() -> None:
    # permutations=199 (not a smaller test-speed value) is required here: with
    # only m=15 pairs and permutations=49, alpha=0.05's BH-FDR threshold at
    # rank 1 is stricter than 49 permutations' p-value floor (1/50=0.02) can
    # ever satisfy, so the "normal" candidate finds nothing regardless of true
    # effect strength -- an artifact of coarse permutation counts, not the
    # arbiter. n_rows=1000 (not 500) is used specifically for this test: an
    # 80/20 split of 500 rows leaves only 400 train rows, which -- unlike the
    # full-sample studies elsewhere in this project -- showed real per-draw
    # detection variance even at coefficient=0.7 for some seeds; 1000 rows
    # gives enough power for a robust, non-flaky assertion.
    frame, _ = generate_stage1_nonlinear_fixture(1000, seed=3, coefficient=0.7)
    result = select_configuration(frame, _CANDIDATES, permutations=199, seed=12)
    assert max(result.consistency_scores.values()) > 0.3


def test_select_configuration_falls_back_to_default_for_pure_noise() -> None:
    rng = np.random.default_rng(4)
    frame = pd.DataFrame(
        {name: rng.standard_normal(200) for name in ("X1", "X2", "X3", "X4", "X5", "X6")}
    )
    result = select_configuration(frame, _CANDIDATES, permutations=199, seed=13)
    assert result.selected == "normal"
    assert all(v == 0.0 for v in result.consistency_scores.values())


@pytest.mark.parametrize("invalid_fraction", [0.0, 1.0, -0.1, 1.1])
def test_select_configuration_rejects_invalid_train_fraction(invalid_fraction: float) -> None:
    frame, _ = generate_stage1_nonlinear_fixture(200, seed=5, coefficient=0.7)
    with pytest.raises(ValueError, match="train_fraction"):
        select_configuration(
            frame, _CANDIDATES, permutations=199, seed=14, train_fraction=invalid_fraction
        )


def test_select_configuration_rejects_empty_candidates() -> None:
    frame, _ = generate_stage1_nonlinear_fixture(200, seed=6, coefficient=0.7)
    with pytest.raises(ValueError, match="candidates"):
        select_configuration(frame, {}, permutations=199, seed=15)
