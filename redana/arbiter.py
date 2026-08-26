"""Held-out-consistency configuration arbiter.

Per docs/superpowers/specs/2026-08-26-track2-adaptive-selection-charter.md.
Unlike Track 1's bootstrap stability -- which resamples the *same* rows
and so can never rule out "this dataset's own particular draw happened
to look convincing" -- this arbiter splits a dataset into disjoint
train/held-out portions, so its check is against genuinely independent
data, at the cost of using less data for each half.

For each candidate configuration, the full pipeline is fit separately on
the train portion and the held-out portion. A configuration's
consistency score is the fraction of its train-detected edges that are
*also* detected, independently, on the held-out portion. The candidate
with the highest consistency score is selected; ties, or every candidate
scoring 0.0, fall back to a fixed default (the first candidate given).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from redana.dependence import derive_seed
from redana.network import NetworkConfig
from redana.prototype import run_prototype
from redana.residuals import PrototypeConfig


@dataclass(frozen=True)
class ArbiterResult:
    """Which candidate configuration was selected, and every candidate's
    held-out consistency score.
    """

    selected: str
    consistency_scores: dict[str, float]


def select_configuration(
    frame: pd.DataFrame,
    candidates: dict[str, tuple[PrototypeConfig, float]],
    permutations: int,
    seed: int,
    train_fraction: float = 0.8,
) -> ArbiterResult:
    """Split ``frame`` into disjoint train/held-out portions and select the
    candidate configuration with the highest held-out consistency score.
    """

    if not candidates:
        raise ValueError("candidates must be non-empty")
    if not 0.0 < train_fraction < 1.0:
        raise ValueError(f"train_fraction must be in (0, 1), got {train_fraction!r}")

    rng = np.random.default_rng(seed)
    n_rows = len(frame)
    shuffled_indices = rng.permutation(n_rows)
    split_point = int(round(n_rows * train_fraction))
    train_frame = frame.iloc[shuffled_indices[:split_point]].reset_index(drop=True)
    heldout_frame = frame.iloc[shuffled_indices[split_point:]].reset_index(drop=True)

    network_config = NetworkConfig()
    consistency_scores: dict[str, float] = {}

    for name, (residual_config, alpha) in candidates.items():
        train_seed = derive_seed("arbiter-train", seed, name)
        heldout_seed = derive_seed("arbiter-heldout", seed, name)
        train_result = run_prototype(
            train_frame, residual_config, network_config, permutations, alpha, train_seed
        )
        heldout_result = run_prototype(
            heldout_frame, residual_config, network_config, permutations, alpha, heldout_seed
        )
        train_edges = {tuple(sorted(edge)) for edge in train_result.residual_edges}
        heldout_edges = {tuple(sorted(edge)) for edge in heldout_result.residual_edges}
        consistency_scores[name] = (
            len(train_edges & heldout_edges) / len(train_edges) if train_edges else 0.0
        )

    default_name = next(iter(candidates))
    best_score = max(consistency_scores.values())
    winners = [name for name, score in consistency_scores.items() if score == best_score]
    selected = winners[0] if best_score > 0.0 and len(winners) == 1 else default_name

    return ArbiterResult(selected=selected, consistency_scores=consistency_scores)
