"""Evidence artifacts and owner-facing decisions for a substantive Gate 0 run."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

_FINAL_OWNER_DECISION = (
    "Owner decision required; this result does not authorize estimator redesign, a new "
    "simulation family, or package work."
)
_GROUP_COLUMNS = ["fixture_id", "pair_role"]


def _statistic_column(records: pd.DataFrame) -> str:
    if "observed_statistic" in records:
        return "observed_statistic"
    return "observed"


def _p_value_column(records: pd.DataFrame) -> str:
    if "permutation_p_value" in records:
        return "permutation_p_value"
    return "p_value"


def classify_pair(records: pd.DataFrame) -> str:
    """Classify exactly ten replications using the frozen Gate 0 thresholds."""

    statistic_column = _statistic_column(records)
    p_value_column = _p_value_column(records)
    statistics = pd.to_numeric(records[statistic_column], errors="coerce")
    p_values = pd.to_numeric(records[p_value_column], errors="coerce")
    if len(records) != 10 or statistics.isna().any() or p_values.isna().any():
        return "ambiguous"
    median_statistic = float(statistics.median())
    if (p_values <= 0.05).sum() <= 2 and median_statistic < 0.05:
        return "null-like"
    if (p_values <= 0.01).sum() >= 8 and median_statistic >= 0.10:
        return "non-null"
    return "ambiguous"


def gate_status(records: pd.DataFrame) -> str:
    """Apply the frozen STOP, NARROW, PASS ordering to complete pair records."""

    if records.empty:
        return "STOP"
    if "exception_text" in records and records["exception_text"].notna().any():
        return "STOP"

    classifications = _pair_classifications(records)
    for item in classifications:
        if item["observed_class"] in {"non-null", "null-like"} and (
            item["observed_class"] != item["expected_class"]
        ):
            return "STOP"
    if any(item["observed_class"] == "ambiguous" for item in classifications):
        return "NARROW"
    return "PASS"


def _pair_classifications(records: pd.DataFrame) -> list[dict[str, Any]]:
    classifications: list[dict[str, Any]] = []
    for (fixture_id, pair_role), group in records.groupby(_GROUP_COLUMNS, sort=True, dropna=False):
        expected_classes = group["expected_class"].dropna().unique()
        expected_class = str(expected_classes[0]) if len(expected_classes) == 1 else "invalid"
        classifications.append(
            {
                "fixture_id": str(fixture_id),
                "pair_role": str(pair_role),
                "expected_class": expected_class,
                "observed_class": classify_pair(group),
            }
        )
    return classifications


def _artifact_path(output_dir: Path, value: object) -> Path | None:
    if value is None or pd.isna(value):
        return None
    path = Path(str(value))
    return path if path.is_absolute() else output_dir / path


def _first_existing_path(records: pd.DataFrame, column: str, output_dir: Path) -> Path | None:
    if column not in records:
        return None
    for value in records[column]:
        path = _artifact_path(output_dir, value)
        if path is not None and path.exists():
            return path
    return None


def _plot_permutation_distribution(records: pd.DataFrame, output_dir: Path, path: Path) -> None:
    null_path = _first_existing_path(records, "null_statistics_path", output_dir)
    statistic_column = _statistic_column(records)
    observed = pd.to_numeric(records[statistic_column], errors="coerce").dropna()
    figure, axis = plt.subplots(figsize=(6, 4))
    if null_path is None:
        axis.text(0.5, 0.5, "No retained permutation sample", ha="center", va="center")
        axis.set_axis_off()
    else:
        null_statistics = np.load(null_path)
        axis.hist(null_statistics, bins="auto", color="#729ece", edgecolor="white")
        if not observed.empty:
            axis.axvline(float(observed.median()), color="#c44e52", label="median observed")
            axis.legend()
        axis.set_xlabel("distance correlation")
        axis.set_ylabel("permutations")
    axis.set_title(f"{records['fixture_id'].iloc[0]} permutation distribution")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def _plot_residual_scatter(records: pd.DataFrame, output_dir: Path, path: Path) -> None:
    sample_path = _first_existing_path(records, "residual_sample_path", output_dir)
    figure, axis = plt.subplots(figsize=(6, 4))
    if sample_path is None:
        axis.text(0.5, 0.5, "No retained residual sample", ha="center", va="center")
        axis.set_axis_off()
    else:
        sample = pd.read_csv(sample_path)
        left = str(records["left"].iloc[0])
        right = str(records["right"].iloc[0])
        axis.scatter(sample[left], sample[right], s=12, alpha=0.55, color="#55a868")
        axis.set_xlabel(f"{left} residual")
        axis.set_ylabel(f"{right} residual")
    axis.set_title(f"{records['fixture_id'].iloc[0]} representative residual pair")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def _format_raw_summary(records: pd.DataFrame) -> list[str]:
    statistic_column = _statistic_column(records)
    p_value_column = _p_value_column(records)
    lines = ["| Fixture | Pair | Median observed | Median p-value |", "| --- | --- | ---: | ---: |"]
    for (fixture_id, pair_role), group in records.groupby(_GROUP_COLUMNS, sort=True, dropna=False):
        statistic = pd.to_numeric(group[statistic_column], errors="coerce").median()
        p_value = pd.to_numeric(group[p_value_column], errors="coerce").median()
        statistic_text = "NA" if pd.isna(statistic) else f"{statistic:.4f}"
        p_value_text = "NA" if pd.isna(p_value) else f"{p_value:.4f}"
        lines.append(f"| {fixture_id} | {pair_role} | {statistic_text} | {p_value_text} |")
    return lines


def _format_messages(records: pd.DataFrame, column: str) -> list[str]:
    if column not in records:
        return ["- None"]
    values = sorted({str(value) for value in records[column].dropna() if str(value)})
    return [f"- {value}" for value in values] or ["- None"]


def write_gate_report(records: pd.DataFrame, output_dir: Path) -> Path:
    """Write raw records, figures, manifest, and a non-automatic owner memo."""

    output_dir.mkdir(parents=True, exist_ok=True)
    records.to_csv(output_dir / "records.csv", index=False)
    classifications = _pair_classifications(records)
    status = gate_status(records)
    plots_dir = output_dir / "plots"
    plots_dir.mkdir(exist_ok=True)
    plot_paths: list[str] = []
    for fixture_id, fixture_records in records.groupby("fixture_id", sort=True, dropna=False):
        target_records = fixture_records.loc[fixture_records["pair_role"] == "target"]
        representative = target_records if not target_records.empty else fixture_records
        permutation_path = plots_dir / f"{fixture_id}-permutation-distribution.png"
        scatter_path = plots_dir / f"{fixture_id}-residual-scatter.png"
        _plot_permutation_distribution(representative, output_dir, permutation_path)
        _plot_residual_scatter(representative, output_dir, scatter_path)
        plot_paths.extend(
            [str(permutation_path.relative_to(output_dir)), str(scatter_path.relative_to(output_dir))]
        )

    profiles = sorted({str(value) for value in records.get("profile", pd.Series(dtype=str)).dropna()})
    manifest = {
        "gate_status": status,
        "profiles": profiles,
        "records": "records.csv",
        "plots": plot_paths,
        "memo": "gate-memo.md",
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    memo_lines = [
        "# Gate 0 evidence memo",
        "",
        f"Overall status: **{status}**",
        f"Selected profile: {', '.join(profiles) if profiles else 'unknown'}",
        "",
        "## Fixture classifications",
        "",
        "| Fixture | Pair | Expected | Observed |",
        "| --- | --- | --- | --- |",
    ]
    memo_lines.extend(
        f"| {item['fixture_id']} | {item['pair_role']} | {item['expected_class']} | "
        f"{item['observed_class']} |"
        for item in classifications
    )
    memo_lines.extend(["", "## Raw-statistic summary", "", *_format_raw_summary(records)])
    memo_lines.extend(["", "## Exceptions", "", *_format_messages(records, "exception_text")])
    memo_lines.extend(["", "## Warnings", "", *_format_messages(records, "warnings")])
    memo_lines.extend(
        [
            "",
            "## F7 collider interpretation",
            "",
            (
                "For F7, an expected non-null result is induced conditional dependence—not a "
                "direct causal relationship. Conditioning on the collider X3 can make the "
                "otherwise independent X1 and X2 residuals dependent."
            ),
            "",
            _FINAL_OWNER_DECISION,
            "",
        ]
    )
    memo_path = output_dir / "gate-memo.md"
    memo_path.write_text("\n".join(memo_lines), encoding="utf-8")
    return memo_path
