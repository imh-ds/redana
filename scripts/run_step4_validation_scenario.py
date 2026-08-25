"""Run the frozen Step 4 first synthetic validation scenario.

Not a Gate 0 study: no hash-pinned calibration, no single-official-run
ceremony, no independent outside verifier. This is a deterministic,
seeded smoke test of the Step 4 prototype mechanism -- does the core
mechanism work? -- per outline/plan.md sections 4 and 5.
"""

from __future__ import annotations

from redana.network import NetworkConfig
from redana.prototype import run_prototype
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_step4_validation_frame
from redana.scoring import EdgeScore, score_edges

_N_ROWS = 5000
_SEED = 20260825
_PERMUTATIONS = 199
_ALPHA = 0.05


def run(n_rows: int = _N_ROWS, seed: int = _SEED) -> dict[str, object]:
    """Run the prototype on the frozen scenario and score both mechanisms."""

    frame, true_linear_edges, true_nonlinear_edges = generate_step4_validation_frame(
        n_rows, seed
    )
    result = run_prototype(
        frame,
        PrototypeConfig(),
        NetworkConfig(),
        permutations=_PERMUTATIONS,
        alpha=_ALPHA,
        seed=seed,
    )

    incumbent_score: EdgeScore = score_edges(set(true_linear_edges), set(result.incumbent_edges))
    all_true_edges = set(true_linear_edges) | set(true_nonlinear_edges)
    residual_score: EdgeScore = score_edges(all_true_edges, set(result.residual_edges))
    nonlinear_edge_detected = bool(set(true_nonlinear_edges) & set(result.residual_edges))

    return {
        "incumbent_edges": result.incumbent_edges,
        "residual_edges": result.residual_edges,
        "incumbent_score": incumbent_score,
        "residual_score": residual_score,
        "nonlinear_edge_detected": nonlinear_edge_detected,
        "pair_statistics": result.pair_statistics,
    }


def main() -> int:
    outcome = run()
    incumbent_score: EdgeScore = outcome["incumbent_score"]
    residual_score: EdgeScore = outcome["residual_score"]

    print(f"Incumbent edges: {sorted(outcome['incumbent_edges'])}")
    print(
        "Incumbent vs true linear edges: "
        f"precision={incumbent_score.precision:.3f} recall={incumbent_score.recall:.3f} "
        f"f1={incumbent_score.f1:.3f}"
    )
    print(f"Residual layer edges: {sorted(outcome['residual_edges'])}")
    print(
        "Residual layer vs all true edges (linear + nonlinear): "
        f"precision={residual_score.precision:.3f} recall={residual_score.recall:.3f} "
        f"f1={residual_score.f1:.3f}"
    )
    print(f"Nonlinear edge (X4, X5) detected by residual layer: {outcome['nonlinear_edge_detected']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
