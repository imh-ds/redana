"""Tests for the redana edge-set scoring."""

from __future__ import annotations

from redana.scoring import score_edges


def test_exact_match_yields_perfect_scores() -> None:
    true_edges = {("X1", "X2"), ("X2", "X3")}
    selected_edges = {("X1", "X2"), ("X2", "X3")}

    score = score_edges(true_edges, selected_edges)

    assert score.precision == 1.0
    assert score.recall == 1.0
    assert score.f1 == 1.0
    assert score.true_positive_count == 2
    assert score.false_positive_count == 0
    assert score.false_negative_count == 0


def test_no_overlap_yields_zero_scores() -> None:
    true_edges = {("X1", "X2")}
    selected_edges = {("X3", "X4")}

    score = score_edges(true_edges, selected_edges)

    assert score.precision == 0.0
    assert score.recall == 0.0
    assert score.f1 == 0.0
    assert score.true_positive_count == 0
    assert score.false_positive_count == 1
    assert score.false_negative_count == 1


def test_partial_overlap_matches_hand_computed_expectation() -> None:
    true_edges = {("X1", "X2"), ("X2", "X3"), ("X3", "X4")}
    selected_edges = {("X1", "X2"), ("X2", "X3"), ("X4", "X5")}

    score = score_edges(true_edges, selected_edges)

    assert score.true_positive_count == 2
    assert score.false_positive_count == 1
    assert score.false_negative_count == 1
    assert score.precision == 2 / 3
    assert score.recall == 2 / 3
    assert score.f1 == 2 / 3


def test_empty_selected_set_gives_zero_precision_not_a_division_error() -> None:
    true_edges = {("X1", "X2")}
    selected_edges: set[tuple[str, str]] = set()

    score = score_edges(true_edges, selected_edges)

    assert score.precision == 0.0
    assert score.recall == 0.0
    assert score.f1 == 0.0
    assert score.false_negative_count == 1


def test_empty_true_set_gives_zero_recall_not_a_division_error() -> None:
    true_edges: set[tuple[str, str]] = set()
    selected_edges = {("X1", "X2")}

    score = score_edges(true_edges, selected_edges)

    assert score.precision == 0.0
    assert score.recall == 0.0
    assert score.f1 == 0.0
    assert score.false_positive_count == 1


def test_both_empty_gives_zero_scores_without_error() -> None:
    score = score_edges(set(), set())

    assert score.precision == 0.0
    assert score.recall == 0.0
    assert score.f1 == 0.0


def test_reversed_pair_order_is_treated_as_the_same_edge() -> None:
    true_edges = {("X1", "X2")}
    selected_edges = {("X2", "X1")}

    score = score_edges(true_edges, selected_edges)

    assert score.true_positive_count == 1
    assert score.false_positive_count == 0
    assert score.false_negative_count == 0
    assert score.precision == 1.0
    assert score.recall == 1.0
