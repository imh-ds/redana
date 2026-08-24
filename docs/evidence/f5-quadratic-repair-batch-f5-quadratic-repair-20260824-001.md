# F5 explicit-quadratic repair evidence

## Frozen identity and one official execution

- Run ID: `batch-f5-quadratic-repair-20260824-001`
- Output: `artifacts/batch-f5-quadratic-repair/batch-f5-quadratic-repair-20260824-001`
- Source revision: `48217ca03ce7c63e632c6449bdc175a323245f9b`
- Task 3 fix present at launch: yes (`48217ca03ce7c63e632c6449bdc175a323245f9b`)
- Output before launch: absent; zero entries
- Official launch count: exactly one; no retry
- Original planned interpreter: `C:\tmp\redana-batch-python\python.exe` (unavailable)
- Recorded replacement: `C:\tmp\scova-v4-test\Scripts\python.exe` (Python 3.12.13)
- Replacement dependency path: `PYTHONPATH=C:\tmp\redana-batch-test-deps;.`
- Started: `2026-08-24T12:08:06.4794656-07:00`
- Ended: `2026-08-24T12:13:38.2143877-07:00`
- Measured wall time: `331.7349221` seconds
- Exit code: `0`

Exact launch:

```powershell
$env:PYTHONPATH='C:\tmp\redana-batch-test-deps;.'
& 'C:\tmp\scova-v4-test\Scripts\python.exe' scripts/run_f5_quadratic_repair.py --output-dir artifacts/batch-f5-quadratic-repair/batch-f5-quadratic-repair-20260824-001 --run-id batch-f5-quadratic-repair-20260824-001
```

Exact terminal output:

```text
F5 QUADRATIC REPAIR [batch-f5-quadratic-repair-20260824-001]: PASS; wrote 1000 F5 records and f5-quadratic-repair-memo.md to artifacts\batch-f5-quadratic-repair\batch-f5-quadratic-repair-20260824-001
```

The current-source preflight used the same replacement interpreter and dependency
path, plus `PYTEST_ADDOPTS=-p no:cacheprovider`. The focused quadratic suite passed
42 tests in 12.58 seconds, the full suite passed 201 tests in 288.95 seconds, and
`ruff check research tests scripts` reported `All checks passed!`. An initial
sandbox-constrained focused attempt was not accepted as source evidence: the sandbox
could not read the external `dcor` package and imported it as an empty namespace,
causing two runner-test failures. The exact focused command passed after the required
read permission was granted; no source changed and the official run was still at zero.

## Independent raw recomputation

A separate verifier did not import the project runner, report, or policy modules. It:

1. parsed `records.csv`, manifests, run state, and the 100-row summary directly;
2. derived each expected unsigned fixture, residual, and permutation seed from the
   first eight bytes of SHA-256 over the frozen identity string;
3. opened every residual CSV, required columns `X1,X2`, exactly 1,000 rows, and finite
   values, then recomputed distance correlation from those values;
4. loaded every NPY file with pickle disabled, required shape `(199,)` and finite
   values, then recomputed `(1 + count(null >= observed)) / 200`;
5. computed SHA-256 directly from current and parent raw files; and
6. grouped raw record values by batch, took the ordinary median of each ten dCor
   values, applied the at-most-two p-values `<= 0.05` guard, the inclusive copied
   dCor boundary, and the frozen STOP/NARROW/PASS precedence.

Raw completeness results:

- Records: 1,000; unique `(batch, replication)` identities: 1,000; exact grid: yes;
  duplicate identities: none.
- Frozen record identity (`F5`, `X1`, `X2`, `f5-quadratic-repair`, run ID, seed
  namespace): exact for all 1,000 records.
- Fixture/residual/permutation seeds: 1,000 unique values in each column; zero
  SHA-256 identity-derivation mismatches.
- Observed dCor: 1,000 finite values; zero recomputation mismatches.
- Empirical p-values: 1,000 finite values in `[0,1]`; zero NPY-based recomputation
  mismatches.
- Residual evidence: 1,000 unique paths and 1,000 files; every file has two columns,
  1,000 rows, and only finite values; zero failures.
- Permutation evidence: 1,000 unique paths and 1,000 files; every array has 199 finite
  values; zero failures.
- Elapsed values: 1,000 finite, nonnegative values.
- Summary comparison: 100 rows and zero raw-recomputation mismatches.
- Record warnings: zero; verbatim warning texts: `[]`.
- Record exceptions: zero; verbatim exception texts: `[]`.
- Manifest warning text: empty string; manifest exception text: empty string.

Current-run SHA-256 values:

- `records.csv`: `f4fbf588fdd66198fcbce18fdb0031f41e4d42787922bfa4cdd1f4a745277836`
- `manifest-input.json`: `6da7a9684409b2091aa3eb21534df0900336cfdb8b3ce5541a4d9f5c39153e30`
- `manifest.json`: `9f45b9c0c80b050fe6e8fd6353b79ed45b1f3076b7e5b07140890f925ed098a7`
- Embedded current record/input hashes match the directly computed hashes: yes.

Directly recomputed raw-calibration parent SHA-256 values:

- `records.csv`: `267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5`
- `manifest-input.json`: `7737bf6b9f57ed0072843df8dd639e603dee3ebb2a9ad85b7d9d22703279ce9c`
- `manifest.json`: `639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`

Directly recomputed original-F5-STOP parent SHA-256 values:

- `records.csv`: `3f38ac7f324c597cf13b84006cf1af35fbce0fb30b497ef2629b29b79a7fee09`
- `manifest-input.json`: `b16367ef572f906df2653447558e31047e0cda0943d3d774725546f213902251`
- `manifest.json`: `521f35953929d46670eb90687e6a4645684f335d878b90090029c31d87c8dce2`
- Both parent blocks match the directly hashed files and the pinned design values.
- Original F5 comparison remains `STOP`: 74 null-like batches and 81 low p-values.

## Batch recomputation

Copied inclusive dCor boundary: `0.058242447845091264`. A batch is null-like only
when its median is at or below this boundary and at most two of its ten p-values are
at or below `0.05`.

| Batch | Median dCor | Low p-values | p-guard | Null-like |
|---:|---:|---:|:---:|:---:|
| 0 | 0.04891233743267587 | 0 | True | True |
| 1 | 0.0515678142278002 | 0 | True | True |
| 2 | 0.05271097698206061 | 2 | True | True |
| 3 | 0.05014789385899884 | 0 | True | True |
| 4 | 0.046566173642954706 | 0 | True | True |
| 5 | 0.054739173203000854 | 0 | True | True |
| 6 | 0.05586058021764424 | 1 | True | True |
| 7 | 0.052978520717518476 | 1 | True | True |
| 8 | 0.05066202978697966 | 0 | True | True |
| 9 | 0.04884355548678677 | 0 | True | True |
| 10 | 0.05161780065659548 | 0 | True | True |
| 11 | 0.0490110714886692 | 0 | True | True |
| 12 | 0.050761643175005325 | 0 | True | True |
| 13 | 0.053118630296457504 | 0 | True | True |
| 14 | 0.05638210801137526 | 1 | True | True |
| 15 | 0.052144530381461475 | 0 | True | True |
| 16 | 0.05390234356882927 | 0 | True | True |
| 17 | 0.06039047244554762 | 0 | True | False |
| 18 | 0.047167706942210716 | 0 | True | True |
| 19 | 0.05291323358014606 | 1 | True | True |
| 20 | 0.053864682676986894 | 0 | True | True |
| 21 | 0.04816191968919432 | 1 | True | True |
| 22 | 0.05233509577763636 | 0 | True | True |
| 23 | 0.05752819910702113 | 0 | True | True |
| 24 | 0.05246001813975445 | 1 | True | True |
| 25 | 0.050976061064425746 | 0 | True | True |
| 26 | 0.05552732492869032 | 0 | True | True |
| 27 | 0.055381669054921215 | 0 | True | True |
| 28 | 0.04794468636292305 | 0 | True | True |
| 29 | 0.049588949645756664 | 1 | True | True |
| 30 | 0.05377580989555701 | 0 | True | True |
| 31 | 0.05724970584618175 | 0 | True | True |
| 32 | 0.056759716837776746 | 0 | True | True |
| 33 | 0.05353996910361401 | 0 | True | True |
| 34 | 0.05263984508290229 | 0 | True | True |
| 35 | 0.05458818063477294 | 1 | True | True |
| 36 | 0.05639611724476339 | 1 | True | True |
| 37 | 0.051825420211076736 | 1 | True | True |
| 38 | 0.05274369054204167 | 0 | True | True |
| 39 | 0.04907479680145167 | 1 | True | True |
| 40 | 0.04759032623014322 | 1 | True | True |
| 41 | 0.052294058539640045 | 0 | True | True |
| 42 | 0.045682663943523175 | 0 | True | True |
| 43 | 0.058470348961864815 | 2 | True | False |
| 44 | 0.051617177387003804 | 0 | True | True |
| 45 | 0.048365774692661866 | 1 | True | True |
| 46 | 0.054332523400385704 | 2 | True | True |
| 47 | 0.06468369559455131 | 3 | False | False |
| 48 | 0.05388099004963151 | 0 | True | True |
| 49 | 0.0476990190905877 | 1 | True | True |
| 50 | 0.050918690184953874 | 0 | True | True |
| 51 | 0.04954425181736288 | 0 | True | True |
| 52 | 0.05001753890471908 | 0 | True | True |
| 53 | 0.049741321935321645 | 1 | True | True |
| 54 | 0.05040536572082223 | 0 | True | True |
| 55 | 0.05089519983051356 | 0 | True | True |
| 56 | 0.05385436873757814 | 0 | True | True |
| 57 | 0.05378268468131199 | 0 | True | True |
| 58 | 0.05412797517499082 | 0 | True | True |
| 59 | 0.060322196269102034 | 2 | True | False |
| 60 | 0.05883134689400722 | 0 | True | False |
| 61 | 0.058616202089193034 | 1 | True | False |
| 62 | 0.05485438264365735 | 0 | True | True |
| 63 | 0.04995502835690304 | 1 | True | True |
| 64 | 0.05443095093312585 | 0 | True | True |
| 65 | 0.055083027242429444 | 0 | True | True |
| 66 | 0.06252946694873836 | 1 | True | False |
| 67 | 0.05460046139740102 | 0 | True | True |
| 68 | 0.05928303108976912 | 0 | True | False |
| 69 | 0.04617838759676097 | 0 | True | True |
| 70 | 0.05055060685161261 | 0 | True | True |
| 71 | 0.056161114684268126 | 3 | False | False |
| 72 | 0.05401392007384122 | 0 | True | True |
| 73 | 0.049444702563718454 | 1 | True | True |
| 74 | 0.05816812774394198 | 2 | True | True |
| 75 | 0.04616098064055661 | 0 | True | True |
| 76 | 0.04691748690048254 | 0 | True | True |
| 77 | 0.0554390851441608 | 0 | True | True |
| 78 | 0.04724369108517153 | 0 | True | True |
| 79 | 0.05633505245399659 | 1 | True | True |
| 80 | 0.05075379025381885 | 0 | True | True |
| 81 | 0.05032214261057761 | 0 | True | True |
| 82 | 0.05182153056148654 | 0 | True | True |
| 83 | 0.0512005400948856 | 2 | True | True |
| 84 | 0.049326817535321574 | 0 | True | True |
| 85 | 0.05297465778007085 | 0 | True | True |
| 86 | 0.052269896218730474 | 0 | True | True |
| 87 | 0.05401932707807297 | 1 | True | True |
| 88 | 0.044951928766217106 | 0 | True | True |
| 89 | 0.05572142251730908 | 1 | True | True |
| 90 | 0.05017519763301913 | 0 | True | True |
| 91 | 0.051125111865484615 | 0 | True | True |
| 92 | 0.05368554113126968 | 0 | True | True |
| 93 | 0.050796287103218894 | 1 | True | True |
| 94 | 0.05191073916345168 | 0 | True | True |
| 95 | 0.06406031919324166 | 1 | True | False |
| 96 | 0.05194217874630713 | 0 | True | True |
| 97 | 0.04552788823463492 | 1 | True | True |
| 98 | 0.048186878904153956 | 1 | True | True |
| 99 | 0.05696637857853734 | 0 | True | True |

P-value guard summary: 98 of 100 batches pass; only batches 47 and 71 fail, with
three low p-values each. Across all records, 44 p-values are at or below `0.05`,
within the frozen maximum of 67. Exactly 90 batches are null-like, meeting the
minimum of 85.

## Terminal decision and governance

Independent terminal outcome: **PASS**.

The evidence is complete, has no retained exception, has 44 low p-values (not more
than 67), and has 90 null-like batches (at least 85). The retained manifest and run
state also report `PASS` and match the independent values.

This PASS supports only that the explicit raw-plus-square basis repairs the prescribed
F5 quadratic null under the frozen 1,000-row procedure. It may authorize only a
separate owner choice about one matched nonlinear alternative. It does not authorize
tuning, recalibration, changed seeds, interactions, a basis search, package work, or
a general nonlinear-robustness claim.
