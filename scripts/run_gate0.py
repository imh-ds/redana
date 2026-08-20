"""Command-line entry point for the disposable Gate 0 research run."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from research.gate0.runner import run_gate0


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the disposable Gate 0 simulation.")
    parser.add_argument("--mode", choices=("smoke", "substantive"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--run-id",
        default=None,
        help=(
            "Run identity. Optional for smoke; substantive mode recovers the persisted "
            "smoke run ID from --output-dir when omitted."
        ),
    )
    return parser.parse_args(argv)


def _recover_smoke_run_id(output_dir: Path) -> str:
    """Return the persisted smoke identity without changing an artifact directory."""

    state_path = output_dir / "run_state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise FileNotFoundError(
            "substantive mode without --run-id requires run_state.json from a prior smoke run"
        ) from error
    except json.JSONDecodeError as error:
        raise ValueError("run_state.json is invalid; supply a valid persisted smoke run") from error
    run_id = state.get("run_id") if isinstance(state, dict) else None
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_state.json does not contain a non-empty persisted smoke run_id")
    return run_id


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    run_id = args.run_id or ("<recovered>" if args.mode == "substantive" else "<generated>")
    try:
        run_id = args.run_id or (
            _recover_smoke_run_id(args.output_dir)
            if args.mode == "substantive"
            else datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        )
        records = run_gate0(args.mode, args.output_dir, run_id=run_id)
    except (FileNotFoundError, FileExistsError, TypeError, ValueError) as error:
        print(f"RUN REFUSED [{run_id}]: {error}", file=sys.stderr)
        return 2

    if records["gate_result"].eq("STOP").any():
        stop_kind = "COMPUTATIONAL" if args.mode == "smoke" else "SCIENTIFIC"
        print(f"{stop_kind} STOP [{run_id}]: see gate-memo.md", file=sys.stderr)
        return 2
    print(f"READY [{run_id}]: wrote {len(records)} pair records to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
