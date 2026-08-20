import json

import numpy as np
import pandas as pd
import pytest

from research.gate0.report import classify_pair, gate_status, write_gate_report


def _complete_frozen_records() -> pd.DataFrame:
    expected_targets = {
        "F1": "null-like",
        "F2": "non-null",
        "F3": "non-null",
        "F4": "null-like",
        "F5": "null-like",
        "F6": "null-like",
        "F7": "non-null",
        "F8": "non-null",
    }
    rows = []
    for fixture_id, target_class in expected_targets.items():
        for replication in range(10):
            for pair_role, expected_class in (
                ("target", target_class),
                ("null_control", "null-like"),
            ):
                is_non_null = expected_class == "non-null"
                rows.append(
                    {
                        "fixture_id": fixture_id,
                        "replication": replication,
                        "pair_role": pair_role,
                        "expected_class": expected_class,
                        "left": "X1" if pair_role == "target" else "X4",
                        "right": (
                            "X3"
                            if fixture_id in {"F4", "F6"} and pair_role == "target"
                            else ("X2" if pair_role == "target" else "X5")
                        ),
                        "observed_statistic": 0.11 if is_non_null else 0.02,
                        "permutation_p_value": 0.01 if is_non_null else 0.5,
                        "exception_text": None,
                    }
                )
    return pd.DataFrame(rows)


def test_non_null_rule_requires_both_frequency_and_effect_size() -> None:
    records = pd.DataFrame({"p_value": [0.01] * 8 + [0.5, 0.5], "observed": [0.11] * 10})
    assert classify_pair(records) == "non-null"


def test_null_like_rule_rejects_three_small_p_values() -> None:
    records = pd.DataFrame({"p_value": [0.01, 0.02, 0.03] + [0.5] * 7, "observed": [0.02] * 10})
    assert classify_pair(records) == "ambiguous"


def test_gate_status_stops_for_a_missing_frozen_matrix_record() -> None:
    records = _complete_frozen_records().iloc[:-1]

    assert gate_status(records) == "STOP"


def test_gate_status_stops_for_a_duplicate_frozen_matrix_record() -> None:
    records = _complete_frozen_records()
    records.loc[records.index[-1], "replication"] = 0

    assert gate_status(records) == "STOP"


def test_gate_status_stops_for_boolean_replication_value() -> None:
    records = _complete_frozen_records()
    records["replication"] = records["replication"].astype(object)
    records.loc[records.index[0], "replication"] = False

    assert gate_status(records) == "STOP"


def test_gate_status_stops_for_a_record_that_contradicts_the_fixture_registry() -> None:
    records = _complete_frozen_records()
    f1_target = (records["fixture_id"] == "F1") & (records["pair_role"] == "target")
    records.loc[f1_target, "expected_class"] = "non-null"
    records.loc[f1_target, "observed_statistic"] = 0.11
    records.loc[f1_target, "permutation_p_value"] = 0.01

    assert gate_status(records) == "STOP"


def test_report_writes_evidence_and_stops_for_unexpected_null_like(tmp_path) -> None:
    null_path = tmp_path / "null_statistics" / "f7-target.npy"
    null_path.parent.mkdir()
    np.save(null_path, np.array([0.01, 0.02, 0.03]))
    sample_path = tmp_path / "residual_samples" / "f7-target.csv"
    sample_path.parent.mkdir()
    pd.DataFrame({"X1": [0.1, 0.2], "X2": [0.3, 0.4]}).to_csv(sample_path, index=False)
    target_rows = {
        "fixture_id": ["F7"] * 10,
        "replication": list(range(10)),
        "pair_role": ["target"] * 10,
        "expected_class": ["non-null"] * 10,
        "left": ["X1"] * 10,
        "right": ["X2"] * 10,
        "observed_statistic": [0.02] * 10,
        "permutation_p_value": [0.5] * 10,
        "null_statistics_path": [str(null_path.relative_to(tmp_path))] + [None] * 9,
        "residual_sample_path": [str(sample_path.relative_to(tmp_path))] + [None] * 9,
        "profile": ["reduced"] * 10,
        "warnings": [""] * 10,
        "exception_text": [None] * 10,
    }
    records = pd.DataFrame(target_rows)

    memo_path = write_gate_report(records, tmp_path, run_id="run-1")

    assert memo_path == tmp_path / "gate-memo.md"
    assert (tmp_path / "records.csv").exists()
    assert (tmp_path / "plots" / "F7-permutation-distribution.png").exists()
    assert (tmp_path / "plots" / "F7-residual-scatter.png").exists()
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["gate_status"] == "STOP"
    assert manifest["run_id"] == "run-1"
    assert manifest["frozen_protocol"]["profile"] == {
        "evaluation_rows": 750,
        "name": "reduced",
        "permutations": 99,
        "replications": 10,
        "source_rows": 20_000,
    }
    assert manifest["frozen_protocol"]["adjustment_model"] == {
        "cross_fitting": True,
        "estimator": "Ridge",
        "n_splits": 5,
        "ridge_alpha": 1.0,
        "scaler": "StandardScaler",
        "spline_degree": 3,
        "spline_include_bias": False,
        "spline_knot_strategy": "quantile",
        "spline_knots": 5,
    }
    assert manifest["frozen_protocol"]["fixture_generation"].items() >= {
        "coefficient": 0.7,
        "linear_relationship": "0.7x",
        "noise_distribution": "independent standard Gaussian",
        "noise_mean": 0.0,
        "noise_standard_deviation": 1.0,
        "quadratic_centered": True,
        "quadratic_relationship": "0.7(x^2 - 1)",
    }.items()
    assert manifest["frozen_protocol"]["procedure"] == {
        "adjustment_set": "all observed variables except both pair endpoints",
        "data_type": "continuous simulated data",
        "dependence_statistic": "distance correlation",
        "fixture_ids": [f"F{number}" for number in range(1, 9)],
        "observed_variables": 6,
        "permutation_reference": "permute one residual vector",
        "residuals": "pair-specific out-of-sample predictions",
    }
    assert manifest["frozen_protocol"]["source_revision"]
    assert set(manifest["frozen_protocol"]["dependencies"]) == {
        "dcor",
        "matplotlib",
        "numpy",
        "pandas",
        "python",
        "scikit-learn",
    }
    memo = memo_path.read_text(encoding="utf-8")
    assert "Run ID: run-1" in memo
    assert "Frozen configuration required by the specification" in memo
    assert "Source rows | 20000" in memo
    assert "Evaluation rows | 750" in memo
    assert "Replications | 10" in memo
    assert "Permutations | 99" in memo
    assert "Cross-fitting folds | 5" in memo
    assert "Spline knots | 5" in memo
    assert "Spline degree | 3" in memo
    assert "Ridge alpha | 1.0" in memo
    assert "Fixture coefficient | 0.7" in memo
    assert "independent standard Gaussian" in memo
    assert "F7 collider interpretation" in memo
    assert "induced conditional dependence—not a direct causal relationship" in memo
    assert memo.rstrip().endswith(
        "Owner decision required; this result does not authorize estimator redesign, a new simulation family, or package work."
    )


def test_report_manifest_records_the_single_replication_used_for_both_figures(tmp_path) -> None:
    null_path = tmp_path / "null_statistics" / "f7-target.npy"
    null_path.parent.mkdir()
    np.save(null_path, np.array([0.01, 0.02, 0.03]))
    sample_path = tmp_path / "residual_samples" / "f7-target.csv"
    sample_path.parent.mkdir()
    pd.DataFrame({"X1": [0.1, 0.2], "X2": [0.3, 0.4]}).to_csv(sample_path, index=False)
    records = pd.DataFrame(
        {
            "fixture_id": ["F7"] * 10,
            "replication": list(range(10)),
            "pair_role": ["target"] * 10,
            "expected_class": ["non-null"] * 10,
            "left": ["X1"] * 10,
            "right": ["X2"] * 10,
            "observed_statistic": [0.11] + [0.91] * 9,
            "permutation_p_value": [0.01] * 10,
            "null_statistics_path": [str(null_path.relative_to(tmp_path))] + [None] * 9,
            "residual_sample_path": [str(sample_path.relative_to(tmp_path))] + [None] * 9,
            "profile": ["reduced"] * 10,
        }
    )

    write_gate_report(records, tmp_path, run_id="run-1")

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["representatives"] == [
        {
            "fixture_id": "F7",
            "observed_statistic": 0.11,
            "pair_role": "target",
            "replication": 0,
            "residual_sample_path": str(sample_path.relative_to(tmp_path)),
            "null_statistics_path": str(null_path.relative_to(tmp_path)),
        }
    ]


def test_report_rejects_records_from_a_different_run_before_writing(tmp_path) -> None:
    records = pd.DataFrame(
        {
            "fixture_id": ["F1"],
            "replication": [0],
            "pair_role": ["target"],
            "expected_class": ["null-like"],
            "left": ["X1"],
            "right": ["X2"],
            "observed_statistic": [0.02],
            "permutation_p_value": [0.5],
            "profile": ["reduced"],
            "run_id": ["old-run"],
        }
    )

    with pytest.raises(ValueError, match="run_id"):
        write_gate_report(records, tmp_path, run_id="new-run")

    assert not (tmp_path / "records.csv").exists()


def test_manifest_and_memo_preserve_the_complete_frozen_protocol(tmp_path) -> None:
    records = _complete_frozen_records()
    records["profile"] = "reduced"
    records["run_id"] = "protocol-run"

    memo_path = write_gate_report(records, tmp_path, run_id="protocol-run")

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    protocol = manifest["frozen_protocol"]
    assert protocol["fixture_generation"]["equations"] == {
        "F1": "X1=e1; X2=e2; X3=e3; X4=e4; X5=e5; X6=e6",
        "F2": "X1=e1; X2=0.7*X1+e2; X3=e3; X4=e4; X5=e5; X6=e6",
        "F3": "X1=e1; X2=0.7*(X1**2-1)+e2; X3=e3; X4=e4; X5=e5; X6=e6",
        "F4": "X1=e1; X2=0.7*X1+e2; X3=0.7*X2+e3; X4=e4; X5=e5; X6=e6",
        "F5": "X3=e3; X1=0.7*(X3**2-1)+e1; X2=0.7*(X3**2-1)+e2; X4=e4; X5=e5; X6=e6",
        "F6": "X1=e1; X2=0.7*(X1**2-1)+e2; X3=0.7*X2+e3; X4=e4; X5=e5; X6=e6",
        "F7": "X1=e1; X2=e2; X3=0.7*X1+0.7*X2+e3; X4=e4; X5=e5; X6=e6",
        "F8": "X1=e1; X3=0.7*X1+e3; X2=0.7*X1+0.7*X3+e2; X4=e4; X5=e5; X6=e6",
    }
    assert protocol["fixture_evaluations"] == {
        "F1": {
            "target_pair": ["X1", "X2"],
            "null_control_pair": ["X4", "X5"],
            "expected_target_class": "null-like",
            "expected_null_control_class": "null-like",
        },
        "F2": {
            "target_pair": ["X1", "X2"],
            "null_control_pair": ["X4", "X5"],
            "expected_target_class": "non-null",
            "expected_null_control_class": "null-like",
        },
        "F3": {
            "target_pair": ["X1", "X2"],
            "null_control_pair": ["X4", "X5"],
            "expected_target_class": "non-null",
            "expected_null_control_class": "null-like",
        },
        "F4": {
            "target_pair": ["X1", "X3"],
            "null_control_pair": ["X4", "X5"],
            "expected_target_class": "null-like",
            "expected_null_control_class": "null-like",
        },
        "F5": {
            "target_pair": ["X1", "X2"],
            "null_control_pair": ["X4", "X5"],
            "expected_target_class": "null-like",
            "expected_null_control_class": "null-like",
        },
        "F6": {
            "target_pair": ["X1", "X3"],
            "null_control_pair": ["X4", "X5"],
            "expected_target_class": "null-like",
            "expected_null_control_class": "null-like",
        },
        "F7": {
            "target_pair": ["X1", "X2"],
            "null_control_pair": ["X4", "X5"],
            "expected_target_class": "non-null",
            "expected_null_control_class": "null-like",
        },
        "F8": {
            "target_pair": ["X1", "X2"],
            "null_control_pair": ["X4", "X5"],
            "expected_target_class": "non-null",
            "expected_null_control_class": "null-like",
        },
    }
    assert protocol["fixture_generation"]["post_generation_standardization"] == (
        "Each X1-X6 column is centered by its generated sample mean and scaled by its "
        "generated population standard deviation (ddof=0)."
    )
    assert protocol["seed_derivation"] == {
        "algorithm": "SHA-256",
        "identity_rule": "Join fixture, replication, pair, and permutation identities with '|' as UTF-8; use the first eight digest bytes as an unsigned big-endian integer.",
        "execution_order_independent": True,
    }
    assert protocol["permutation_p_value"] == "(1 + count(null >= observed)) / (B + 1)"
    assert protocol["classification_thresholds"] == {
        "null-like": "At most 2 of 10 p-values <= 0.05 and median observed distance correlation < 0.05.",
        "non-null": "At least 8 of 10 p-values <= 0.01 and median observed distance correlation >= 0.10.",
        "ambiguous": "Any other result.",
    }
    assert protocol["fixture_gate_thresholds"] == {
        "PASS": "Every target matches its expected class and every null-control pair is null-like.",
        "STOP": "Any unexpected non-null target/control result or expected direct-dependence target that is null-like.",
        "NARROW": "Any remaining ambiguity.",
    }

    memo = memo_path.read_text(encoding="utf-8")
    assert "## Exact fixture equations and evaluation pairs" in memo
    assert "| F8 | X1=e1; X3=0.7*X1+e3; X2=0.7*X1+0.7*X3+e2; X4=e4; X5=e5; X6=e6 | X1, X2 | X4, X5 | non-null | null-like |" in memo
    assert "Post-generation standardization: Each X1-X6 column is centered" in memo
    assert "Seed derivation: Join fixture, replication, pair, and permutation identities" in memo
    assert "Empirical permutation p-value: `(1 + count(null >= observed)) / (B + 1)`" in memo
    assert "## Pair and fixture gate thresholds" in memo
