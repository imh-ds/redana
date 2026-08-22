from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from research.gate0 import f4_link_runner
from research.gate0.f4_link_policy import F4LinkConfig
from research.gate0.f4_link_runner import generate_f4_link_fixture, run_f4_link


def _small_config() -> F4LinkConfig:
    return F4LinkConfig(batches=2, replications_per_batch=3, rows=100, permutations=19)


def test_generator_uses_the_exact_f4_residual_link_equations() -> None:
    seed = 917
    rows = 100
    actual = generate_f4_link_fixture(rows, seed)
    rng = np.random.default_rng(seed)
    e1, e2, e3, e4, e5, e6 = rng.standard_normal((rows, 6)).T
    x1 = e1
    x2 = 0.7 * x1 + e2
    x3 = 0.7 * x2 + 0.7 * e1 + e3
    expected = pd.DataFrame({"X1": x1, "X2": x2, "X3": x3, "X4": e4, "X5": e5, "X6": e6})
    expected = (expected - expected.mean()) / expected.std(ddof=0)

    pd.testing.assert_frame_equal(actual, expected)


def test_runner_retains_f4_link_identities_samples_arrays_and_uint64_seeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[int, int]] = []
    original = f4_link_runner.generate_f4_link_fixture

    def spy(rows: int, seed: int) -> pd.DataFrame:
        calls.append((rows, seed))
        return original(rows, seed)

    monkeypatch.setattr(f4_link_runner, "generate_f4_link_fixture", spy)
    frame = run_f4_link(tmp_path, "unit", _small_config())

    assert len(frame) == 6
    assert len(calls) == 6
    assert set(frame[["fixture_id", "left", "right", "phase"]].itertuples(index=False, name=None)) == {
        ("F4-residual-link", "X1", "X3", "f4-residual-link")
    }
    assert frame["seed_namespace"].eq("batch-f4-residual-link").all()
    assert set(frame[["batch", "replication"]].itertuples(index=False, name=None)) == {
        (batch, replication) for batch in range(2) for replication in range(3)
    }
    assert frame["exception_text"].isna().all()
    for column in ("fixture_seed", "residual_seed", "permutation_seed"):
        assert str(frame[column].dtype) == "UInt64"
    for relative_path in frame["residual_samples_path"]:
        residuals = pd.read_csv(tmp_path / relative_path)
        assert list(residuals) == ["X1", "X3"]
        assert len(residuals) == 100
    for relative_path in frame["null_statistics_path"]:
        assert len(np.load(tmp_path / relative_path)) == 19


def test_runner_retains_one_failure_and_continues(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = f4_link_runner.cross_fitted_pair_residuals
    calls = 0

    def fail_once(*args: object, **kwargs: object) -> pd.DataFrame:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("retained residual failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(f4_link_runner, "cross_fitted_pair_residuals", fail_once)
    frame = run_f4_link(tmp_path, "failure", _small_config())

    assert len(frame) == 6
    assert frame["exception_text"].notna().sum() == 1
    assert "RuntimeError: retained residual failure" in frame.loc[0, "exception_text"]
    assert pd.isna(frame.loc[0, "residual_samples_path"])
    assert frame.loc[1:, "exception_text"].isna().all()


def test_runner_refuses_nonempty_output_without_modifying_it(tmp_path: Path) -> None:
    output_dir = tmp_path / "taken"
    output_dir.mkdir()
    sentinel = output_dir / "existing.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError, match="initialized"):
        run_f4_link(output_dir, "taken", _small_config())

    assert sentinel.read_text(encoding="utf-8") == "keep"
