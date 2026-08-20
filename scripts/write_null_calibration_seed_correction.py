"""Write an exact-seed correction sidecar without rerunning a calibration."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import pandas as pd

from research.gate0.calibration import CALIBRATION_FIXTURES
from research.gate0.config import derive_seed

IDENTITY_COLUMNS = ("run_id", "arm", "fixture_id", "replication", "evaluation_rows")
SEED_COLUMNS = (
    "fixture_seed",
    "residual_seed",
    "evaluation_seed",
    "left_seed",
    "right_seed",
    "permutation_seed",
)
SCHEDULE_NAME = "calibration-v1"


def _parse_arguments(arguments: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write an exact-seed correction sidecar from calibration record identities."
    )
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--run-manifest", type=Path)
    return parser.parse_args(arguments)


def _seed_values(
    *, arm: str, fixture_id: str, replication: int, evaluation_rows: int
) -> dict[str, int | None]:
    if arm == "fitted":
        if fixture_id not in CALIBRATION_FIXTURES:
            raise ValueError(f"unsupported fitted fixture: {fixture_id}")
        return {
            "fixture_seed": derive_seed("calibration", "fitted", fixture_id, replication, "fixture"),
            "residual_seed": derive_seed("calibration", "fitted", fixture_id, replication, "residual"),
            "evaluation_seed": derive_seed(
                "calibration", "fitted", fixture_id, replication, "evaluation", evaluation_rows
            ),
            "left_seed": None,
            "right_seed": None,
            "permutation_seed": derive_seed(
                "calibration", "fitted", fixture_id, replication, "permutation", evaluation_rows
            ),
        }
    if arm == "reference":
        if fixture_id != "reference":
            raise ValueError(f"reference rows must use fixture_id='reference', got {fixture_id!r}")
        return {
            "fixture_seed": None,
            "residual_seed": None,
            "evaluation_seed": None,
            "left_seed": derive_seed(
                "calibration", "reference", replication, evaluation_rows, "left"
            ),
            "right_seed": derive_seed(
                "calibration", "reference", replication, evaluation_rows, "right"
            ),
            "permutation_seed": derive_seed(
                "calibration", "reference", replication, evaluation_rows, "permutation"
            ),
        }
    raise ValueError(f"unsupported arm: {arm}")


def _exact_seed_rows(records: pd.DataFrame) -> pd.DataFrame:
    missing_columns = set(IDENTITY_COLUMNS).difference(records.columns)
    if missing_columns:
        raise ValueError(f"records are missing identity columns: {sorted(missing_columns)}")

    rows: list[dict[str, object]] = []
    for source_record_index, record in records.loc[:, IDENTITY_COLUMNS].iterrows():
        if record.isna().any():
            raise ValueError(f"record {source_record_index} has an incomplete identity")
        seeds = _seed_values(
            arm=str(record.arm),
            fixture_id=str(record.fixture_id),
            replication=int(record.replication),
            evaluation_rows=int(record.evaluation_rows),
        )
        rows.append(
            {
                "source_record_index": source_record_index,
                **{column: str(record[column]) for column in IDENTITY_COLUMNS},
                **{column: None if value is None else str(value) for column, value in seeds.items()},
            }
        )
    return pd.DataFrame(rows, columns=("source_record_index", *IDENTITY_COLUMNS, *SEED_COLUMNS))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative_path(source: Path, destination: Path) -> str:
    return Path(os.path.relpath(source.resolve(), destination.resolve())).as_posix()


def _initialize_output(output_dir: Path, records_path: Path) -> None:
    if output_dir.resolve().is_relative_to(records_path.resolve().parent):
        raise ValueError("correction output must be outside the immutable artifact directory")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"correction output directory is already initialized: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)


def _write_readme(output_dir: Path, manifest: dict[str, object]) -> None:
    original_records = manifest["original_records_path"]
    original_sha256 = manifest["original_records_sha256"]
    schedule = manifest["schedule"]
    source_revision = manifest["source_revision"]
    (output_dir / "README.md").write_text(
        "# Exact seed correction sidecar\n\n"
        "This versioned sidecar corrects only the seed audit trail for the linked immutable "
        "calibration records. It was derived from each retained row identity and the frozen "
        "deterministic schedule; it did not rerun a simulation or change a numerical result, "
        "classification, or outcome.\n\n"
        f"- Original records: [{original_records}]({original_records})\n"
        f"- Original records SHA-256: `{original_sha256}`\n"
        f"- Seed schedule: `{schedule}`\n"
        f"- Frozen run source revision: `{source_revision}`\n"
        "- Exact values: `exact-seeds.csv` (read seed columns as strings; blank seed cells are null)\n",
        encoding="utf-8",
    )


def main(arguments: list[str] | None = None) -> int:
    args = _parse_arguments(arguments)
    records_path = args.records.resolve()
    output_dir = args.output_dir.resolve()
    if not args.version.strip():
        raise ValueError("version must be non-empty")
    _initialize_output(output_dir, records_path)

    records = pd.read_csv(records_path, dtype="string")
    sidecar = _exact_seed_rows(records)
    sidecar.to_csv(output_dir / "exact-seeds.csv", index=False)

    source_revision = "not supplied"
    run_manifest_path: str | None = None
    run_manifest_sha256: str | None = None
    if args.run_manifest is not None:
        manifest_path = args.run_manifest.resolve()
        source_revision = json.loads(manifest_path.read_text(encoding="utf-8")).get(
            "source_revision", "not supplied"
        )
        run_manifest_path = _relative_path(manifest_path, output_dir)
        run_manifest_sha256 = _sha256(manifest_path)

    manifest: dict[str, object] = {
        "schema": "null-calibration-exact-seed-correction",
        "version": args.version,
        "record_count": len(sidecar),
        "original_records_path": _relative_path(records_path, output_dir),
        "original_records_sha256": _sha256(records_path),
        "original_run_manifest_path": run_manifest_path,
        "original_run_manifest_sha256": run_manifest_sha256,
        "source_revision": source_revision,
        "schedule": SCHEDULE_NAME,
        "schedule_source": {
            "seed_function": "research.gate0.config.derive_seed",
            "fitted": "derive_seed('calibration', 'fitted', fixture_id, replication, purpose, evaluation_rows?)",
            "reference": "derive_seed('calibration', 'reference', replication, evaluation_rows, purpose)",
        },
        "seed_columns": list(SEED_COLUMNS),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_readme(output_dir, manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
