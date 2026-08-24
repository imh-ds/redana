"""Command-line contracts for the frozen F5 quadratic repair."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from research.gate0.f5_quadratic_repair_runner import F5QuadraticRepairConfig


def test_cli_refuses_altered_parent_provenance_before_creating_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Parent refusal must happen before the runner can initialize its directory."""

    from scripts import run_f5_quadratic_repair as cli

    output = tmp_path / "official"
    runner_called = False

    def refuse_parents() -> None:
        raise ValueError("F5 STOP records SHA-256 does not match frozen provenance")

    def forbidden_runner(*args: object, **kwargs: object) -> pd.DataFrame:
        nonlocal runner_called
        runner_called = True
        raise AssertionError("runner must not start")

    monkeypatch.setattr(cli, "_verify_frozen_parents", refuse_parents)
    monkeypatch.setattr(cli, "run_f5_quadratic_repair", forbidden_runner)

    assert cli.main(["--output-dir", str(output), "--run-id", "unit"]) == 2

    captured = capsys.readouterr()
    assert not runner_called
    assert not output.exists()
    assert captured.out == ""
    assert captured.err.count("\n") == 1
    assert (
        "F5 QUADRATIC REPAIR REFUSED [unit]: F5 STOP records SHA-256 does not "
        "match frozen provenance"
        in captured.err
    )


def test_cli_uses_frozen_defaults_and_refuses_reused_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The command must use exactly the frozen config and cannot reuse its output."""

    from scripts import run_f5_quadratic_repair as cli

    output = tmp_path / "official"
    captured: dict[str, object] = {}

    def fake_runner(path: Path, run_id: str, config: F5QuadraticRepairConfig) -> pd.DataFrame:
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
        f5_stop_dir: Path,
        _config: F5QuadraticRepairConfig,
    ) -> Path:
        captured.update(calibration_dir=calibration_dir, f5_stop_dir=f5_stop_dir)
        (path / "manifest.json").write_text(
            json.dumps({"terminal_outcome": "PASS"}), encoding="utf-8"
        )
        memo = path / "f5-quadratic-repair-memo.md"
        memo.write_text("memo", encoding="utf-8")
        return memo

    monkeypatch.setattr(cli, "_verify_frozen_parents", lambda: None)
    monkeypatch.setattr(cli, "run_f5_quadratic_repair", fake_runner)
    monkeypatch.setattr(cli, "write_f5_quadratic_repair_report", fake_report)

    args = ["--output-dir", str(output), "--run-id", "unit"]
    assert cli.main(args) == 0
    assert cli.main(args) == 2

    streams = capsys.readouterr()
    assert captured["path"] == output
    assert captured["run_id"] == "unit"
    assert captured["config"] == F5QuadraticRepairConfig()
    assert captured["calibration_dir"] == cli._CALIBRATION_DIR
    assert captured["f5_stop_dir"] == cli._F5_STOP_DIR
    assert streams.out.count("\n") == 1
    assert streams.err.count("\n") == 1
    assert "F5 QUADRATIC REPAIR [unit]: PASS" in streams.out
    assert "F5 QUADRATIC REPAIR REFUSED [unit]" in streams.err


def test_main_returns_single_line_refusal_for_unknown_configuration_flag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An unknown study flag must not escape main as argparse usage/SystemExit."""

    from scripts import run_f5_quadratic_repair as cli

    result = cli.main(
        [
            "--output-dir",
            str(tmp_path / "official"),
            "--run-id",
            "unit",
            "--rows",
            "changed",
        ]
    )

    streams = capsys.readouterr()
    assert result == 2
    assert streams.out == ""
    assert streams.err == (
        "F5 QUADRATIC REPAIR REFUSED [unit]: unrecognized arguments: --rows changed\n"
    )


def test_main_returns_single_line_refusal_for_missing_required_argument(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A missing required option must return 2 without argparse usage output."""

    from scripts import run_f5_quadratic_repair as cli

    result = cli.main(["--output-dir", str(tmp_path / "official")])

    streams = capsys.readouterr()
    assert result == 2
    assert streams.out == ""
    assert streams.err == (
        "F5 QUADRATIC REPAIR REFUSED [<missing>]: the following arguments are required: "
        "--run-id\n"
    )


@pytest.mark.parametrize(
    "forbidden",
    [
        "--batches",
        "--rows",
        "--permutations",
        "--threshold",
        "--fixture-id",
        "--pair",
        "--basis",
        "--seed-namespace",
        "--fixture-seed",
        "--calibration-dir",
        "--f5-stop-dir",
    ],
)
def test_cli_exposes_no_mutable_study_configuration(forbidden: str) -> None:
    """Adding any study-setting flag must remain an argparse refusal."""

    from scripts import run_f5_quadratic_repair as cli

    with pytest.raises(SystemExit):
        cli._parse_args(
            ["--output-dir", "out", "--run-id", "unit", forbidden, "changed"]
        )
