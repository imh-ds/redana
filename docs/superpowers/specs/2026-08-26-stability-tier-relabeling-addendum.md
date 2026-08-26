# Addendum: tier relabeling and disclosure caveat

Amends `docs/superpowers/specs/2026-08-26-stability-reporting-charter.md`
Decision 2, following `docs/evidence/stability-validation-20260826.md`'s
finding and an independent peer review of that finding (both dated
2026-08-26).

## What changed and why

The validation run found that at a marginal effect size
(`coefficient=0.15, n=1000`), mean bootstrap stability (`0.78-0.81`)
substantially exceeded actual between-dataset replication (`0.34`) --
7 of 10 datasets classified "Core" despite only ~1-in-3 true replication.
Peer review confirmed the finding but flagged that the original
charter's tier labels ("Core" / "Provisional" / "Background") read as a
confidence ladder toward *truth*, which bootstrap stability -- a
within-dataset resampling statistic -- cannot actually support. Peer
review also flagged that the initially-proposed fix (auto-attaching a
detectability-lookup-based caveat when a result falls in a "comparable"
regime to the tested marginal cell) has an identifiability problem: the
lookup is keyed on the true population coefficient, which an applied
researcher does not know and cannot look up. That fix is rejected.

## Decision 2, amended

**Tier labels change from `"core"` / `"provisional"` / `"background"` to
`"frequently_selected"` / `"intermittently_selected"` / `"rarely_selected"`.**
Thresholds are unchanged (`>=0.75` / `0.40-0.75` / `<0.40`) -- only the
labels change, to describe what the statistic actually measures
(selection frequency under resampling of the one dataset in hand) rather
than implying a claim about independent-study replication.

**A single, unconditional disclosure caveat is attached to every tier,
always** (not regime-matched, not gated on any lookup, no identifiability
assumption required):

> Bootstrap selection frequency reflects robustness to resampling this
> dataset. It is not an estimate of independent-study replication
> probability.

No rendering/display layer exists yet (out of charter scope per the
original charter), so this caveat is defined as a source-level constant
(`redana.stability.STABILITY_DISCLOSURE_CAVEAT`) for future reporting
code to use verbatim, rather than built into any report format now.

**The originally-proposed detectability-fusion caveat is explicitly
rejected**, not merely deferred: `redana.detectability` remains useful
for simulation-facing evidence notes (where the true coefficient is
known), but is not wired into any per-result applied-data caveat. Doing
so would require a validated, observable proxy for effective power that
does not currently exist -- a separate, later, explicitly-chartered
question if pursued at all.

`docs/evidence/stability-validation-20260826.md` is also being revised
for precision per peer review: distinguishing conditional
(within-dataset) from unconditional (between-dataset) quantities
explicitly, flagging the small-sample uncertainty in both the 10-dataset
bootstrap subset and the 50-dataset replication rate, softening the
ceiling-agreement claim, and marking the null-pair result as an
illustrative counterexample rather than a general rate.

## Governance

Per `outline/plan.md` §18 rule 10, this addendum authorizes only the
relabeling and disclosure-caveat addition described above. It does not
authorize Track 2, any change to the tier thresholds themselves, any
automatic real-data caveat wiring, or any package decision.
