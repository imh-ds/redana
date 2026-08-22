from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from research.gate0 import f4_transfer_runner
from research.gate0.f4_transfer_runner import F4TransferConfig, run_f4_transfer


def _small_config() -> F4TransferConfig:
    return F4TransferConfig(batches=2, replications_per_batch=3, rows=100, permutations=19)


def test_runner_generates_only_f4_and_retains_every_successful_cell(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Wrong fixture, pair, namespace, or missing primary artifacts must fail here."""

    calls: list[tuple[str, int]] = []
    original = f4_transfer_runner.generate_fixture

    def spy(fixture_id: str, rows: int, seed: int) -> pd.DataFrame:
        calls.append((fixture_id, rows))
        return original(fixture_id, rows, seed)

    monkeypatch.setattr(f4_transfer_runner, "generate_fixture", spy)

    frame = run_f4_transfer(tmp_path, "unit", _small_config())

    assert calls == [("F4", 100)] * 6
    assert len(frame) == 6
    assert set(frame[["fixture_id", "left", "right"]].itertuples(index=False, name=None)) == {
        ("F4", "X1", "X3")
    }
    assert set(frame[["batch", "replication"]].itertuples(index=False, name=None)) == {
        (batch, replication) for batch in range(2) for replication in range(3)
    }
    assert frame["seed_namespace"].eq("batch-f4-linear-null-transfer").all()
    assert frame["phase"].eq("f4-linear-null-transfer").all()
    assert frame["exception_text"].isna().all()
    for relative_path in frame["residual_samples_path"]:
        residuals = pd.read_csv(tmp_path / relative_path)
        assert list(residuals) == ["X1", "X3"]
        assert len(residuals) == 100
    for relative_path in frame["null_statistics_path"]:
        values = __import__("numpy").load(tmp_path / relative_path)
        assert len(values) == 19


def test_runner_retains_one_residualization_failure_and_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A single failed frozen cell must remain in records while later cells run."""

    original = f4_transfer_runner.cross_fitted_pair_residuals
    calls = 0

    def fail_once(*args: object, **kwargs: object) -> pd.DataFrame:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("retained residual failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(f4_transfer_runner, "cross_fitted_pair_residuals", fail_once)

    frame = run_f4_transfer(tmp_path, "failure", _small_config())

    assert len(frame) == 6
    assert frame["exception_text"].notna().sum() == 1
    assert "RuntimeError: retained residual failure" in frame.loc[0, "exception_text"]
    assert pd.isna(frame.loc[0, "residual_samples_path"])
    assert pd.isna(frame.loc[0, "null_statistics_path"])
    assert frame.loc[1:, "exception_text"].isna().all()


def test_runner_refuses_nonempty_output_without_modifying_it(tmp_path: Path) -> None:
    """Reusing a run directory must preserve its existing contents unchanged."""

    output_dir = tmp_path / "taken"
    output_dir.mkdir()
    sentinel = output_dir / "existing.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError, match="initialized"):
        run_f4_transfer(output_dir, "taken", _small_config())

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_f4_cli_refuses_tampered_calibration_before_creating_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The narrow CLI validates frozen calibration before initializing a run directory."""

    from scripts import run_f4_linear_residual_null_transfer as cli

    output_dir = tmp_path / "official"
    monkeypatch.setattr(
        cli,
        "_verified_calibration",
        lambda _path: (_ for _ in ()).throw(ValueError("SHA-256 mismatch")),
    )

    assert cli.main(["--output-dir", str(output_dir), "--run-id", "unit"]) == 2

    assert not output_dir.exists()
    assert "F4 LINEAR RESIDUAL-NULL TRANSFER REFUSED [unit]: SHA-256 mismatch" in capsys.readouterr().err


def test_f4_cli_uses_only_frozen_defaults_and_refuses_reused_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A successful narrow CLI run cannot be repeated at its output path."""

    from scripts import run_f4_linear_residual_null_transfer as cli

    output_dir = tmp_path / "official"
    captured: dict[str, object] = {}

    def fake_runner(path: Path, run_id: str, config: F4TransferConfig) -> pd.DataFrame:
        if path.exists() and any(path.iterdir()):
            raise FileExistsError("run directory is already initialized")
        path.mkdir(parents=True)
        (path / "records.csv").write_text("record\n", encoding="utf-8")
        captured.update(path=path, run_id=run_id, config=config)
        return pd.DataFrame({"record": [1]})

    def fake_report(
        _records: pd.DataFrame,
        path: Path,
        _run_id: str,
        calibration_dir: Path,
        _config: F4TransferConfig,
    ) -> Path:
        captured["calibration_dir"] = calibration_dir
        (path / "manifest.json").write_text('{"terminal_outcome": "PASS"}', encoding="utf-8")
        memo = path / "f4-transfer-memo.md"
        memo.write_text("memo", encoding="utf-8")
        return memo

    monkeypatch.setattr(cli, "run_f4_transfer", fake_runner)
    monkeypatch.setattr(cli, "write_f4_transfer_report", fake_report)

    args = ["--output-dir", str(output_dir), "--run-id", "unit"]
    assert cli.main(args) == 0
    assert cli.main(args) == 2
    assert captured["path"] == output_dir
    assert captured["run_id"] == "unit"
    assert captured["config"] == F4TransferConfig()
    assert captured["calibration_dir"] == cli._CALIBRATION_DIR


def test_f4_cli_exposes_no_mutable_study_configuration() -> None:
    """The approved CLI accepts only output location and run identity."""

    from scripts import run_f4_linear_residual_null_transfer as cli

    for forbidden in (
        "--batches",
        "--rows",
        "--threshold",
        "--fixture-id",
        "--pair",
        "--calibration-dir",
        "--seed-namespace",
    ):
        with pytest.raises(SystemExit):
            cli._parse_args(["--output-dir", "out", "--run-id", "unit", forbidden, "changed"])
