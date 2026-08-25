"""Contract tests for the immutable F5 quadratic-residual-link runner."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from research.gate0 import f5_quadratic_link_runner
from research.gate0.config import FIXTURE_COEFFICIENT
from research.gate0.f4_link_policy import F4LinkConfig
from research.gate0.f5_quadratic_link_runner import (
    generate_f5_quadratic_link_fixture,
    run_f5_quadratic_link,
)


def _small_config() -> F4LinkConfig:
    return F4LinkConfig(batches=2, replications_per_batch=3, rows=100, permutations=19)


def test_generator_uses_the_exact_candidate_one_equations() -> None:
    seed = 4231
    rows = 100
    actual = generate_f5_quadratic_link_fixture(rows, seed)

    rng = np.random.default_rng(seed)
    e1, e2, e3, e4, e5, e6 = rng.standard_normal((rows, 6)).T
    p = FIXTURE_COEFFICIENT * (e3**2 - 1)
    x1 = p + e1
    x2 = p + FIXTURE_COEFFICIENT * (e1**2 - 1) + e2
    expected = pd.DataFrame({"X1": x1, "X2": x2, "X3": e3, "X4": e4, "X5": e5, "X6": e6})
    expected = (expected - expected.mean()) / expected.std(ddof=0)

    pd.testing.assert_frame_equal(actual, expected)


def test_generator_rejects_too_few_rows() -> None:
    with pytest.raises(ValueError, match="rows must be at least 2"):
        generate_f5_quadratic_link_fixture(1, 1)


def test_runner_uses_quadratic_residuals_and_retains_every_successful_cell(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A spline call or wrong identity must make this contract fail."""

    quadratic_calls: list[tuple[str, str, int, int]] = []
    original = f5_quadratic_link_runner.cross_fitted_pair_quadratic_residuals

    def quadratic_spy(
        frame: pd.DataFrame, left: str, right: str, config: object, seed: int
    ) -> pd.DataFrame:
        quadratic_calls.append((left, right, len(frame), seed))
        return original(frame, left, right, config, seed)

    def spline_forbidden(*args: object, **kwargs: object) -> pd.DataFrame:
        raise AssertionError("quadratic-link alternative must not use spline residualization")

    monkeypatch.setattr(
        f5_quadratic_link_runner, "cross_fitted_pair_quadratic_residuals", quadratic_spy
    )
    monkeypatch.setattr(
        f5_quadratic_link_runner, "cross_fitted_pair_residuals", spline_forbidden, raising=False
    )

    frame = run_f5_quadratic_link(tmp_path, "unit", _small_config())

    assert len(frame) == 6
    assert set(frame[["batch", "replication"]].itertuples(index=False, name=None)) == {
        (batch, replication) for batch in range(2) for replication in range(3)
    }
    assert set(frame[["fixture_id", "left", "right"]].itertuples(index=False, name=None)) == {
        ("F5-quadratic-residual-link", "X1", "X2")
    }
    assert frame["phase"].eq("f5-quadratic-residual-link").all()
    assert frame["seed_namespace"].eq("batch-f5-quadratic-residual-link").all()
    assert frame["exception_text"].isna().all()
    assert len(quadratic_calls) == 6
    assert {(left, right, rows) for left, right, rows, _seed in quadratic_calls} == {
        ("X1", "X2", 100)
    }
    for column in ("fixture_seed", "residual_seed", "permutation_seed"):
        assert str(frame[column].dtype) == "UInt64"
    for relative_path in frame["residual_samples_path"]:
        residuals = pd.read_csv(tmp_path / relative_path)
        assert residuals.shape == (100, 2)
        assert list(residuals.columns) == ["X1", "X2"]
    for relative_path in frame["null_statistics_path"]:
        assert np.load(tmp_path / relative_path).shape == (19,)

    manifest = json.loads((tmp_path / "manifest-input.json").read_text(encoding="utf-8"))
    assert manifest["basis"] == "raw-plus-square"
    assert manifest["uses_splines"] is False
    assert manifest["fixture_id"] == "F5-quadratic-residual-link"
    assert manifest["pair"] == ["X1", "X2"]
    assert manifest["phase"] == "f5-quadratic-residual-link"
    assert manifest["seed_namespace"] == "batch-f5-quadratic-residual-link"
    assert manifest["run_id"] == "unit"
    assert manifest["attempted_records"] == 6
    assert manifest["source_revision"]


def test_runner_retains_one_quadratic_residualization_failure_and_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A cell failure must remain recorded without preventing later cells."""

    original = f5_quadratic_link_runner.cross_fitted_pair_quadratic_residuals
    calls = 0

    def fail_once(*args: object, **kwargs: object) -> pd.DataFrame:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("retained quadratic link residual failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(
        f5_quadratic_link_runner, "cross_fitted_pair_quadratic_residuals", fail_once
    )

    frame = run_f5_quadratic_link(tmp_path, "failure", _small_config())

    assert len(frame) == 6
    assert frame["exception_text"].notna().sum() == 1
    assert "RuntimeError: retained quadratic link residual failure" in frame.loc[0, "exception_text"]
    assert pd.isna(frame.loc[0, "residual_samples_path"])
    assert pd.isna(frame.loc[0, "null_statistics_path"])
    assert frame.loc[1:, "exception_text"].isna().all()


def test_runner_refuses_nonempty_output_without_modifying_it(tmp_path: Path) -> None:
    """A reused run directory must retain its original evidence unchanged."""

    output_dir = tmp_path / "taken"
    output_dir.mkdir()
    sentinel = output_dir / "existing.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError, match="initialized"):
        run_f5_quadratic_link(output_dir, "taken", _small_config())

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_runner_rejects_blank_run_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="run_id must be non-empty"):
        run_f5_quadratic_link(tmp_path / "out", "  ", _small_config())
