# redana
Residual Dependence Annotation for Networks

## Gate 0 CLI lifecycle

Run the smoke and substantive phases against the same empty artifact directory. `--run-id`
is optional: smoke generates a UTC run ID when it is omitted, and substantive mode recovers
that exact persisted ID from `run_state.json` in `--output-dir`. Supplying `--run-id` remains
supported and must match the smoke artifact identity. The runner rejects an initialized smoke
directory or a second substantive run, preserving immutable artifacts.

```powershell
python scripts/run_gate0.py --mode smoke --output-dir artifacts/gate0/my-run
python scripts/run_gate0.py --mode substantive --output-dir artifacts/gate0/my-run
```
