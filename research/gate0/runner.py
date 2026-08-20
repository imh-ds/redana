"""Record-first execution orchestration for the disposable Gate 0 run."""

from __future__ import annotations

import json
import time
import tracemalloc
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from research.gate0.config import (
    FULL_PROFILE,
    REDUCED_PROFILE,
    SMOKE_PROFILE,
    ComputationalProfile,
    Gate0Config,
    derive_seed,
)
from research.gate0.fixtures import FIXTURES, FixtureDefinition, generate_fixture
from research.gate0.metrics import permutation_distance_correlation
from research.gate0.residuals import cross_fitted_pair_residuals

_MAX_PROJECTED_SECONDS = 4 * 60 * 60
_MAX_PYTHON_ALLOCATION_GIB = 4.0
_PROFILE_BY_NAME = {profile.name: profile for profile in (FULL_PROFILE, REDUCED_PROFILE)}


@dataclass(frozen=True)
class SmokeMeasurement:
    """Measured smoke cost projected to the full research workload."""

    projected_seconds: float
    peak_gib: float


@dataclass(frozen=True)
class PairRecord:
    """One attempted fixture-pair calculation, including any caught failure."""

    fixture_id: str
    replication: int
    pair_role: str
    expected_class: str
    left: str
    right: str
    observed_statistic: float | None
    permutation_p_value: float | None
    null_statistics_path: str | None
    fixture_seed: int
    residual_seed: int
    evaluation_seed: int
    permutation_seed: int
    profile: str
    elapsed_seconds: float
    warnings: str
    exception_text: str | None


def select_profile(smoke: SmokeMeasurement) -> ComputationalProfile | None:
    """Select only an approved profile from a smoke cost measurement."""

    if smoke.peak_gib > _MAX_PYTHON_ALLOCATION_GIB:
        return None
    if smoke.projected_seconds <= _MAX_PROJECTED_SECONDS:
        return FULL_PROFILE
    reduced_projected_seconds = smoke.projected_seconds * (
        _profile_work(REDUCED_PROFILE) / _profile_work(FULL_PROFILE)
    )
    if reduced_projected_seconds <= _MAX_PROJECTED_SECONDS:
        return REDUCED_PROFILE
    return None


def _pairs_for_fixture(fixture: FixtureDefinition) -> tuple[tuple[str, tuple[str, str], str], ...]:
    return (
        ("target", fixture.target_pair, fixture.expected_target_class),
        ("null_control", fixture.null_control_pair, "null-like"),
    )


def _identity_seed(fixture_id: str, replication: int, role: str, purpose: str) -> int:
    return derive_seed("gate0", fixture_id, replication, role, purpose)


def _sklearn_seed(identity_seed: int) -> int:
    """Project an identity seed into scikit-learn's accepted seed range."""

    return identity_seed % 2**32


def _null_statistics_filename(fixture_id: str, replication: int, role: str) -> str:
    return f"{fixture_id}-replication-{replication}-{role}.npy"


def _execute_pair(
    *,
    fixture_id: str,
    fixture: FixtureDefinition,
    replication: int,
    role: str,
    pair: tuple[str, str],
    expected_class: str,
    profile: ComputationalProfile,
    output_dir: Path,
) -> PairRecord:
    left, right = pair
    fixture_seed = _identity_seed(fixture_id, replication, "fixture", "dataset")
    residual_seed = _identity_seed(fixture_id, replication, role, "residual")
    evaluation_seed = _identity_seed(fixture_id, replication, role, "evaluation")
    permutation_seed = _identity_seed(fixture_id, replication, role, "permutation")
    null_path = output_dir / "null_statistics" / _null_statistics_filename(fixture_id, replication, role)
    started = time.perf_counter()
    caught_warnings: list[warnings.WarningMessage] = []

    try:
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            frame = generate_fixture(fixture_id, profile.source_rows, fixture_seed)
            residuals = cross_fitted_pair_residuals(
                frame, left, right, Gate0Config(profile), _sklearn_seed(residual_seed)
            )
            evaluation_rows = np.random.default_rng(evaluation_seed).choice(
                residuals.index.to_numpy(), size=profile.evaluation_rows, replace=False
            )
            evaluation = residuals.loc[evaluation_rows]
            result = permutation_distance_correlation(
                evaluation[left].to_numpy(),
                evaluation[right].to_numpy(),
                profile.permutations,
                permutation_seed,
            )
            null_path.parent.mkdir(parents=True, exist_ok=True)
            np.save(null_path, result.null_statistics)
        warning_text = "; ".join(str(item.message) for item in caught_warnings) or ""
        return PairRecord(
            fixture_id=fixture_id,
            replication=replication,
            pair_role=role,
            expected_class=expected_class,
            left=left,
            right=right,
            observed_statistic=result.observed,
            permutation_p_value=result.p_value,
            null_statistics_path=str(null_path.relative_to(output_dir)),
            fixture_seed=fixture_seed,
            residual_seed=residual_seed,
            evaluation_seed=evaluation_seed,
            permutation_seed=permutation_seed,
            profile=profile.name,
            elapsed_seconds=time.perf_counter() - started,
            warnings=warning_text,
            exception_text=None,
        )
    except Exception as error:  # noqa: BLE001 - every pair failure must be recorded.
        return PairRecord(
            fixture_id=fixture_id,
            replication=replication,
            pair_role=role,
            expected_class=expected_class,
            left=left,
            right=right,
            observed_statistic=None,
            permutation_p_value=None,
            null_statistics_path=None,
            fixture_seed=fixture_seed,
            residual_seed=residual_seed,
            evaluation_seed=evaluation_seed,
            permutation_seed=permutation_seed,
            profile=profile.name,
            elapsed_seconds=time.perf_counter() - started,
            warnings="; ".join(str(item.message) for item in caught_warnings) or "",
            exception_text=f"{type(error).__name__}: {error}",
        )


def _run_pairs(mode: Literal["smoke", "substantive"], profile: ComputationalProfile, output_dir: Path) -> list[PairRecord]:
    records: list[PairRecord] = []
    fixtures = (("F1", FIXTURES["F1"]),) if mode == "smoke" else tuple(FIXTURES.items())
    replications = 1 if mode == "smoke" else profile.replications
    for fixture_id, fixture in fixtures:
        for replication in range(replications):
            for role, pair, expected_class in _pairs_for_fixture(fixture):
                records.append(
                    _execute_pair(
                        fixture_id=fixture_id,
                        fixture=fixture,
                        replication=replication,
                        role=role,
                        pair=pair,
                        expected_class=expected_class,
                        profile=profile,
                        output_dir=output_dir,
                    )
                )
    return records


def _profile_work(profile: ComputationalProfile) -> int:
    """Comparable per-pair source-row plus permutation-row work units."""

    return profile.source_rows + profile.evaluation_rows * profile.permutations


def _estimate_full_seconds(records: list[PairRecord]) -> float:
    if not records:
        return float("inf")
    smoke_pair_seconds = sum(record.elapsed_seconds for record in records) / len(records)
    full_pair_count = len(FIXTURES) * FULL_PROFILE.replications * 2
    return smoke_pair_seconds * (_profile_work(FULL_PROFILE) / _profile_work(SMOKE_PROFILE)) * full_pair_count


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_selected_profile(output_dir: Path) -> ComputationalProfile:
    selection_path = output_dir / "selected_profile.json"
    if not selection_path.exists():
        raise FileNotFoundError(
            f"substantive Gate 0 runs require {selection_path.name} from a prior smoke run"
        )
    selected = json.loads(selection_path.read_text(encoding="utf-8"))
    try:
        return _PROFILE_BY_NAME[selected["name"]]
    except (KeyError, TypeError) as error:
        raise ValueError("selected_profile.json does not name an approved profile") from error


def _persist_records(
    records: list[PairRecord], output_dir: Path, gate_result: str | None = None
) -> tuple[pd.DataFrame, str]:
    frame = pd.DataFrame(asdict(record) for record in records)
    gate_result = gate_result or (
        "STOP" if any(record.exception_text for record in records) else "READY"
    )
    frame["gate_result"] = gate_result
    frame.to_csv(output_dir / "pair_records.csv", index=False)
    _write_json(
        output_dir / "run_summary.json",
        {"attempted_pairs": len(records), "gate_result": gate_result},
    )
    return frame, gate_result


def run_gate0(
    mode: Literal["smoke", "substantive"], output_dir: Path
) -> pd.DataFrame:
    """Run Gate 0, persisting a record for each attempted pair."""

    if mode not in {"smoke", "substantive"}:
        raise ValueError("mode must be 'smoke' or 'substantive'")
    output_dir.mkdir(parents=True, exist_ok=True)
    if mode == "smoke":
        (output_dir / "selected_profile.json").unlink(missing_ok=True)
    if mode == "substantive":
        profile = _load_selected_profile(output_dir)
        records = _run_pairs(mode, profile, output_dir)
        frame, _ = _persist_records(records, output_dir)
        return frame

    tracemalloc.start()
    tracemalloc.reset_peak()
    started = time.perf_counter()
    try:
        records = _run_pairs(mode, SMOKE_PROFILE, output_dir)
        elapsed_seconds = time.perf_counter() - started
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    smoke = SmokeMeasurement(
        projected_seconds=_estimate_full_seconds(records),
        peak_gib=peak_bytes / 1024**3,
    )
    _write_json(
        output_dir / "smoke_measurement.json",
        {
            "elapsed_seconds": elapsed_seconds,
            "projected_seconds": smoke.projected_seconds,
            "python_allocation_peak_bytes": peak_bytes,
            "peak_gib": smoke.peak_gib,
        },
    )
    selected_profile = (
        select_profile(smoke) if not any(record.exception_text for record in records) else None
    )
    frame, _ = _persist_records(
        records, output_dir, "READY" if selected_profile is not None else "STOP"
    )
    if selected_profile is not None:
        _write_json(output_dir / "selected_profile.json", asdict(selected_profile))
    return frame
