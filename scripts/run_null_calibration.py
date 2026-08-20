"""Run the immutable null-calibration diagnostic and retain its evidence."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from research.gate0.calibration import CalibrationConfig, run_calibration
from research.gate0.calibration_report import diagnostic_outcome, write_calibration_report


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the frozen null-calibration diagnostic.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    return parser.parse_args(argv)


def _require_empty_output_directory(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"run directory is already initialized: {output_dir}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    run_id = args.run_id
    try:
        if not run_id.strip():
            raise ValueError("run_id must be non-empty")
        _require_empty_output_directory(args.output_dir)
        records = run_calibration(args.output_dir, run_id, CalibrationConfig())
        memo_path = write_calibration_report(records, args.output_dir)
    except (FileExistsError, OSError, ValueError) as error:
        print(f"CALIBRATION REFUSED [{run_id or '<missing>'}]: {error}", file=sys.stderr)
        return 2

    outcome = diagnostic_outcome(records)
    print(
        f"DIAGNOSTIC OUTCOME [{run_id}]: {outcome}; wrote {len(records)} calibration records "
        f"and {memo_path.name} to {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
