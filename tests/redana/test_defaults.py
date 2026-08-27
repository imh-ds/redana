"""Tests for sample-size-aware recommended prototype settings."""

from __future__ import annotations

import pytest

from redana.defaults import recommended_settings


@pytest.mark.parametrize(
    "n_rows,expected_n_splits,expected_alpha",
    [
        (50, 2, 0.15),
        (100, 2, 0.15),
        (175, 2, 0.15),
        (176, 5, 0.05),
        (200, 5, 0.05),
        (225, 5, 0.05),
        (500, 5, 0.05),
        (1000, 5, 0.05),
    ],
)
def test_recommended_settings_by_sample_size(
    n_rows: int, expected_n_splits: int, expected_alpha: float
) -> None:
    settings = recommended_settings(n_rows)
    assert settings.residual_config.n_splits == expected_n_splits
    assert settings.alpha == expected_alpha
