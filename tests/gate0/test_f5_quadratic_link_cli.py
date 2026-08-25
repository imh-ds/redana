"""Command-line contracts for the frozen F5 quadratic-residual-link alternative."""

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


def _approved_f5_quadratic_repair(path: Path) -> None:
    path.mkdir(parents=True)
    records = path / "records.csv"
    runner_input = path / "manifest-input.json"
    records.write_text("f5 quadratic repair\n", encoding="utf-8")
    runner_input.write_text("{}\n", encoding="utf-8")
    (path / "manifest.json").write_text(
        json.dumps(
            {
                "terminal_outcome": "PASS",
                "fixture_id": "F5",
                "pair": ["X1", "X2"],
                "phase": "f5-quadratic-repair",
                "records": {"sha256": _sha256(records)},
                "manifest_input": {"sha256": _sha256(runner_input)},
                "confirmation_check": {
                    "null_like_batch_count": 90,
                    "low_p_value_count": 44,
                },
            }
        ),
        encoding="utf-8",
    )


@pytest.mark.parametrize("parent", ["calibration", "f5_quadratic_repair"])
def test_cli_refuses_altered_parent_provenance_before_creating_output(
    tmp_path: Path, monkeypatch, capsys, parent: str
) -> None:
    from scripts import run_f5_quadratic_residual_link_alternative as cli

    calibration = tmp_path / "calibration"
    f5_quadratic_repair = tmp_path / "f5-quadratic-repair"
    _approved_calibration(calibration, cli._FROZEN_BOUNDARY)
    _approved_f5_quadratic_repair(f5_quadratic_repair)
    monkeypatch.setattr(cli, "_CALIBRATION_DIR", calibration)
    monkeypatch.setattr(cli, "_F5_QUADRATIC_REPAIR_DIR", f5_quadratic_repair)
    (calibration if parent == "calibration" else f5_quadratic_repair).joinpath(
        "records.csv"
    ).write_text("altered\n", encoding="utf-8")
    output = tmp_path / "output"

    assert cli.main(["--output-dir", str(output), "--run-id", "unit"]) == 2
    assert not output.exists()
    assert "REFUSED [unit]" in capsys.readouterr().err


def test_cli_uses_only_output_and_run_id_and_refuses_reuse(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from scripts import run_f5_quadratic_residual_link_alternative as cli

    calibration = tmp_path / "calibration"
    f5_quadratic_repair = tmp_path / "f5-quadratic-repair"
    _approved_calibration(calibration, cli._FROZEN_BOUNDARY)
    _approved_f5_quadratic_repair(f5_quadratic_repair)
    monkeypatch.setattr(cli, "_CALIBRATION_DIR", calibration)
    monkeypatch.setattr(cli, "_F5_QUADRATIC_REPAIR_DIR", f5_quadratic_repair)
    monkeypatch.setattr(cli, "_verify_frozen_parents", lambda: None)
    calls: dict[str, object] = {}

    def fake_run(output_dir: Path, run_id: str, config: object) -> pd.DataFrame:
        if output_dir.exists() and any(output_dir.iterdir()):
            raise FileExistsError("run directory is already initialized")
        calls.update(output_dir=output_dir, run_id=run_id, config=config)
        output_dir.mkdir(parents=True)
        (output_dir / "records.csv").write_text("records\n", encoding="utf-8")
        return pd.DataFrame({"value": [1]})

    def fake_report(
        records: pd.DataFrame,
        output_dir: Path,
        run_id: str,
        parent: Path,
        calibration_dir: Path,
        config: object,
    ) -> Path:
        assert len(records) == 1
        assert parent == f5_quadratic_repair
        assert calibration_dir == calibration
        (output_dir / "manifest.json").write_text('{"terminal_outcome": "PASS"}', encoding="utf-8")
        memo = output_dir / "memo.md"
        memo.write_text("memo\n", encoding="utf-8")
        return memo

    monkeypatch.setattr(cli, "run_f5_quadratic_link", fake_run)
    monkeypatch.setattr(cli, "write_f5_quadratic_link_report", fake_report)
    output = tmp_path / "output"

    assert cli.main(["--output-dir", str(output), "--run-id", "unit"]) == 0
    assert calls["output_dir"] == output
    assert calls["run_id"] == "unit"
    assert type(calls["config"]).__name__ == "F4LinkConfig"
    assert set(vars(cli._parse_args(["--output-dir", str(output), "--run-id", "unit"]))) == {
        "output_dir", "run_id"
    }
    assert cli.main(["--output-dir", str(output), "--run-id", "unit"]) == 2
    assert "REFUSED [unit]" in capsys.readouterr().err


def test_cli_rejects_unknown_flags(tmp_path: Path) -> None:
    from scripts import run_f5_quadratic_residual_link_alternative as cli

    with pytest.raises(SystemExit):
        cli._parse_args(
            [
                "--output-dir", str(tmp_path / "out"),
                "--run-id", "unit",
                "--rows", "10",
            ]
        )
