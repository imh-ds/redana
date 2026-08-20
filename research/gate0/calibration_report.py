"""Owner-facing summaries for the frozen null-calibration diagnostic."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")

from research.gate0.config import OWNER_DECISION_SENTENCE
from research.gate0.report import classify_pair

_SUMMARY_COLUMNS = [
    "arm",
    "fixture_id",
    "evaluation_rows",
    "count",
    "observed_median",
    "observed_p05",
    "observed_p95",
    "p_value_p05",
    "p_value_median",
    "p_value_p95",
    "gate_batches",
    "null_like_share",
    "non_null_share",
    "ambiguous_share",
]


def _p_value_column(records: pd.DataFrame) -> str:
    if "permutation_p_value" in records:
        return "permutation_p_value"
    return "p_value"


def _numeric_column(records: pd.DataFrame, column: str) -> pd.Series:
    if column not in records:
        return pd.Series(index=records.index, dtype=float)
    return pd.to_numeric(records[column], errors="coerce")


def _reference_p_values_are_concentrated(records: pd.DataFrame) -> bool:
    reference = records.loc[records["arm"] == "reference"]
    p_values = _numeric_column(reference, _p_value_column(reference)).dropna()
    return len(p_values) >= 5 and float((p_values <= 0.05).mean()) >= 0.20


def _reference_baseline_exceeds_effect_size_clause(records: pd.DataFrame) -> bool:
    reference = records.loc[records["arm"] == "reference"]
    if "evaluation_rows" in reference:
        at_one_thousand = reference.loc[reference["evaluation_rows"] == 1_000]
        if at_one_thousand.empty:
            return False
        reference = at_one_thousand
    statistics = _numeric_column(reference, "observed_statistic").dropna()
    return statistics.notna().any() and float((statistics >= 0.05).mean()) >= 0.50


def _fitted_fixture_departs_from_reference(records: pd.DataFrame) -> bool:
    """Identify fitted arms higher than their same-size reference in multiple sizes."""

    required = {"arm", "fixture_id", "evaluation_rows", "observed_statistic"}
    if not required.issubset(records.columns):
        return False
    reference = records.loc[records["arm"] == "reference"]
    fitted = records.loc[records["arm"] == "fitted"]
    for _, fixture_records in fitted.groupby("fixture_id", sort=True):
        departures = 0
        evaluated_sizes = 0
        for evaluation_rows, fitted_at_size in fixture_records.groupby("evaluation_rows", sort=True):
            reference_at_size = reference.loc[reference["evaluation_rows"] == evaluation_rows]
            reference_statistics = _numeric_column(reference_at_size, "observed_statistic").dropna()
            fitted_statistics = _numeric_column(fitted_at_size, "observed_statistic").dropna()
            if reference_statistics.empty or fitted_statistics.empty:
                continue
            evaluated_sizes += 1
            if fitted_statistics.median() > reference_statistics.quantile(0.95):
                departures += 1
        if evaluated_sizes >= 2 and departures >= max(2, int(np.ceil(evaluated_sizes / 2))):
            return True
    return False


def diagnostic_outcome(records: pd.DataFrame) -> str:
    """Return the precommitted owner-facing diagnostic outcome, not a Gate 0 result."""

    if "exception_text" in records and records["exception_text"].notna().any():
        return "STOP"

    if _reference_p_values_are_concentrated(records):
        return "STOP"

    if _reference_baseline_exceeds_effect_size_clause(records):
        return "CALIBRATION QUESTION"

    if _fitted_fixture_departs_from_reference(records):
        return "RESIDUALIZATION QUESTION"

    return "MIXED / OWNER DECISION"


def _gate_shares(records: pd.DataFrame) -> dict[str, float | int]:
    """Apply the unchanged ten-replication rule to complete sequential batches only."""

    if "replication" not in records:
        return {"gate_batches": 0, "null_like_share": np.nan, "non_null_share": np.nan, "ambiguous_share": np.nan}
    ordered = records.sort_values("replication", kind="stable")
    classifications: list[str] = []
    for start in range(0, len(ordered) - 9, 10):
        batch = ordered.iloc[start : start + 10]
        classifications.append(classify_pair(batch))
    if not classifications:
        return {"gate_batches": 0, "null_like_share": np.nan, "non_null_share": np.nan, "ambiguous_share": np.nan}
    return {
        "gate_batches": len(classifications),
        "null_like_share": classifications.count("null-like") / len(classifications),
        "non_null_share": classifications.count("non-null") / len(classifications),
        "ambiguous_share": classifications.count("ambiguous") / len(classifications),
    }


def _distribution_summary(records: pd.DataFrame) -> pd.DataFrame:
    """Summarize calibration distributions without revising any Gate 0 threshold."""

    required = {"arm", "fixture_id", "evaluation_rows"}
    if not required.issubset(records.columns):
        return pd.DataFrame(columns=_SUMMARY_COLUMNS)
    rows: list[dict[str, float | int | str]] = []
    p_value_column = _p_value_column(records)
    for (arm, fixture_id, evaluation_rows), group in records.groupby(
        ["arm", "fixture_id", "evaluation_rows"], sort=True, dropna=False
    ):
        statistics = _numeric_column(group, "observed_statistic").dropna()
        p_values = _numeric_column(group, p_value_column).dropna()
        summary: dict[str, float | int | str] = {
            "arm": str(arm),
            "fixture_id": str(fixture_id),
            "evaluation_rows": int(evaluation_rows),
            "count": len(group),
            "observed_median": statistics.median(),
            "observed_p05": statistics.quantile(0.05),
            "observed_p95": statistics.quantile(0.95),
            "p_value_p05": p_values.quantile(0.05),
            "p_value_median": p_values.median(),
            "p_value_p95": p_values.quantile(0.95),
        }
        summary.update(_gate_shares(group))
        rows.append(summary)
    return pd.DataFrame(rows, columns=_SUMMARY_COLUMNS)


def _plot_reference_vs_fitted(records: pd.DataFrame, output_dir: Path) -> list[Path]:
    """Plot observed-statistic distributions paired by evaluation size."""

    plots_dir = output_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    if "evaluation_rows" not in records:
        return []
    paths: list[Path] = []
    for evaluation_rows, group in records.groupby("evaluation_rows", sort=True):
        figure, axis = plt.subplots(figsize=(8, 4.5))
        labels: list[str] = []
        values: list[np.ndarray] = []
        reference = _numeric_column(
            group.loc[group["arm"] == "reference"], "observed_statistic"
        ).dropna()
        if not reference.empty:
            labels.append("reference")
            values.append(reference.to_numpy())
        fitted = group.loc[group["arm"] == "fitted"]
        for fixture_id, fixture_records in fitted.groupby("fixture_id", sort=True):
            statistics = _numeric_column(fixture_records, "observed_statistic").dropna()
            if not statistics.empty:
                labels.append(str(fixture_id))
                values.append(statistics.to_numpy())
        if values:
            axis.boxplot(values, tick_labels=labels, showmeans=True)
            axis.set_ylabel("observed distance correlation")
        else:
            axis.text(0.5, 0.5, "No observed statistics", ha="center", va="center")
            axis.set_axis_off()
        axis.set_title(f"Reference versus fitted distributions at {int(evaluation_rows):,} rows")
        figure.tight_layout()
        path = plots_dir / f"evaluation-{int(evaluation_rows)}-reference-vs-fitted.png"
        figure.savefig(path, dpi=150)
        plt.close(figure)
        paths.append(path)
    return paths


def _summary_markdown(summary: pd.DataFrame) -> list[str]:
    lines = [
        "| Arm | Fixture | Evaluation rows | Count | Median observed | Observed 5th/95th | P-value 5th/50th/95th | Null-like / non-null / ambiguous shares |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary.itertuples(index=False):
        observed_interval = f"{row.observed_p05:.4f} / {row.observed_p95:.4f}"
        p_value_quantiles = f"{row.p_value_p05:.4f} / {row.p_value_median:.4f} / {row.p_value_p95:.4f}"
        shares = f"{row.null_like_share:.2f} / {row.non_null_share:.2f} / {row.ambiguous_share:.2f}"
        lines.append(
            f"| {row.arm} | {row.fixture_id} | {row.evaluation_rows} | {row.count} | "
            f"{row.observed_median:.4f} | {observed_interval} | {p_value_quantiles} | {shares} |"
        )
    return lines


def write_calibration_report(records: pd.DataFrame, output_dir: Path) -> Path:
    """Write calibration summaries, paired comparisons, and an owner-facing memo."""

    output_dir.mkdir(parents=True, exist_ok=True)
    summary = _distribution_summary(records)
    summary_path = output_dir / "calibration-summary.csv"
    summary.to_csv(summary_path, index=False)
    plot_paths = _plot_reference_vs_fitted(records, output_dir)
    outcome = diagnostic_outcome(records)
    memo_lines = [
        "# Null-calibration diagnostic memo",
        "",
        f"Diagnostic outcome: **{outcome}**",
        "",
        "This is calibration evidence, not a revised Gate 0 conclusion.",
        "No threshold, estimator, or fixture has changed.",
        "",
        "## Distribution summaries",
        "",
        (
            "Shares apply the unchanged Gate 0 ten-replication classification rule to complete "
            "sequential batches; incomplete batches are not classified."
        ),
        "",
        *_summary_markdown(summary),
        "",
        "## Paired reference-versus-fitted comparisons",
        "",
        (
            "Each plot compares the independent standard-normal reference arm with every fitted "
            "fixture at the same evaluation size. Retained paths in the input records remain the "
            "underlying permutation and residual-sample evidence."
        ),
    ]
    memo_lines.extend(f"- {path.relative_to(output_dir).as_posix()}" for path in plot_paths)
    memo_lines.extend(["", OWNER_DECISION_SENTENCE, ""])
    memo_path = output_dir / "calibration-memo.md"
    memo_path.write_text("\n".join(memo_lines), encoding="utf-8")
    return memo_path
