import json
from pathlib import Path

import pandas as pd
import pytest

from research.gate0.config import OWNER_DECISION_SENTENCE
from research.gate0.confirmation_policy import ConfirmationPolicy
from research.gate0.confirmation_report import write_confirmation_report
from research.gate0.fixtures import FIXTURES


def _passing_records(output_dir: Path, run_id: str = "unit") -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for replication in range(30):
        null_path = f"reference/null_statistics/replication-{replication}.npy"
        _artifact(output_dir / null_path)
        rows.append(
            _record(
                run_id=run_id,
                component="reference",
                fixture_id="reference",
                pair_role=None,
                expected_class=None,
                replication=replication,
                observed_statistic=0.04,
                permutation_p_value=0.50,
                null_statistics_path=null_path,
                residual_sample_path=None,
            )
        )
    for fixture_id, fixture in FIXTURES.items():
        for pair_role, expected_class in (
            ("target", fixture.expected_target_class),
            ("null-control", "null-like"),
        ):
            for replication in range(10):
                null_path = f"fixtures/{fixture_id}/replication-{replication}/{pair_role}-null.npy"
                sample_path = f"fixtures/{fixture_id}/replication-{replication}/{pair_role}-sample.csv"
                _artifact(output_dir / null_path)
                _artifact(output_dir / sample_path)
                is_null_like = expected_class == "null-like"
                rows.append(
                    _record(
                        run_id=run_id,
                        component="fixture",
                        fixture_id=fixture_id,
                        pair_role=pair_role,
                        expected_class=expected_class,
                        replication=replication,
                        observed_statistic=0.04 if is_null_like else 0.12,
                        permutation_p_value=0.50 if is_null_like else 0.01,
                        null_statistics_path=null_path,
                        residual_sample_path=sample_path,
                    )
                )
    return pd.DataFrame(rows)


def _record(**overrides: object) -> dict[str, object]:
    return {
        "run_id": "unit",
        "component": "fixture",
        "fixture_id": "F1",
        "pair_role": "target",
        "expected_class": "null-like",
        "replication": 0,
        "observed_statistic": 0.04,
        "permutation_p_value": 0.50,
        "null_statistics_path": None,
        "residual_sample_path": None,
        "seed_namespace": "reference-confirmation",
        "fixture_seed": 11,
        "residual_seed": 12,
        "evaluation_seed": 13,
        "left_seed": None,
        "right_seed": None,
        "permutation_seed": 14,
        "elapsed_seconds": 0.1,
        "warnings": None,
        "exception_text": None,
    } | overrides


def _artifact(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("retained evidence", encoding="utf-8")


def test_confirmation_memo_records_frozen_boundary_and_governance(tmp_path: Path) -> None:
    memo = write_confirmation_report(
        _passing_records(tmp_path), tmp_path, "unit", ConfirmationPolicy.frozen()
    )

    text = memo.read_text(encoding="utf-8")
    assert "0.07078970914915612" in text
    assert "57160bf69892c4047e8a089487d5b894d09243c1a3bcf60164f4daa881369197" in text
    assert text.rstrip().endswith(OWNER_DECISION_SENTENCE)


def test_reference_p_value_failure_is_stop(tmp_path: Path) -> None:
    records = _passing_records(tmp_path)
    records.loc[records.component == "reference", "permutation_p_value"] = 0.05

    memo = write_confirmation_report(records, tmp_path, "stop", ConfirmationPolicy.frozen())

    assert "Terminal outcome: **STOP**" in memo.read_text(encoding="utf-8")


def test_reference_count_failure_is_narrow(tmp_path: Path) -> None:
    records = _passing_records(tmp_path)
    records.loc[records.component == "reference", "observed_statistic"] = 0.2

    memo = write_confirmation_report(records, tmp_path, "narrow", ConfirmationPolicy.frozen())

    assert "Terminal outcome: **NARROW**" in memo.read_text(encoding="utf-8")


def test_report_writes_summary_manifest_and_reference_plot(tmp_path: Path) -> None:
    write_confirmation_report(_passing_records(tmp_path), tmp_path, "artifacts", ConfirmationPolicy.frozen())

    assert (tmp_path / "confirmation-summary.csv").exists()
    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "plots" / "reference-dcor.png").exists()
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["terminal_outcome"] == "PASS"
    assert manifest["calibration"]["quantile_interpolation"] == "linear"
    assert (tmp_path / "run_state.json").read_text(encoding="utf-8").find("complete") >= 0


def test_definite_fixture_mismatch_requires_owner_decision(tmp_path: Path) -> None:
    records = _passing_records(tmp_path)
    target = (records.fixture_id == "F1") & (records.pair_role == "target")
    records.loc[target, "observed_statistic"] = 0.12
    records.loc[target, "permutation_p_value"] = 0.01

    memo = write_confirmation_report(records, tmp_path, "mixed", ConfirmationPolicy.frozen())

    assert "Terminal outcome: **MIXED / OWNER DECISION**" in memo.read_text(encoding="utf-8")


def test_ambiguous_fixture_is_narrow(tmp_path: Path) -> None:
    records = _passing_records(tmp_path)
    target = (records.fixture_id == "F1") & (records.pair_role == "target")
    records.loc[target, "observed_statistic"] = 0.08
    records.loc[target, "permutation_p_value"] = 0.50

    memo = write_confirmation_report(records, tmp_path, "ambiguous", ConfirmationPolicy.frozen())

    assert "Terminal outcome: **NARROW**" in memo.read_text(encoding="utf-8")


def test_malformed_records_are_stop(tmp_path: Path) -> None:
    records = _passing_records(tmp_path)
    records.loc[records.component == "reference", "observed_statistic"] = None

    memo = write_confirmation_report(records, tmp_path, "malformed", ConfirmationPolicy.frozen())

    assert "Terminal outcome: **STOP**" in memo.read_text(encoding="utf-8")
    assert "NaN" not in (tmp_path / "manifest.json").read_text(encoding="utf-8")


def test_mixed_run_ids_are_rejected(tmp_path: Path) -> None:
    records = _passing_records(tmp_path)
    records.loc[0, "run_id"] = "other"

    with pytest.raises(ValueError, match="mixed run IDs"):
        write_confirmation_report(records, tmp_path, "unit", ConfirmationPolicy.frozen())
