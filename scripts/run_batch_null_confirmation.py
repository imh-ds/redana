"""Run the immutable, independent batch-level null confirmation half."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research.gate0.batch_null_policy import BatchNullConfig
from research.gate0.batch_null_report import _verified_calibration, write_confirmation_report
from research.gate0.batch_null_runner import run_batch_phase

_CALIBRATION_ARTIFACT_ROOT = Path("artifacts") / "batch-null-calibration"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the frozen batch-level null confirmation.")
    parser.add_argument("--calibration-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    return parser.parse_args(argv)


def _require_calibration_artifact_root(calibration_dir: Path) -> None:
    root = _CALIBRATION_ARTIFACT_ROOT.resolve()
    try:
        calibration_dir.resolve().relative_to(root)
    except ValueError as error:
        raise ValueError(f"calibration_dir must be inside {root}") from error


def main(argv: list[str] | None = None) -> int:
    """Verify READY calibration provenance before creating independent confirmation evidence."""

    args = _parse_args(argv)
    run_id = args.run_id
    try:
        if not run_id.strip():
            raise ValueError("run_id must be non-empty")
        _require_calibration_artifact_root(args.calibration_dir)
        _verified_calibration(args.calibration_dir)
        config = BatchNullConfig()
        records = run_batch_phase("confirmation", args.output_dir, run_id, config)
        memo_path = write_confirmation_report(
            records, args.output_dir, run_id, args.calibration_dir, config
        )
        outcome = json.loads((args.output_dir / "manifest.json").read_text(encoding="utf-8"))["terminal_outcome"]
    except (FileExistsError, OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"BATCH NULL CONFIRMATION REFUSED [{run_id or '<missing>'}]: {error}", file=sys.stderr)
        return 2

    print(
        f"BATCH NULL CONFIRMATION [{run_id}]: {outcome}; wrote {len(records)} reference records "
        f"and {memo_path.name} to {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
