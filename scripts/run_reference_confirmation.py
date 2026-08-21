"""Execute one immutable reference-calibrated confirmation run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research.gate0.confirmation_policy import (
    ConfirmationPolicy,
    verify_calibration_provenance,
)
from research.gate0.confirmation_report import write_confirmation_report
from research.gate0.confirmation_runner import (
    CALIBRATION_SOURCE,
    ConfirmationConfig,
    run_confirmation,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the frozen reference-calibrated confirmation.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    return parser.parse_args(argv)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _require_empty_output_directory(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"run directory is already initialized: {output_dir}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    run_id = args.run_id
    try:
        if not run_id.strip():
            raise ValueError("run_id must be non-empty")

        frozen_policy = ConfirmationPolicy.frozen()
        verified_policy = verify_calibration_provenance(
            _repository_root() / CALIBRATION_SOURCE
        )
        if verified_policy != frozen_policy:
            raise ValueError("calibration provenance did not return the frozen confirmation policy")

        _require_empty_output_directory(args.output_dir)
        records = run_confirmation(args.output_dir, run_id, frozen_policy, ConfirmationConfig())
        memo_path = write_confirmation_report(records, args.output_dir, run_id, frozen_policy)
    except (FileExistsError, OSError, ValueError) as error:
        print(f"CONFIRMATION REFUSED [{run_id or '<missing>'}]: {error}", file=sys.stderr)
        return 2

    manifest = json.loads((args.output_dir / "manifest.json").read_text(encoding="utf-8"))
    print(
        f"CONFIRMATION OUTCOME [{run_id}]: {manifest['terminal_outcome']}; wrote {len(records)} confirmation "
        f"records and {memo_path.name} to {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
