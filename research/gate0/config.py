"""Frozen computational settings for the disposable Gate 0 research run."""

from dataclasses import dataclass
import hashlib


@dataclass(frozen=True)
class ComputationalProfile:
    """Dataset and replication dimensions for one Gate 0 execution profile."""

    name: str
    source_rows: int
    evaluation_rows: int
    replications: int
    permutations: int


@dataclass(frozen=True)
class Gate0Config:
    """Statistical settings shared by every Gate 0 profile."""

    profile: ComputationalProfile
    n_splits: int = 5
    spline_knots: int = 5
    spline_degree: int = 3
    ridge_alpha: float = 1.0


FULL_PROFILE = ComputationalProfile("full", 50_000, 1_000, 10, 199)
REDUCED_PROFILE = ComputationalProfile("reduced", 20_000, 750, 10, 99)
SMOKE_PROFILE = ComputationalProfile("smoke", 5_000, 500, 1, 19)


def derive_seed(*parts: str | int) -> int:
    """Derive a stable unsigned 64-bit seed from an identity tuple."""

    identity = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(identity).digest()[:8], byteorder="big", signed=False)

