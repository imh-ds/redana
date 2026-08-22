"""Command-line contracts for the frozen F4 residual-null transfer."""


def test_f4_cli_module_is_available() -> None:
    """The approved F4 transfer command has a dedicated module."""

    from scripts import run_f4_linear_residual_null_transfer

    assert run_f4_linear_residual_null_transfer is not None
