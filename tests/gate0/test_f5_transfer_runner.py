from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from research.gate0 import f5_transfer_runner
from research.gate0.f5_transfer_runner import F5TransferConfig, run_f5_transfer


def _small_config() -> F5TransferConfig:
    return F5TransferConfig(batches=2, replications_per_batch=3, rows=100, permutations=19)


def test_runner_generates_only_f5_and_retains_every_successful_cell(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, int]] = []
    original = f5_transfer_runner.generate_fixture

    def spy(fixture_id: str, rows: int, seed: int) -> pd.DataFrame:
        calls.append((fixture_id, rows))
        return original(fixture_id, rows, seed)

    monkeypatch.setattr(f5_transfer_runner, "generate_fixture", spy)

    frame = run_f5_transfer(tmp_path, "unit", _small_config())

    assert calls == [("F5", 100)] * 6
    assert len(frame) == 6
    assert set(frame[["fixture_id", "left", "right"]].itertuples(index=False, name=None)) == {
        ("F5", "X1", "X2")
    }
    assert set(frame[["batch", "replication"]].itertuples(index=False, name=None)) == {
        (batch, replication) for batch in range(2) for replication in range(3)
    }
    assert frame["seed_namespace"].eq("batch-f5-null-transfer").all()
    assert frame["exception_text"].isna().all()
    for relative_path in frame["residual_samples_path"]:
        assert len(pd.read_csv(tmp_path / relative_path)) == 100
    for relative_path in frame["null_statistics_path"]:
        assert (tmp_path / relative_path).is_file()


def test_runner_retains_one_residualization_failure_and_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = f5_transfer_runner.cross_fitted_pair_residuals
    calls = 0

    def fail_once(*args: object, **kwargs: object) -> pd.DataFrame:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("retained residual failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(f5_transfer_runner, "cross_fitted_pair_residuals", fail_once)

    frame = run_f5_transfer(tmp_path, "failure", _small_config())

    assert len(frame) == 6
    assert frame["exception_text"].notna().sum() == 1
    assert "RuntimeError: retained residual failure" in frame.loc[0, "exception_text"]
    assert pd.isna(frame.loc[0, "residual_samples_path"])
    assert pd.isna(frame.loc[0, "null_statistics_path"])
    assert frame.loc[1:, "exception_text"].isna().all()


def test_runner_refuses_nonempty_output_without_modifying_it(tmp_path: Path) -> None:
    output_dir = tmp_path / "taken"
    output_dir.mkdir()
    sentinel = output_dir / "existing.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError, match="initialized"):
        run_f5_transfer(output_dir, "taken", _small_config())

    assert sentinel.read_text(encoding="utf-8") == "keep"
