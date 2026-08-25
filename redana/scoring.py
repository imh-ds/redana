"""Precision/recall/F1 scoring of a selected edge set against ground truth."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EdgeScore:
    """Precision, recall, and F1 for one selected edge set against ground truth."""

    precision: float
    recall: float
    f1: float
    true_positive_count: int
    false_positive_count: int
    false_negative_count: int


def _canonical(edges: set[tuple[str, str]]) -> set[tuple[str, str]]:
    return {tuple(sorted(edge)) for edge in edges}


def score_edges(
    true_edges: set[tuple[str, str]], selected_edges: set[tuple[str, str]]
) -> EdgeScore:
    """Score ``selected_edges`` against ``true_edges``, ignoring pair order."""

    true_canonical = _canonical(true_edges)
    selected_canonical = _canonical(selected_edges)

    true_positive_count = len(true_canonical & selected_canonical)
    false_positive_count = len(selected_canonical - true_canonical)
    false_negative_count = len(true_canonical - selected_canonical)

    precision = (
        true_positive_count / len(selected_canonical) if selected_canonical else 0.0
    )
    recall = true_positive_count / len(true_canonical) if true_canonical else 0.0
    f1 = (
        2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    )

    return EdgeScore(
        precision=precision,
        recall=recall,
        f1=f1,
        true_positive_count=true_positive_count,
        false_positive_count=false_positive_count,
        false_negative_count=false_negative_count,
    )
