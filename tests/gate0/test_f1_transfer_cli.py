"""Command-line contracts for the frozen F1 independence null transfer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _approved_calibration(path: Path, boundary: float) -> None:
    path.mkdir(parents=True)
    records = path / "records.csv"
    runner_input = path / "manifest-input.json"
    records.write_text("calibration\n", encoding="utf-8")
    runner_input.write_text("{}\n", encoding="utf-8")
    (path / "manifest.json").write_text(
        json.dumps(
            {
                "records": {"sha256": _sha256(records)},
                "manifest_input": {"sha256": _sha256(runner_input)},
                "selection": {"status": "READY", "boundary": boundary},
            }
        ),
        encoding="utf-8",
    )


def test_f1_cli_refuses_tampered_calibration_before_creating_output(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """The narrow CLI validates its frozen calibration before initializing a run directory."""

    from scripts import run_f1_independence_null_transfer as cli

    output_dir = tmp_path / "official"
    monkeypatch.setattr(
        cli,
        "_verified_calibration",
        lambda _path: (_ for _ in ()).throw(ValueError("SHA-256 mismatch")),
    )

    assert cli.main(["--output-dir", str(output_dir), "--run-id", "unit"]) == 2

    assert not output_dir.exists()
    assert "F1 INDEPENDENCE NULL TRANSFER REFUSED [unit]: SHA-256 mismatch" in capsys.readouterr().err


def test_f1_cli_uses_only_frozen_defaults_and_refuses_reused_output(
    tmp_path: Path, monkeypatch
) -> None:
    """A successful narrow CLI run cannot be repeated at the same output path."""

    from scripts import run_f1_independence_null_transfer as cli
    from research.gate0.f1_transfer_runner import F1TransferConfig

    output_dir = tmp_path / "official"
    captured: dict[str, object] = {}

    def fake_runner(path: Path, run_id: str, config: F1TransferConfig) -> pd.DataFrame:
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
        _config: F1TransferConfig,
    ) -> Path:
        captured["calibration_dir"] = calibration_dir
        (path / "manifest.json").write_text('{"terminal_outcome": "PASS"}', encoding="utf-8")
        memo = path / "f1-transfer-memo.md"
        memo.write_text("memo", encoding="utf-8")
        return memo

    monkeypatch.setattr(cli, "run_f1_transfer", fake_runner)
    monkeypatch.setattr(cli, "write_f1_transfer_report", fake_report)

    args = ["--output-dir", str(output_dir), "--run-id", "unit"]
    assert cli.main(args) == 0
    assert cli.main(args) == 2
    assert captured["path"] == output_dir
    assert captured["run_id"] == "unit"
    assert captured["config"] == F1TransferConfig()
    assert captured["calibration_dir"] == cli._CALIBRATION_DIR


def test_f1_cli_exposes_no_mutable_study_configuration() -> None:
    """The approved CLI accepts only output location and run identity."""

    from scripts import run_f1_independence_null_transfer as cli

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
