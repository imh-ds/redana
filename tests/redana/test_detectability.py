"""Tests for the detectability lookup table."""

from __future__ import annotations

from redana.detectability import lookup_detectability, nearest_detectability


def test_lookup_detectability_returns_exact_known_value() -> None:
    # from docs/evidence/sample-size-dependence-20260825.md Stage B's grid
    entry = lookup_detectability(0.15, 1000)
    assert entry is not None
    assert entry.per_edge_detection_fraction == 0.29
    assert "sample-size-dependence" in entry.source_note


def test_lookup_detectability_returns_none_for_untested_combination() -> None:
    assert lookup_detectability(0.15, 100) is None


def test_nearest_detectability_returns_exact_match_when_available() -> None:
    entry, was_exact = nearest_detectability(0.7, 1000)
    assert was_exact is True
    assert entry.coefficient == 0.7
    assert entry.n_rows == 1000


def test_nearest_detectability_returns_approximate_for_untested_point() -> None:
    entry, was_exact = nearest_detectability(0.15, 150)
    assert was_exact is False
    assert entry is not None
