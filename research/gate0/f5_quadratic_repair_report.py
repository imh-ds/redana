"""Hash-pinned evidence report for the frozen F5 quadratic repair."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from research.gate0.batch_null_policy import (
    BatchNullConfig,
    BatchSummary,
    batch_terminal_status,
    check_confirmation,
    summarize_batches,
)
from research.gate0.batch_null_report import _verified_calibration
from research.gate0.config import OWNER_DECISION_SENTENCE
from research.gate0.f5_quadratic_repair_runner import F5QuadraticRepairConfig

_BOUNDARY = 0.058242447845091264
_PHASE = "f5-quadratic-repair"
_FIXTURE = "F5"
_PAIR = ("X1", "X2")
_NAMESPACE = "batch-f5-quadratic-repair"
_CALIBRATION_HASHES = {
    "records_sha256": "267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5",
    "manifest_input_sha256": (
        "7737bf6b9f57ed0072843df8dd639e603dee3ebb2a9ad85b7d9d22703279ce9c"
    ),
    "manifest_sha256": "639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef",
}
_F5_STOP_HASHES = {
    "records_sha256": "3f38ac7f324c597cf13b84006cf1af35fbce0fb30b497ef2629b29b79a7fee09",
    "manifest_input_sha256": (
        "b16367ef572f906df2653447558e31047e0cda0943d3d774725546f213902251"
    ),
    "manifest_sha256": "521f35953929d46670eb90687e6a4645684f335d878b90090029c31d87c8dce2",
}
_REQUIRED_COLUMNS = {
    "fixture_id",
    "left",
    "right",
    "phase",
    "batch",
    "replication",
    "observed_statistic",
    "permutation_p_value",
    "residual_samples_path",
    "null_statistics_path",
    "seed_namespace",
    "fixture_seed",
    "residual_seed",
    "permutation_seed",
    "elapsed_seconds",
    "warnings",
    "exception_text",
    "run_id",
}


def write_f5_quadratic_repair_report(
    records: pd.DataFrame,
    output_dir: Path,
    run_id: str,
    calibration_dir: Path,
    f5_stop_dir: Path,
    config: F5QuadraticRepairConfig,
) -> Path:
    """Write repair evidence against the exact calibration and F5 STOP parents."""

    if config != F5QuadraticRepairConfig():
        raise ValueError("F5 report requires the frozen F5 quadratic repair configuration")
    _validate_records(records, output_dir, run_id, config)
    calibration = _verified_frozen_calibration(calibration_dir)
    f5_stop = _verified_f5_stop(f5_stop_dir)
    provenance = _runner_provenance(output_dir, records, config)
    policy = _batch_policy(config)
    batches = summarize_batches(records, policy)
    confirmation = check_confirmation(batches, records, _BOUNDARY, policy)
    terminal_outcome = batch_terminal_status(None, confirmation)
    summary = _batch_summary(records, batches, _BOUNDARY)
    _write_csv(output_dir / "f5-quadratic-repair-summary.csv", summary)
    _write_plot_atomic(
        summary, output_dir / "plots" / "f5-quadratic-batch-classifications.png"
    )
    manifest = {
        "run_id": run_id,
        "phase": _PHASE,
        "fixture_id": _FIXTURE,
        "pair": list(_PAIR),
        "terminal_outcome": terminal_outcome,
        "configuration": provenance["configuration"],
        "basis": {"name": "raw-plus-square", "uses_splines": False},
        "seed_namespace": _NAMESPACE,
        "source_revision": provenance["source_revision"],
        "record_count": len(records),
        "records": {
            "relative_path": "records.csv",
            "sha256": provenance["records_sha256"],
        },
        "manifest_input": {
            "relative_path": "manifest-input.json",
            "sha256": provenance["manifest_input_sha256"],
        },
        "calibration": calibration,
        "f5_stop": f5_stop,
        "copied_boundary": _BOUNDARY,
        "confirmation_check": asdict(confirmation),
        "summary_path": "f5-quadratic-repair-summary.csv",
        "plots": ["plots/f5-quadratic-batch-classifications.png"],
        "warnings": _retained_text(records, "warnings"),
        "exceptions": _retained_text(records, "exception_text"),
        "owner_governance": OWNER_DECISION_SENTENCE,
    }
    _write_json(output_dir / "manifest.json", manifest)
    memo_path = output_dir / "f5-quadratic-repair-memo.md"
    _write_text(
        memo_path,
        _memo(
            run_id,
            calibration,
            f5_stop,
            confirmation,
            terminal_outcome,
            provenance,
            records,
        ),
    )
    _write_json(
        output_dir / "run_state.json",
        {"run_id": run_id, "state": "complete", "terminal_outcome": terminal_outcome},
    )
    return memo_path


def _validate_records(
    records: pd.DataFrame,
    output_dir: Path,
    run_id: str,
    config: F5QuadraticRepairConfig,
) -> None:
    missing = _REQUIRED_COLUMNS.difference(records.columns)
    if missing:
        raise ValueError(f"F5 quadratic repair requires record columns: {sorted(missing)}")
    if records.empty or records["run_id"].isna().any() or not records["run_id"].eq(run_id).all():
        raise ValueError("F5 quadratic repair record run ID does not match report run_id")
    if not records["fixture_id"].eq(_FIXTURE).all():
        raise ValueError("F5 quadratic repair requires only fixture F5")
    if not records["left"].eq(_PAIR[0]).all() or not records["right"].eq(_PAIR[1]).all():
        raise ValueError("F5 quadratic repair requires only pair X1/X2")
    if not records["phase"].eq(_PHASE).all():
        raise ValueError("F5 quadratic repair requires the frozen phase")
    if not records["seed_namespace"].eq(_NAMESPACE).all():
        raise ValueError("F5 quadratic repair requires the frozen seed namespace")
    expected = {
        (batch, replication)
        for batch in range(config.batches)
        for replication in range(config.replications_per_batch)
    }
    actual = set(records[["batch", "replication"]].itertuples(index=False, name=None))
    if len(records) != len(expected) or actual != expected:
        raise ValueError("F5 quadratic repair requires every frozen batch/replication identity")
    for row in records.itertuples(index=False):
        if isinstance(row.exception_text, str) and row.exception_text:
            continue
        _require_evidence_file(output_dir, row.residual_samples_path, "residual sample")
        _require_evidence_file(output_dir, row.null_statistics_path, "null array")


def _require_evidence_file(output_dir: Path, value: object, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"F5 quadratic repair requires every retained {label}")
    relative_path = Path(value)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"F5 quadratic repair requires an in-run {label}")
    if not (output_dir / relative_path).is_file():
        raise ValueError(f"F5 quadratic repair requires retained {label}: {value}")


def _verified_frozen_calibration(calibration_dir: Path) -> dict[str, object]:
    _verify_parent_hashes(calibration_dir, _CALIBRATION_HASHES, "calibration")
    calibration = _verified_calibration(calibration_dir)
    selection = calibration.get("selection")
    if not isinstance(selection, dict) or selection.get("boundary") != _BOUNDARY:
        raise ValueError("calibration does not contain the frozen F5 boundary")
    for key, expected in _CALIBRATION_HASHES.items():
        if calibration.get(key) != expected:
            raise ValueError(f"calibration {key} does not match frozen SHA-256 provenance")
    return calibration


def _verified_f5_stop(f5_stop_dir: Path) -> dict[str, object]:
    _verify_parent_hashes(f5_stop_dir, _F5_STOP_HASHES, "F5 STOP")
    manifest_path = f5_stop_dir / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("F5 STOP manifest is not valid JSON") from error
    if not isinstance(manifest, dict):
        raise TypeError("F5 STOP manifest must be an object")
    if _nested_text(manifest, "records", "sha256") != _F5_STOP_HASHES["records_sha256"]:
        raise ValueError("F5 STOP manifest records SHA-256 does not match frozen provenance")
    if (
        _nested_text(manifest, "manifest_input", "sha256")
        != _F5_STOP_HASHES["manifest_input_sha256"]
    ):
        raise ValueError("F5 STOP input manifest SHA-256 does not match frozen provenance")
    identity = (
        manifest.get("terminal_outcome"),
        manifest.get("fixture_id"),
        manifest.get("pair"),
        manifest.get("phase"),
    )
    if identity != ("STOP", _FIXTURE, list(_PAIR), "f5-null-transfer"):
        raise ValueError("F5 STOP parent is not the recorded F5 STOP comparator")
    check = manifest.get("confirmation_check")
    if not isinstance(check, dict):
        raise ValueError("F5 STOP parent lacks its recorded confirmation outcome")
    if check.get("null_like_batch_count") != 74:
        raise ValueError("F5 STOP parent must record exactly 74 null-like batches")
    if check.get("low_p_value_count") != 81:
        raise ValueError("F5 STOP parent must record exactly 81 low p-values")
    return {
        "directory": str(f5_stop_dir),
        **_F5_STOP_HASHES,
        "terminal_outcome": "STOP",
        "null_like_batch_count": 74,
        "low_p_value_count": 81,
    }


def _verify_parent_hashes(
    directory: Path, expected: dict[str, str], label: str
) -> None:
    paths = {
        "records_sha256": directory / "records.csv",
        "manifest_input_sha256": directory / "manifest-input.json",
        "manifest_sha256": directory / "manifest.json",
    }
    for key, path in paths.items():
        if not path.is_file():
            raise ValueError(f"{label} evidence is missing SHA-256-pinned {path.name}")
        if _sha256(path) != expected[key]:
            raise ValueError(f"{label} {path.name} SHA-256 does not match frozen provenance")


def _runner_provenance(
    output_dir: Path,
    records: pd.DataFrame,
    config: F5QuadraticRepairConfig,
) -> dict[str, object]:
    records_path = output_dir / "records.csv"
    input_path = output_dir / "manifest-input.json"
    if not records_path.is_file() or not input_path.is_file():
        raise ValueError("F5 quadratic repair requires retained records.csv and manifest-input.json")
    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("F5 quadratic repair requires valid manifest-input.json") from error
    if not isinstance(payload, dict):
        raise TypeError("F5 quadratic repair requires object manifest-input.json")
    expected = {
        "basis": "raw-plus-square",
        "config": asdict(config),
        "fixture_id": _FIXTURE,
        "pair": list(_PAIR),
        "phase": _PHASE,
        "run_id": records["run_id"].iloc[0],
        "seed_namespace": _NAMESPACE,
        "uses_splines": False,
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise ValueError("F5 quadratic runner provenance does not match the frozen scenario")
    return {
        "configuration": payload["config"],
        "source_revision": payload.get("source_revision", _source_revision()),
        "records_sha256": _sha256(records_path),
        "manifest_input_sha256": _sha256(input_path),
    }


def _batch_policy(config: F5QuadraticRepairConfig) -> BatchNullConfig:
    return BatchNullConfig(
        batches=config.batches,
        replications_per_batch=config.replications_per_batch,
        evaluation_rows=config.rows,
        permutations=config.permutations,
    )


def _batch_summary(
    records: pd.DataFrame, batches: list[BatchSummary], boundary: float
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for batch in batches:
        batch_records = records.loc[records["batch"] == batch.batch]
        p_values = pd.to_numeric(batch_records["permutation_p_value"], errors="coerce")
        rows.append(
            {
                "batch": batch.batch,
                "complete": batch.complete,
                "p_guard_passed": batch.p_guard_passed,
                "median_dcor": batch.median_dcor,
                "low_p_value_count": int((p_values <= 0.05).sum()),
                "null_like": bool(
                    batch.complete
                    and batch.p_guard_passed
                    and batch.median_dcor is not None
                    and batch.median_dcor <= boundary
                ),
                "warnings": _retained_text(batch_records, "warnings"),
                "exceptions": _retained_text(batch_records, "exception_text"),
            }
        )
    return pd.DataFrame(rows)


def _plot_batch_classes(summary: pd.DataFrame, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    labels = summary["null_like"].map({True: "null-like", False: "not null-like"})
    counts = labels.value_counts()
    figure, axis = plt.subplots(figsize=(6, 4.5))
    axis.bar(counts.index, counts.values, color="#72b7b2")
    axis.set_ylabel("batches")
    axis.set_title("F5 quadratic-repair batch classifications")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def _memo(
    run_id: str,
    calibration: dict[str, object],
    f5_stop: dict[str, object],
    confirmation: object,
    terminal_outcome: str,
    provenance: dict[str, object],
    records: pd.DataFrame,
) -> str:
    return "\n".join(
        [
            "# F5 explicit-quadratic repair memo",
            "",
            f"Run ID: `{run_id}`",
            f"Terminal outcome: **{terminal_outcome}**",
            "",
            "## Frozen basis and parents",
            "",
            "- Basis: raw value followed by its square for each adjustment variable",
            "- Splines and interactions: none",
            f"- Copied raw-calibration boundary: `{_BOUNDARY}`",
            f"- Calibration manifest SHA-256: `{calibration['manifest_sha256']}`",
            f"- Original F5 STOP manifest SHA-256: `{f5_stop['manifest_sha256']}`",
            "- Original F5 outcome: `STOP` (74 null-like batches; 81 low p-values)",
            "",
            "## Frozen confirmation rule",
            "",
            f"- Complete: `{confirmation.complete}`",
            (
                f"- Null-like batches: {confirmation.null_like_batch_count} of 100 "
                "(requires 85)"
            ),
            (
                f"- Low p-values: {confirmation.low_p_value_count} of 1,000 "
                "(allows at most 67)"
            ),
            "",
            "## Scope and governance",
            "",
            f"- Repair records SHA-256: `{provenance['records_sha256']}`",
            (
                "A PASS supports only that this explicit raw-plus-square basis repairs the "
                "prescribed F5 quadratic null under this frozen 1,000-row procedure."
            ),
            (
                "It does not establish general nonlinear robustness or authorize tuning, "
                "a matched alternative, recalibration, or package work."
            ),
            f"Warnings: {_retained_text(records, 'warnings') or 'none'}",
            f"Exceptions: {_retained_text(records, 'exception_text') or 'none'}",
            "",
            OWNER_DECISION_SENTENCE,
            "",
        ]
    )


def _nested_text(payload: dict[str, object], key: str, nested_key: str) -> str | None:
    nested = payload.get(key)
    value = nested.get(nested_key) if isinstance(nested, dict) else None
    return value if isinstance(value, str) else None


def _retained_text(records: pd.DataFrame, column: str) -> str:
    if column not in records:
        return ""
    return "; ".join(sorted({str(value) for value in records[column].dropna() if str(value)}))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        frame.to_csv(temporary, index=False)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_plot_atomic(summary: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.stem}.tmp{path.suffix}")
    try:
        _plot_batch_classes(summary, temporary)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_json(path: Path, payload: object) -> None:
    _write_text(path, json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _write_text(path: Path, value: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_text(value, encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _source_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        check=False,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"
