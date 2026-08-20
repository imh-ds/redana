# Final whole-branch review fix report

Date: 2026-08-20

## Findings addressed

- Resource selection now projects both runtime and Python allocation peak from the same smoke measurement for both the full and reduced frozen profiles. Boundary coverage includes exact and just-over time and memory limits.
- A smoke run that cannot select a profile now writes a computational `STOP` `gate-memo.md` with measured and projected resources, the stop reason, one `STOP` outcome, and the required owner-decision sentence. Smoke execution failures receive a distinct, accurate reason. The CLI labels computational and scientific stops separately.
- Substantive `manifest.json` and `gate-memo.md` now retain the run ID, estimand, complete frozen profile/model/fixture procedure, dependency versions, and source revision. The fixture coefficient is a shared frozen constant used by generation and reporting.
- Run IDs now flow from the CLI into records and metadata. A persisted state machine permits only a fresh smoke run followed by one substantive run with the same ID and frozen selected profile. Completed or interrupted run directories cannot be reused. Smoke and substantive records, summaries, null arrays, and residual samples use separate paths so the transition cannot overwrite or mix evidence.

## Regression and verification evidence

- Focused review tests: `19 passed`.
- Full test suite: `27 passed`.
- Ruff: `All checks passed!` for `research`, `tests`, and `scripts`.
- No runtime smoke test or substantive simulation was executed; Task 7 remains owner-controlled.

## Remaining concerns

- Memory feasibility remains a conservative linear projection of the measured per-pair Python allocation peak by source-row ratio. It is explicitly labeled as Python allocation rather than total process memory, matching the frozen protocol.
