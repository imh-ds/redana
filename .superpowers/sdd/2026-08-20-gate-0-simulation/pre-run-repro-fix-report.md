# Pre-run reproducibility fixes

Date: 2026-08-20

## Scope

Implemented only the two authorized pre-run reproducibility fixes. No smoke command, substantive simulation, or generated Gate 0 evidence artifact was run or created.

## Frozen protocol artifacts

`manifest.json` now includes the exact F1-F8 data-generating equations, target and null-control pairs, expected classes, post-generation sample centering/population-standard-deviation scaling, identity-based SHA-256 seed derivation, the empirical permutation p-value formula, pair thresholds, and PASS/STOP/NARROW fixture gates. It continues to include the selected profile, adjustment-model configuration, dependency versions, and source revision.

`gate-memo.md` renders the same complete protocol, including a fixture table and explicit threshold section, so it can be interpreted without source-code lookup.

## CLI lifecycle

With no `--run-id`, smoke still creates a UTC identity. A following substantive invocation against the same output directory now reads the persisted identity from `run_state.json`; it only reads that artifact and leaves the existing immutable lifecycle checks in the runner intact. A missing or malformed persisted state produces a clean refusal. README and CLI help document this behavior.

## Verification

- Focused TDD red: the new protocol and CLI-recovery tests failed for the missing behavior.
- Focused green: `14 passed` across the CLI and report test modules using `.venv`.
- Full suite: `30 passed` using `.venv`.
- Ruff: `.venv\\Scripts\\python.exe -m ruff check research tests scripts` completed with `All checks passed!`.

## Review round 2: reproducibility and gate-semantics correction

The frozen protocol in both `manifest.json` and `gate-memo.md` now specifies the exact identity-based seed schedule: SHA-256 of a UTF-8 pipe join, first eight digest bytes interpreted as an unsigned big-endian integer, and independence from execution order. It distinguishes the shared fixture-dataset seed (without pair identity), pair-role residual/evaluation/permutation seeds, the fixture generator's nested rehash, permutation-child rehashing, and the 32-bit projection supplied to scikit-learn `KFold`.

The published gate language now matches runtime behavior: STOP covers every expected target-class mismatch (including F7's collider target), every non-null control, exceptions, and malformed or incomplete matrices; NARROW is reserved for remaining ambiguity; PASS requires the exact expected matrix.

Verification for this correction:

- TDD red: `tests\\gate0\\test_report.py` failed on the missing complete seed schedule in the frozen protocol.
- Focused green: `11 passed` via `.venv\\Scripts\\python.exe -m pytest tests\\gate0\\test_report.py -q`.
- Full suite: `31 passed` via `.venv\\Scripts\\python.exe -m pytest -q`.
- Ruff: `.venv\\Scripts\\python.exe -m ruff check research tests scripts` completed with `All checks passed!`.
