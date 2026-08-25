"""Run the Stage I clean mechanistic benchmark (outline/plan.md section 5).

Two conditions, 100 replications each at n=1,000 rows: a linear fixture
and a pure nonlinear fixture. Not a Gate 0 study -- no hash-pinned
calibration, no single-official-run ceremony, no per-replication
artifact retention. Reuses every Step 4 component unchanged.
"""

from __future__ import annotations

from redana.benchmark import ConditionResult, run_replicated_condition
from redana.network import NetworkConfig
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_stage1_linear_fixture, generate_stage1_nonlinear_fixture

_N_REPS = 100
_N_ROWS = 1000
_PERMUTATIONS = 199
_ALPHA = 0.05
_BASE_SEED = 20260825


def run() -> tuple[ConditionResult, ConditionResult]:
    """Run both Stage I conditions and return their results."""

    residual_config = PrototypeConfig()
    network_config = NetworkConfig()

    linear_result = run_replicated_condition(
        generate_stage1_linear_fixture,
        condition_name="stage1-linear",
        n_reps=_N_REPS,
        n_rows=_N_ROWS,
        residual_config=residual_config,
        network_config=network_config,
        permutations=_PERMUTATIONS,
        alpha=_ALPHA,
        base_seed=_BASE_SEED,
    )
    nonlinear_result = run_replicated_condition(
        generate_stage1_nonlinear_fixture,
        condition_name="stage1-nonlinear",
        n_reps=_N_REPS,
        n_rows=_N_ROWS,
        residual_config=residual_config,
        network_config=network_config,
        permutations=_PERMUTATIONS,
        alpha=_ALPHA,
        base_seed=_BASE_SEED,
    )
    return linear_result, nonlinear_result


def _print_condition(result: ConditionResult) -> None:
    summary = result.summary
    print(f"== {result.condition_name} ({len(result.replications)} replications) ==")
    for label, incumbent, residual in (
        ("precision", summary.incumbent_precision, summary.residual_precision),
        ("recall", summary.incumbent_recall, summary.residual_recall),
        ("f1", summary.incumbent_f1, summary.residual_f1),
    ):
        print(
            f"  incumbent {label}: mean={incumbent.mean:.3f} median={incumbent.median:.3f} "
            f"min={incumbent.minimum:.3f} max={incumbent.maximum:.3f}"
        )
        print(
            f"  residual  {label}: mean={residual.mean:.3f} median={residual.median:.3f} "
            f"min={residual.minimum:.3f} max={residual.maximum:.3f}"
        )
    print(f"  incumbent exact-match fraction: {summary.incumbent_exact_match_fraction:.3f}")
    print(f"  residual  exact-match fraction: {summary.residual_exact_match_fraction:.3f}")
    print("  residual per-edge detection fraction:")
    for edge, fraction in sorted(summary.residual_per_edge_detection_fraction.items()):
        print(f"    {edge}: {fraction:.3f}")


def main() -> int:
    linear_result, nonlinear_result = run()
    _print_condition(linear_result)
    _print_condition(nonlinear_result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
