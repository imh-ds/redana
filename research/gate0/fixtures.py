"""Immutable synthetic fixtures for the disposable Gate 0 simulation."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from research.gate0.config import derive_seed


@dataclass(frozen=True)
class FixtureDefinition:
    """Metadata describing one approved fixture and its evaluation pairs."""

    target_pair: tuple[str, str]
    null_control_pair: tuple[str, str]
    expected_target_class: str


FIXTURES: dict[str, FixtureDefinition] = {
    "F1": FixtureDefinition(("X1", "X2"), ("X4", "X5"), "null-like"),
    "F2": FixtureDefinition(("X1", "X2"), ("X4", "X5"), "non-null"),
    "F3": FixtureDefinition(("X1", "X2"), ("X4", "X5"), "non-null"),
    "F4": FixtureDefinition(("X1", "X3"), ("X4", "X5"), "null-like"),
    "F5": FixtureDefinition(("X1", "X2"), ("X4", "X5"), "null-like"),
    "F6": FixtureDefinition(("X1", "X3"), ("X4", "X5"), "null-like"),
    "F7": FixtureDefinition(("X1", "X2"), ("X4", "X5"), "non-null"),
    "F8": FixtureDefinition(("X1", "X2"), ("X4", "X5"), "non-null"),
}

_COLUMNS = ["X1", "X2", "X3", "X4", "X5", "X6"]


def generate_fixture(fixture_id: str, rows: int, seed: int) -> pd.DataFrame:
    """Generate one standardized, deterministic synthetic fixture."""

    if fixture_id not in FIXTURES:
        raise ValueError(f"unknown fixture_id: {fixture_id}")
    if rows < 2:
        raise ValueError("rows must be at least 2")

    rng = np.random.default_rng(derive_seed("fixture", fixture_id, seed))
    errors = rng.standard_normal((rows, 6))
    e1, e2, e3, e4, e5, e6 = errors.T

    if fixture_id == "F1":
        values = [e1, e2, e3, e4, e5, e6]
    elif fixture_id == "F2":
        values = [e1, 0.7 * e1 + e2, e3, e4, e5, e6]
    elif fixture_id == "F3":
        values = [e1, 0.7 * (e1**2 - 1) + e2, e3, e4, e5, e6]
    elif fixture_id == "F4":
        x2 = 0.7 * e1 + e2
        values = [e1, x2, 0.7 * x2 + e3, e4, e5, e6]
    elif fixture_id == "F5":
        parent = 0.7 * (e3**2 - 1)
        values = [parent + e1, parent + e2, e3, e4, e5, e6]
    elif fixture_id == "F6":
        x2 = 0.7 * (e1**2 - 1) + e2
        values = [e1, x2, 0.7 * x2 + e3, e4, e5, e6]
    elif fixture_id == "F7":
        values = [e1, e2, 0.7 * e1 + 0.7 * e2 + e3, e4, e5, e6]
    else:
        x3 = 0.7 * e1 + e3
        values = [e1, 0.7 * e1 + 0.7 * x3 + e2, x3, e4, e5, e6]

    frame = pd.DataFrame(dict(zip(_COLUMNS, values, strict=True)))
    return (frame - frame.mean()) / frame.std(ddof=0)
