# News

A running log of what's been done on this project, in brief. Full
research detail (design specs, implementation plans, evidence write-ups)
is kept as an internal log and isn't part of this repo's tracked
history; this file is the public-facing summary.

## Gate 0 — mathematical sanity (2026-08-20 to 2026-08-24)

- Calibrated and independently confirmed a practical-null decision rule
  for the residual-dependence statistic, using fresh known-independent
  reference data.
- Validated the frozen workflow against eight canonical structures
  (independence, direct edges, colliders, mediators, and mixed
  direct+indirect paths) at 1,000 rows, confirming correct behavior on
  both null and non-null cases before any benchmarking began.

## Minimal prototype and Stage I (2026-08-25)

- Built the minimal residual-dependence prototype: pair-specific
  cross-fitted residualization, a permutation-based nonlinear dependence
  statistic, and BH-FDR multiplicity control.
- Stage I clean mechanistic benchmark: confirmed the core result the
  project depends on — the incumbent linear method and the residual
  mechanism perform comparably on linear structure, but only the
  residual mechanism detects genuinely nonlinear structure.

## Stage II — controlled degradation, one dimension at a time (2026-08-25)

Tested all seven degradation dimensions from the project plan, each in
isolation, at n=1,000:

- **Effect strength** — found a real detection cliff between
  coefficient 0.10 and 0.20.
- **Relationship shape** — no degradation across the linear-to-quadratic
  spectrum.
- **Noise** — no cliff in the originally tested range; a follow-up study
  matching noise levels to effect-strength's variance-explained scale
  confirmed the two dimensions hit the same underlying cliff.
- **Distribution** — no cliff, but caught and reported a real confound:
  skewed distributions on source variables reintroduce linear covariance
  the nonlinear fixture is supposed to avoid.
- **Residual variance (heteroskedasticity)** — no degradation.
- **Measurement quality** — a real, meaningful degradation found:
  detection drops from ceiling to ~66% as measurement reliability falls
  to 0.5.
- **Network structure** — no meaningful degradation across hub,
  community, and chain topologies, after correcting a fixture labeling
  issue that had inflated one condition's apparent false-positive rate.

## Sample-size dependence (2026-08-25)

- Found that every Stage II result above was specific to n=1,000 — at
  n=100, even a strong signal collapses to ~16% detection, and the
  effect-strength cliff itself shifts substantially with sample size.
  This directly motivated the two tracks below.

## Track 1 — stability and detectability reporting (2026-08-26)

- Built bootstrap edge stability and a three-tier confidence classifier,
  plus a minimal detectability lookup.
- Validated bootstrap stability against actual replication and found it
  significantly overstates confidence at weak effect sizes — an
  independent review confirmed the finding and helped correct the
  proposed fix. Resolved by relabeling the tiers and adding an explicit
  disclosure caveat rather than changing the underlying statistic.

## Track 2 — low-n power levers (2026-08-26)

- Tested two tuning levers (cross-fitting fold count, FDR threshold) for
  recovering detection power at low sample sizes; found a combination
  that helps substantially at low n with no precision cost.
- Found the benefit is conditional on sample size, not universal — the
  same combination costs precision at high n with no benefit, so it was
  adopted as a sample-size-conditional recommendation, not a global
  default change.
- Bracketed the exact crossover point empirically and set the
  recommended threshold at n=175, after review found the study's own
  mechanically-selected value carried a much larger, unfavorable
  precision cost than its detection benefit justified.
- Tested (and rejected) an adaptive, data-driven configuration selector
  as an alternative to the static threshold — it performed worse than
  chance in evaluation, a clean negative result.

## Stage III — first hybrid benchmark, round 1 (2026-08-27)

- Built the first hybrid fixture combining multiple realistic
  characteristics at once (mixed edge types, heterogeneous strength,
  hub/community structure, a redundant pair, isolated nodes), plus a
  second comparator-fairness scoring protocol (AUPRC and precision at a
  matched false-positive rate) to complement the existing native-workflow
  comparison.
- Found the residual layer's practical value on this harder, more
  realistic structure is real but modest at its default threshold —
  recovering only 0.7–13% of the edges the incumbent method missed
  across n=200–1,000 — while its underlying pairwise ranking is
  substantially stronger than that number alone suggests, a genuine
  divergence between the two fairness protocols worth following up.
- Found the incumbent method flags a deliberately collinear, non-causal
  pair as an edge 100% of the time, regardless of sample size — a stark
  version of a false-positive pattern seen earlier in Stage II.
- Caught and disclosed a reliability problem in the incumbent's
  continuous scoring: its underlying solver doesn't converge on this
  fixture, making its fine-grained ranking-based scores noisy and not
  exactly reproducible run to run, while its final edge decisions stay
  stable. Reported transparently rather than papered over.
