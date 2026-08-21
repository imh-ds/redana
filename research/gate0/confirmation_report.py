"""Immutable evidence summaries for reference-calibrated confirmation runs."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from research.gate0.config import OWNER_DECISION_SENTENCE
from research.gate0.confirmation_policy import (
    ConfirmationPolicy,
    ReferenceCheck,
    check_reference,
    classify_confirmation_pair,
    confirmation_status,
)
from research.gate0.confirmation_runner import (
    CALIBRATION_SOURCE,
    SEED_NAMESPACE,
    ConfirmationConfig,
)
from research.gate0.fixtures import FIXTURES

_SUMMARY_COLUMNS = [
    "component",
    "fixture_id",
    "pair_role",
    "expected_class",
    "observed_class",
    "count",
    "reference_count",
    "reference_below_boundary_count",
    "reference_low_p_value_count",
    "observed_p05",
    "observed_median",
    "observed_p95",
    "p_value_p05",
    "p_value_median",
    "p_value_p95",
    "warnings",
    "exceptions",
    "null_statistics_paths",
    "residual_sample_paths",
]


def write_confirmation_report(
    records: pd.DataFrame, output_dir: Path, run_id: str, policy: ConfirmationPolicy
) -> Path:
    """Write final report artifacts using the frozen policy without altering its outcome."""

    _reject_mixed_run_ids(records)
    output_dir.mkdir(parents=True, exist_ok=True)
    reference_records = _component_records(records, "reference")
    fixture_records = _component_records(records, "fixture")
    reference = check_reference(reference_records, policy)
    terminal_outcome = confirmation_status(reference, fixture_records, policy)
    summary = _summary(records, reference_records, fixture_records, reference, policy)
    summary.to_csv(output_dir / "confirmation-summary.csv", index=False)
    _plot_reference(reference_records, output_dir / "plots" / "reference-dcor.png", policy)
    _plot_fixture_classes(summary, output_dir / "plots" / "fixture-classifications.png")
    provenance = _input_provenance(output_dir)
    manifest = _manifest(
        run_id, policy, reference, terminal_outcome, provenance, summary, records
    )
    _write_json(output_dir / "manifest.json", manifest)
    memo = _memo(run_id, policy, reference, terminal_outcome, provenance, summary)
    memo_path = output_dir / "confirmation-memo.md"
    memo_path.write_text(memo, encoding="utf-8")
    _write_json(
        output_dir / "run_state.json",
        {"run_id": run_id, "state": "complete", "terminal_outcome": terminal_outcome},
    )
    return memo_path


def _reject_mixed_run_ids(records: pd.DataFrame) -> None:
    if "run_id" not in records:
        return
    run_ids = {str(value) for value in records["run_id"].dropna().unique()}
    if len(run_ids) > 1:
        raise ValueError("confirmation report rejects mixed run IDs")


def _component_records(records: pd.DataFrame, component: str) -> pd.DataFrame:
    if "component" not in records:
        return pd.DataFrame()
    return records.loc[records["component"] == component].copy()


def _summary(
    records: pd.DataFrame,
    reference_records: pd.DataFrame,
    fixture_records: pd.DataFrame,
    reference: ReferenceCheck,
    policy: ConfirmationPolicy,
) -> pd.DataFrame:
    rows = [_reference_summary(reference_records, reference)]
    for fixture_id, fixture in FIXTURES.items():
        for pair_role, expected_class in (
            ("target", fixture.expected_target_class),
            ("null-control", "null-like"),
        ):
            pair_records = fixture_records.loc[
                (fixture_records.get("fixture_id") == fixture_id)
                & (fixture_records.get("pair_role") == pair_role)
            ] if {"fixture_id", "pair_role"}.issubset(fixture_records.columns) else pd.DataFrame()
            rows.append(_pair_summary(pair_records, fixture_id, pair_role, expected_class, policy))
    if records.empty:
        rows[0]["warnings"] = "no confirmation records supplied"
    return pd.DataFrame(rows, columns=_SUMMARY_COLUMNS)


def _reference_summary(records: pd.DataFrame, reference: ReferenceCheck) -> dict[str, object]:
    row = _base_summary(records, "reference", "reference", "", "")
    row.update(
        {
            "reference_count": len(records),
            "reference_below_boundary_count": reference.below_boundary_count,
            "reference_low_p_value_count": reference.low_p_value_count,
        }
    )
    return row


def _pair_summary(
    records: pd.DataFrame,
    fixture_id: str,
    pair_role: str,
    expected_class: str,
    policy: ConfirmationPolicy,
) -> dict[str, object]:
    observed_class = "incomplete"
    try:
        observed_class = classify_confirmation_pair(records, policy)
    except ValueError:
        pass
    return _base_summary(records, "fixture", fixture_id, pair_role, expected_class) | {
        "observed_class": observed_class
    }


def _base_summary(
    records: pd.DataFrame,
    component: str,
    fixture_id: str,
    pair_role: str,
    expected_class: str,
) -> dict[str, object]:
    statistics = _numeric(records, "observed_statistic")
    p_values = _numeric(records, "permutation_p_value")
    return {
        "component": component,
        "fixture_id": fixture_id,
        "pair_role": pair_role,
        "expected_class": expected_class,
        "observed_class": "",
        "count": len(records),
        "reference_count": None,
        "reference_below_boundary_count": None,
        "reference_low_p_value_count": None,
        "observed_p05": statistics.quantile(0.05),
        "observed_median": statistics.median(),
        "observed_p95": statistics.quantile(0.95),
        "p_value_p05": p_values.quantile(0.05),
        "p_value_median": p_values.median(),
        "p_value_p95": p_values.quantile(0.95),
        "warnings": _retained_text(records, "warnings"),
        "exceptions": _retained_text(records, "exception_text"),
        "null_statistics_paths": _retained_text(records, "null_statistics_path"),
        "residual_sample_paths": _retained_text(records, "residual_sample_path"),
    }


def _numeric(records: pd.DataFrame, column: str) -> pd.Series:
    if column not in records:
        return pd.Series(dtype=float)
    return pd.to_numeric(records[column], errors="coerce").dropna()


def _retained_text(records: pd.DataFrame, column: str) -> str:
    if column not in records:
        return ""
    return "; ".join(sorted({str(value) for value in records[column].dropna() if str(value)}))


def _plot_reference(records: pd.DataFrame, path: Path, policy: ConfirmationPolicy) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(7, 4.5))
    values = _numeric(records, "observed_statistic")
    if values.empty:
        axis.text(0.5, 0.5, "No complete reference statistics", ha="center", va="center")
        axis.set_axis_off()
    else:
        axis.hist(values, bins=min(10, len(values)), color="#4c78a8", edgecolor="white")
        axis.axvline(policy.practical_null_boundary, color="#e45756", linestyle="--", label="boundary")
        axis.legend()
        axis.set_xlabel("observed distance correlation")
        axis.set_ylabel("reference replications")
    axis.set_title("Independent reference distance correlations")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def _plot_fixture_classes(summary: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fixture_summary = summary.loc[summary["component"] == "fixture"]
    counts = fixture_summary["observed_class"].value_counts().reindex(
        ["null-like", "non-null", "ambiguous", "incomplete"], fill_value=0
    )
    figure, axis = plt.subplots(figsize=(7, 4.5))
    axis.bar(counts.index, counts.values, color="#72b7b2")
    axis.set_ylabel("fixture pairs")
    axis.set_title("Observed fixture-pair classifications")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def _input_provenance(output_dir: Path) -> dict[str, object]:
    source = output_dir / "manifest-input.json"
    if source.is_file():
        payload = json.loads(source.read_text(encoding="utf-8"))
        return {
            "configuration": payload.get("config", asdict(ConfirmationConfig())),
            "seed_namespace": payload.get("seed_namespace", SEED_NAMESPACE),
            "source_revision": payload.get("source_revision", _source_revision()),
        }
    return {
        "configuration": asdict(ConfirmationConfig()),
        "seed_namespace": SEED_NAMESPACE,
        "source_revision": _source_revision(),
    }


def _manifest(
    run_id: str,
    policy: ConfirmationPolicy,
    reference: ReferenceCheck,
    terminal_outcome: str,
    provenance: dict[str, object],
    summary: pd.DataFrame,
    records: pd.DataFrame,
) -> dict[str, object]:
    return {
        "run_id": run_id,
        "terminal_outcome": terminal_outcome,
        "calibration": {
            "relative_path": CALIBRATION_SOURCE,
            "sha256": policy.calibration_sha256,
            "quantile": policy.calibration_quantile,
            "quantile_interpolation": policy.quantile_interpolation,
            "practical_null_boundary": policy.practical_null_boundary,
        },
        "reference_check": asdict(reference),
        "fixture_rule": {
            "null_like": "median dCor < boundary and at most 2 p-values <= 0.05",
            "non_null": "median dCor >= 0.10 and at least 8 p-values <= 0.01",
        },
        "configuration": provenance["configuration"],
        "seed_namespace": provenance["seed_namespace"],
        "source_revision": provenance["source_revision"],
        "record_count": len(records),
        "summary_path": "confirmation-summary.csv",
        "plots": ["plots/reference-dcor.png", "plots/fixture-classifications.png"],
        "owner_governance": OWNER_DECISION_SENTENCE,
        "warnings": _retained_text(records, "warnings"),
        "exceptions": _retained_text(records, "exception_text"),
        "retained_artifacts": {
            "null_statistics": _retained_text(records, "null_statistics_path"),
            "residual_samples": _retained_text(records, "residual_sample_path"),
        },
        "fixture_pairs": summary.loc[summary["component"] == "fixture"].to_dict("records"),
    }


def _memo(
    run_id: str,
    policy: ConfirmationPolicy,
    reference: ReferenceCheck,
    terminal_outcome: str,
    provenance: dict[str, object],
    summary: pd.DataFrame,
) -> str:
    lines = [
        "# Reference-calibrated confirmation memo",
        "",
        f"Run ID: `{run_id}`",
        f"Terminal outcome: **{terminal_outcome}**",
        "",
        "## Immutable calibration provenance",
        "",
        f"- Calibration records: `{CALIBRATION_SOURCE}`",
        f"- SHA-256: `{policy.calibration_sha256}`",
        f"- Practical-null boundary: `{policy.practical_null_boundary}`",
        f"- Reference quantile: `{policy.calibration_quantile}` using `{policy.quantile_interpolation}` interpolation",
        "",
        "## Reference acceptance check",
        "",
        f"- Complete: `{reference.complete}`; count: `{reference.below_boundary_count}` below boundary (requires 27 of 30)",
        f"- Low p-values: `{reference.low_p_value_count}` at p <= 0.05 (allows at most 4)",
        "",
        "## Frozen execution identity",
        "",
        f"- Configuration: `{json.dumps(provenance['configuration'], sort_keys=True)}`",
        f"- Seed namespace: `{provenance['seed_namespace']}`",
        f"- Source revision: `{provenance['source_revision']}`",
        "",
        "## Fixture-pair classes",
        "",
        "| Fixture | Pair | Expected | Observed | Count |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for row in summary.loc[summary["component"] == "fixture"].itertuples(index=False):
        lines.append(
            f"| {row.fixture_id} | {row.pair_role} | {row.expected_class} | "
            f"{row.observed_class} | {row.count} |"
        )
    lines.extend(
        [
            "",
            "The unchanged non-null rule is median dCor >= 0.10 with at least eight p-values <= 0.01.",
            "Warnings, retained exceptions, and artifact paths are recorded in `confirmation-summary.csv` and `manifest.json`.",
            "This confirms or fails to confirm behavior of this residual-dependence diagnostic under the specified fixtures and frozen pipeline. It does not establish causal edges, conditional independence in general, or researcher-facing network recovery.",
            "",
            OWNER_DECISION_SENTENCE,
            "",
        ]
    )
    return "\n".join(lines)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(_json_ready(payload), indent=2, sort_keys=True, default=str, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _json_ready(value: object) -> object:
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if pd.api.types.is_scalar(value) and pd.isna(value):
        return None
    return value


def _source_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        check=False,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"
