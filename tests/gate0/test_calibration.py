from pathlib import Path

import pytest

from research.gate0.calibration import (
    CALIBRATION_FIXTURES,
    EVALUATION_SIZES,
    CalibrationConfig,
    run_calibration,
    run_reference_cell,
)


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
