# Redesign proposals

September 15, 2026. **Design documents only.** The current Step 12 decision and Step 13 hold remain active. No runtime, schedule, model call, data-source integration, or paper trade was started by this work.

## Reading order

1. [How the Characters learn today](CURRENT_STATE.md): implementation findings, actual reading/memory counts, examples of knowledge, and the missing forecast feedback loop.
2. [Fresh design](DESIGN.md): a laboratory built around theories, discriminating tests, modular memory, reviewed learning, bounded usage, research requests, and public disclosures. This document was written first.
3. [Adapted design](ADAPTED_DESIGN.md): the same core learning loop added to the existing system, with explicit evidence-gathering side-steps, reuse boundaries, acceptance checks, and effort estimates. Written afterwards.

## The key answers

**More evidence should mean more than volume.** Measure independent episodes, coverage of relevant conditions, and facts that distinguish competing explanations. Nonoverlapping forecasts are useful within a fixed stream, but different assets can still share the same underlying event. Some questions need months or quarters.

**A forecast tests reasoning when rival explanations predict different observations.** Record what would support and challenge the Character's explanation before the outcome. A correct price prediction with a failed mechanism is different from understanding why the price moved. An anomaly can justify a new hypothesis without confirming that new hypothesis.

**Today's memory is largely an accumulation of accepted book claims.** The current exports contain 43, 138, and 83 accepted/qualified claims for Index, Value, and Trend respectively. The current forward runtime uses fixed rules, and matured forecasts do not automatically revise these memories. The [current-state report](CURRENT_STATE.md) explains the exact boundary.

**The proposed learning unit is a reviewed belief change.** It links a prior version to new evidence, a specific before/after claim, a critique, and a later test. A model can propose the change; source checks, outcome contracts, and future comparisons determine whether it is justified and useful.

**Git can version minds, with storage boundaries.** Public original syntheses and manifests can live here. Private or restricted source-derived memory stays private. A branch from an old mind is a new experiment, and it cannot backdate information learned later.

**A watched stock gets bounded memory.** Its current capsule has a size limit and links to dated episodes; it does not expand forever. Scripts maintain observations and summaries of numerical data. AI receives selected modules and new evidence under a fixed budget. More archive history need not mean more routine model input; unlimited active coverage still costs more.

**Characters can ask for research.** A request names the theory, desired observation, competing predictions, source, duration, and budget. An approved finite watch lease can be granted within policy. The Character does not grant itself new authority.

**Public trading disclosures are a plausible research source.** Congressional PTRs, SEC insider filings, and institutional holdings reports differ in timing, coverage, and permitted use. A study of imitation also needs an attention measure and competing-news controls. The [disclosure design](DESIGN.md#10-public-disclosures-as-evidence) links the primary official guidance and defines these dependencies; no causal claim or connector qualification has been established.

**Paper trading can accompany evidence collection.** It adds execution and portfolio evidence. It does not replace forecast learning. The adaptation proposes separate engineering and research-maturity gates, plus explicit shadow-collection side-steps if the existing hold is retained.

## Comparison

| Question | Fresh design | Adapted design |
| --- | --- | --- |
| Main objective | Build a general theory-learning laboratory | Add the same core loop to the current observatory |
| Historical work | Reference material; new infrastructure | Preserved checkpoints, trials, accounting and operating controls |
| Memory | Native modules and version graph | Derived modules over existing immutable checkpoints |
| Initial paper mode | Internal controller and matched controls | Extend existing internal accounting and matched controls |
| First engineering milestone | Bounded research → outcome → reviewed memory → subsequent comparison, with finite internal paper operation | Same milestone |
| Estimated development effort | 24–34 developer days | 12–18 developer days |
| Expected advantage | More architectural freedom | At least 6 days in the stated planning ranges; conditional, not guaranteed |
| Additional elapsed time | Real forecast horizons and source/access dependencies | Same dependencies; earlier construction may start collection sooner |

**Recommendation:** adopt the bounded adaptation and use the fresh design as the longer-term destination. The [work-package estimate](ADAPTED_DESIGN.md#development-estimate) explains the assumptions. Its [explicit side-steps](ADAPTED_DESIGN.md#6-make-the-missing-evidence-programme-explicit) assign collection, resolution, consolidation, review, and remaining blockers rather than assuming somebody will perform them outside the roadmap.
