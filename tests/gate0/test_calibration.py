import hashlib
import json
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from research.gate0.calibration import (
    CALIBRATION_FIXTURES,
    EVALUATION_SIZES,
    CalibrationConfig,
    run_calibration,
    run_reference_cell,
)
from research.gate0.calibration import permutation_distance_correlation as real_metric
from scripts import run_null_calibration as calibration_cli


def test_calibration_cli_refuses_to_overwrite_completed_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "run"

    def fake_run_calibration(output_dir: Path, run_id: str, _config: object) -> pd.DataFrame:
        output_dir.mkdir(parents=True)
        (output_dir / "records.csv").write_text(f"run_id\n{run_id}\n", encoding="utf-8")
        return pd.DataFrame(
            {
                "run_id": [run_id],
                "arm": ["reference"],
                "exception_text": [None],
                "permutation_p_value": [0.5],
                "evaluation_rows": [250],
                "observed_statistic": [0.01],
            }
        )

    def fake_write_report(_records: pd.DataFrame, output_dir: Path) -> Path:
        memo = output_dir / "calibration-memo.md"
        memo.write_text("diagnostic evidence\n", encoding="utf-8")
        return memo

    monkeypatch.setattr(calibration_cli, "run_calibration", fake_run_calibration)
    monkeypatch.setattr(calibration_cli, "write_calibration_report", fake_write_report)

    first = calibration_cli.main(["--output-dir", str(output), "--run-id", "calibration-unit"])
    second = calibration_cli.main(["--output-dir", str(output), "--run-id", "calibration-unit"])

    assert first == 0
    assert second != 0


def test_calibration_matrix_is_frozen() -> None:
    assert CALIBRATION_FIXTURES == ("F1", "F4", "F5", "F6")
    assert EVALUATION_SIZES == (250, 500, 1_000, 2_000)


def test_reference_cell_is_identity_seeded_and_uses_independent_normals() -> None:
    first = run_reference_cell(evaluation_rows=250, replication=3, permutations=19)
    second = run_reference_cell(evaluation_rows=250, replication=3, permutations=19)
    assert first.observed_statistic == second.observed_statistic
    assert first.arm == "reference"
    assert first.fixture_id == "reference"
    assert first.exception_text is None


def test_fitted_arm_records_only_the_four_approved_null_fixtures(tmp_path: Path) -> None:
    frame = run_calibration(
        tmp_path, "unit", CalibrationConfig(replications=1, evaluation_sizes=(250,), permutations=19)
    )
    assert set(frame.loc[frame.arm == "fitted", "fixture_id"]) == {"F1", "F4", "F5", "F6"}
    assert set(frame.loc[frame.arm == "reference", "fixture_id"]) == {"reference"}


def test_calibration_records_name_the_empirical_permutation_p_value(tmp_path: Path) -> None:
    """The report consumes the explicit permutation p-value record field."""

    frame = run_calibration(
        tmp_path,
        "p-value-field",
        CalibrationConfig(replications=1, source_rows=300, evaluation_sizes=(250,), permutations=19),
    )

    assert "permutation_p_value" in frame


def test_calibration_csv_round_trip_preserves_exact_nullable_seed_values(tmp_path: Path) -> None:
    """A CSV reader using strings sees every nullable seed without float coercion."""

    frame = run_calibration(
        tmp_path,
        "exact-seeds",
        CalibrationConfig(replications=1, source_rows=300, evaluation_sizes=(250,), permutations=19),
    )

    persisted = pd.read_csv(tmp_path / "records.csv", dtype="string")
    fitted = persisted.loc[(persisted.arm == "fitted") & (persisted.fixture_id == "F1")].iloc[0]
    reference = persisted.loc[persisted.arm == "reference"].iloc[0]

    assert int(frame.loc[(frame.arm == "fitted") & (frame.fixture_id == "F1"), "fixture_seed"].item()) > 2**53
    assert fitted.fixture_seed == "6433342065636847493"
    assert fitted.residual_seed == "17936904942616992301"
    assert fitted.evaluation_seed == "14107422319196904710"
    assert fitted.permutation_seed == "3384096685922538534"
    assert pd.isna(reference.fixture_seed)
    assert pd.isna(reference.residual_seed)
    assert pd.isna(reference.evaluation_seed)
    assert pd.isna(fitted.left_seed)
    assert pd.isna(fitted.right_seed)


def test_seed_correction_sidecar_derives_exact_values_from_record_identities(tmp_path: Path) -> None:
    """Corrupted source seed text cannot affect the exact correction sidecar."""

    records = tmp_path / "records.csv"
    records.write_text(
        "run_id,arm,fixture_id,replication,evaluation_rows,fixture_seed\n"
        "unit,fitted,F1,0,250,6.433342065636848e+18\n"
        "unit,reference,reference,0,250,\n",
        encoding="utf-8",
    )
    output_dir = tmp_path.parent / "seed-correction-v1"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/write_null_calibration_seed_correction.py",
            "--records",
            str(records),
            "--output-dir",
            str(output_dir),
            "--version",
            "v1",
        ],
        capture_output=True,
        check=False,
        cwd=Path(__file__).resolve().parents[2],
        text=True,
    )

    assert result.returncode == 0, result.stderr
    sidecar = pd.read_csv(output_dir / "exact-seeds.csv", dtype="string")
    fitted = sidecar.loc[sidecar.arm == "fitted"].iloc[0]
    reference = sidecar.loc[sidecar.arm == "reference"].iloc[0]
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))

    assert fitted.fixture_seed == "6433342065636847493"
    assert fitted.residual_seed == "17936904942616992301"
    assert fitted.evaluation_seed == "14107422319196904710"
    assert fitted.permutation_seed == "3384096685922538534"
    assert pd.isna(fitted.left_seed)
    assert pd.isna(fitted.right_seed)
    assert pd.isna(reference.fixture_seed)
    assert pd.isna(reference.residual_seed)
    assert pd.isna(reference.evaluation_seed)
    assert reference.left_seed == "17926931931858939750"
    assert reference.right_seed == "9070928938777396677"
    assert reference.permutation_seed == "1079019629264358956"
    assert manifest["original_records_sha256"] == hashlib.sha256(records.read_bytes()).hexdigest()
    assert manifest["schedule"] == "calibration-v1"
    assert manifest["version"] == "v1"


def test_calibration_retains_a_fitted_arm_exception(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "research.gate0.calibration.generate_fixture",
        lambda *args: (_ for _ in ()).throw(RuntimeError("fixture failed")),
    )
    frame = run_calibration(
        tmp_path, "failure", CalibrationConfig(replications=1, evaluation_sizes=(250,), permutations=19)
    )
    assert frame.loc[frame.arm == "fitted", "exception_text"].notna().all()


def test_calibration_rejects_an_initialized_run_directory(tmp_path: Path) -> None:
    (tmp_path / "prior-artifact.txt").write_text("immutable", encoding="utf-8")
    with pytest.raises(FileExistsError, match="already initialized"):
        run_calibration(tmp_path, "unit", CalibrationConfig(replications=1, evaluation_sizes=(250,)))


def test_reference_arm_retains_each_successful_null_array(tmp_path: Path) -> None:
    frame = run_calibration(
        tmp_path,
        "reference-arrays",
        CalibrationConfig(
            replications=1, source_rows=300, evaluation_sizes=(250,), permutations=19
        ),
    )
    reference = frame.loc[frame.arm == "reference"].iloc[0]
    assert reference.null_statistics_path == "reference/null_statistics/replication-0-evaluation-250.npy"
    assert np.load(tmp_path / reference.null_statistics_path).shape == (19,)


def test_evaluation_warnings_do_not_leak_to_later_fitted_cells(monkeypatch, tmp_path: Path) -> None:
    def warn_for_first_size(left, right, permutations, seed):
        if len(left) == 250:
            warnings.warn("first evaluation warning", UserWarning)
        return real_metric(left, right, permutations, seed)

    monkeypatch.setattr("research.gate0.calibration.permutation_distance_correlation", warn_for_first_size)
    frame = run_calibration(
        tmp_path,
        "warning-isolation",
        CalibrationConfig(
            replications=1, source_rows=300, evaluation_sizes=(250, 300), permutations=19
        ),
    )
    fitted = frame.loc[(frame.arm == "fitted") & (frame.fixture_id == "F1")]
    assert fitted.loc[fitted.evaluation_rows == 250, "warnings"].item() == "first evaluation warning"
    assert fitted.loc[fitted.evaluation_rows == 300, "warnings"].item() == ""


def test_fitted_record_retains_the_null_path_when_residual_sample_write_fails(
    monkeypatch, tmp_path: Path
) -> None:
    original_to_csv = pd.DataFrame.to_csv

    def fail_residual_sample(self, path_or_buf=None, *args, **kwargs):
        if "residual_samples" in str(path_or_buf):
            raise OSError("residual sample write failed")
        return original_to_csv(self, path_or_buf, *args, **kwargs)

    monkeypatch.setattr("pandas.DataFrame.to_csv", fail_residual_sample)
    frame = run_calibration(
        tmp_path,
        "partial-artifact",
        CalibrationConfig(
            replications=1, source_rows=300, evaluation_sizes=(250,), permutations=19
        ),
    )
    fitted = frame.loc[frame.arm == "fitted"]
    assert fitted.exception_text.str.contains("residual sample write failed").all()
    assert fitted.null_statistics_path.notna().all()
    assert fitted.residual_sample_path.isna().all()
    assert all((tmp_path / path).exists() for path in fitted.null_statistics_path)
