from research.gate0.fixtures import FIXTURES, generate_fixture


def test_fixture_registry_is_exactly_the_approved_eight() -> None:
    assert tuple(FIXTURES) == ("F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8")
    assert FIXTURES["F5"].target_pair == ("X1", "X2")
    assert FIXTURES["F7"].expected_target_class == "non-null"


def test_generation_is_deterministic_and_standardized() -> None:
    frame = generate_fixture("F3", rows=2_000, seed=9)
    assert frame.equals(generate_fixture("F3", rows=2_000, seed=9))
    assert list(frame.columns) == ["X1", "X2", "X3", "X4", "X5", "X6"]
    assert frame.mean().abs().max() < 1e-12
    assert (frame.std(ddof=0) - 1).abs().max() < 1e-12
