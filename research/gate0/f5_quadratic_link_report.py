"""Hash-pinned evidence reports for the F5 quadratic-residual-link alternative."""

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

_PHASE = "f5-quadratic-residual-link"
_FIXTURE = "F5-quadratic-residual-link"
_PAIR = ("X1", "X2")
_NAMESPACE = "batch-f5-quadratic-residual-link"
_REQUIRED_COLUMNS = {
    "fixture_id", "left", "right", "phase", "batch", "replication",
    "observed_statistic", "permutation_p_value", "residual_samples_path",
    "null_statistics_path", "seed_namespace", "run_id", "warnings", "exception_text",
}
_CALIBRATION_HASHES = {
    "records_sha256": "267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5",
    "manifest_input_sha256": "7737bf6b9f57ed0072843df8dd639e603dee3ebb2a9ad85b7d9d22703279ce9c",
    "manifest_sha256": "639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef",
}
_F5_QUADRATIC_REPAIR_HASHES = {
    "records_sha256": "f4fbf588fdd66198fcbce18fdb0031f41e4d42787922bfa4cdd1f4a745277836",
    "manifest_input_sha256": "6da7a9684409b2091aa3eb21534df0900336cfdb8b3ce5541a4d9f5c39153e30",
    "manifest_sha256": "9f45b9c0c80b050fe6e8fd6353b79ed45b1f3076b7e5b07140890f925ed098a7",
}


def write_f5_quadratic_link_report(
    records: pd.DataFrame,
    output_dir: Path,
    run_id: str,
    f5_quadratic_repair_dir: Path,
    calibration_dir: Path,
    config: F4LinkConfig,
) -> Path:
    """Write immutable detection evidence pinned to both approved parents."""

    _validate_records(records, output_dir, run_id)
    f5_quadratic_repair = _verified_f5_quadratic_repair(f5_quadratic_repair_dir)
    calibration = _verified_calibration(calibration_dir)
    boundary = float(calibration["selection"]["boundary"])
    if boundary != config.detection_boundary:
        raise ValueError("calibration boundary does not match the frozen detection boundary")
    provenance = _runner_provenance(output_dir, records, config)
    batches = summarize_detection_batches(records, config)
    check = check_detection(batches, records, boundary, config)
    invalidating_evidence = _retained_text(records, "warnings") or _retained_text(
        records, "exception_text"
    )
    terminal_outcome = "STOP" if invalidating_evidence else detection_terminal_status(check)
    summary = _detection_summary(records, batches)
    summary.to_csv(output_dir / "f5-quadratic-link-summary.csv", index=False)
    _plot_detection_batches(summary, output_dir / "plots" / "f5-quadratic-link-detections.png")
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
        "f5_quadratic_repair": f5_quadratic_repair,
        "calibration": calibration,
        "detection_check": asdict(check),
        "detection_boundary": boundary,
        "summary_path": "f5-quadratic-link-summary.csv",
        "plots": ["plots/f5-quadratic-link-detections.png"],
        "warnings": _retained_text(records, "warnings"),
        "exceptions": _retained_text(records, "exception_text"),
        "owner_governance": OWNER_DECISION_SENTENCE,
    }
    _write_json(output_dir / "manifest.json", manifest)
    memo_path = output_dir / "f5-quadratic-link-memo.md"
    memo_path.write_text(
        _memo(run_id, f5_quadratic_repair, calibration, check, terminal_outcome, provenance, records),
        encoding="utf-8",
    )
    _write_json(
        output_dir / "run_state.json",
        {"run_id": run_id, "state": "complete", "terminal_outcome": terminal_outcome},
    )
    return memo_path


def _validate_records(records: pd.DataFrame, output_dir: Path, run_id: str) -> None:
    missing = _REQUIRED_COLUMNS.difference(records.columns)
    if missing:
        raise ValueError(f"F5 quadratic-link report requires record columns: {sorted(missing)}")
    if records.empty or records["run_id"].isna().any() or not records["run_id"].eq(run_id).all():
        raise ValueError("F5 quadratic-link record run ID does not match report run_id")
    if not records["fixture_id"].eq(_FIXTURE).all():
        raise ValueError("F5 quadratic-link report requires the F5 quadratic-link fixture")
    if not records["left"].eq(_PAIR[0]).all() or not records["right"].eq(_PAIR[1]).all():
        raise ValueError("F5 quadratic-link report requires pair X1/X2")
    if not records["phase"].eq(_PHASE).all():
        raise ValueError("F5 quadratic-link report requires the frozen phase")
    if not records["seed_namespace"].eq(_NAMESPACE).all():
        raise ValueError("F5 quadratic-link report requires the frozen seed namespace")
    for row in records.itertuples(index=False):
        if isinstance(row.exception_text, str) and row.exception_text:
            continue
        for name, label in (
            (row.residual_samples_path, "residual sample"),
            (row.null_statistics_path, "null array"),
        ):
            if not isinstance(name, str) or not name or not (output_dir / name).is_file():
                raise ValueError(f"F5 quadratic-link report requires retained {label}")


def _verify_parent_hashes(directory: Path, expected: dict[str, str], label: str) -> None:
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


def _verified_f5_quadratic_repair(f5_quadratic_repair_dir: Path) -> dict[str, object]:
    _verify_parent_hashes(f5_quadratic_repair_dir, _F5_QUADRATIC_REPAIR_HASHES, "F5 quadratic-repair")
    manifest_path = f5_quadratic_repair_dir / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("F5 quadratic-repair manifest is not valid JSON") from error
    if not isinstance(manifest, dict):
        raise TypeError("F5 quadratic-repair manifest must be an object")
    identity = (
        manifest.get("terminal_outcome"),
        manifest.get("fixture_id"),
        manifest.get("pair"),
        manifest.get("phase"),
    )
    if identity[0] != "PASS":
        raise ValueError("F5 quadratic-repair parent must record terminal outcome PASS")
    if identity[1:] != ("F5", ["X1", "X2"], "f5-quadratic-repair"):
        raise ValueError("F5 quadratic-repair parent is not the recorded F5 quadratic-repair comparator")
    check = manifest.get("confirmation_check")
    if not isinstance(check, dict):
        raise ValueError("F5 quadratic-repair parent lacks its recorded confirmation outcome")
    if check.get("null_like_batch_count") != 90:
        raise ValueError("F5 quadratic-repair parent must record exactly 90 null-like batches")
    if check.get("low_p_value_count") != 44:
        raise ValueError("F5 quadratic-repair parent must record exactly 44 low p-values")
    return {
        "directory": str(f5_quadratic_repair_dir),
        **_F5_QUADRATIC_REPAIR_HASHES,
        "terminal_outcome": "PASS",
        "null_like_batch_count": 90,
        "low_p_value_count": 44,
    }


def _runner_provenance(
    output_dir: Path, records: pd.DataFrame, config: F4LinkConfig
) -> dict[str, object]:
    records_path, input_path = output_dir / "records.csv", output_dir / "manifest-input.json"
    if not records_path.is_file() or not input_path.is_file():
        raise ValueError("F5 quadratic-link report requires retained records.csv and manifest-input.json")
    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("F5 quadratic-link report requires valid manifest-input.json") from error
    if not isinstance(payload, dict):
        raise TypeError("F5 quadratic-link report requires object manifest-input.json")
    expected = {
        "fixture_id": _FIXTURE, "pair": list(_PAIR), "phase": _PHASE,
        "run_id": records["run_id"].iloc[0], "seed_namespace": _NAMESPACE,
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise ValueError("F5 quadratic-link runner provenance does not match the frozen scenario")
    return {
        "configuration": payload.get("config", asdict(config)),
        "source_revision": payload.get("source_revision", _source_revision()),
        "records_sha256": _sha256(records_path),
        "manifest_input_sha256": _sha256(input_path),
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
    axis.bar(counts.index, counts.values, color="#4c78a8")
    axis.set_ylabel("batches")
    axis.set_title("F5 quadratic-link batch detections")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def _memo(
    run_id: str,
    f5_quadratic_repair: dict[str, object],
    calibration: dict[str, object],
    check: object,
    outcome: str,
    provenance: dict[str, object],
    records: pd.DataFrame,
) -> str:
    return "\n".join([
        "# F5 quadratic-residual-link alternative memo", "", f"Run ID: `{run_id}`",
        f"Terminal outcome: **{outcome}**", "",
        "## Pinned parents", "",
        f"- F5 quadratic-repair manifest SHA-256: `{f5_quadratic_repair['manifest_sha256']}`",
        f"- F5 quadratic-repair records SHA-256: `{f5_quadratic_repair['records_sha256']}`",
        f"- Calibration manifest SHA-256: `{calibration['manifest_sha256']}`",
        f"- Calibration records SHA-256: `{calibration['records_sha256']}`",
        f"- Frozen detection boundary: `{calibration['selection']['boundary']}`", "",
        "## Detection check", "",
        "- Fixture and pair: `F5-quadratic-residual-link`, `(X1, X2)`",
        "- Adjustment variables: `(X3, X4, X5, X6)`",
        f"- Complete: `{check.complete}`",
        f"- Detected batches: {check.detected_batch_count} of 100 (requires 85)", "",
        "## Governance", "",
        f"- Alternative records SHA-256: `{provenance['records_sha256']}`",
        (
            "This result supports detection of one planted nonlinear residual link, layered "
            "on the F5 quadratic common cause, under the same raw-plus-square repair basis "
            "only; it makes no general nonlinear-power or package-readiness claim."
        ),
        "It does not authorize recalibration, changed signal strength, a new simulation family, or package work.",
        f"Warnings: {_retained_text(records, 'warnings') or 'none'}",
        f"Exceptions: {_retained_text(records, 'exception_text') or 'none'}", "",
        OWNER_DECISION_SENTENCE, "",
    ])


def _retained_text(records: pd.DataFrame, column: str) -> str:
    return "; ".join(sorted({str(value) for value in records[column].dropna() if str(value)})) if column in records else ""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _source_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[2],
        capture_output=True, check=False, text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"
