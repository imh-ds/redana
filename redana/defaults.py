"""Sample-size-aware recommended settings for the redana prototype.

docs/evidence/track2-low-n-power-levers-20260826.md found that
n_splits=2, alpha=0.15 meaningfully improves detection with no precision
cost at n_rows in {100, 200}, but a regression check at n_rows=1000,
coefficient=0.7 found the same values cost ~14 points of residual
precision there for zero detection benefit. The gap between 200 and
1,000 was subsequently bracketed at 25-row resolution, at coefficient=0.7
(the known-costly anchor), by
docs/evidence/track2-threshold-justification-20260826.md: the crossover
falls between n_rows=225 (still net-favorable) and n_rows=250 (detection
improvement drops to exactly zero, precision cost remains). A
coefficient=0.20 sanity check confirmed the tuned values stay safe
throughout the same bracket for weak effects.

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

_LOW_N_THRESHOLD = 225
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

    ``n_rows <= 225`` (the largest bracketed point still classified
    "safe" in docs/evidence/track2-threshold-justification-20260826.md)
    returns the tuned low-n values (``n_splits=2, alpha=0.15``). Above
    that, returns the original settings (``n_splits=5, alpha=0.05``)
    used throughout every prior study in this project. Note the ``225``
    classification is a narrow one -- see that evidence note's discussion
    of its detection-improvement margin relative to its precision cost.
    """

    if n_rows <= _LOW_N_THRESHOLD:
        return RecommendedSettings(PrototypeConfig(n_splits=_LOW_N_SPLITS), _LOW_N_ALPHA)
    return RecommendedSettings(PrototypeConfig(n_splits=_DEFAULT_N_SPLITS), _DEFAULT_ALPHA)
