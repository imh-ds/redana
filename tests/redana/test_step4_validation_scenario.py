"""Fast smoke test for the frozen Step 4 first synthetic validation scenario."""

from __future__ import annotations

from redana.network import NetworkConfig
from redana.prototype import run_prototype
from redana.residuals import PrototypeConfig
from redana.scenarios import generate_step4_validation_frame


def test_generator_produces_the_frozen_p6_scenario_with_known_true_edges() -> None:
    frame, true_linear_edges, true_nonlinear_edges = generate_step4_validation_frame(300, seed=1)

    assert list(frame.columns) == ["X1", "X2", "X3", "X4", "X5", "X6"]
    assert len(frame) == 300
    assert true_linear_edges == frozenset({("X1", "X2"), ("X2", "X3")})
    assert true_nonlinear_edges == frozenset({("X4", "X5")})


def test_pipeline_runs_end_to_end_at_reduced_rows_without_error() -> None:
    frame, _, _ = generate_step4_validation_frame(300, seed=1)

    result = run_prototype(
        frame,
        PrototypeConfig(n_splits=3, spline_knots=3, spline_degree=2),
        NetworkConfig(alphas=(0.1, 0.3, 0.5)),
        permutations=19,
        alpha=0.05,
        seed=2,
    )

    assert len(result.pair_statistics) == 15  # C(6, 2)
    for stat in result.pair_statistics:
        assert 0.0 < stat.p_value <= 1.0
    assert isinstance(result.incumbent_edges, frozenset)
    assert isinstance(result.residual_edges, frozenset)


def test_script_run_function_returns_well_formed_results_at_reduced_rows() -> None:
    from scripts.run_step4_validation_scenario import run

    outcome = run(n_rows=300, seed=3)

    assert set(outcome) == {
        "incumbent_edges",
        "residual_edges",
        "incumbent_score",
        "residual_score",
        "nonlinear_edge_detected",
        "pair_statistics",
    }
    assert isinstance(outcome["nonlinear_edge_detected"], bool)
    assert 0.0 <= outcome["incumbent_score"].precision <= 1.0
    assert 0.0 <= outcome["residual_score"].precision <= 1.0
    assert len(outcome["pair_statistics"]) == 15
