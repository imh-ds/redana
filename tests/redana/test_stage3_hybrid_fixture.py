"""Tests for the Stage III round 1 hybrid fixture: hub communities, mixed edge
types, heterogeneous strength, a redundant pair, and isolated nodes."""

from __future__ import annotations

import pandas as pd

from redana.scenarios import generate_stage3_hybrid_fixture


def test_hybrid_fixture_has_correct_shape() -> None:
    frame, _, _ = generate_stage3_hybrid_fixture(1000, seed=1)
    assert frame.shape == (1000, 12)
    assert list(frame.columns) == [f"X{i}" for i in range(1, 13)]


def test_hybrid_fixture_is_deterministic_given_the_same_seed() -> None:
    first, _, _ = generate_stage3_hybrid_fixture(300, seed=2)
    second, _, _ = generate_stage3_hybrid_fixture(300, seed=2)
    pd.testing.assert_frame_equal(first, second)


def test_hybrid_fixture_differs_across_seeds() -> None:
    first, _, _ = generate_stage3_hybrid_fixture(300, seed=2)
    second, _, _ = generate_stage3_hybrid_fixture(300, seed=3)
    assert not first["X2"].equals(second["X2"])


def test_hybrid_fixture_true_edges_are_disjoint_and_nonempty() -> None:
    _, linear_edges, nonlinear_edges = generate_stage3_hybrid_fixture(1000, seed=1)
    assert linear_edges
    assert nonlinear_edges
    assert linear_edges.isdisjoint(nonlinear_edges)


def test_hybrid_fixture_true_edge_split_is_linear_majority() -> None:
    _, linear_edges, nonlinear_edges = generate_stage3_hybrid_fixture(1000, seed=1)
    assert len(linear_edges) > len(nonlinear_edges)


def test_hybrid_fixture_has_a_bridge_edge_between_the_two_communities() -> None:
    # X1 (community A's hub) and X12 (community B) are the only true edge
    # crossing between the two hub-and-spoke clusters.
    _, linear_edges, nonlinear_edges = generate_stage3_hybrid_fixture(1000, seed=1)
    all_edges = linear_edges | nonlinear_edges
    assert ("X1", "X12") in all_edges


def test_hybrid_fixture_has_two_isolated_nodes_with_no_true_edges() -> None:
    # X5 is also absent from the true-edge set (it's the redundant/collinear
    # node, not a true cause of anything), but it's distinct from a truly
    # isolated node: it's strongly correlated with X1 by construction, so it
    # is excluded from "isolated" here and checked separately below.
    _, linear_edges, nonlinear_edges = generate_stage3_hybrid_fixture(1000, seed=1)
    all_edges = linear_edges | nonlinear_edges
    touched = {node for edge in all_edges for node in edge}
    all_nodes = {f"X{i}" for i in range(1, 13)}
    isolated = all_nodes - touched - {"X5"}
    assert isolated == {"X6", "X11"}


def test_hybrid_fixture_redundant_pair_is_highly_correlated_but_not_a_true_edge() -> None:
    frame, linear_edges, nonlinear_edges = generate_stage3_hybrid_fixture(5000, seed=4)
    all_edges = linear_edges | nonlinear_edges
    assert ("X1", "X5") not in all_edges
    assert ("X5", "X1") not in all_edges
    correlation = abs(frame["X1"].corr(frame["X5"]))
    assert correlation > 0.7


def test_hybrid_fixture_reuses_hub_topology_for_each_community() -> None:
    # Community A's hub (X1) drives three spokes (X2, X3, X4); community B's
    # hub (X7) drives three spokes (X8, X9, X10) -- same degree-3 hub shape
    # as generate_stage2_hub_fixture, replicated twice.
    _, linear_edges, nonlinear_edges = generate_stage3_hybrid_fixture(1000, seed=1)
    all_edges = linear_edges | nonlinear_edges
    community_a_spokes = {("X1", "X2"), ("X1", "X3"), ("X1", "X4")}
    community_b_spokes = {("X7", "X8"), ("X7", "X9"), ("X7", "X10")}
    assert community_a_spokes <= all_edges
    assert community_b_spokes <= all_edges
