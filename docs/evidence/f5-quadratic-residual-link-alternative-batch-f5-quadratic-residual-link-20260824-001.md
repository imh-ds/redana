# F5 quadratic-residual-link alternative evidence

## Frozen identity and one official execution

- Run ID: `batch-f5-quadratic-residual-link-20260824-001`
- Output: `artifacts/batch-f5-quadratic-residual-link/batch-f5-quadratic-residual-link-20260824-001`
- Source revision: `9ca2c91d6b2cd5a9edd8921a12f91801009829f8`
- Task 3 CLI source present at launch: yes (`9ca2c91d6b2cd5a9edd8921a12f91801009829f8`)
- Output before launch: absent; zero entries
- Official launch count: exactly one; no retry
- Interpreter: `C:\tmp\scova-v4-test\Scripts\python.exe` (Python 3.12.13)
- Dependency path: `PYTHONPATH=C:\tmp\redana-batch-test-deps;.`
- Ended (retained file timestamps): `records.csv` `2026-08-24T21:52:48.85-07:00`;
  `manifest.json` `2026-08-24T21:52:49.78-07:00`
- Sum of per-record `elapsed_seconds` (fixture generation, quadratic residualization,
  and permutation dCor across all 1,000 cells): `182.297` seconds
- Exit code: `0`

Exact launch:

```bash
PYTHONPATH="C:\tmp\redana-batch-test-deps;." "/c/tmp/scova-v4-test/Scripts/python.exe" \
  scripts/run_f5_quadratic_residual_link_alternative.py \
  --output-dir artifacts/batch-f5-quadratic-residual-link/batch-f5-quadratic-residual-link-20260824-001 \
  --run-id batch-f5-quadratic-residual-link-20260824-001
```

Exact terminal output:

```text
F5 QUADRATIC RESIDUAL LINK [batch-f5-quadratic-residual-link-20260824-001]: PASS; wrote 1000 records and f5-quadratic-link-memo.md to artifacts\batch-f5-quadratic-residual-link\batch-f5-quadratic-residual-link-20260824-001
```

Preflight before launch: focused Task 1/2/3 test suites and the full
`tests/gate0` suite (249 tests) all passed with the same interpreter and
`PYTHONPATH`, and `ruff check research tests scripts` reported all checks
passed. The official output directory was confirmed absent immediately
before launch.

## Independent raw recomputation

A separate verifier script did not import `research.gate0.f5_quadratic_link_runner`,
`research.gate0.f5_quadratic_link_report`, or `research.gate0.f4_link_policy`. It:

1. parsed `records.csv`, `manifest.json`, `manifest-input.json`, `run_state.json`,
   and the 100-row batch summary directly;
2. re-derived each expected unsigned fixture, residual, and permutation seed from
   the first eight bytes of SHA-256 over the frozen identity string
   (`batch-f5-quadratic-residual-link|{batch}|{replication}|{component}`);
3. opened every one of the 1,000 residual CSVs, required columns `X1,X2`, exactly
   1,000 rows, and finite values, then recomputed distance correlation directly
   with the `dcor` package;
4. loaded every one of the 1,000 `.npy` null arrays with pickle disabled, required
   shape `(199,)` and finite values, then independently recomputed all 199
   permutation values and the empirical p-value `(1 + count(null >= observed)) / 200`;
5. computed SHA-256 directly from the current run's files and from both pinned
   parent evidence sets; and
6. grouped raw record values by batch, took the ordinary median of each 10 dCor
   values, applied the `>=8/10` p-value guard, the strict `>` copied dCor
   boundary, and the frozen PASS/NARROW/STOP precedence.

Raw completeness and recomputation results:

- Records: 1,000; unique `(batch, replication)` identities: 1,000; exact grid: yes;
  duplicate identities: none.
- Frozen record identity (`F5-quadratic-residual-link`, `X1`, `X2`,
  `f5-quadratic-residual-link`, run ID, seed namespace): exact for all 1,000 records.
- Fixture/residual/permutation seeds: zero SHA-256 identity-derivation mismatches
  across all 3,000 seed values.
- Residual evidence: 1,000 files; every file has two columns, 1,000 rows, and only
  finite values; zero shape or finiteness failures.
- Permutation evidence: 1,000 files; every array has 199 finite values; zero shape
  or finiteness failures.
- Observed dCor: zero recomputation mismatches against the retained
  `observed_statistic` values.
- Empirical p-values and null arrays: zero recomputation mismatches (permutation
  arrays and derived p-values match retained evidence exactly).
- Record warnings: zero; verbatim warning texts: `[]`.
- Record exceptions: zero; verbatim exception texts: `[]`.

Current-run SHA-256 values (independently computed; match the embedded manifest):

- `records.csv`: `514ce6073d2010654d1ebe4fa9d501d2b0aab570b3b4e3f9ee6aa72faae75e83`
- `manifest-input.json`: `78ba4262fcd8dbdb06aa26c6a7ceb6d882cac6b1a9cd12a56f9ba038ad84f745`

Directly recomputed raw-calibration parent SHA-256 values (match both the pinned
`_CALIBRATION_HASHES` in `research/gate0/f5_quadratic_link_report.py` and the
manifest's embedded `calibration` block):

- `records.csv`: `267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5`
- `manifest-input.json`: `7737bf6b9f57ed0072843df8dd639e603dee3ebb2a9ad85b7d9d22703279ce9c`
- `manifest.json`: `639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`

Directly recomputed F5 quadratic-repair PASS parent SHA-256 values (match both the
pinned `_F5_QUADRATIC_REPAIR_HASHES` and the manifest's embedded
`f5_quadratic_repair` block):

- `records.csv`: `f4fbf588fdd66198fcbce18fdb0031f41e4d42787922bfa4cdd1f4a745277836`
- `manifest-input.json`: `6da7a9684409b2091aa3eb21534df0900336cfdb8b3ce5541a4d9f5c39153e30`
- `manifest.json`: `9f45b9c0c80b050fe6e8fd6353b79ed45b1f3076b7e5b07140890f925ed098a7`
- Parent `terminal_outcome`: `PASS`; `confirmation_check`:
  `null_like_batch_count=90`, `low_p_value_count=44` (matches the frozen pin
  exactly).

## Batch recomputation

Copied inclusive dCor boundary: `0.058242447845091264`. A batch is detected when
its median dCor is strictly above this boundary and at least 8 of its 10
p-values are at or below `0.05`.

Every one of the 100 batches was detected. Summary statistics across batches
(independently recomputed from `f5-quadratic-link-summary.csv` and raw records):

| Quantity | Value |
| --- | --- |
| Detected batches | 100 of 100 (requires >= 85) |
| Batches with `complete = True` | 100 of 100 |
| Median dCor across batches — min / mean / max | 0.3054 / 0.3207 / 0.3396 |
| Low p-value count per batch (`<= 0.05` of 10) — min / max | 10 / 10 |
| Total low p-values across all 1,000 records | 1,000 of 1,000 |

The detected median dCor (~0.31–0.34) sits roughly five to six times above the
copied boundary (`0.058`), and every one of the 1,000 permutation p-values
individually cleared `<= 0.05` — a saturated, unambiguous detection with no
borderline batches, consistent with the deliberately clear (`0.7`-coefficient,
not tuned) planted signal the design specified.

## Terminal decision and governance

Independent terminal outcome: **PASS**.

The evidence is complete, has no retained warning or exception, and has 100
detected batches (at least 85 required). The retained manifest and run state
also report `PASS` and match the independently recomputed values exactly.

This PASS supports only that the raw-plus-square repair basis, already shown to
repair the F5 quadratic common-cause null, also detects one planted nonlinear
(zero-linear-covariance) residual dependence layered on that same common cause,
under this frozen 1,000-row procedure. It does not establish general nonlinear
robustness, other nonlinear shapes, weaker effect sizes, real-data readiness, or
package readiness.

It may authorize only a later, separate owner decision about whether to
document or implement this one matched pair of findings (F5 quadratic-repair
PASS + F5 quadratic-residual-link PASS). It does not authorize tuning,
recalibration, changed seeds, interactions, a basis search, a new simulation
family, or package work.
