# Batch-level null confirmation evidence

Run ID: `batch-null-confirmation-20260821-001`
Terminal outcome: **PASS**

This immutable, reference-only confirmation contains 100 fresh batches of 10
independent standard-normal reference replications (1,000 retained records), each
using 1,000 evaluation rows and 199 permutations. It ran from source revision
`7861cdb80615d7ca0cd2e91af332e2f581334076` using the distinct
`batch-null-confirmation` seed namespace.

## Frozen calibration provenance

- Calibration evidence: [pointer](batch-null-calibration-batch-null-calibration-20260821-001.md)
- Calibration manifest SHA-256: `639573ec49dc0d19ff64c056380f30f6717d12c79479c4a0b552423775f28cef`.
- Calibration records SHA-256: `267af397026e59c7169b393b648ed8bf1023f2f6a6f9f8ed18de55aa0589e7a5`.
- Copied inclusive median-dCor boundary: `0.058242447845091264`.

The confirmation did not recompute or alter this selection.

## Confirmation check

- Complete reference replications: 1,000 of 1,000.
- Null-like batches: 91 of 100 (PASS requires at least 85).
- Low permutation p-values: 55 of 1,000 (PASS allows at most 67).
- Warnings and exceptions: none.

## Retained artifacts

- [Manifest](../../artifacts/batch-null-confirmation/batch-null-confirmation-20260821-001/manifest.json)
- [Runner input manifest](../../artifacts/batch-null-confirmation/batch-null-confirmation-20260821-001/manifest-input.json)
- [Records](../../artifacts/batch-null-confirmation/batch-null-confirmation-20260821-001/records.csv)
- [Batch summary](../../artifacts/batch-null-confirmation/batch-null-confirmation-20260821-001/confirmation-summary.csv)
- [Owner memo](../../artifacts/batch-null-confirmation/batch-null-confirmation-20260821-001/confirmation-memo.md)
- [Batch-classification plot](../../artifacts/batch-null-confirmation/batch-null-confirmation-20260821-001/plots/batch-classifications.png)
- [Completion state](../../artifacts/batch-null-confirmation/batch-null-confirmation-20260821-001/run_state.json)

The confirmation manifest pins `records.csv` as
`65ed76023aa93931a814a4bf3650a0f16d8df481f4fefceff99a6b1e895edf62` and
`manifest-input.json` as
`ff688aa80bbc54b5c8439725e08ee99fb479eda8dd105a360691bc51956a459d`.

This PASS validates the precommitted reference-only batch rule for the stated
1,000-row workflow. It does not authorize F1--F8, residualization, recalibration,
estimator redesign, a new simulation family, or package work; owner decision is
required before any successor work.
