"""Tests for redana.fairness: comparator-fairness protocol B scoring."""

from __future__ import annotations

import numpy as np
import pytest

from redana.fairness import (
    average_precision,
    precision_at_matched_fpr,
    precision_recall_curve,
)

# Fixed 4-node hand-computed example: 6 pairs, 2 true edges, scores rank the
# true edges first (a perfect ranking).
_ALL_PAIRS = {("A", "B"), ("A", "C"), ("A", "D"), ("B", "C"), ("B", "D"), ("C", "D")}
_TRUE_EDGES = {("A", "B"), ("C", "D")}
_PERFECT_SCORES = {
    ("A", "B"): 0.9,
    ("C", "D"): 0.8,
    ("A", "C"): 0.7,
    ("B", "D"): 0.6,
    ("A", "D"): 0.5,
    ("B", "C"): 0.4,
}


def test_perfect_ranking_gives_auprc_one() -> None:
    assert average_precision(_PERFECT_SCORES, _TRUE_EDGES) == pytest.approx(1.0)


def test_random_scores_give_auprc_near_base_rate() -> None:
    # Average precision under a random ranking has a genuine finite-sample
    # upward bias relative to the base rate (confirmed independently: at
    # n_pairs=100 the bias is ~0.04 above a 0.10 base rate, not sampling
    # noise -- it shrinks only as the pair universe grows large relative to
    # the number of true edges). Use a large enough universe for the
    # asymptotic "near the base rate" behavior to actually hold.
    n_pairs = 2000
    n_true = 200
    base_rate = n_true / n_pairs
    all_pairs = [(f"N{i}", f"N{i + 1}") for i in range(n_pairs)]
    true_edges = set(all_pairs[:n_true])

    aps = []
    for seed in range(50):
        rng = np.random.default_rng(seed)
        random_scores = {pair: value for pair, value in zip(all_pairs, rng.random(n_pairs))}
        aps.append(average_precision(random_scores, true_edges))

    assert np.mean(aps) == pytest.approx(base_rate, abs=0.03)


def test_precision_recall_curve_matches_hand_computed_example() -> None:
    curve = precision_recall_curve(_PERFECT_SCORES, _TRUE_EDGES)
    expected = [
        (0.5, 1.0),
        (1.0, 1.0),
        (1.0, pytest.approx(2 / 3)),
        (1.0, 0.5),
        (1.0, 0.4),
        (1.0, pytest.approx(1 / 3)),
    ]
    assert len(curve) == len(expected)
    for (recall, precision), (expected_recall, expected_precision) in zip(curve, expected):
        assert recall == pytest.approx(expected_recall)
        assert precision == pytest.approx(expected_precision)


def test_average_precision_matches_hand_computed_example() -> None:
    # True edges land at ranks 1 and 2: AP = (1/2) * (1/1 + 2/2) = 1.0
    assert average_precision(_PERFECT_SCORES, _TRUE_EDGES) == pytest.approx(1.0)


def test_precision_at_matched_fpr_matches_hand_computed_example() -> None:
    # n_negative = 4; target_fpr=0.25 allows exactly 1 false positive.
    # Sweep stops after (A,C) (rank 3, fpr=0.25<=0.25, precision=2/3), since
    # (B,D) at rank 4 pushes fpr to 0.5 > 0.25.
    precision = precision_at_matched_fpr(_PERFECT_SCORES, _TRUE_EDGES, _ALL_PAIRS, target_fpr=0.25)
    assert precision == pytest.approx(2 / 3)


def test_precision_at_matched_fpr_is_zero_when_top_pick_already_exceeds_budget() -> None:
    scores = {
        ("A", "C"): 0.9,  # false positive, ranked first
        ("A", "B"): 0.8,
        ("C", "D"): 0.7,
        ("B", "D"): 0.6,
        ("A", "D"): 0.5,
        ("B", "C"): 0.4,
    }
    precision = precision_at_matched_fpr(scores, _TRUE_EDGES, _ALL_PAIRS, target_fpr=0.0)
    assert precision == 0.0


def test_lower_is_more_significant_convention_works_like_p_values() -> None:
    # p-value convention: lower score is more significant. Inverting the
    # perfect-ranking scores (1 - score) and flipping the convention flag
    # should reproduce the exact same AP as the original higher-is-better scores.
    p_value_scores = {pair: 1.0 - score for pair, score in _PERFECT_SCORES.items()}
    ap_as_p_values = average_precision(p_value_scores, _TRUE_EDGES, higher_is_more_significant=False)
    ap_as_scores = average_precision(_PERFECT_SCORES, _TRUE_EDGES, higher_is_more_significant=True)
    assert ap_as_p_values == pytest.approx(ap_as_scores)


def test_true_edges_must_be_non_empty() -> None:
    with pytest.raises(ValueError, match="true_edges"):
        average_precision(_PERFECT_SCORES, set())


def test_all_pairs_must_contain_at_least_one_negative() -> None:
    with pytest.raises(ValueError, match="all_pairs"):
        precision_at_matched_fpr(_PERFECT_SCORES, _TRUE_EDGES, _TRUE_EDGES, target_fpr=0.1)
