import json

import pandas as pd
import pytest

from research.gate0.config import FULL_PROFILE, REDUCED_PROFILE
from research.gate0.fixtures import FIXTURES
from research.gate0.metrics import PermutationResult
from research.gate0.runner import SmokeMeasurement, run_gate0, select_profile


def test_profile_selection_uses_only_the_two_predeclared_profiles() -> None:
    assert select_profile(SmokeMeasurement(projected_seconds=14_000, peak_gib=3.0)) == FULL_PROFILE
    assert select_profile(SmokeMeasurement(projected_seconds=14_500, peak_gib=3.0)) == REDUCED_PROFILE
    assert select_profile(SmokeMeasurement(projected_seconds=14_500, peak_gib=4.1)) is None


def test_substantive_run_requires_a_smoke_selected_profile(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="selected_profile.json"):
        run_gate0("substantive", tmp_path)


def test_smoke_persists_two_f1_records_and_the_selected_profile(tmp_path, monkeypatch) -> None:
    frame = pd.DataFrame({f"X{index}": range(800) for index in range(1, 7)})
    residual_seeds: list[int] = []

    monkeypatch.setattr("research.gate0.runner.generate_fixture", lambda *_: frame)

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

    records = run_gate0("smoke", tmp_path)

    assert records.shape[0] == 2
    assert records["fixture_id"].tolist() == ["F1", "F1"]
    assert records["pair_role"].tolist() == ["target", "null_control"]
    assert all(0 <= seed < 2**32 for seed in residual_seeds)
    assert records["residual_seed"].max() >= 2**32
    assert (tmp_path / "pair_records.csv").exists()
    assert json.loads((tmp_path / "selected_profile.json").read_text(encoding="utf-8"))["name"] == "full"


def test_pair_failures_are_recorded_and_force_stop(tmp_path, monkeypatch) -> None:
    (tmp_path / "selected_profile.json").write_text(
        json.dumps({"name": "reduced"}), encoding="utf-8"
    )
    frame = pd.DataFrame({f"X{index}": range(800) for index in range(1, 7)})

    monkeypatch.setattr("research.gate0.runner.FIXTURES", {"F1": FIXTURES["F1"]})
    monkeypatch.setattr("research.gate0.runner.generate_fixture", lambda *_: frame)

    def fake_residuals(data, left, right, *_):
        if (left, right) == FIXTURES["F1"].target_pair:
            raise RuntimeError("target residualization failed")
        return data.loc[:, [left, right]]

    monkeypatch.setattr("research.gate0.runner.cross_fitted_pair_residuals", fake_residuals)
    monkeypatch.setattr(
        "research.gate0.runner.permutation_distance_correlation",
        lambda *_args, **_kwargs: PermutationResult(0.2, null_statistics=[0.1], p_value=0.5),
    )

    records = run_gate0("substantive", tmp_path)

    assert records.shape[0] == 20
    assert records["exception_text"].notna().sum() == 10
    assert set(records["gate_result"]) == {"STOP"}
    assert records.loc[records["pair_role"] == "null_control", "observed_statistic"].notna().all()
