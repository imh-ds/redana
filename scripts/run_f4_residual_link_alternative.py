"""Run the one immutable F4 residual-link alternative study."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research.gate0.batch_null_report import _verified_calibration
from research.gate0.f4_link_policy import F4LinkConfig
from research.gate0.f4_link_report import _verified_f4_null, write_f4_link_report
from research.gate0.f4_link_runner import run_f4_link

_F4_NULL_DIR = Path("artifacts") / "batch-f4-linear-null-transfer" / "batch-f4-linear-null-transfer-20260822-001"
_CALIBRATION_DIR = Path("artifacts") / "batch-null-calibration" / "batch-null-calibration-20260821-001"
_FROZEN_BOUNDARY = 0.058242447845091264
_FROZEN_F4_NULL_HASHES = {
    "manifest_sha256": "c96ac45595af6eb2ecefbce1531ed84c5435e4b187f5073d36360ad659b0a44c",
    "records_sha256": "de6324eda4fc9897e7a5320b49c20f939042751d4339889d9d72f3b4ab06bca5",
    "manifest_input_sha256": "ff808366d2a9b6b2397f9f86aecf57b71d1005c54241714fe87ae4e245b0008a",
}
_FROZEN_CALIBRATION_HASHES = {
    "manifest_sha256": "639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef",
    "records_sha256": "267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5",
    "manifest_input_sha256": "7737bf6b9f57ed0072843df8dd639e603dee3ebb2a9ad85b7d9d22703279ce9c",
}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the frozen F4 residual-link alternative.")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    return parser.parse_args(argv)


def _verify_frozen_parents() -> None:
    f4_null = _verified_f4_null(_F4_NULL_DIR)
    calibration = _verified_calibration(_CALIBRATION_DIR)
    _verify_hashes(f4_null, _FROZEN_F4_NULL_HASHES, "F4-null")
    _verify_hashes(calibration, _FROZEN_CALIBRATION_HASHES, "calibration")
    selection = calibration.get("selection")
    if not isinstance(selection, dict) or selection.get("boundary") != _FROZEN_BOUNDARY:
        raise ValueError("calibration selection does not match the frozen detection boundary")


def _verify_hashes(actual: dict[str, object], expected: dict[str, str], label: str) -> None:
    for key, value in expected.items():
        if actual.get(key) != value:
            raise ValueError(f"{label} {key} does not match frozen provenance")


def main(argv: list[str] | None = None) -> int:
    """Verify frozen provenance, execute once, and report the retained outcome."""

    args = _parse_args(argv)
    run_id = args.run_id
    try:
        if not run_id.strip():
            raise ValueError("run_id must be non-empty")
        _verify_frozen_parents()
        config = F4LinkConfig()
        records = run_f4_link(args.output_dir, run_id, config)
        memo_path = write_f4_link_report(
            records, args.output_dir, run_id, _F4_NULL_DIR, _CALIBRATION_DIR, config
        )
        outcome = json.loads((args.output_dir / "manifest.json").read_text(encoding="utf-8"))["terminal_outcome"]
    except (FileExistsError, OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"F4 RESIDUAL-LINK ALTERNATIVE REFUSED [{run_id or '<missing>'}]: {error}", file=sys.stderr)
        return 2
    print(
        f"F4 RESIDUAL-LINK ALTERNATIVE [{run_id}]: {outcome}; wrote {len(records)} records "
        f"and {memo_path.name} to {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
