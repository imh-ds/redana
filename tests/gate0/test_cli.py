import pandas as pd

from scripts import run_gate0 as cli


def test_cli_passes_run_id_and_labels_computational_stop(tmp_path, monkeypatch, capsys) -> None:
    captured = {}

    def fake_run(mode, output_dir, *, run_id):
        captured.update(mode=mode, output_dir=output_dir, run_id=run_id)
        return pd.DataFrame({"gate_result": ["STOP"]})

    monkeypatch.setattr(cli, "run_gate0", fake_run)

    exit_code = cli.main(
        ["--mode", "smoke", "--output-dir", str(tmp_path / "run-1"), "--run-id", "run-1"]
    )

    assert exit_code == 2
    assert captured == {"mode": "smoke", "output_dir": tmp_path / "run-1", "run_id": "run-1"}
    assert "COMPUTATIONAL STOP [run-1]" in capsys.readouterr().err


def test_cli_labels_substantive_gate_failure_as_scientific_stop(
    tmp_path, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(
        cli,
        "run_gate0",
        lambda *_args, **_kwargs: pd.DataFrame({"gate_result": ["STOP"]}),
    )

    exit_code = cli.main(
        [
            "--mode",
            "substantive",
            "--output-dir",
            str(tmp_path / "run-1"),
            "--run-id",
            "run-1",
        ]
    )

    assert exit_code == 2
    assert "SCIENTIFIC STOP [run-1]" in capsys.readouterr().err


def test_substantive_cli_recovers_the_persisted_smoke_run_id_when_omitted(
    tmp_path, monkeypatch
) -> None:
    output_dir = tmp_path / "run-1"
    output_dir.mkdir()
    (output_dir / "run_state.json").write_text(
        '{"run_id": "persisted-smoke-id", "state": "smoke_complete"}\n', encoding="utf-8"
    )
    captured = {}

    def fake_run(mode, passed_output_dir, *, run_id):
        captured.update(mode=mode, output_dir=passed_output_dir, run_id=run_id)
        return pd.DataFrame({"gate_result": ["READY"]})

    monkeypatch.setattr(cli, "run_gate0", fake_run)

    exit_code = cli.main(["--mode", "substantive", "--output-dir", str(output_dir)])

    assert exit_code == 0
    assert captured == {
        "mode": "substantive",
        "output_dir": output_dir,
        "run_id": "persisted-smoke-id",
    }


def test_substantive_cli_without_a_persisted_run_id_refuses_cleanly(tmp_path, capsys) -> None:
    exit_code = cli.main(["--mode", "substantive", "--output-dir", str(tmp_path / "missing")])

    assert exit_code == 2
    assert "RUN REFUSED [<recovered>]" in capsys.readouterr().err
