"""Run the one immutable F5 explicit-quadratic repair study."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research.gate0.f5_quadratic_repair_report import (
    _verified_f5_stop,
    _verified_frozen_calibration,
    write_f5_quadratic_repair_report,
)
from research.gate0.f5_quadratic_repair_runner import (
    F5QuadraticRepairConfig,
    run_f5_quadratic_repair,
)

_CALIBRATION_DIR = (
    Path("artifacts") / "batch-null-calibration" / "batch-null-calibration-20260821-001"
)
_F5_STOP_DIR = (
    Path("artifacts") / "batch-f5-null-transfer" / "batch-f5-null-transfer-20260821-001"
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the frozen F5 quadratic repair.")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    return parser.parse_args(argv)


def _verify_frozen_parents() -> None:
    """Refuse altered parents before the runner initializes an output directory."""

    _verified_frozen_calibration(_CALIBRATION_DIR)
    _verified_f5_stop(_F5_STOP_DIR)


def main(argv: list[str] | None = None) -> int:
    """Verify frozen provenance, execute once, and retain the terminal outcome."""

    args = _parse_args(argv)
    run_id = args.run_id
    try:
        if not run_id.strip():
            raise ValueError("run_id must be non-empty")
        _verify_frozen_parents()
        config = F5QuadraticRepairConfig()
        records = run_f5_quadratic_repair(args.output_dir, run_id, config)
        memo_path = write_f5_quadratic_repair_report(
            records,
            args.output_dir,
            run_id,
            _CALIBRATION_DIR,
            _F5_STOP_DIR,
            config,
        )
        manifest = json.loads(
            (args.output_dir / "manifest.json").read_text(encoding="utf-8")
        )
        outcome = manifest["terminal_outcome"]
    except (
        FileExistsError,
        OSError,
        TypeError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ) as error:
        print(f"F5 QUADRATIC REPAIR REFUSED [{run_id or '<missing>'}]: {error}", file=sys.stderr)
        return 2

    print(
        f"F5 QUADRATIC REPAIR [{run_id}]: {outcome}; wrote {len(records)} F5 records "
        f"and {memo_path.name} to {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
