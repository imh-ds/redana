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
