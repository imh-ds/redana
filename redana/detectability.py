"""A minimal detectability lookup: what per-edge detection rate has this project
already observed at a given (coefficient, n_rows) combination?

Implements a first, narrow slice of ``outline/plan.md`` section 15
("Detectability Reporting"), per
``docs/superpowers/specs/2026-08-26-stability-reporting-charter.md``
(Track 1): a frozen transcription of already-published numbers from this
project's own evidence notes, not a new statistical claim, not
interpolated or curve-fit. All entries are for the pure nonlinear
fixture (``redana.scenarios.generate_stage1_nonlinear_fixture``) at its
default noise/distribution/heteroskedasticity/measurement-error
baseline.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DetectabilityEntry:
    """One already-published (coefficient, n_rows) -> detection-rate observation."""

    coefficient: float
    n_rows: int
    per_edge_detection_fraction: float
    source_note: str


_KNOWN_DETECTABILITY: tuple[DetectabilityEntry, ...] = (
    # docs/evidence/stage2-nonlinear-boundary-followup-20260825.md
    DetectabilityEntry(0.05, 1000, 0.00, "stage2-nonlinear-boundary-followup-20260825"),
    # docs/evidence/sample-size-dependence-20260825.md, Stage B grid
    # (chosen as the canonical n=1000 source for 0.10/0.15/0.20 over the
    # boundary follow-up's independently-drawn near-duplicate values,
    # to avoid ambiguous multiple entries at the same coordinate)
    DetectabilityEntry(0.10, 500, 0.00, "sample-size-dependence-20260825"),
    DetectabilityEntry(0.10, 1000, 0.05, "sample-size-dependence-20260825"),
    DetectabilityEntry(0.10, 2000, 0.28, "sample-size-dependence-20260825"),
    DetectabilityEntry(0.15, 500, 0.02, "sample-size-dependence-20260825"),
    DetectabilityEntry(0.15, 1000, 0.29, "sample-size-dependence-20260825"),
    DetectabilityEntry(0.15, 2000, 0.92, "sample-size-dependence-20260825"),
    DetectabilityEntry(0.20, 500, 0.20, "sample-size-dependence-20260825"),
    DetectabilityEntry(0.20, 1000, 0.90, "sample-size-dependence-20260825"),
    DetectabilityEntry(0.20, 2000, 1.00, "sample-size-dependence-20260825"),
    # docs/evidence/sample-size-dependence-20260825.md, Stage A
    DetectabilityEntry(0.7, 100, 0.16, "sample-size-dependence-20260825"),
    DetectabilityEntry(0.7, 200, 0.92, "sample-size-dependence-20260825"),
    DetectabilityEntry(0.7, 500, 1.00, "sample-size-dependence-20260825"),
    DetectabilityEntry(0.7, 1000, 1.00, "sample-size-dependence-20260825"),
    DetectabilityEntry(0.7, 2000, 1.00, "sample-size-dependence-20260825"),
)


def lookup_detectability(coefficient: float, n_rows: int) -> DetectabilityEntry | None:
    """Return the exact recorded entry for ``(coefficient, n_rows)``, or ``None`` if
    that combination has never been tested.
    """

    for entry in _KNOWN_DETECTABILITY:
        if entry.coefficient == coefficient and entry.n_rows == n_rows:
            return entry
    return None


def nearest_detectability(coefficient: float, n_rows: int) -> tuple[DetectabilityEntry, bool]:
    """Return the nearest tested entry to ``(coefficient, n_rows)``, and whether it
    was an exact match. Distance is Euclidean in (coefficient, n_rows / 1000) space,
    a crude but transparent way to avoid n_rows's much larger scale dominating the
    comparison. This is an explicit approximation, not interpolation -- the returned
    entry describes a *different*, nearby tested condition, not the queried one.
    """

    exact = lookup_detectability(coefficient, n_rows)
    if exact is not None:
        return exact, True

    def distance(entry: DetectabilityEntry) -> float:
        coefficient_delta = entry.coefficient - coefficient
        n_rows_delta = (entry.n_rows - n_rows) / 1000
        return (coefficient_delta**2 + n_rows_delta**2) ** 0.5

    nearest = min(_KNOWN_DETECTABILITY, key=distance)
    return nearest, False
