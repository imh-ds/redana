"""Lightweight follow-up: does noise_scale hit the same cliff coefficient did?

Round 1's boundary follow-up (docs/evidence/stage2-nonlinear-boundary-followup-20260825.md)
found a sharp detectability cliff for the nonlinear fixture between
coefficient=0.10 (~2% variance explained) and coefficient=0.20 (~7.4%
variance explained). Round 3 (noise) tested noise_scale only up to 2.0,
which -- at coefficient=0.7 fixed -- only pushes variance explained down
to ~19.7%, well above that danger zone. This script pushes noise_scale
further, to the levels that land in the same variance-explained range
round 1's cliff occupied, as a for-completeness check of whether the
apparent "noise doesn't matter" finding was actually just under-tested
rather than a real contrast with effect strength.

Not a new Stage II dimension, not a Gate 0 study, no new redana source:
reuses redana.benchmark.run_replicated_condition and
redana.scenarios.generate_stage1_nonlinear_fixture exactly as built for
round 3, at coefficient=0.7 fixed.
"""

from __future__ import annotations

from functools import partial

from redana.benchmark import ConditionResult, run_replicated_condition
from redana.network import NetworkConfig
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage1_nonlinear_fixture

_N_REPS = 50
_N_ROWS = 1000
_PERMUTATIONS = 199
_ALPHA = 0.05
_BASE_SEED = 20260825
_COEFFICIENT = 0.7
# noise_scale values chosen so variance-explained (0.98 / (0.98 + noise_scale^2))
# lands near round 1's tested levels: ~20% (anchor, already tested), ~7.4%, ~4.3%, ~2.0%
_LEVELS = (
    ("2.0_anchor", 2.0),
    ("3.5", 3.5),
    ("4.7", 4.7),
    ("6.9", 6.9),
)


def run() -> list[ConditionResult]:
    """Run the nonlinear fixture at each of the four higher noise_scale levels."""

    residual_config = PrototypeConfig()
    network_config = NetworkConfig()
    results: list[ConditionResult] = []

    for level_name, noise_scale in _LEVELS:
        condition_name = f"stage2-noise-boundary-{level_name}"
        fixture_fn = partial(
            generate_stage1_nonlinear_fixture, coefficient=_COEFFICIENT, noise_scale=noise_scale
        )
        result = run_replicated_condition(
            fixture_fn,
            condition_name=condition_name,
            n_reps=_N_REPS,
            n_rows=_N_ROWS,
            residual_config=residual_config,
            network_config=network_config,
            permutations=_PERMUTATIONS,
            alpha=_ALPHA,
            base_seed=_BASE_SEED,
        )
        results.append(result)

    return results


def main() -> int:
    results = run()
    print("== nonlinear fixture, pushing noise_scale into the effect-strength danger zone ==")
    for (level_name, noise_scale), result in zip(_LEVELS, results, strict=True):
        summary = result.summary
        variance_explained = 0.98 / (0.98 + noise_scale**2)
        print(f"  -- noise_scale={level_name} (~{variance_explained:.1%} variance explained) --")
        print(
            f"    residual precision: mean={summary.residual_precision.mean:.3f} "
            f"median={summary.residual_precision.median:.3f}"
        )
        print(
            f"    residual recall:    mean={summary.residual_recall.mean:.3f} "
            f"median={summary.residual_recall.median:.3f}"
        )
        print(f"    residual exact-match fraction: {summary.residual_exact_match_fraction:.3f}")
        print(
            "    residual per-edge detection fraction: "
            f"{dict(sorted(summary.residual_per_edge_detection_fraction.items()))}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
