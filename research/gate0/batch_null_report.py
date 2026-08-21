"""Hash-pinned evidence reports for batch-level null calibration."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from research.gate0.batch_null_policy import (
    BatchNullConfig,
    BatchSummary,
    CalibrationSelection,
    ConfirmationCheck,
    batch_terminal_status,
    check_confirmation,
    select_calibration_boundary,
    summarize_batches,
)
from research.gate0.config import OWNER_DECISION_SENTENCE


def write_calibration_report(
    records: pd.DataFrame, output_dir: Path, run_id: str, config: BatchNullConfig
) -> Path:
    """Write immutable calibration evidence and its frozen rank selection."""

    _validate_record_run_id(records, run_id, "calibration")
    provenance = _runner_provenance(output_dir, records, config, "calibration")
    batches = summarize_batches(records, config)
    selection = select_calibration_boundary(batches, config)
    summary = _batch_summary(records, batches, selection.boundary)
    summary.to_csv(output_dir / "batch-summary.csv", index=False)
    _plot_batch_medians(summary, output_dir / "plots" / "batch-medians.png", selection.boundary)
    terminal_outcome = batch_terminal_status(selection, None)
    manifest = {
        "run_id": run_id,
        "phase": "calibration",
        "terminal_outcome": terminal_outcome,
        "configuration": provenance["configuration"],
        "seed_namespace": provenance["seed_namespace"],
        "source_revision": provenance["source_revision"],
        "record_count": len(records),
        "records": {"relative_path": "records.csv", "sha256": provenance["records_sha256"]},
        "manifest_input": {
            "relative_path": "manifest-input.json",
            "sha256": provenance["manifest_input_sha256"],
        },
        "selection": asdict(selection),
        "summary_path": "batch-summary.csv",
        "plots": ["plots/batch-medians.png"],
        "warnings": _retained_text(records, "warnings"),
        "exceptions": _retained_text(records, "exception_text"),
        "owner_governance": OWNER_DECISION_SENTENCE,
    }
    _write_json(output_dir / "manifest.json", manifest)
    memo_path = output_dir / "calibration-memo.md"
    memo_path.write_text(
        _calibration_memo(run_id, selection, terminal_outcome, provenance, records), encoding="utf-8"
    )
    _write_json(
        output_dir / "run_state.json",
        {"run_id": run_id, "state": "complete", "terminal_outcome": terminal_outcome},
    )
    return memo_path


def write_confirmation_report(
    records: pd.DataFrame,
    output_dir: Path,
    run_id: str,
    calibration_dir: Path,
    config: BatchNullConfig,
) -> Path:
    """Write confirmation evidence using a copied, hash-verified calibration selection."""

    _validate_record_run_id(records, run_id, "confirmation")
    calibration = _verified_calibration(calibration_dir)
    provenance = _runner_provenance(output_dir, records, config, "confirmation")
    selection = calibration["selection"]
    boundary = float(selection["boundary"])
    batches = summarize_batches(records, config)
    confirmation = check_confirmation(batches, records, boundary, config)
    terminal_outcome = batch_terminal_status(None, confirmation)
    summary = _batch_summary(records, batches, boundary)
    summary.to_csv(output_dir / "confirmation-summary.csv", index=False)
    _plot_batch_classes(summary, output_dir / "plots" / "batch-classifications.png")
    manifest = {
        "run_id": run_id,
        "phase": "confirmation",
        "terminal_outcome": terminal_outcome,
        "configuration": provenance["configuration"],
        "seed_namespace": provenance["seed_namespace"],
        "source_revision": provenance["source_revision"],
        "record_count": len(records),
        "records": {"relative_path": "records.csv", "sha256": provenance["records_sha256"]},
        "manifest_input": {
            "relative_path": "manifest-input.json",
            "sha256": provenance["manifest_input_sha256"],
        },
        "calibration": calibration,
        "confirmation_check": asdict(confirmation),
        "summary_path": "confirmation-summary.csv",
        "plots": ["plots/batch-classifications.png"],
        "warnings": _retained_text(records, "warnings"),
        "exceptions": _retained_text(records, "exception_text"),
        "owner_governance": OWNER_DECISION_SENTENCE,
    }
    _write_json(output_dir / "manifest.json", manifest)
    memo_path = output_dir / "confirmation-memo.md"
    memo_path.write_text(
        _confirmation_memo(run_id, calibration, confirmation, terminal_outcome, provenance, records),
        encoding="utf-8",
    )
    _write_json(
        output_dir / "run_state.json",
        {"run_id": run_id, "state": "complete", "terminal_outcome": terminal_outcome},
    )
    return memo_path


def _validate_record_run_id(records: pd.DataFrame, run_id: str, phase: str) -> None:
    if "run_id" not in records or records["run_id"].isna().any():
        raise ValueError(f"{phase} report requires record run_id")
    run_ids = {str(value) for value in records["run_id"].unique()}
    if len(run_ids) != 1 or run_ids.pop() != run_id:
        raise ValueError(f"{phase} record run ID does not match report run_id")
    if "phase" not in records or not records["phase"].eq(phase).all():
        raise ValueError(f"{phase} report requires only {phase} records")


def _runner_provenance(
    output_dir: Path, records: pd.DataFrame, config: BatchNullConfig, phase: str
) -> dict[str, object]:
    records_path = output_dir / "records.csv"
    input_path = output_dir / "manifest-input.json"
    if not records_path.is_file() or not input_path.is_file():
        raise ValueError("report requires retained records.csv and manifest-input.json")
    try:
        runner_input = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("report requires valid manifest-input.json") from error
    if not isinstance(runner_input, dict):
        raise TypeError("report requires object manifest-input.json")
    return {
        "configuration": runner_input.get("config", asdict(config)),
        "seed_namespace": runner_input.get("seed_namespace", f"batch-null-{phase}"),
        "source_revision": runner_input.get("source_revision", _source_revision()),
        "records_sha256": _sha256(records_path),
        "manifest_input_sha256": _sha256(input_path),
        "records_supplied": len(records),
    }


def _verified_calibration(calibration_dir: Path) -> dict[str, object]:
    manifest_path = calibration_dir / "manifest.json"
    records_path = calibration_dir / "records.csv"
    input_path = calibration_dir / "manifest-input.json"
    if not manifest_path.is_file() or not records_path.is_file() or not input_path.is_file():
        raise ValueError("calibration evidence is missing SHA-256-pinned inputs")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("calibration manifest is not valid JSON with SHA-256 evidence") from error
    if not isinstance(manifest, dict):
        raise TypeError("calibration manifest lacks SHA-256 evidence")
    expected_records_hash = _nested_text(manifest, "records", "sha256")
    expected_input_hash = _nested_text(manifest, "manifest_input", "sha256")
    if not expected_records_hash or not expected_input_hash:
        raise ValueError("calibration manifest lacks SHA-256 evidence")
    if _sha256(records_path) != expected_records_hash or _sha256(input_path) != expected_input_hash:
        raise ValueError("calibration SHA-256 evidence does not match retained inputs")
    selection = manifest.get("selection")
    if not isinstance(selection, dict) or selection.get("status") != "READY":
        raise ValueError("calibration selection must be READY before confirmation")
    boundary = selection.get("boundary")
    if not isinstance(boundary, int | float) or not math.isfinite(boundary):
        raise ValueError("READY calibration selection requires a finite boundary")
    return {
        "directory": str(calibration_dir),
        "manifest_sha256": _sha256(manifest_path),
        "records_sha256": expected_records_hash,
        "manifest_input_sha256": expected_input_hash,
        "selection": selection.copy(),
    }


def _nested_text(payload: dict[str, object], key: str, nested_key: str) -> str | None:
    nested = payload.get(key)
    value = nested.get(nested_key) if isinstance(nested, dict) else None
    return value if isinstance(value, str) else None


def _batch_summary(
    records: pd.DataFrame, batches: list[BatchSummary], boundary: float | None
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for batch in batches:
        batch_records = records.loc[records["batch"] == batch.batch]
        p_values = pd.to_numeric(batch_records.get("permutation_p_value"), errors="coerce")
        is_null_like = (
            batch.complete
            and batch.p_guard_passed
            and batch.median_dcor is not None
            and boundary is not None
            and batch.median_dcor <= boundary
        )
        rows.append(
            {
                "phase": batch.phase,
                "batch": batch.batch,
                "complete": batch.complete,
                "p_guard_passed": batch.p_guard_passed,
                "median_dcor": batch.median_dcor,
                "low_p_value_count": int((p_values <= 0.05).sum()),
                "null_like": is_null_like,
                "warnings": _retained_text(batch_records, "warnings"),
                "exceptions": _retained_text(batch_records, "exception_text"),
            }
        )
    return pd.DataFrame(rows)


def _plot_batch_medians(summary: pd.DataFrame, path: Path, boundary: float | None) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(8, 4.5))
    values = pd.to_numeric(summary["median_dcor"], errors="coerce").dropna()
    axis.scatter(summary.loc[values.index, "batch"], values, color="#4c78a8")
    if boundary is not None:
        axis.axhline(boundary, color="#e45756", linestyle="--", label="selected boundary")
        axis.legend()
    axis.set_xlabel("batch")
    axis.set_ylabel("median distance correlation")
    axis.set_title("Calibration batch medians")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def _plot_batch_classes(summary: pd.DataFrame, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    counts = summary["null_like"].map({True: "null-like", False: "not null-like"}).value_counts()
    figure, axis = plt.subplots(figsize=(6, 4.5))
    axis.bar(counts.index, counts.values, color="#72b7b2")
    axis.set_ylabel("batches")
    axis.set_title("Confirmation batch classifications")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def _calibration_memo(
    run_id: str,
    selection: CalibrationSelection,
    terminal_outcome: str,
    provenance: dict[str, object],
    records: pd.DataFrame,
) -> str:
    boundary = "not selected" if selection.boundary is None else f"`{selection.boundary}`"
    lines = [
        "# Batch-level null calibration memo",
        "",
        f"Run ID: `{run_id}`",
        f"Terminal outcome: **{terminal_outcome}**",
        "",
        "## Frozen calibration selection",
        "",
        f"- Guard-passing batches: {selection.guard_passing_batch_count} of 100 (requires 90 of 100)",
        f"- Selected boundary: {boundary}",
        f"- Batches null-like at the selected boundary: {selection.null_like_batch_count} of 100",
        f"- Qualifying batch IDs: `{list(selection.qualifying_batch_ids)}`",
        "",
        "## Retained provenance",
        "",
        f"- Records SHA-256: `{provenance['records_sha256']}`",
        f"- Manifest-input SHA-256: `{provenance['manifest_input_sha256']}`",
        f"- Seed namespace: `{provenance['seed_namespace']}`",
        f"- Source revision: `{provenance['source_revision']}`",
        "",
        "## Governance",
        "",
        "This reference-only study does not run F1--F8, residualization, or any automatic successor work.",
        f"Warnings: {_retained_text(records, 'warnings') or 'none'}",
        f"Exceptions: {_retained_text(records, 'exception_text') or 'none'}",
        "",
        OWNER_DECISION_SENTENCE,
        "",
    ]
    return "\n".join(lines)


def _confirmation_memo(
    run_id: str,
    calibration: dict[str, object],
    confirmation: ConfirmationCheck,
    terminal_outcome: str,
    provenance: dict[str, object],
    records: pd.DataFrame,
) -> str:
    selection = calibration["selection"]
    lines = [
        "# Batch-level null confirmation memo",
        "",
        f"Run ID: `{run_id}`",
        f"Terminal outcome: **{terminal_outcome}**",
        "",
        "## Copied calibration provenance",
        "",
        f"- Calibration directory: `{calibration['directory']}`",
        f"- Calibration manifest SHA-256: `{calibration['manifest_sha256']}`",
        f"- Calibration records SHA-256: `{calibration['records_sha256']}`",
        f"- Copied selected boundary: `{selection['boundary']}`",
        "",
        "## Confirmation check",
        "",
        f"- Complete: `{confirmation.complete}`",
        f"- Null-like batches: {confirmation.null_like_batch_count} of 100 (requires 85)",
        f"- Low p-values: {confirmation.low_p_value_count} of 1,000 (allows at most 67)",
        "",
        "## Retained provenance and governance",
        "",
        f"- Confirmation records SHA-256: `{provenance['records_sha256']}`",
        f"- Seed namespace: `{provenance['seed_namespace']}`",
        "This reference-only study does not run F1--F8, residualization, or any automatic successor work.",
        f"Warnings: {_retained_text(records, 'warnings') or 'none'}",
        f"Exceptions: {_retained_text(records, 'exception_text') or 'none'}",
        "",
        OWNER_DECISION_SENTENCE,
        "",
    ]
    return "\n".join(lines)


def _retained_text(records: pd.DataFrame, column: str) -> str:
    if column not in records:
        return ""
    return "; ".join(sorted({str(value) for value in records[column].dropna() if str(value)}))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _source_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        check=False,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"
