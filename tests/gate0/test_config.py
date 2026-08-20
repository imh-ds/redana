from research.gate0.config import FULL_PROFILE, Gate0Config, derive_seed


def test_seed_depends_on_identity_not_call_order() -> None:
    first = derive_seed("F3", 2, "X1-X2", 17)
    assert first == derive_seed("F3", 2, "X1-X2", 17)
    assert first != derive_seed("F3", 3, "X1-X2", 17)


def test_full_profile_matches_frozen_protocol() -> None:
    assert FULL_PROFILE.source_rows == 50_000
    assert FULL_PROFILE.evaluation_rows == 1_000
    assert FULL_PROFILE.replications == 10
    assert FULL_PROFILE.permutations == 199
    assert Gate0Config(profile=FULL_PROFILE).n_splits == 5
