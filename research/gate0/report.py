"""Evidence artifacts and owner-facing decisions for a substantive Gate 0 run."""

from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import asdict
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from research.gate0.config import (
    FIXTURE_COEFFICIENT,
    FIXTURE_NOISE_DISTRIBUTION,
    FIXTURE_NOISE_MEAN,
    FIXTURE_NOISE_STANDARD_DEVIATION,
    FULL_PROFILE,
    OWNER_DECISION_SENTENCE,
    REDUCED_PROFILE,
    ComputationalProfile,
    Gate0Config,
)
from research.gate0.fixtures import FIXTURES

_PROFILE_BY_NAME = {profile.name: profile for profile in (FULL_PROFILE, REDUCED_PROFILE)}
_GROUP_COLUMNS = ["fixture_id", "pair_role"]
_FROZEN_FIXTURE_IDS = tuple(f"F{number}" for number in range(1, 9))
_FROZEN_ROLES = ("target", "null_control")
_FIXTURE_EQUATIONS = {
    "F1": "X1=e1; X2=e2; X3=e3; X4=e4; X5=e5; X6=e6",
    "F2": "X1=e1; X2=0.7*X1+e2; X3=e3; X4=e4; X5=e5; X6=e6",
    "F3": "X1=e1; X2=0.7*(X1**2-1)+e2; X3=e3; X4=e4; X5=e5; X6=e6",
    "F4": "X1=e1; X2=0.7*X1+e2; X3=0.7*X2+e3; X4=e4; X5=e5; X6=e6",
    "F5": "X3=e3; X1=0.7*(X3**2-1)+e1; X2=0.7*(X3**2-1)+e2; X4=e4; X5=e5; X6=e6",
    "F6": "X1=e1; X2=0.7*(X1**2-1)+e2; X3=0.7*X2+e3; X4=e4; X5=e5; X6=e6",
    "F7": "X1=e1; X2=e2; X3=0.7*X1+0.7*X2+e3; X4=e4; X5=e5; X6=e6",
    "F8": "X1=e1; X3=0.7*X1+e3; X2=0.7*X1+0.7*X3+e2; X4=e4; X5=e5; X6=e6",
}
_REQUIRED_MATRIX_COLUMNS = {
    "fixture_id",
    "replication",
    "pair_role",
    "expected_class",
    "left",
    "right",
}


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

    if not _has_exact_frozen_matrix(records):
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


def _has_exact_frozen_matrix(records: pd.DataFrame) -> bool:
    """Require every approved fixture-pair-replication record exactly once."""

    if not _REQUIRED_MATRIX_COLUMNS.issubset(records.columns):
        return False
    if tuple(FIXTURES) != _FROZEN_FIXTURE_IDS:
        return False

    expected_pairs = {
        (fixture_id, "target"): (fixture.target_pair, fixture.expected_target_class)
        for fixture_id, fixture in FIXTURES.items()
    }
    expected_pairs.update(
        {
            (fixture_id, "null_control"): (fixture.null_control_pair, "null-like")
            for fixture_id, fixture in FIXTURES.items()
        }
    )
    expected_identities = {
        (fixture_id, pair_role, replication)
        for fixture_id in _FROZEN_FIXTURE_IDS
        for pair_role in _FROZEN_ROLES
        for replication in range(10)
    }
    if len(records) != len(expected_identities):
        return False

    if records["replication"].map(lambda value: isinstance(value, (bool, np.bool_))).any():
        return False
    replications = pd.to_numeric(records["replication"], errors="coerce")
    if replications.isna().any() or (replications % 1 != 0).any():
        return False

    identities = set()
    columns = sorted(_REQUIRED_MATRIX_COLUMNS)
    for record, replication in zip(
        records.loc[:, columns].itertuples(index=False, name=None), replications, strict=True
    ):
        values = dict(zip(columns, record, strict=True))
        fixture_id = values["fixture_id"]
        pair_role = values["pair_role"]
        if not isinstance(fixture_id, str) or not isinstance(pair_role, str):
            return False
        expected = expected_pairs.get((fixture_id, pair_role))
        if expected is None:
            return False
        expected_pair, expected_class = expected
        if (
            values["expected_class"] != expected_class
            or (values["left"], values["right"]) != expected_pair
        ):
            return False
        identities.add((fixture_id, pair_role, int(replication)))
    return identities == expected_identities


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


def _representative_record(records: pd.DataFrame, output_dir: Path) -> pd.Series:
    """Select one retained record whose own artifacts drive both figures."""

    ordered = records.sort_values("replication", kind="stable", na_position="last")
    for _, record in ordered.iterrows():
        null_path = _artifact_path(output_dir, record.get("null_statistics_path"))
        sample_path = _artifact_path(output_dir, record.get("residual_sample_path"))
        if null_path is not None and null_path.exists() and sample_path is not None and sample_path.exists():
            return record
    return ordered.iloc[0]


def _plot_permutation_distribution(record: pd.Series, output_dir: Path, path: Path) -> None:
    null_path = _artifact_path(output_dir, record.get("null_statistics_path"))
    observed = pd.to_numeric(
        pd.Series([record.get(_statistic_column(record.to_frame().T))]), errors="coerce"
    ).iloc[0]
    replication = record.get("replication", "unknown")
    figure, axis = plt.subplots(figsize=(6, 4))
    if null_path is None or not null_path.exists():
        axis.text(0.5, 0.5, "No retained permutation sample", ha="center", va="center")
        axis.set_axis_off()
    else:
        null_statistics = np.load(null_path)
        axis.hist(null_statistics, bins="auto", color="#729ece", edgecolor="white")
        if not pd.isna(observed):
            axis.axvline(float(observed), color="#c44e52", label=f"observed (replication {replication})")
            axis.legend()
        axis.set_xlabel("distance correlation")
        axis.set_ylabel("permutations")
    axis.set_title(f"{record['fixture_id']} permutation distribution (replication {replication})")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def _plot_residual_scatter(record: pd.Series, output_dir: Path, path: Path) -> None:
    sample_path = _artifact_path(output_dir, record.get("residual_sample_path"))
    replication = record.get("replication", "unknown")
    figure, axis = plt.subplots(figsize=(6, 4))
    if sample_path is None or not sample_path.exists():
        axis.text(0.5, 0.5, "No retained residual sample", ha="center", va="center")
        axis.set_axis_off()
    else:
        sample = pd.read_csv(sample_path)
        left = str(record["left"])
        right = str(record["right"])
        axis.scatter(sample[left], sample[right], s=12, alpha=0.55, color="#55a868")
        axis.set_xlabel(f"{left} residual")
        axis.set_ylabel(f"{right} residual")
    axis.set_title(
        f"{record['fixture_id']} illustrative residual pair (replication {replication}; not confirmatory)"
    )
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


def _dependency_versions() -> dict[str, str]:
    dependencies = {"python": platform.python_version()}
    for distribution in ("numpy", "pandas", "scikit-learn", "dcor", "matplotlib"):
        try:
            dependencies[distribution] = version(distribution)
        except PackageNotFoundError:
            dependencies[distribution] = "unavailable"
    return dependencies


def _source_revision() -> str:
    repository = Path(__file__).resolve().parents[2]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return "unavailable"
    revision = result.stdout.strip()
    return revision if result.returncode == 0 and revision else "unavailable"


def _frozen_protocol(profile: ComputationalProfile) -> dict[str, Any]:
    config = Gate0Config(profile)
    return {
        "profile": asdict(profile),
        "procedure": {
            "data_type": "continuous simulated data",
            "observed_variables": 6,
            "fixture_ids": list(_FROZEN_FIXTURE_IDS),
            "adjustment_set": "all observed variables except both pair endpoints",
            "residuals": "pair-specific out-of-sample predictions",
            "dependence_statistic": "distance correlation",
            "permutation_reference": "permute one residual vector",
        },
        "adjustment_model": {
            "cross_fitting": True,
            "n_splits": config.n_splits,
            "spline_knots": config.spline_knots,
            "spline_degree": config.spline_degree,
            "spline_include_bias": False,
            "spline_knot_strategy": "quantile",
            "scaler": "StandardScaler",
            "estimator": "Ridge",
            "ridge_alpha": config.ridge_alpha,
        },
        "fixture_generation": {
            "coefficient": FIXTURE_COEFFICIENT,
            "linear_relationship": "0.7x",
            "quadratic_relationship": "0.7(x^2 - 1)",
            "quadratic_centered": True,
            "noise_distribution": FIXTURE_NOISE_DISTRIBUTION,
            "noise_mean": FIXTURE_NOISE_MEAN,
            "noise_standard_deviation": FIXTURE_NOISE_STANDARD_DEVIATION,
            "equations": _FIXTURE_EQUATIONS,
            "post_generation_standardization": (
                "Each X1-X6 column is centered by its generated sample mean and scaled by its "
                "generated population standard deviation (ddof=0)."
            ),
        },
        "fixture_evaluations": {
            fixture_id: {
                "target_pair": list(definition.target_pair),
                "null_control_pair": list(definition.null_control_pair),
                "expected_target_class": definition.expected_target_class,
                "expected_null_control_class": "null-like",
            }
            for fixture_id, definition in FIXTURES.items()
        },
        "seed_derivation": {
            "algorithm": "SHA-256",
            "identity_rule": (
                "SHA-256 of UTF-8 text formed by joining identity parts with '|'; the first "
                "eight digest bytes are interpreted as an unsigned big-endian integer."
            ),
            "execution_order_independent": True,
            "shared_fixture_dataset": {
                "purpose": "fixture-dataset",
                "identity_parts": ["gate0", "fixture_id", "replication", "fixture", "dataset"],
                "pair_identity_included": False,
                "nested_rehashing": ["fixture", "fixture_id", "seed"],
            },
            "pair_role_residual": {
                "purpose": "pair-role-residual",
                "identity_parts": ["gate0", "fixture_id", "replication", "pair_role", "residual"],
                "scikit_learn_seed": "identity seed modulo 2**32 for KFold random_state",
            },
            "pair_role_evaluation": {
                "purpose": "pair-role-evaluation",
                "identity_parts": ["gate0", "fixture_id", "replication", "pair_role", "evaluation"],
            },
            "pair_role_permutation": {
                "purpose": "pair-role-permutation",
                "identity_parts": ["gate0", "fixture_id", "replication", "pair_role", "permutation"],
                "permutation_child": ["permutation", "permutation_seed", "permutation_index"],
            },
        },
        "permutation_p_value": "(1 + count(null >= observed)) / (B + 1)",
        "classification_thresholds": {
            "null-like": (
                "At most 2 of 10 p-values <= 0.05 and median observed distance correlation < 0.05."
            ),
            "non-null": (
                "At least 8 of 10 p-values <= 0.01 and median observed distance correlation >= 0.10."
            ),
            "ambiguous": "Any other result.",
        },
        "fixture_gate_thresholds": {
            "PASS": (
                "Every target matches its expected class and every null-control pair is null-like."
            ),
            "STOP": (
                "Any expected target-class mismatch (including the F7 collider target), any "
                "non-null control, any exception, or any malformed or incomplete matrix."
            ),
            "NARROW": "Any remaining ambiguity.",
        },
        "dependencies": _dependency_versions(),
        "source_revision": _source_revision(),
    }


def _protocol_memo_lines(protocol: dict[str, Any]) -> list[str]:
    profile = protocol["profile"]
    procedure = protocol["procedure"]
    model = protocol["adjustment_model"]
    fixture = protocol["fixture_generation"]
    evaluations = protocol["fixture_evaluations"]
    seed = protocol["seed_derivation"]
    classifications = protocol["classification_thresholds"]
    gate = protocol["fixture_gate_thresholds"]
    lines = [
        "## Frozen configuration required by the specification",
        "",
        "| Setting | Value |",
        "| --- | --- |",
        f"| Source rows | {profile['source_rows']} |",
        f"| Evaluation rows | {profile['evaluation_rows']} |",
        f"| Replications | {profile['replications']} |",
        f"| Permutations | {profile['permutations']} |",
        f"| Cross-fitting folds | {model['n_splits']} |",
        f"| Adjustment set | {procedure['adjustment_set']} |",
        f"| Residuals | {procedure['residuals']} |",
        f"| Spline knots | {model['spline_knots']} |",
        f"| Spline degree | {model['spline_degree']} |",
        f"| Spline knot strategy | {model['spline_knot_strategy']} |",
        f"| Spline include bias | {model['spline_include_bias']} |",
        f"| Feature scaler | {model['scaler']} |",
        f"| Ridge alpha | {model['ridge_alpha']} |",
        f"| Dependence statistic | {procedure['dependence_statistic']} |",
        f"| Permutation reference | {procedure['permutation_reference']} |",
        f"| Fixture coefficient | {fixture['coefficient']} |",
        f"| Linear relationship | {fixture['linear_relationship']} |",
        f"| Quadratic relationship | {fixture['quadratic_relationship']} |",
        (
            f"| Exogenous noise | {fixture['noise_distribution']}; mean "
            f"{fixture['noise_mean']}; standard deviation "
            f"{fixture['noise_standard_deviation']} |"
        ),
        f"| Source revision | {protocol['source_revision']} |",
        "",
        "Dependency versions:",
        "",
    ]
    lines.extend(
        f"- {name}: {dependency_version}"
        for name, dependency_version in protocol["dependencies"].items()
    )
    lines.extend(
        [
            "",
            "## Exact fixture equations and evaluation pairs",
            "",
            "| Fixture | Generating equation | Target pair | Null-control pair | Expected target | Expected control |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    lines.extend(
        f"| {fixture_id} | {fixture['equations'][fixture_id]} | "
        f"{', '.join(evaluations[fixture_id]['target_pair'])} | "
        f"{', '.join(evaluations[fixture_id]['null_control_pair'])} | "
        f"{evaluations[fixture_id]['expected_target_class']} | "
        f"{evaluations[fixture_id]['expected_null_control_class']} |"
        for fixture_id in _FROZEN_FIXTURE_IDS
    )
    lines.extend(
        [
            "",
            f"Post-generation standardization: {fixture['post_generation_standardization']}",
            "",
            f"Seed derivation: {seed['identity_rule']}",
            "Seed derivation is identity-based and independent of execution order.",
            (
                "Shared fixture dataset (`fixture-dataset`): `gate0 | fixture_id | replication "
                "| fixture | dataset`; pair identity is not included; fixture generation rehashes "
                "`fixture | fixture_id | seed`."
            ),
            (
                "Pair-role residual (`pair-role-residual`): `gate0 | fixture_id | replication | "
                "pair_role | residual`; KFold receives the identity seed modulo `2**32`."
            ),
            (
                "Pair-role evaluation (`pair-role-evaluation`): `gate0 | fixture_id | replication "
                "| pair_role | evaluation`."
            ),
            (
                "Pair-role permutation (`pair-role-permutation`): `gate0 | fixture_id | replication "
                "| pair_role | permutation`; each permutation child rehashes `permutation | "
                "permutation_seed | permutation_index`."
            ),
            "",
            f"Empirical permutation p-value: `{protocol['permutation_p_value']}`",
            "",
            "## Pair and fixture gate thresholds",
            "",
            f"- null-like: {classifications['null-like']}",
            f"- non-null: {classifications['non-null']}",
            f"- ambiguous: {classifications['ambiguous']}",
            f"- PASS: {gate['PASS']}",
            f"- STOP: {gate['STOP']}",
            f"- NARROW: {gate['NARROW']}",
        ]
    )
    return lines


def write_gate_report(records: pd.DataFrame, output_dir: Path, *, run_id: str) -> Path:
    """Write raw records, figures, manifest, and a non-automatic owner memo."""

    record_run_ids = sorted(
        {str(value) for value in records.get("run_id", pd.Series(dtype=str)).dropna()}
    )
    if record_run_ids and record_run_ids != [run_id]:
        raise ValueError("record run_id values do not match the requested run_id")
    profiles = sorted({str(value) for value in records.get("profile", pd.Series(dtype=str)).dropna()})
    if len(profiles) != 1 or profiles[0] not in _PROFILE_BY_NAME:
        raise ValueError("records must contain exactly one approved substantive profile")
    protocol = _frozen_protocol(_PROFILE_BY_NAME[profiles[0]])

    output_dir.mkdir(parents=True, exist_ok=True)
    records.to_csv(output_dir / "records.csv", index=False)
    classifications = _pair_classifications(records)
    status = gate_status(records)
    plots_dir = output_dir / "plots"
    plots_dir.mkdir(exist_ok=True)
    plot_paths: list[str] = []
    representatives: list[dict[str, Any]] = []
    for fixture_id, fixture_records in records.groupby("fixture_id", sort=True, dropna=False):
        target_records = fixture_records.loc[fixture_records["pair_role"] == "target"]
        representative = _representative_record(
            target_records if not target_records.empty else fixture_records, output_dir
        )
        permutation_path = plots_dir / f"{fixture_id}-permutation-distribution.png"
        scatter_path = plots_dir / f"{fixture_id}-residual-scatter.png"
        _plot_permutation_distribution(representative, output_dir, permutation_path)
        _plot_residual_scatter(representative, output_dir, scatter_path)
        observed = pd.to_numeric(
            pd.Series([representative.get(_statistic_column(representative.to_frame().T))]),
            errors="coerce",
        ).iloc[0]
        representatives.append(
            {
                "fixture_id": str(fixture_id),
                "pair_role": str(representative["pair_role"]),
                "replication": int(representative["replication"]),
                "observed_statistic": None if pd.isna(observed) else float(observed),
                "null_statistics_path": representative.get("null_statistics_path"),
                "residual_sample_path": representative.get("residual_sample_path"),
            }
        )
        plot_paths.extend(
            [str(permutation_path.relative_to(output_dir)), str(scatter_path.relative_to(output_dir))]
        )

    manifest = {
        "gate_status": status,
        "run_id": run_id,
        "profiles": profiles,
        "frozen_protocol": protocol,
        "records": "records.csv",
        "plots": plot_paths,
        "representatives": representatives,
        "memo": "gate-memo.md",
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    memo_lines = [
        "# Gate 0 evidence memo",
        "",
        f"Run ID: {run_id}",
        f"Overall status: **{status}**",
        f"Selected profile: {', '.join(profiles) if profiles else 'unknown'}",
        "",
        (
            "Estimand: Residual dependence remaining after adjustment for the other observed "
            "variables under the specified model."
        ),
        "",
        *_protocol_memo_lines(protocol),
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
            "## Illustrative residual scatterplots",
            "",
            (
                "Each residual scatterplot shows one representative replication only and is "
                "illustrative rather than confirmatory evidence."
            ),
        ]
    )
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
            OWNER_DECISION_SENTENCE,
            "",
        ]
    )
    memo_path = output_dir / "gate-memo.md"
    memo_path.write_text("\n".join(memo_lines), encoding="utf-8")
    return memo_path
