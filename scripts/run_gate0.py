"""Command-line entry point for the disposable Gate 0 research run."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from research.gate0.runner import run_gate0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the disposable Gate 0 simulation.")
    parser.add_argument("--mode", choices=("smoke", "substantive"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", default=None)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    run_id = args.run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    try:
        records = run_gate0(args.mode, args.output_dir)
    except (FileNotFoundError, ValueError) as error:
        print(f"STOP [{run_id}]: {error}", file=sys.stderr)
        return 2

    if records["gate_result"].eq("STOP").any() or (
        args.mode == "smoke" and not (args.output_dir / "selected_profile.json").exists()
    ):
        print(f"STOP [{run_id}]: computational smoke gate did not select a profile", file=sys.stderr)
        return 2
    print(f"READY [{run_id}]: wrote {len(records)} pair records to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
