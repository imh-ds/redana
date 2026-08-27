"""Sample-size-aware recommended settings for the redana prototype.

docs/evidence/track2-low-n-power-levers-20260826.md found that
n_splits=2, alpha=0.15 meaningfully improves detection with no precision
cost at n_rows in {100, 200}, but a regression check at n_rows=1000,
coefficient=0.7 found the same values cost ~14 points of residual
precision there for zero detection benefit. The gap between 200 and
1,000 was subsequently bracketed at 25-row resolution, at coefficient=0.7
(the known-costly anchor), by
docs/evidence/track2-threshold-justification-20260826.md.

That bracketing run's own pre-registered classification rule mechanically
selected n_rows=225, but the rule turned out to have a real flaw: it
only requires detection improvement to clear a 5pp floor, with no check
that the improvement is actually large relative to any precision cost
-- so it let n_rows=225 through as "safe" despite a mere +6.0pp
detection gain paying for a -21.1pp precision loss. Owner review (see
docs/superpowers/specs/2026-08-26-track2-threshold-final-decision-addendum.md)
selected n_rows<=175 instead: at that point detection gain (+19.0pp)
comfortably exceeds precision cost (-10.1pp) by roughly 2x, a margin
wide enough to very likely exceed this study's own Monte Carlo noise
(n_reps=50 per arm); n_rows=200's own gain/cost gap (10.0pp vs. 12.8pp)
is narrow enough to plausibly be noise, i.e. statistically
indistinguishable from a coin flip on this evidence. A coefficient=0.20
sanity check confirmed the tuned values stay safe throughout the entire
bracket for weak effects, so this choice is conservative only on the
strong-coefficient side, which is what actually constrains it.

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

_LOW_N_THRESHOLD = 175
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

    ``n_rows <= 175`` returns the tuned low-n values (``n_splits=2,
    alpha=0.15``); above that, the original settings (``n_splits=5,
    alpha=0.05``). ``175`` was chosen over the bracketing study's own
    mechanically-selected ``225`` because at ``175`` detection gain
    comfortably exceeds precision cost (roughly 2x), while at ``200``-
    ``225`` the two are close enough to be statistically indistinguishable
    from noise on this evidence -- see
    docs/superpowers/specs/2026-08-26-track2-threshold-final-decision-addendum.md
    for the full reasoning and
    docs/evidence/track2-threshold-justification-20260826.md for the raw
    per-point measurements.
    """

    if n_rows <= _LOW_N_THRESHOLD:
        return RecommendedSettings(PrototypeConfig(n_splits=_LOW_N_SPLITS), _LOW_N_ALPHA)
    return RecommendedSettings(PrototypeConfig(n_splits=_DEFAULT_N_SPLITS), _DEFAULT_ALPHA)
