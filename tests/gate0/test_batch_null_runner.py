from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from research.gate0 import batch_null_runner
from research.gate0.batch_null_policy import BatchNullConfig
from research.gate0.batch_null_runner import run_batch_phase
from scripts import run_batch_null_calibration as calibration_cli


def _small_config() -> BatchNullConfig:
    return BatchNullConfig(
        batches=2,
        replications_per_batch=3,
        evaluation_rows=100,
        permutations=19,
    )


def test_small_phase_contains_each_batch_and_replication_once(tmp_path: Path) -> None:
    frame = run_batch_phase("calibration", tmp_path, "unit", _small_config())

    assert len(frame) == 6
    assert set(frame[["batch", "replication"]].itertuples(index=False, name=None)) == {
        (batch, replication) for batch in range(2) for replication in range(3)
    }
    assert frame["seed_namespace"].eq("batch-null-calibration").all()


def test_reference_runner_has_no_fixture_or_residual_dependencies(tmp_path: Path) -> None:
    frame = run_batch_phase("calibration", tmp_path, "isolated", _small_config())

    assert frame["exception_text"].isna().all()
    assert not hasattr(batch_null_runner, "generate_fixture")
    assert not hasattr(batch_null_runner, "cross_fitted_pair_residuals")


def test_runner_retains_every_successful_permutation_array(tmp_path: Path) -> None:
    frame = run_batch_phase("confirmation", tmp_path, "arrays", _small_config())

    assert frame["null_statistics_path"].notna().all()
    for relative_path in frame["null_statistics_path"]:
        assert (tmp_path / relative_path).is_file()


def test_runner_refuses_nonempty_output(tmp_path: Path) -> None:
    output = tmp_path / "taken"
    output.mkdir()
    (output / "existing.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError, match="initialized"):
        run_batch_phase("calibration", output, "taken", _small_config())


def test_runner_retains_metric_exception_and_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = batch_null_runner.permutation_distance_correlation
    calls = 0

    def fail_once(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("retained metric failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(batch_null_runner, "permutation_distance_correlation", fail_once)

    frame = run_batch_phase("calibration", tmp_path, "failure", _small_config())

    assert len(frame) == 6
    assert frame["exception_text"].notna().sum() == 1
    assert "RuntimeError: retained metric failure" in frame.loc[0, "exception_text"]
    assert pd.isna(frame.loc[0, "null_statistics_path"])


def test_runner_round_trips_large_nullable_seeds_exactly(tmp_path: Path) -> None:
    frame = run_batch_phase("calibration", tmp_path, "large-seeds", _small_config())
    seed_columns = ["left_seed", "right_seed", "permutation_seed"]
    persisted = pd.read_csv(
        tmp_path / "records.csv", dtype={column: "UInt64" for column in seed_columns}
    )

    assert any(int(seed) > 2**53 for seed in frame["permutation_seed"].dropna().tolist())
    for column in seed_columns:
        assert persisted[column].astype("UInt64").tolist() == frame[column].astype("UInt64").tolist()


def test_phases_use_disjoint_seed_namespaces(tmp_path: Path) -> None:
    calibration = run_batch_phase("calibration", tmp_path / "calibration", "cal", _small_config())
    confirmation = run_batch_phase("confirmation", tmp_path / "confirmation", "con", _small_config())

    assert calibration["seed_namespace"].eq("batch-null-calibration").all()
    assert confirmation["seed_namespace"].eq("batch-null-confirmation").all()
    assert set(calibration["left_seed"]).isdisjoint(set(confirmation["left_seed"]))
    assert set(calibration["right_seed"]).isdisjoint(set(confirmation["right_seed"]))
    assert set(calibration["permutation_seed"]).isdisjoint(set(confirmation["permutation_seed"]))


def test_runner_persists_records_and_manifest_after_all_attempts(tmp_path: Path) -> None:
    frame = run_batch_phase("confirmation", tmp_path, "manifest", _small_config())

    persisted = pd.read_csv(tmp_path / "records.csv")
    manifest = json.loads((tmp_path / "manifest-input.json").read_text(encoding="utf-8"))

    assert len(persisted) == len(frame)
    assert manifest["attempted_records"] == 6
    assert manifest["phase"] == "confirmation"
    assert manifest["seed_namespace"] == "batch-null-confirmation"
    assert manifest["run_id"] == "manifest"


def test_calibration_cli_refuses_completed_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "calibration"
    received: list[BatchNullConfig] = []

    def fake_run(
        phase: str, output_dir: Path, run_id: str, config: BatchNullConfig
    ) -> pd.DataFrame:
        assert phase == "calibration"
        output_dir.mkdir(parents=True)
        (output_dir / "records.csv").write_text("run_id\n" + run_id + "\n", encoding="utf-8")
        (output_dir / "manifest-input.json").write_text("{}\n", encoding="utf-8")
        received.append(config)
        return pd.DataFrame({"run_id": [run_id], "phase": [phase]})

    def fake_report(
        _records: pd.DataFrame, output_dir: Path, _run_id: str, _config: BatchNullConfig
    ) -> Path:
        memo = output_dir / "calibration-memo.md"
        memo.write_text("calibration evidence\n", encoding="utf-8")
        (output_dir / "manifest.json").write_text(
            '{"terminal_outcome": "READY"}\n', encoding="utf-8"
        )
        return memo

    monkeypatch.setattr(calibration_cli, "run_batch_phase", fake_run)
    monkeypatch.setattr(calibration_cli, "write_calibration_report", fake_report)

    first = calibration_cli.main(["--output-dir", str(output), "--run-id", "batch-calibration-unit"])
    second = calibration_cli.main(["--output-dir", str(output), "--run-id", "batch-calibration-unit"])

    assert first == 0
    assert second != 0
    assert received == [BatchNullConfig()]
