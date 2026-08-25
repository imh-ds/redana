"""Tests for the redana Benjamini-Hochberg FDR multiplicity control."""

from __future__ import annotations

import numpy as np

from redana.fdr import benjamini_hochberg


def test_textbook_example_flags_only_the_bh_significant_subset() -> None:
    p_values = [0.29, 0.011, 0.4, 0.005, 0.13, 0.6, 0.02, 0.99, 0.45, 0.04]

    significant = benjamini_hochberg(p_values, alpha=0.05)

    expected = np.zeros(10, dtype=bool)
    expected[3] = True  # the single p-value (0.005) satisfying (k/m)*alpha at k=1
    assert np.array_equal(significant, expected)


def test_all_null_case_flags_nothing() -> None:
    p_values = [0.9, 0.85, 0.95, 0.99, 0.88]

    significant = benjamini_hochberg(p_values, alpha=0.05)

    assert not significant.any()


def test_all_signal_case_flags_everything() -> None:
    p_values = [0.001] * 5

    significant = benjamini_hochberg(p_values, alpha=0.05)

    assert significant.all()


def test_tied_p_values_are_treated_consistently() -> None:
    p_values = [0.01, 0.01, 0.01, 0.9, 0.95]

    significant = benjamini_hochberg(p_values, alpha=0.05)

    assert significant[0] and significant[1] and significant[2]
    assert not significant[3] and not significant[4]


def test_returns_boolean_array_of_input_length() -> None:
    p_values = [0.5, 0.2, 0.01]

    significant = benjamini_hochberg(p_values, alpha=0.1)

    assert significant.dtype == np.bool_
    assert significant.shape == (3,)


def test_empty_input_returns_empty_array() -> None:
    significant = benjamini_hochberg([], alpha=0.05)

    assert significant.shape == (0,)
