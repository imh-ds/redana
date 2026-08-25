"""Hash-pinned evidence reports for the frozen F1 independence null transfer."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Protocol

import pandas as pd

from research.gate0.batch_null_policy import (
    BatchNullConfig,
    batch_terminal_status,
    check_confirmation,
    summarize_batches,
)
from research.gate0.batch_null_report import _verified_calibration
from research.gate0.config import OWNER_DECISION_SENTENCE

_PHASE = "f1-null-transfer"
_FIXTURE = "F1"
_PAIR = ("X1", "X2")
_NAMESPACE = "batch-f1-null-transfer"
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
    "seed_namespace",
    "run_id",
    "exception_text",
}


class _TransferConfig(Protocol):
    batches: int
    replications_per_batch: int
    rows: int
    permutations: int


def write_f1_transfer_report(
    records: pd.DataFrame,
    output_dir: Path,
    run_id: str,
    calibration_dir: Path,
    config: _TransferConfig,
) -> Path:
    """Write immutable F1 transfer evidence against the copied reference boundary."""

    _validate_f1_records(records, output_dir, run_id)
    calibration = _verified_calibration(calibration_dir)
    provenance = _runner_provenance(output_dir, records, config)
    policy = _batch_policy(config)
    policy_records = records.assign(phase=_PHASE)
    batches = summarize_batches(policy_records, policy)
    boundary = float(calibration["selection"]["boundary"])
    confirmation = check_confirmation(batches, policy_records, boundary, policy)
    terminal_outcome = batch_terminal_status(None, confirmation)
    summary = _batch_summary(policy_records, batches, boundary)
    summary.to_csv(output_dir / "f1-transfer-summary.csv", index=False)
    _plot_batch_classes(summary, output_dir / "plots" / "f1-batch-classifications.png")
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
            "relative_path": "manifest-input.json",
            "sha256": provenance["manifest_input_sha256"],
        },
        "calibration": calibration,
        "confirmation_check": asdict(confirmation),
        "summary_path": "f1-transfer-summary.csv",
        "plots": ["plots/f1-batch-classifications.png"],
        "warnings": _retained_text(records, "warnings"),
        "exceptions": _retained_text(records, "exception_text"),
        "owner_governance": OWNER_DECISION_SENTENCE,
    }
    _write_json(output_dir / "manifest.json", manifest)
    memo_path = output_dir / "f1-transfer-memo.md"
    memo_path.write_text(
        _memo(run_id, calibration, confirmation, terminal_outcome, provenance, records),
        encoding="utf-8",
    )
    _write_json(
        output_dir / "run_state.json",
        {"run_id": run_id, "state": "complete", "terminal_outcome": terminal_outcome},
    )
    return memo_path


def _validate_f1_records(records: pd.DataFrame, output_dir: Path, run_id: str) -> None:
    missing = _REQUIRED_COLUMNS.difference(records.columns)
    if missing:
        raise ValueError(f"F1 report requires record columns: {sorted(missing)}")
    if records.empty or records["run_id"].isna().any() or not records["run_id"].eq(run_id).all():
        raise ValueError("F1 record run ID does not match report run_id")
    if not records["fixture_id"].eq(_FIXTURE).all() or not records["left"].eq(_PAIR[0]).all() or not records[
        "right"
    ].eq(_PAIR[1]).all():
        raise ValueError("F1 report requires only fixture F1 and pair X1/X2")
    if not records["seed_namespace"].eq(_NAMESPACE).all():
        raise ValueError("F1 report requires the frozen seed namespace")
    if not records["phase"].eq(_PHASE).all():
        raise ValueError("F1 report requires only F1 residual-null transfer records")
    for relative_path in records["residual_samples_path"]:
        if not isinstance(relative_path, str) or not relative_path:
            raise ValueError("F1 report requires every residual sample path")
        path = output_dir / relative_path
        if not path.is_file():
            raise ValueError(f"F1 report requires retained residual sample: {relative_path}")


def _batch_policy(config: _TransferConfig) -> BatchNullConfig:
    """Reuse the frozen rule; transfer configuration cannot override its thresholds."""

    return BatchNullConfig(
        batches=config.batches,
        replications_per_batch=config.replications_per_batch,
        evaluation_rows=config.rows,
        permutations=config.permutations,
    )


def _runner_provenance(
    output_dir: Path, records: pd.DataFrame, config: _TransferConfig
) -> dict[str, object]:
    records_path = output_dir / "records.csv"
    input_path = output_dir / "manifest-input.json"
    if not records_path.is_file() or not input_path.is_file():
        raise ValueError("F1 report requires retained records.csv and manifest-input.json")
    try:
        runner_input = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError("F1 report requires valid manifest-input.json") from error
    if not isinstance(runner_input, dict):
        raise TypeError("F1 report requires object manifest-input.json")
    if runner_input.get("fixture_id") not in (None, _FIXTURE):
        raise ValueError("F1 runner provenance has the wrong fixture")
    if runner_input.get("pair") not in (None, list(_PAIR)):
        raise ValueError("F1 runner provenance has the wrong pair")
    if runner_input.get("run_id") not in (None, records["run_id"].iloc[0]):
        raise ValueError("F1 runner provenance has the wrong run ID")
    if runner_input.get("seed_namespace") != _NAMESPACE:
        raise ValueError("F1 runner provenance has the wrong seed namespace")
    return {
        "configuration": runner_input.get("config", asdict(config)),
        "source_revision": runner_input.get("source_revision", _source_revision()),
        "records_sha256": _sha256(records_path),
        "manifest_input_sha256": _sha256(input_path),
    }


def _batch_summary(records: pd.DataFrame, batches: list[object], boundary: float) -> pd.DataFrame:
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
    counts = summary["null_like"].map({True: "null-like", False: "not null-like"}).value_counts()
    figure, axis = plt.subplots(figsize=(6, 4.5))
    axis.bar(counts.index, counts.values, color="#b279a2")
    axis.set_ylabel("batches")
    axis.set_title("F1 independence batch classifications")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def _memo(
    run_id: str,
    calibration: dict[str, object],
    confirmation: object,
    terminal_outcome: str,
    provenance: dict[str, object],
    records: pd.DataFrame,
) -> str:
    selection = calibration["selection"]
    return "\n".join(
        [
            "# F1 independence null-transfer memo",
            "",
            f"Run ID: `{run_id}`",
            f"Terminal outcome: **{terminal_outcome}**",
            "",
            "## Copied reference calibration",
            "",
            f"- Calibration directory: `{calibration['directory']}`",
            f"- Calibration manifest SHA-256: `{calibration['manifest_sha256']}`",
            f"- Calibration records SHA-256: `{calibration['records_sha256']}`",
            f"- Copied selected boundary: `{selection['boundary']}`",
            "",
            "## F1 transfer check",
            "",
            "- Fixture and pair: `F1`, `(X1, X2)`",
            "- Adjustment variables: `(X3, X4, X5, X6)` -- signal-free by construction",
            "- Structure: complete mutual independence; no common cause, mediator, collider, or direct edge",
            f"- Complete: `{confirmation.complete}`",
            f"- Null-like batches: {confirmation.null_like_batch_count} of 100 (requires 85)",
            f"- Low p-values: {confirmation.low_p_value_count} of 1,000 (allows at most 67)",
            "",
            "## Provenance and governance",
            "",
            f"- F1 records SHA-256: `{provenance['records_sha256']}`",
            f"- Manifest-input SHA-256: `{provenance['manifest_input_sha256']}`",
            "This result does not authorize recalibration, alternate fixtures, dependent alternatives, or package work.",
            f"Warnings: {_retained_text(records, 'warnings') or 'none'}",
            f"Exceptions: {_retained_text(records, 'exception_text') or 'none'}",
            "",
            OWNER_DECISION_SENTENCE,
            "",
        ]
    )


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
