import json
import warnings
from dataclasses import asdict

import pandas as pd
import pytest

from research.gate0.config import FULL_PROFILE, REDUCED_PROFILE
from research.gate0.fixtures import FIXTURES
from research.gate0.metrics import PermutationResult
from research.gate0.runner import PairRecord, SmokeMeasurement, run_gate0, select_profile


def test_profile_selection_uses_only_the_two_predeclared_profiles() -> None:
    assert select_profile(SmokeMeasurement(projected_seconds=14_400, peak_gib=0.4)) == FULL_PROFILE
    assert select_profile(SmokeMeasurement(projected_seconds=14_401, peak_gib=0.4)) == REDUCED_PROFILE
    assert select_profile(SmokeMeasurement(projected_seconds=14_000, peak_gib=0.400_001)) == (
        REDUCED_PROFILE
    )


def test_profile_selection_includes_reduced_time_and_memory_boundaries() -> None:
    assert select_profile(
        SmokeMeasurement(projected_seconds=38_043.501_326_259_9, peak_gib=1.0)
    ) == REDUCED_PROFILE
    assert select_profile(
        SmokeMeasurement(projected_seconds=38_043.502, peak_gib=1.0)
    ) is None
    assert select_profile(
        SmokeMeasurement(projected_seconds=38_000, peak_gib=1.000_001)
    ) is None


def test_substantive_run_requires_a_smoke_selected_profile(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="prior smoke run"):
        run_gate0("substantive", tmp_path / "run-1", run_id="run-1")


def test_smoke_persists_two_f1_records_and_the_selected_profile(tmp_path, monkeypatch) -> None:
    output_dir = tmp_path / "run-1"
    frame = pd.DataFrame({f"X{index}": range(800) for index in range(1, 7)})
    residual_seeds: list[int] = []
    fixture_seeds: list[int] = []

    def fake_fixture(_fixture_id, _rows, seed):
        fixture_seeds.append(seed)
        return frame

    monkeypatch.setattr("research.gate0.runner.generate_fixture", fake_fixture)

    def fake_residuals(data, left, right, _config, seed):
        residual_seeds.append(seed)
        return data.loc[:, [left, right]]

    monkeypatch.setattr(
        "research.gate0.runner.cross_fitted_pair_residuals",
        fake_residuals,
    )
    monkeypatch.setattr(
        "research.gate0.runner.permutation_distance_correlation",
        lambda *_args, **_kwargs: PermutationResult(0.2, null_statistics=[0.1], p_value=0.5),
    )

    records = run_gate0("smoke", output_dir, run_id="run-1")

    assert records.shape[0] == 2
    assert records["fixture_id"].tolist() == ["F1", "F1"]
    assert records["pair_role"].tolist() == ["target", "null_control"]
    assert fixture_seeds == [fixture_seeds[0]] * 2
    assert records["fixture_seed"].nunique() == 1
    assert all(0 <= seed < 2**32 for seed in residual_seeds)
    assert records["residual_seed"].max() >= 2**32
    assert records["run_id"].eq("run-1").all()
    assert (output_dir / "smoke_records.csv").exists()
    assert (output_dir / "smoke" / "null_statistics").exists()
    selection = json.loads((output_dir / "selected_profile.json").read_text(encoding="utf-8"))
    assert selection["name"] == "full"
    assert selection["run_id"] == "run-1"
    measurement = json.loads((output_dir / "smoke_measurement.json").read_text(encoding="utf-8"))
    assert measurement["profile_projections"]["full"]["projected_peak_gib"] == pytest.approx(
        measurement["peak_gib"] * 10
    )
    assert measurement["profile_projections"]["reduced"][
        "projected_peak_gib"
    ] == pytest.approx(measurement["peak_gib"] * 4)
    state = json.loads((output_dir / "run_state.json").read_text(encoding="utf-8"))
    assert state == {"run_id": "run-1", "state": "smoke_complete"}


def test_pair_failures_are_recorded_and_force_stop(tmp_path, monkeypatch) -> None:
    (tmp_path / "run_state.json").write_text(
        json.dumps({"run_id": "run-1", "state": "smoke_complete"}), encoding="utf-8"
    )
    (tmp_path / "selected_profile.json").write_text(
        json.dumps({"run_id": "run-1", **asdict(REDUCED_PROFILE)}), encoding="utf-8"
    )
    frame = pd.DataFrame({f"X{index}": range(800) for index in range(1, 7)})

    monkeypatch.setattr("research.gate0.runner.FIXTURES", {"F1": FIXTURES["F1"]})
    monkeypatch.setattr("research.gate0.runner.generate_fixture", lambda *_: frame)

    def fake_residuals(data, left, right, *_):
        if (left, right) == FIXTURES["F1"].target_pair:
            warnings.warn("target residualization warning", UserWarning)
            raise RuntimeError("target residualization failed")
        return data.loc[:, [left, right]]

    monkeypatch.setattr("research.gate0.runner.cross_fitted_pair_residuals", fake_residuals)
    monkeypatch.setattr(
        "research.gate0.runner.permutation_distance_correlation",
        lambda *_args, **_kwargs: PermutationResult(0.2, null_statistics=[0.1], p_value=0.5),
    )

    records = run_gate0("substantive", tmp_path, run_id="run-1")

    assert records.shape[0] == 20
    assert records["exception_text"].notna().sum() == 10
    assert set(records["gate_result"]) == {"STOP"}
    assert (
        records.loc[records["pair_role"] == "target", "warnings"].eq(
            "target residualization warning"
        ).all()
    )
    assert records.loc[records["pair_role"] == "null_control", "observed_statistic"].notna().all()
    state = json.loads((tmp_path / "run_state.json").read_text(encoding="utf-8"))
    assert state == {"run_id": "run-1", "state": "substantive_complete"}


def test_computational_stop_writes_required_memo_and_terminal_state(tmp_path, monkeypatch) -> None:
    output_dir = tmp_path / "run-stop"
    record = PairRecord(
        fixture_id="F1",
        replication=0,
        pair_role="target",
        expected_class="null-like",
        left="X1",
        right="X2",
        observed_statistic=0.1,
        permutation_p_value=0.5,
        null_statistics_path=None,
        fixture_seed=1,
        residual_seed=2,
        evaluation_seed=3,
        permutation_seed=4,
        profile="smoke",
        elapsed_seconds=0.01,
        warnings="",
        exception_text=None,
    )
    monkeypatch.setattr("research.gate0.runner._run_pairs", lambda *_: [record])
    monkeypatch.setattr("research.gate0.runner._estimate_full_seconds", lambda _: 40_000.0)

    records = run_gate0("smoke", output_dir, run_id="run-stop")

    assert set(records["gate_result"]) == {"STOP"}
    assert not (output_dir / "selected_profile.json").exists()
    summary = json.loads((output_dir / "smoke_summary.json").read_text(encoding="utf-8"))
    assert summary["gate_result"] == "STOP"
    assert summary["stop_kind"] == "computational"
    memo = (output_dir / "gate-memo.md").read_text(encoding="utf-8")
    assert "Overall outcome: **STOP**" in memo
    assert "Measured smoke resources" in memo
    assert "Neither frozen computational profile is feasible" in memo
    assert "PASS" not in memo
    assert "NARROW" not in memo
    assert memo.rstrip().endswith(
        "Owner decision required; this result does not authorize estimator redesign, a new simulation family, or package work."
    )
    state = json.loads((output_dir / "run_state.json").read_text(encoding="utf-8"))
    assert state == {"run_id": "run-stop", "state": "computational_stop"}
    with pytest.raises(ValueError, match="computational_stop"):
        run_gate0("substantive", output_dir, run_id="run-stop")


def test_completed_run_directory_cannot_be_reused_or_mixed(tmp_path, monkeypatch) -> None:
    output_dir = tmp_path / "immutable-run"
    record = PairRecord(
        fixture_id="F1",
        replication=0,
        pair_role="target",
        expected_class="null-like",
        left="X1",
        right="X2",
        observed_statistic=0.1,
        permutation_p_value=0.5,
        null_statistics_path=None,
        fixture_seed=1,
        residual_seed=2,
        evaluation_seed=3,
        permutation_seed=4,
        profile="smoke",
        elapsed_seconds=0.01,
        warnings="",
        exception_text=None,
    )
    monkeypatch.setattr("research.gate0.runner._run_pairs", lambda *_args, **_kwargs: [record])
    monkeypatch.setattr("research.gate0.runner._estimate_full_seconds", lambda _: 1.0)

    run_gate0("smoke", output_dir, run_id="immutable-run")
    smoke_records = (output_dir / "smoke_records.csv").read_bytes()

    with pytest.raises(FileExistsError, match="already initialized"):
        run_gate0("smoke", output_dir, run_id="immutable-run")
    with pytest.raises(ValueError, match="does not match"):
        run_gate0("substantive", output_dir, run_id="different-run")

    monkeypatch.setattr("research.gate0.runner.gate_status", lambda _records: "PASS")
    monkeypatch.setattr(
        "research.gate0.runner.write_gate_report",
        lambda _records, _output_dir, *, run_id: _output_dir / "gate-memo.md",
    )
    run_gate0("substantive", output_dir, run_id="immutable-run")

    assert (output_dir / "smoke_records.csv").read_bytes() == smoke_records
    assert (output_dir / "pair_records.csv").exists()
    with pytest.raises(ValueError, match="substantive_complete"):
        run_gate0("substantive", output_dir, run_id="immutable-run")


def test_smoke_execution_failure_has_an_accurate_computational_stop_reason(
    tmp_path, monkeypatch
) -> None:
    output_dir = tmp_path / "smoke-error"
    record = PairRecord(
        fixture_id="F1",
        replication=0,
        pair_role="target",
        expected_class="null-like",
        left="X1",
        right="X2",
        observed_statistic=None,
        permutation_p_value=None,
        null_statistics_path=None,
        fixture_seed=1,
        residual_seed=2,
        evaluation_seed=3,
        permutation_seed=4,
        profile="smoke",
        elapsed_seconds=0.01,
        warnings="",
        exception_text="RuntimeError: smoke failure",
    )
    monkeypatch.setattr("research.gate0.runner._run_pairs", lambda *_args: [record])
    monkeypatch.setattr("research.gate0.runner._estimate_full_seconds", lambda _: 1.0)

    run_gate0("smoke", output_dir, run_id="smoke-error")

    memo = (output_dir / "gate-memo.md").read_text(encoding="utf-8")
    assert "Smoke execution recorded exceptions; profile feasibility was not established" in memo
    assert "RuntimeError: smoke failure" in memo
    assert "Neither frozen computational profile is feasible" not in memo
