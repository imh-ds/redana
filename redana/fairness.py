"""Comparator-fairness protocol B: matched-operating-characteristic scoring.

Per ``outline/plan.md`` section 8, redana-vs-incumbent comparisons must not
depend on whichever default significance threshold each method happens to
use. These are pure functions over per-pair continuous scores (e.g.
``redana.network.fit_incumbent_network``'s ``partial_correlation`` magnitude,
or ``redana.prototype``'s per-pair ``p_value``), independent of any
``redana.network`` or ``redana.prototype`` internals, so they apply equally
to either method's output.
"""

from __future__ import annotations

Pair = tuple[str, str]


def _normalize(pair: Pair) -> Pair:
    return tuple(sorted(pair))  # type: ignore[return-value]


def _rank_pairs(
    scores: dict[Pair, float], higher_is_more_significant: bool
) -> list[tuple[Pair, float]]:
    if not scores:
        raise ValueError("scores must be non-empty")
    return sorted(scores.items(), key=lambda item: item[1], reverse=higher_is_more_significant)


def precision_recall_curve(
    scores: dict[Pair, float],
    true_edges: set[Pair],
    higher_is_more_significant: bool = True,
) -> list[tuple[float, float]]:
    """Sweep score thresholds from most to least significant, returning (recall, precision) points."""

    normalized_true = {_normalize(edge) for edge in true_edges}
    if not normalized_true:
        raise ValueError("true_edges must be non-empty")

    ranked = _rank_pairs(scores, higher_is_more_significant)
    n_true = len(normalized_true)
    true_positives = 0
    points = []
    for rank, (pair, _score) in enumerate(ranked, start=1):
        if _normalize(pair) in normalized_true:
            true_positives += 1
        points.append((true_positives / n_true, true_positives / rank))
    return points


def average_precision(
    scores: dict[Pair, float],
    true_edges: set[Pair],
    higher_is_more_significant: bool = True,
) -> float:
    """Non-interpolated average precision (AUPRC) over the full ranking."""

    normalized_true = {_normalize(edge) for edge in true_edges}
    if not normalized_true:
        raise ValueError("true_edges must be non-empty")

    ranked = _rank_pairs(scores, higher_is_more_significant)
    n_true = len(normalized_true)
    true_positives = 0
    precision_sum = 0.0
    for rank, (pair, _score) in enumerate(ranked, start=1):
        if _normalize(pair) in normalized_true:
            true_positives += 1
            precision_sum += true_positives / rank
    return precision_sum / n_true


def precision_at_matched_fpr(
    scores: dict[Pair, float],
    true_edges: set[Pair],
    all_pairs: set[Pair],
    target_fpr: float,
    higher_is_more_significant: bool = True,
) -> float:
    """Precision at the most permissive threshold whose false-positive rate stays within ``target_fpr``.

    False-positive rate is computed against the full ``all_pairs`` universe
    (``all_pairs`` minus ``true_edges`` are the negatives), not just the
    pairs present in ``scores``. Since cumulative false positives only grow
    as the threshold relaxes, false-positive rate is monotonically
    non-decreasing across the sweep, so the first point that exceeds
    ``target_fpr`` ends the search. Returns ``0.0`` if even the single
    most-significant pair already exceeds the budget.
    """

    normalized_true = {_normalize(edge) for edge in true_edges}
    normalized_all = {_normalize(pair) for pair in all_pairs}
    if not normalized_true:
        raise ValueError("true_edges must be non-empty")
    n_negative = len(normalized_all) - len(normalized_true)
    if n_negative <= 0:
        raise ValueError("all_pairs must contain at least one negative pair")

    ranked = _rank_pairs(scores, higher_is_more_significant)
    true_positives = 0
    false_positives = 0
    matched_precision = 0.0
    for rank, (pair, _score) in enumerate(ranked, start=1):
        if _normalize(pair) in normalized_true:
            true_positives += 1
        else:
            false_positives += 1
        fpr = false_positives / n_negative
        if fpr > target_fpr:
            break
        matched_precision = true_positives / rank
    return matched_precision
