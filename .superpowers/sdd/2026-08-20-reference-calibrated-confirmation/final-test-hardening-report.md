# Final test hardening report

Date: 2026-08-21
Worktree: `C:\\Users\\imhoh\\GitHub\\redana\\.worktrees\\gate0-simulation`

## Scope

This final wave is limited to direct regression coverage requested by review. No
production runner semantics, policy, artifact layout, evidence commits,
boundary, or outcomes were changed.

## Files changed

- `tests/gate0/test_confirmation_runner.py`
  - Added direct assertions for the production `ConfirmationConfig()` defaults:
    30 reference replications, 10 fixture replications, 50,000 source rows,
    1,000 evaluation rows, and 199 permutations.
  - Added manifest assertions for calibration source path, calibration SHA-256,
    matrix counts, seed namespace, run ID, and source revision.
  - Added a reference-only isolation regression. It monkeypatches fixture
    generation and cross-fitted residualization to raise, then invokes the
    narrowly exposed `_run_reference_cell` unit and verifies independent normal
    draws plus the production permutation metric still produce a successful
    reference record and null-statistics artifact.

- `.superpowers/sdd/2026-08-20-reference-calibrated-confirmation/final-test-hardening-report.md`
  - This report.

## Verification

- Focused new checks:
  - Command: `.venv\\Scripts\\python.exe -m pytest -q --basetemp .pytest-final-test-hardening-red tests/gate0/test_confirmation_runner.py -k "config_defaults or manifest_records or reference_cell_isolated"`
  - Result: `3 passed, 8 deselected in 9.66s`
- Full confirmation-runner module:
  - Command: `.venv\\Scripts\\python.exe -m pytest -q --basetemp .pytest-final-test-hardening-focused tests/gate0/test_confirmation_runner.py`
  - Result: `11 passed in 191.58s (0:03:11)`
- Full test suite:
  - Command: `.venv\\Scripts\\python.exe -m pytest -q --basetemp .pytest-final-test-hardening-full`
  - Result: `83 passed in 213.27s (0:03:33)`
- Ruff:
  - Command: `.venv\\Scripts\\ruff.exe check research tests scripts`
  - Result: `All checks passed!`
- Patch hygiene:
  - `git diff --check` completed without whitespace errors.

The first focused invocation without `--basetemp` was blocked during pytest
fixture setup by the host's permission error scanning
`C:\\Users\\imhoh\\AppData\\Local\\Temp\\pytest-of-imhoh`; rerunning with
an in-worktree base directory passed. This is an environment limitation, not a
test failure.

## Self-review

- The defaults test reads the production dataclass directly and checks every
  requested matrix dimension, including the values inherited from the full
  computational profile.
- The manifest test exercises `run_confirmation` and reads the emitted JSON,
  so it validates persisted provenance rather than only constants in memory.
- The isolation test patches both fixture-related call sites named in review
  and executes the reference-only unit directly. It asserts successful metric
  output and artifact retention, making an accidental fixture/residual path
  invocation fail loudly.
- Assertions are intentionally limited to requested behavior; no production
  code or runner interface was broadened for testability.

## Concerns

- The reference isolation test uses the existing private `_run_reference_cell`
  helper as the narrowly exposed testable unit. No additional production
  testability surface was necessary.
- The full suite and module run include the existing default CLI matrix and
  therefore take several minutes, but both completed successfully.
