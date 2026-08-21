"""Run the immutable, reference-only batch null calibration half."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research.gate0.batch_null_policy import BatchNullConfig
from research.gate0.batch_null_report import write_calibration_report
from research.gate0.batch_null_runner import run_batch_phase


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the frozen batch-level null calibration.")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run calibration once and report its frozen READY or STOP result."""

    args = _parse_args(argv)
    run_id = args.run_id
    try:
        if not run_id.strip():
            raise ValueError("run_id must be non-empty")
        config = BatchNullConfig()
        records = run_batch_phase("calibration", args.output_dir, run_id, config)
        memo_path = write_calibration_report(records, args.output_dir, run_id, config)
        outcome = json.loads((args.output_dir / "manifest.json").read_text(encoding="utf-8"))["terminal_outcome"]
    except (FileExistsError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"BATCH NULL CALIBRATION REFUSED [{run_id or '<missing>'}]: {error}", file=sys.stderr)
        return 2

    print(
        f"BATCH NULL CALIBRATION [{run_id}]: {outcome}; wrote {len(records)} reference records "
        f"and {memo_path.name} to {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
