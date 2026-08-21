import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from research.gate0 import confirmation_runner
from research.gate0.confirmation_policy import ConfirmationPolicy
from research.gate0.confirmation_runner import ConfirmationConfig, run_confirmation


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    """Invoke the reference-confirmation command at its public boundary."""

    return subprocess.run(
        [sys.executable, "scripts/run_reference_confirmation.py", *arguments],
        capture_output=True,
        check=False,
        cwd=Path(__file__).resolve().parents[2],
        text=True,
    )


def _small_config() -> ConfirmationConfig:
    return ConfirmationConfig(
        reference_replications=1,
        fixture_replications=1,
        source_rows=500,
        evaluation_rows=100,
        permutations=19,
    )


def test_confirmation_runs_reference_and_full_fixture_matrix(tmp_path: Path) -> None:
    frame = run_confirmation(tmp_path, "unit", ConfirmationPolicy.frozen(), _small_config())

    assert len(frame.loc[frame.component == "reference"]) == 1
    assert len(frame.loc[frame.component == "fixture"]) == 16
    assert set(frame.loc[frame.component == "fixture", "fixture_id"]) == {
        f"F{index}" for index in range(1, 9)
    }


def test_confirmation_uses_a_new_seed_namespace(tmp_path: Path) -> None:
    frame = run_confirmation(tmp_path, "seeds", ConfirmationPolicy.frozen(), _small_config())

    assert frame["seed_namespace"].eq("reference-confirmation").all()


def test_confirmation_config_defaults_match_production_confirmation_matrix() -> None:
    config = ConfirmationConfig()

    assert config.reference_replications == 30
    assert config.fixture_replications == 10
    assert config.source_rows == 50_000
    assert config.evaluation_rows == 1_000
    assert config.permutations == 199


def test_confirmation_manifest_records_calibration_and_run_provenance(tmp_path: Path) -> None:
    run_id = "manifest-provenance"
    policy = ConfirmationPolicy.frozen()
    config = _small_config()

    run_confirmation(tmp_path, run_id, policy, config)
    manifest = json.loads((tmp_path / "manifest-input.json").read_text(encoding="utf-8"))

    assert manifest["calibration_source"] == confirmation_runner.CALIBRATION_SOURCE
    assert manifest["calibration_sha256"] == policy.calibration_sha256
    assert manifest["matrix_counts"] == {"reference": 1, "fixture": 16}
    assert manifest["seed_namespace"] == "reference-confirmation"
    assert manifest["run_id"] == run_id
    assert manifest["source_revision"] == confirmation_runner._source_revision()


def test_reference_cell_isolated_from_fixture_generation_and_residualization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_fixture(*args: object, **kwargs: object) -> object:
        raise AssertionError("reference execution must not generate fixtures")

    def fail_residuals(*args: object, **kwargs: object) -> object:
        raise AssertionError("reference execution must not residualize fixtures")

    monkeypatch.setattr(confirmation_runner, "generate_fixture", fail_fixture)
    monkeypatch.setattr(confirmation_runner, "cross_fitted_pair_residuals", fail_residuals)

    record = confirmation_runner._run_reference_cell(tmp_path, 0, _small_config())

    assert record.exception_text is None
    assert record.observed_statistic is not None
    assert record.permutation_p_value is not None
    assert record.null_statistics_path == "reference/null_statistics/replication-0.npy"


def test_confirmation_retains_reference_arrays_and_fixture_samples(tmp_path: Path) -> None:
    frame = run_confirmation(tmp_path, "artifacts", ConfirmationPolicy.frozen(), _small_config())

    assert frame.loc[frame.component == "reference", "null_statistics_path"].notna().all()
    assert frame.loc[frame.component == "fixture", "null_statistics_path"].notna().all()
    assert frame.loc[frame.component == "fixture", "residual_sample_path"].notna().all()
    for artifact in frame["null_statistics_path"].dropna():
        assert (tmp_path / artifact).is_file()
    for artifact in frame["residual_sample_path"].dropna():
        assert (tmp_path / artifact).is_file()


def test_confirmation_refuses_nonempty_output(tmp_path: Path) -> None:
    output = tmp_path / "taken"
    output.mkdir()
    (output / "existing.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError, match="initialized"):
        run_confirmation(output, "taken", ConfirmationPolicy.frozen(), _small_config())


def test_confirmation_cli_refuses_completed_run(tmp_path: Path) -> None:
    """A completed immutable run directory cannot be executed a second time."""

    output = tmp_path / "confirmation"
    first = run_cli("--output-dir", str(output), "--run-id", "confirmation-unit")
    second = run_cli("--output-dir", str(output), "--run-id", "confirmation-unit")

    assert first.returncode == 0
    assert second.returncode != 0


def test_confirmation_retains_fixture_cell_exception_and_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = confirmation_runner.cross_fitted_pair_residuals
    calls = 0

    def fail_once(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("retained fixture failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(confirmation_runner, "cross_fitted_pair_residuals", fail_once)

    frame = run_confirmation(tmp_path, "exceptions", ConfirmationPolicy.frozen(), _small_config())

    failed = frame.loc[frame["exception_text"].notna()]
    assert len(failed) == 1
    assert "RuntimeError: retained fixture failure" in failed.iloc[0]["exception_text"]
    assert len(frame.loc[frame.component == "fixture"]) == 16
    assert frame.loc[frame.component == "fixture", "exception_text"].notna().sum() == 1


def test_source_fixture_failure_retains_blocked_pair_seed_identities(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = confirmation_runner.generate_fixture

    def fail_f1(fixture_id: str, rows: int, seed: int) -> pd.DataFrame:
        if fixture_id == "F1":
            raise RuntimeError("retained source failure")
        return original(fixture_id, rows, seed)

    monkeypatch.setattr(confirmation_runner, "generate_fixture", fail_f1)

    frame = run_confirmation(tmp_path, "source-failure", ConfirmationPolicy.frozen(), _small_config())

    failed = frame.loc[frame["exception_text"].notna()]
    assert len(failed) == 2
    assert failed[["fixture_seed", "residual_seed", "evaluation_seed", "permutation_seed"]].notna().all().all()
    assert len(frame.loc[frame.component == "fixture"]) == 16


def test_persisted_csv_round_trips_large_nullable_seeds_exactly(tmp_path: Path) -> None:
    frame = run_confirmation(tmp_path, "large-seeds", ConfirmationPolicy.frozen(), _small_config())
    seed_columns = [
        "fixture_seed",
        "residual_seed",
        "evaluation_seed",
        "left_seed",
        "right_seed",
        "permutation_seed",
    ]
    persisted = pd.read_csv(tmp_path / "records.csv", dtype={column: "UInt64" for column in seed_columns})

    assert any(
        int(seed) > 2**53
        for seed in frame["permutation_seed"].dropna().tolist()
    )
    for column in seed_columns:
        expected = frame[column].astype("UInt64")
        actual = persisted[column].astype("UInt64")
        assert actual.tolist() == expected.tolist()
