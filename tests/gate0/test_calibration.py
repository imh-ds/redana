from research.gate0.calibration import CALIBRATION_FIXTURES, EVALUATION_SIZES, run_reference_cell


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
