"""Hash-pinned evidence reports for the F4 residual-link alternative."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from research.gate0.batch_null_report import _verified_calibration
from research.gate0.config import OWNER_DECISION_SENTENCE
from research.gate0.f4_link_policy import (
    DetectionBatch,
    F4LinkConfig,
    check_detection,
    detection_terminal_status,
    summarize_detection_batches,
)

_PHASE = "f4-residual-link"
_FIXTURE = "F4-residual-link"
_PAIR = ("X1", "X3")
_NAMESPACE = "batch-f4-residual-link"
_REQUIRED_COLUMNS = {
    "fixture_id", "left", "right", "phase", "batch", "replication",
    "observed_statistic", "permutation_p_value", "residual_samples_path",
    "null_statistics_path", "seed_namespace", "run_id", "warnings", "exception_text",
}


def write_f4_link_report(
    records: pd.DataFrame,
    output_dir: Path,
    run_id: str,
    f4_null_dir: Path,
    calibration_dir: Path,
    config: F4LinkConfig,
) -> Path:
    """Write immutable clear-signal evidence pinned to both approved parents."""

    _validate_records(records, output_dir, run_id)
    f4_null = _verified_f4_null(f4_null_dir)
    calibration = _verified_calibration(calibration_dir)
    boundary = float(calibration["selection"]["boundary"])
    if boundary != config.detection_boundary:
        raise ValueError("calibration boundary does not match the frozen detection boundary")
    provenance = _runner_provenance(output_dir, records, config)
    batches = summarize_detection_batches(records, config)
    check = check_detection(batches, records, boundary, config)
    invalidating_evidence = _retained_text(records, "warnings") or _retained_text(records, "exception_text")
    terminal_outcome = "STOP" if invalidating_evidence else detection_terminal_status(check)
    summary = _detection_summary(records, batches)
    summary.to_csv(output_dir / "f4-link-summary.csv", index=False)
    _plot_detection_batches(summary, output_dir / "plots" / "f4-link-detections.png")
    manifest = {
        "run_id": run_id,
        "phase": _PHASE,
        "fixture_id": _FIXTURE,
        "pair": list(_PAIR),
        "terminal_outcome": terminal_outcome,
        "configuration": provenance["configuration"],
        "seed_namespace": _NAMESPACE,
        "source_revision": provenance["source_revision"],
        "record_count": len(records),
        "records": {"relative_path": "records.csv", "sha256": provenance["records_sha256"]},
        "manifest_input": {
            "relative_path": "manifest-input.json", "sha256": provenance["manifest_input_sha256"],
        },
        "f4_null": f4_null,
        "calibration": calibration,
        "detection_check": asdict(check),
        "detection_boundary": boundary,
        "summary_path": "f4-link-summary.csv",
        "plots": ["plots/f4-link-detections.png"],
        "warnings": _retained_text(records, "warnings"),
        "exceptions": _retained_text(records, "exception_text"),
        "owner_governance": OWNER_DECISION_SENTENCE,
    }
    _write_json(output_dir / "manifest.json", manifest)
    memo_path = output_dir / "f4-link-memo.md"
    memo_path.write_text(
        _memo(run_id, f4_null, calibration, check, terminal_outcome, provenance, records), encoding="utf-8"
    )
    _write_json(
        output_dir / "run_state.json",
        {"run_id": run_id, "state": "complete", "terminal_outcome": terminal_outcome},
    )
    return memo_path


def _validate_records(records: pd.DataFrame, output_dir: Path, run_id: str) -> None:
    missing = _REQUIRED_COLUMNS.difference(records.columns)
    if missing:
        raise ValueError(f"F4 link report requires record columns: {sorted(missing)}")
    if records.empty or records["run_id"].isna().any() or not records["run_id"].eq(run_id).all():
        raise ValueError("F4 link record run ID does not match report run_id")
    if not records["fixture_id"].eq(_FIXTURE).all():
        raise ValueError("F4 link report requires the F4 residual-link fixture")
    if not records["left"].eq(_PAIR[0]).all() or not records["right"].eq(_PAIR[1]).all():
        raise ValueError("F4 link report requires pair X1/X3")
    if not records["phase"].eq(_PHASE).all():
        raise ValueError("F4 link report requires the frozen phase")
    if not records["seed_namespace"].eq(_NAMESPACE).all():
        raise ValueError("F4 link report requires the frozen seed namespace")
    for row in records.itertuples(index=False):
        if isinstance(row.exception_text, str) and row.exception_text:
            continue
        for name, label in ((row.residual_samples_path, "residual sample"), (row.null_statistics_path, "null array")):
            if not isinstance(name, str) or not name or not (output_dir / name).is_file():
                raise ValueError(f"F4 link report requires retained {label}")


def _verified_f4_null(f4_null_dir: Path) -> dict[str, object]:
    manifest_path, records_path, input_path = (
        f4_null_dir / "manifest.json", f4_null_dir / "records.csv", f4_null_dir / "manifest-input.json"
    )
    if not all(path.is_file() for path in (manifest_path, records_path, input_path)):
        raise ValueError("reviewed F4-null evidence is missing SHA-256-pinned inputs")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("reviewed F4-null manifest is not valid JSON") from error
    if not isinstance(manifest, dict):
        raise TypeError("reviewed F4-null manifest must be an object")
    expected_records = _nested_text(manifest, "records", "sha256")
    expected_input = _nested_text(manifest, "manifest_input", "sha256")
    if not expected_records or not expected_input:
        raise ValueError("reviewed F4-null manifest lacks SHA-256 evidence")
    if _sha256(records_path) != expected_records or _sha256(input_path) != expected_input:
        raise ValueError("reviewed F4-null SHA-256 evidence does not match retained inputs")
    if (manifest.get("terminal_outcome"), manifest.get("fixture_id"), manifest.get("pair"), manifest.get("phase")) != (
        "PASS", "F4", list(_PAIR), "f4-linear-null-transfer"
    ):
        raise ValueError("reviewed F4-null evidence is not the approved F4 PASS comparator")
    return {
        "directory": str(f4_null_dir), "manifest_sha256": _sha256(manifest_path),
        "records_sha256": expected_records, "manifest_input_sha256": expected_input,
        "terminal_outcome": "PASS",
    }


def _runner_provenance(output_dir: Path, records: pd.DataFrame, config: F4LinkConfig) -> dict[str, object]:
    records_path, input_path = output_dir / "records.csv", output_dir / "manifest-input.json"
    if not records_path.is_file() or not input_path.is_file():
        raise ValueError("F4 link report requires retained records.csv and manifest-input.json")
    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("F4 link report requires valid manifest-input.json") from error
    if not isinstance(payload, dict):
        raise TypeError("F4 link report requires object manifest-input.json")
    expected = {"fixture_id": _FIXTURE, "pair": list(_PAIR), "phase": _PHASE, "run_id": records["run_id"].iloc[0], "seed_namespace": _NAMESPACE}
    if any(payload.get(key) != value for key, value in expected.items()):
        raise ValueError("F4 link runner provenance does not match the frozen scenario")
    return {
        "configuration": payload.get("config", asdict(config)), "source_revision": payload.get("source_revision", _source_revision()),
        "records_sha256": _sha256(records_path), "manifest_input_sha256": _sha256(input_path),
    }


def _detection_summary(records: pd.DataFrame, batches: list[DetectionBatch]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for batch in batches:
        batch_records = records.loc[records["batch"] == batch.batch]
        rows.append({
            "batch": batch.batch, "complete": batch.complete, "median_dcor": batch.median_dcor,
            "low_p_value_count": batch.low_p_value_count, "detected": batch.detected,
            "warnings": _retained_text(batch_records, "warnings"),
            "exceptions": _retained_text(batch_records, "exception_text"),
        })
    return pd.DataFrame(rows)


def _plot_detection_batches(summary: pd.DataFrame, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    path.parent.mkdir(parents=True, exist_ok=True)
    counts = summary["detected"].map({True: "detected", False: "not detected"}).value_counts()
    figure, axis = plt.subplots(figsize=(6, 4.5))
    axis.bar(counts.index, counts.values, color="#e45756")
    axis.set_ylabel("batches")
    axis.set_title("F4 residual-link batch detections")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def _memo(run_id: str, f4_null: dict[str, object], calibration: dict[str, object], check: object, outcome: str, provenance: dict[str, object], records: pd.DataFrame) -> str:
    return "\n".join([
        "# F4 residual-link alternative memo", "", f"Run ID: `{run_id}`", f"Terminal outcome: **{outcome}**", "",
        "## Pinned parents", "", f"- F4-null manifest SHA-256: `{f4_null['manifest_sha256']}`",
        f"- F4-null records SHA-256: `{f4_null['records_sha256']}`", f"- Calibration manifest SHA-256: `{calibration['manifest_sha256']}`",
        f"- Calibration records SHA-256: `{calibration['records_sha256']}`",
        f"- Frozen detection boundary: `{calibration['selection']['boundary']}`", "", "## Detection check", "",
        "- Fixture and pair: `F4-residual-link`, `(X1, X3)`", "- Adjustment variables: `(X2, X4, X5, X6)`",
        f"- Complete: `{check.complete}`", f"- Detected batches: {check.detected_batch_count} of 100 (requires 85)", "",
        "## Governance", "", f"- Alternative records SHA-256: `{provenance['records_sha256']}`",
        "This result supports detection of one clear linear residual link only; it makes no weak-effect power or package-readiness claim.",
        "It does not authorize recalibration, changed signal strength, a new simulation family, or package work.",
        f"Warnings: {_retained_text(records, 'warnings') or 'none'}", f"Exceptions: {_retained_text(records, 'exception_text') or 'none'}", "", OWNER_DECISION_SENTENCE, "",
    ])


def _nested_text(payload: dict[str, object], key: str, nested_key: str) -> str | None:
    nested = payload.get(key)
    value = nested.get(nested_key) if isinstance(nested, dict) else None
    return value if isinstance(value, str) else None


def _retained_text(records: pd.DataFrame, column: str) -> str:
    return "; ".join(sorted({str(value) for value in records[column].dropna() if str(value)})) if column in records else ""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _source_revision() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[2], capture_output=True, check=False, text=True)
    return result.stdout.strip() if result.returncode == 0 else "unavailable"
