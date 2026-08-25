"""Re-run the frozen Step 4 validation scenario across a few seeds.

Diagnostic follow-up to docs/evidence/step4-first-validation-scenario-20260825.md:
that note found the incumbent network selected two false-positive edges
(X3-X4, X4-X5) in one seeded run at n=5000, and explicitly flagged that
one run cannot distinguish sampling noise from a systematic issue. This
script re-runs the same frozen scenario at the same n across a handful
of additional seeds to see whether those false positives recur.

Not a Gate 0 study and not Stage I/II/III benchmarking: no replication
design, no hash-pinning, no claim about detection power or
false-positive rates in general. It only reports what happened across
these five specific seeds.
"""

from __future__ import annotations

from scripts.run_step4_validation_scenario import run

_SEEDS = (20260825, 1, 2, 3, 4)
_N_ROWS = 5000


def main() -> int:
    for seed in _SEEDS:
        outcome = run(n_rows=_N_ROWS, seed=seed)
        incumbent_score = outcome["incumbent_score"]
        residual_score = outcome["residual_score"]
        print(f"seed={seed}")
        print(f"  incumbent edges: {sorted(outcome['incumbent_edges'])}")
        print(
            f"  incumbent precision={incumbent_score.precision:.3f} "
            f"recall={incumbent_score.recall:.3f}"
        )
        print(f"  residual edges: {sorted(outcome['residual_edges'])}")
        print(
            f"  residual precision={residual_score.precision:.3f} "
            f"recall={residual_score.recall:.3f}"
        )
        print(f"  nonlinear edge (X4, X5) detected: {outcome['nonlinear_edge_detected']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
