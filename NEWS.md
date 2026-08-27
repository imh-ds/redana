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
- Caught and disclosed a reliability problem in the incumbent's
  continuous scoring: its underlying solver doesn't converge on this
  fixture, making its fine-grained ranking-based scores noisy and not
  exactly reproducible run to run, while its final edge decisions stay
  stable. Reported transparently rather than papered over.
- *(Correction, 2026-08-27: an earlier version of this entry described
  the incumbent flagging a deliberately-collinear pair as a "false
  positive." That framing was wrong — the pair was constructed as a real
  linear relationship, just one we'd chosen not to label a "true edge."
  See the permutation-diagnostic entry below.)*

## Stage III — permutation-resolution diagnostic (2026-08-27)

- Independent peer review of round 1's results identified two
  measurement problems worth resolving before trusting its sample-size
  findings: too few permutations to resolve statistical significance
  once many relationships are tested at once, and an evaluation design
  that mixed together two different effects when it removed a
  problematic variable. Built a diagnostic to test both cleanly.
- Confirmed both were real and quantified each one separately: raising
  permutation resolution alone roughly doubled the nonlinear layer's
  detection power; separately fixing the collinear-variable problem (see
  below) roughly doubled it again at the larger sample size tested.
  Detection at n=500 rose from 8% to 33% from these two measurement and
  design fixes alone, with no change to the underlying method.
- Found a third, larger, previously-unquantified cost: simply testing
  many relationships at once costs about half the achievable detection
  power, even after both fixes above — the single biggest lever left on
  the table, and not yet addressed.
- Confirmed, with a cleaner test design than before, that a variable
  built to closely mimic another variable can suppress the nonlinear
  layer's ability to detect a real relationship attached to the original
  — and corrected an earlier write-up that had mislabeled that mimicking
  variable's own strong relationship as a false positive when it was
  actually a real, correctly-detected one.

## Stage III — fair matched comparison (2026-08-27)

- Before drawing further conclusions, ran the current, actually-usable
  version of the tool head-to-head against the incumbent, on identical
  datasets, at three realistic sample sizes — the direct comparison no
  earlier round had actually done. Committed in advance to specific,
  concrete pass/fail criteria before seeing any results, and to not
  automatically pursuing further fixes on a failing result without a
  fresh, independently justified reason.
- Result: did not meet the predeclared bar at any of the three sample
  sizes tested. Reporting this plainly, as committed to in advance,
  rather than reframing it after the fact.
- The result was not a flat "no signal" finding, though — one of the two
  relationships tested cleared the detection bar cleanly at the largest
  sample size, but came with more spurious extra findings than the
  predeclared standard allowed. The other relevant relationship (the one
  affected by the mimicking-variable problem above) recovered nothing at
  any sample size, exactly as that finding would predict, since this
  round deliberately used the current, unmodified default rather than an
  unvalidated fix.
- Per the commitment made in advance, this result does not by itself
  authorize further attempts to fix or work around the outcome — any
  such next step needs its own independent justification going forward.
