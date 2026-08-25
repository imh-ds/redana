"""Run the one immutable F5 quadratic-residual-link alternative study."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research.gate0.batch_null_report import _verified_calibration
from research.gate0.f4_link_policy import F4LinkConfig
from research.gate0.f5_quadratic_link_report import (
    _verified_f5_quadratic_repair,
    write_f5_quadratic_link_report,
)
from research.gate0.f5_quadratic_link_runner import run_f5_quadratic_link

_CALIBRATION_DIR = Path("artifacts") / "batch-null-calibration" / "batch-null-calibration-20260821-001"
_F5_QUADRATIC_REPAIR_DIR = (
    Path("artifacts") / "batch-f5-quadratic-repair" / "batch-f5-quadratic-repair-20260824-001"
)
_FROZEN_BOUNDARY = 0.058242447845091264
_FROZEN_CALIBRATION_HASHES = {
    "manifest_sha256": "639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef",
    "records_sha256": "267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5",
    "manifest_input_sha256": "7737bf6b9f57ed0072843df8dd639e603dee3ebb2a9ad85b7d9d22703279ce9c",
}
_FROZEN_F5_QUADRATIC_REPAIR_HASHES = {
    "manifest_sha256": "9f45b9c0c80b050fe6e8fd6353b79ed45b1f3076b7e5b07140890f925ed098a7",
    "records_sha256": "f4fbf588fdd66198fcbce18fdb0031f41e4d42787922bfa4cdd1f4a745277836",
    "manifest_input_sha256": "6da7a9684409b2091aa3eb21534df0900336cfdb8b3ce5541a4d9f5c39153e30",
}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the frozen F5 quadratic-residual-link alternative."
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    return parser.parse_args(argv)


def _verify_hashes(actual: dict[str, object], expected: dict[str, str], label: str) -> None:
    for key, value in expected.items():
        if actual.get(key) != value:
            raise ValueError(f"{label} {key} does not match frozen provenance")


def _verify_frozen_parents() -> None:
    """Refuse altered parents before the runner initializes an output directory."""

    calibration = _verified_calibration(_CALIBRATION_DIR)
    _verify_hashes(calibration, _FROZEN_CALIBRATION_HASHES, "calibration")
    selection = calibration.get("selection")
    if not isinstance(selection, dict) or selection.get("boundary") != _FROZEN_BOUNDARY:
        raise ValueError("calibration selection does not match the frozen detection boundary")
    f5_quadratic_repair = _verified_f5_quadratic_repair(_F5_QUADRATIC_REPAIR_DIR)
    _verify_hashes(f5_quadratic_repair, _FROZEN_F5_QUADRATIC_REPAIR_HASHES, "F5 quadratic-repair")


def main(argv: list[str] | None = None) -> int:
    """Verify frozen provenance, execute once, and report the retained outcome."""

    args = _parse_args(argv)
    run_id = args.run_id
    try:
        if not run_id.strip():
            raise ValueError("run_id must be non-empty")
        _verify_frozen_parents()
        config = F4LinkConfig()
        records = run_f5_quadratic_link(args.output_dir, run_id, config)
        memo_path = write_f5_quadratic_link_report(
            records, args.output_dir, run_id, _F5_QUADRATIC_REPAIR_DIR, _CALIBRATION_DIR, config
        )
        outcome = json.loads(
            (args.output_dir / "manifest.json").read_text(encoding="utf-8")
        )["terminal_outcome"]
    except (FileExistsError, OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(
            f"F5 QUADRATIC RESIDUAL LINK REFUSED [{run_id or '<missing>'}]: {error}",
            file=sys.stderr,
        )
        return 2
    print(
        f"F5 QUADRATIC RESIDUAL LINK [{run_id}]: {outcome}; wrote {len(records)} records "
        f"and {memo_path.name} to {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
