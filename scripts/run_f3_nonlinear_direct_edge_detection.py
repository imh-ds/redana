"""Run the one immutable F3 nonlinear direct-edge detection study."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research.gate0.batch_null_report import _verified_calibration
from research.gate0.f3_nonlinear_direct_edge_detection_report import (
    write_f3_nonlinear_direct_edge_detection_report,
)
from research.gate0.f3_nonlinear_direct_edge_detection_runner import (
    run_f3_nonlinear_direct_edge_detection,
)
from research.gate0.f4_link_policy import F4LinkConfig

_CALIBRATION_DIR = Path("artifacts") / "batch-null-calibration" / "batch-null-calibration-20260821-001"
_FROZEN_BOUNDARY = 0.058242447845091264
_FROZEN_HASHES = {
    "manifest_sha256": "639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef",
    "records_sha256": "267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5",
    "manifest_input_sha256": "7737bf6b9f57ed0072843df8dd639e603dee3ebb2a9ad85b7d9d22703279ce9c",
}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the frozen F3 nonlinear direct-edge detection study."
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    return parser.parse_args(argv)


def _verify_frozen_calibration() -> None:
    calibration = _verified_calibration(_CALIBRATION_DIR)
    selection = calibration.get("selection")
    if not isinstance(selection, dict) or selection.get("boundary") != _FROZEN_BOUNDARY:
        raise ValueError("calibration selection does not match the frozen F3 boundary")
    for key, expected in _FROZEN_HASHES.items():
        if calibration.get(key) != expected:
            raise ValueError(f"calibration {key} does not match frozen F3 provenance")


def main(argv: list[str] | None = None) -> int:
    """Verify frozen provenance, execute once, and report the retained terminal outcome."""

    args = _parse_args(argv)
    run_id = args.run_id
    try:
        if not run_id.strip():
            raise ValueError("run_id must be non-empty")
        _verify_frozen_calibration()
        config = F4LinkConfig()
        records = run_f3_nonlinear_direct_edge_detection(args.output_dir, run_id, config)
        memo_path = write_f3_nonlinear_direct_edge_detection_report(
            records, args.output_dir, run_id, _CALIBRATION_DIR, config
        )
        outcome = json.loads((args.output_dir / "manifest.json").read_text(encoding="utf-8"))["terminal_outcome"]
    except (FileExistsError, OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"F3 NONLINEAR DIRECT-EDGE DETECTION REFUSED [{run_id or '<missing>'}]: {error}", file=sys.stderr)
        return 2

    print(
        f"F3 NONLINEAR DIRECT-EDGE DETECTION [{run_id}]: {outcome}; wrote {len(records)} records "
        f"and {memo_path.name} to {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
