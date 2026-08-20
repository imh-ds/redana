import json

import numpy as np
import pandas as pd

from research.gate0.report import classify_pair, write_gate_report


def test_non_null_rule_requires_both_frequency_and_effect_size() -> None:
    records = pd.DataFrame({"p_value": [0.01] * 8 + [0.5, 0.5], "observed": [0.11] * 10})
    assert classify_pair(records) == "non-null"


def test_null_like_rule_rejects_three_small_p_values() -> None:
    records = pd.DataFrame({"p_value": [0.01, 0.02, 0.03] + [0.5] * 7, "observed": [0.02] * 10})
    assert classify_pair(records) == "ambiguous"


def test_report_writes_evidence_and_stops_for_unexpected_null_like(tmp_path) -> None:
    null_path = tmp_path / "null_statistics" / "f7-target.npy"
    null_path.parent.mkdir()
    np.save(null_path, np.array([0.01, 0.02, 0.03]))
    sample_path = tmp_path / "residual_samples" / "f7-target.csv"
    sample_path.parent.mkdir()
    pd.DataFrame({"X1": [0.1, 0.2], "X2": [0.3, 0.4]}).to_csv(sample_path, index=False)
    target_rows = {
        "fixture_id": ["F7"] * 10,
        "replication": list(range(10)),
        "pair_role": ["target"] * 10,
        "expected_class": ["non-null"] * 10,
        "left": ["X1"] * 10,
        "right": ["X2"] * 10,
        "observed_statistic": [0.02] * 10,
        "permutation_p_value": [0.5] * 10,
        "null_statistics_path": [str(null_path.relative_to(tmp_path))] + [None] * 9,
        "residual_sample_path": [str(sample_path.relative_to(tmp_path))] + [None] * 9,
        "profile": ["reduced"] * 10,
        "warnings": [""] * 10,
        "exception_text": [None] * 10,
    }
    records = pd.DataFrame(target_rows)

    memo_path = write_gate_report(records, tmp_path)

    assert memo_path == tmp_path / "gate-memo.md"
    assert (tmp_path / "records.csv").exists()
    assert (tmp_path / "plots" / "F7-permutation-distribution.png").exists()
    assert (tmp_path / "plots" / "F7-residual-scatter.png").exists()
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["gate_status"] == "STOP"
    memo = memo_path.read_text(encoding="utf-8")
    assert "F7 collider interpretation" in memo
    assert "induced conditional dependence—not a direct causal relationship" in memo
    assert memo.rstrip().endswith(
        "Owner decision required; this result does not authorize estimator redesign, a new simulation family, or package work."
    )
