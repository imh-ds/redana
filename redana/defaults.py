"""Sample-size-aware recommended settings for the redana prototype.

docs/evidence/track2-low-n-power-levers-20260826.md found that
n_splits=2, alpha=0.15 meaningfully improves detection with no precision
cost at n_rows in {100, 200} (the tested regime), but a follow-up
regression check at n_rows=1000, coefficient=0.7 (recorded in
docs/superpowers/specs/2026-08-26-track2-default-adoption-addendum.md)
found the same values cost ~14 points of residual precision there for
zero detection benefit -- detection was already at ceiling with the
original settings. Neither combination was tested at n_rows strictly
between 200 and 1000.

This module packages that as a conditional recommendation rather than a
global default: below the tested low-n threshold, use the tuned values;
at or above it, use the settings used throughout every prior study in
this project. Existing scripts are unaffected unless they opt in by
calling recommended_settings -- no existing redana signature or default
changes.
"""

from __future__ import annotations

from dataclasses import dataclass

from redana.residuals import PrototypeConfig

_LOW_N_THRESHOLD = 200
_LOW_N_SPLITS = 2
_LOW_N_ALPHA = 0.15
_DEFAULT_N_SPLITS = 5
_DEFAULT_ALPHA = 0.05


@dataclass(frozen=True)
class RecommendedSettings:
    """A sample-size-appropriate (residualization config, FDR alpha) pair."""

    residual_config: PrototypeConfig
    alpha: float


def recommended_settings(n_rows: int) -> RecommendedSettings:
    """Return the sample-size-appropriate settings for ``n_rows`` rows.

    ``n_rows <= 200`` (the regime directly validated in
    docs/evidence/track2-low-n-power-levers-20260826.md) returns the
    tuned low-n values (``n_splits=2, alpha=0.15``). Above that, returns
    the original settings (``n_splits=5, alpha=0.05``) used throughout
    every prior study in this project, since the tuned values were found
    to cost precision with no detection benefit at ``n_rows=1000`` and
    were never tested in between.
    """

    if n_rows <= _LOW_N_THRESHOLD:
        return RecommendedSettings(PrototypeConfig(n_splits=_LOW_N_SPLITS), _LOW_N_ALPHA)
    return RecommendedSettings(PrototypeConfig(n_splits=_DEFAULT_N_SPLITS), _DEFAULT_ALPHA)
