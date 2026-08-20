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
    OWNER_DECISION_SENTENCE,
    REDUCED_PROFILE,
    SMOKE_PROFILE,
    ComputationalProfile,
    Gate0Config,
    derive_seed,
)
from research.gate0.fixtures import FIXTURES, FixtureDefinition, generate_fixture
from research.gate0.metrics import permutation_distance_correlation
from research.gate0.report import gate_status, write_gate_report
from research.gate0.residuals import cross_fitted_pair_residuals

_MAX_PROJECTED_SECONDS = 4 * 60 * 60
_MAX_PYTHON_ALLOCATION_GIB = 4.0
_PROFILE_BY_NAME = {profile.name: profile for profile in (FULL_PROFILE, REDUCED_PROFILE)}


@dataclass(frozen=True)
class SmokeMeasurement:
    """Measured smoke peak plus its projected full-profile runtime."""

    projected_seconds: float
    peak_gib: float


@dataclass(frozen=True)
class ProfileProjection:
    """Projected sequential runtime and per-pair memory for one frozen profile."""

    projected_seconds: float
    projected_peak_gib: float


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
    residual_sample_path: str | None = None


def select_profile(smoke: SmokeMeasurement) -> ComputationalProfile | None:
    """Select only an approved profile from a smoke cost measurement."""

    for profile in (FULL_PROFILE, REDUCED_PROFILE):
        projection = _project_profile(smoke, profile)
        if (
            projection.projected_seconds <= _MAX_PROJECTED_SECONDS
            and projection.projected_peak_gib <= _MAX_PYTHON_ALLOCATION_GIB
        ):
            return profile
    return None


def _project_profile(
    smoke: SmokeMeasurement, profile: ComputationalProfile
) -> ProfileProjection:
    """Scale the same smoke measurement coherently to a frozen profile."""

    return ProfileProjection(
        projected_seconds=smoke.projected_seconds
        * (_profile_work(profile) / _profile_work(FULL_PROFILE)),
        projected_peak_gib=smoke.peak_gib
        * (profile.source_rows / SMOKE_PROFILE.source_rows),
    )


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


def _residual_sample_filename(fixture_id: str, replication: int, role: str) -> str:
    return f"{fixture_id}-replication-{replication}-{role}.csv"


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
    artifact_namespace: str,
) -> PairRecord:
    left, right = pair
    fixture_seed = _identity_seed(fixture_id, replication, "fixture", "dataset")
    residual_seed = _identity_seed(fixture_id, replication, role, "residual")
    evaluation_seed = _identity_seed(fixture_id, replication, role, "evaluation")
    permutation_seed = _identity_seed(fixture_id, replication, role, "permutation")
    artifact_dir = output_dir / artifact_namespace
    null_path = (
        artifact_dir / "null_statistics" / _null_statistics_filename(fixture_id, replication, role)
    )
    residual_sample_path = (
        artifact_dir
        / "residual_samples"
        / _residual_sample_filename(fixture_id, replication, role)
    )
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
            residual_sample_path.parent.mkdir(parents=True, exist_ok=True)
            evaluation.loc[:, [left, right]].to_csv(residual_sample_path, index=False)
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
            residual_sample_path=str(residual_sample_path.relative_to(output_dir)),
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
            residual_sample_path=None,
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
                        artifact_namespace=mode,
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


def _read_state(output_dir: Path) -> dict[str, str]:
    state_path = output_dir / "run_state.json"
    if not state_path.exists():
        raise FileNotFoundError("substantive Gate 0 runs require a prior smoke run state")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise TypeError("run_state.json is invalid")
    return state


def _write_state(output_dir: Path, run_id: str, state: str) -> None:
    _write_json(output_dir / "run_state.json", {"run_id": run_id, "state": state})


def _initialize_smoke(output_dir: Path, run_id: str) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"run directory is already initialized: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_state(output_dir, run_id, "smoke_running")


def _require_smoke_complete(output_dir: Path, run_id: str) -> None:
    state = _read_state(output_dir)
    if state.get("run_id") != run_id:
        raise ValueError("requested run_id does not match the initialized run directory")
    if state.get("state") != "smoke_complete":
        raise ValueError(
            f"substantive run requires state smoke_complete; found {state.get('state', 'invalid')}"
        )


def _load_selected_profile(output_dir: Path, run_id: str) -> ComputationalProfile:
    selection_path = output_dir / "selected_profile.json"
    if not selection_path.exists():
        raise FileNotFoundError(
            f"substantive Gate 0 runs require {selection_path.name} from a prior smoke run"
        )
    selected = json.loads(selection_path.read_text(encoding="utf-8"))
    if selected.get("run_id") != run_id:
        raise ValueError("selected_profile.json run_id does not match the requested run")
    try:
        profile = _PROFILE_BY_NAME[selected["name"]]
    except (KeyError, TypeError) as error:
        raise ValueError("selected_profile.json does not name an approved profile") from error
    expected = {"run_id": run_id, **asdict(profile)}
    if selected != expected:
        raise ValueError("selected_profile.json does not match the frozen profile")
    return profile


def _persist_records(
    records: list[PairRecord],
    output_dir: Path,
    *,
    mode: Literal["smoke", "substantive"],
    run_id: str,
    gate_result: str | None = None,
    stop_kind: str | None = None,
) -> tuple[pd.DataFrame, str]:
    frame = pd.DataFrame(asdict(record) for record in records)
    gate_result = gate_result or (
        "STOP" if any(record.exception_text for record in records) else "READY"
    )
    frame["run_id"] = run_id
    frame["gate_result"] = gate_result
    records_name = "smoke_records.csv" if mode == "smoke" else "pair_records.csv"
    summary_name = "smoke_summary.json" if mode == "smoke" else "substantive_summary.json"
    frame.to_csv(output_dir / records_name, index=False)
    summary = {
        "attempted_pairs": len(records),
        "gate_result": gate_result,
        "mode": mode,
        "run_id": run_id,
    }
    if stop_kind is not None:
        summary["stop_kind"] = stop_kind
    _write_json(
        output_dir / summary_name,
        summary,
    )
    return frame, gate_result


def _write_computational_stop_memo(
    output_dir: Path,
    run_id: str,
    smoke: SmokeMeasurement,
    elapsed_seconds: float,
    records: list[PairRecord],
) -> None:
    projections = {
        profile.name: _project_profile(smoke, profile)
        for profile in (FULL_PROFILE, REDUCED_PROFILE)
    }
    exceptions = sorted(
        {record.exception_text for record in records if record.exception_text is not None}
    )
    reason_lines = (
        [
            "Smoke execution recorded exceptions; profile feasibility was not established.",
            "",
            *(f"- {exception}" for exception in exceptions),
        ]
        if exceptions
        else [
            (
                "Neither frozen computational profile is feasible within both the four-hour "
                "runtime limit and the 4 GiB Python-allocation limit. No substantive scientific "
                "fixture run was started."
            )
        ]
    )
    lines = [
        "# Gate 0 computational feasibility memo",
        "",
        f"Run ID: {run_id}",
        "Overall outcome: **STOP**",
        "",
        "## Measured smoke resources",
        "",
        f"- Elapsed seconds: {elapsed_seconds:.6f}",
        f"- Python allocation peak GiB: {smoke.peak_gib:.6f}",
        f"- Full projected seconds: {projections['full'].projected_seconds:.6f}",
        f"- Full projected peak GiB: {projections['full'].projected_peak_gib:.6f}",
        f"- Reduced projected seconds: {projections['reduced'].projected_seconds:.6f}",
        f"- Reduced projected peak GiB: {projections['reduced'].projected_peak_gib:.6f}",
        "",
        "## Reason",
        "",
        *reason_lines,
        "",
        OWNER_DECISION_SENTENCE,
        "",
    ]
    (output_dir / "gate-memo.md").write_text("\n".join(lines), encoding="utf-8")


def run_gate0(
    mode: Literal["smoke", "substantive"], output_dir: Path, *, run_id: str
) -> pd.DataFrame:
    """Run Gate 0, persisting a record for each attempted pair."""

    if mode not in {"smoke", "substantive"}:
        raise ValueError("mode must be 'smoke' or 'substantive'")
    if not run_id or not run_id.strip():
        raise ValueError("run_id must be non-empty")
    if mode == "smoke":
        _initialize_smoke(output_dir, run_id)
    if mode == "substantive":
        _require_smoke_complete(output_dir, run_id)
        profile = _load_selected_profile(output_dir, run_id)
        _write_state(output_dir, run_id, "substantive_running")
        records = _run_pairs(mode, profile, output_dir)
        initial_frame = pd.DataFrame(asdict(record) for record in records)
        result = gate_status(initial_frame)
        frame, _ = _persist_records(
            records,
            output_dir,
            mode=mode,
            run_id=run_id,
            gate_result=result,
            stop_kind="scientific" if result == "STOP" else None,
        )
        write_gate_report(frame, output_dir, run_id=run_id)
        _write_state(output_dir, run_id, "substantive_complete")
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
    projections = {
        profile.name: asdict(_project_profile(smoke, profile))
        for profile in (FULL_PROFILE, REDUCED_PROFILE)
    }
    _write_json(
        output_dir / "smoke_measurement.json",
        {
            "elapsed_seconds": elapsed_seconds,
            "projected_seconds": smoke.projected_seconds,
            "python_allocation_peak_bytes": peak_bytes,
            "peak_gib": smoke.peak_gib,
            "profile_projections": projections,
            "run_id": run_id,
        },
    )
    selected_profile = (
        select_profile(smoke) if not any(record.exception_text for record in records) else None
    )
    frame, _ = _persist_records(
        records,
        output_dir,
        mode=mode,
        run_id=run_id,
        gate_result="READY" if selected_profile is not None else "STOP",
        stop_kind="computational" if selected_profile is None else None,
    )
    if selected_profile is not None:
        _write_json(
            output_dir / "selected_profile.json",
            {"run_id": run_id, **asdict(selected_profile)},
        )
        _write_state(output_dir, run_id, "smoke_complete")
    else:
        _write_computational_stop_memo(output_dir, run_id, smoke, elapsed_seconds, records)
        _write_state(output_dir, run_id, "computational_stop")
    return frame
