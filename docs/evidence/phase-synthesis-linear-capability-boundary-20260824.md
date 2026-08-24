# Phase synthesis: current capability boundary

## Completed evidence

- Raw independent-reference calibration: READY; a finite-sample 1,000-row dCor boundary was selected before transfer studies.
- Fresh independent-reference confirmation: PASS; the frozen raw-reference rule behaved as expected on fresh independent pairs.
- F5 nonlinear residual-null transfer: STOP; the frozen residualizer did not transfer cleanly through this nonlinear common-cause setting.
- F5 oracle forensic spike: true-null oracle noises narrowly NARROWed, while fitted F5 residuals added a clear upward dCor/low-p shift.
- F4 linear residual-null transfer: PASS.
- F4 matched residual-link alternative: PASS.

## Supported capability

At the tested 1,000-row dimensions, with the frozen five-fold spline/Ridge residualizer and raw-reference boundary, the workflow has evidence for one matched linear pair: F4 linear residual null PASS and F4 clear residual-link detection PASS.

## Explicit boundary

This is a linear-workflow proof of concept only. Evidence does not support reliable nonlinear residual adjustment at these dimensions, weak-effect sensitivity, arbitrary alternatives, general conditional-independence claims, network recovery, causal claims, real-data use, or package implementation.

## Next decision

The next permitted research action is design of one precommitted nonlinear residualization-repair feasibility spike. It must preserve the raw-reference ruler and assess a single specified residualizer change against F5; it is not a rerun, recalibration, or automatic nonlinear-alternative expansion.
