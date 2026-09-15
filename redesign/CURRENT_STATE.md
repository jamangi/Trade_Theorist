# How the Characters learn today

Inspected September 15, 2026, against repository commit `50f1221ac76d7d0b8273d4f632b8e77b8b5dd4cf`. This is a description of the existing implementation. The accompanying [fresh design](DESIGN.md) and [adapted design](ADAPTED_DESIGN.md) are proposals.

## The short answer

The project already has careful, cited book learning and immutable ancestry. Its current consolidation **accumulates accepted claims**. It does not yet implement a general compression process or a feedback loop that turns matured forecasts into revised Character memories.

The prospective trial uses fixed, foundation-informed rules. It does not call a live model to deliberate over the accumulated book knowledge. Thus the five collected sessions test important engineering, but they do not establish that an adaptive theorist has learned to predict markets.

## What exists in a Character

The state is external: constitution, curriculum, checkpoints, accepted claims, theory records, and saved experimental outputs. A fresh process can load these artifacts. This is neither a newly trained neural network nor a persistent human-like mind. A future model's behavior will also depend on the model version, instructions, selected context, and runtime.

### What has actually been read

Counts below are lengths of the checked-in current consolidated JSON lists, not measurements of understanding or independent empirical evidence. Accepted totals include claims whose reviewed disposition was qualified.

| Character | Completed foundation | Accepted/qualified claims | Rejected claims | Reading deltas | Remaining curriculum |
| --- | --- | ---: | ---: | ---: | --- |
| Index Steward | Bogle, 21 sections | 43 | 3 | 21 | Books 2–4 unread |
| Value Rationalist | Graham/Zweig, 28 substantive units | 138 | 30 | 28 | Books 2–4 unread |
| Systematic Trend Operator | Faith, 17 units including the original-rules appendix | 83 | 12 | 17 | Books 2–4 unread |

Evidence: [Index memory](../characters/index_steward/memory/bogle-2017-consolidated.json), [Value memory](../characters/value_rationalist/memory/foundation-v2-consolidated.json), [Trend memory](../characters/systematic_trend_operator/memory/foundation-v2-consolidated.json), and the [training continuation map](../docs/character-training.md).

The other planned Characters—Market Microstructure Mechanic, Probabilistic Risk Skeptic, Event and Disclosure Detective, and Mean-Reversion Experimentalist—do not yet have completed curriculum learning runs. The training map records seven declared Microstructure sources and four curriculum positions for each of the other three. Source availability in the library is not learned knowledge. Historical partial versions remain preserved; they are not additional completed books.

### Examples of current knowledge

**Index Steward:** recurring costs compound; fair comparisons require matched exposures and after-cost results; passive holdings still experience losses; selecting historical winners can hide survivorship and selection effects; useful advice or adherence should be separated from stock-selection skill. Its memory retains tensions around global versus US exposure, allocation and liabilities, and fees versus useful services. Its [Bogle theory record](../characters/index_steward/theories/bogle-2017.json) proposes testing the cost/shortfall relationship; the theory evaluation is not completed.

**Value Rationalist:** distinguish business value from the price paid; normalize earnings; inspect debt, liquidity, dilution, and governance; a margin of safety is conditional and does not guarantee protection; a good business can be a bad purchase at an excessive price. It qualifies historical thresholds and hindsight. Daily VTI prices alone cannot establish business value, so abstention is appropriate. See the [current foundation constitution](../characters/value_rationalist/constitution.foundation-v2.md) and the cited memory above.

**Systematic Trend Operator:** entries, exits, and position sizing form a complete system; volatility sizing does not eliminate gaps and liquidity risk; apparently diverse instruments may share exposures; all searched variants, costs, and drawdowns matter; discipline cannot repair a strategy without an edge. Historical futures examples do not validate a direct transfer to VTI. See its [current foundation constitution](../characters/systematic_trend_operator/constitution.foundation-v2.md).

These are paraphrases of recorded beliefs. Having the text does not demonstrate reliable retrieval, application, or forecasting skill. Those require separate tests.

## The actual book-learning process

The [learning engine](../src/trade_theorist/learn/engine.py) freezes the constitution, curriculum, source identity, source scope, and prior checkpoint. It checks ordered reading, eligibility, source permissions, and contiguous sections. A reading request contains the current source section and prior accepted memory, rather than exposing future sections.

The structured response extracts claims with exact locators and short matching quotations; partitions them into accepted and rejected claims; records assimilation, adversarial review, and a memory delta; and can produce a theory paired with a preregistration. Claims cannot silently replace earlier claim IDs.

The existing reviewed reading path uses [ReviewedTranscriptProvider](../src/trade_theorist/learn/reviewed.py). It imports previously authored, reviewed section analyses into those contracts. It is not a new model call at import time, and it is not an independent replication of the reading. The import records zero model tokens; the original session's authoring usage is unavailable and is not thereby free.

The [bounded model interface](../src/trade_theorist/learn/model.py) already supplies useful infrastructure: request hashing, resource reservations, completed-output reuse, finite budgets, and conservative handling of unfinished calls. It does not by itself make the prospective runtime a live reasoning agent.

## What “consolidation” currently does

The core operation in `Learner.step` is effectively:

```python
consolidated_memory = previous_memory + newly_accepted_claims
```

There is meaningful intellectual selection in the reviewed reading: accept, qualify, or reject a claim and explain the choice. The engine validates and preserves that selection. But the consolidation operation itself does not rank structural importance, reconcile semantically overlapping claims, merge recurring lessons, compress old material, or enforce a fixed working-memory budget.

The exported files also preserve rejected claims and reading deltas. However, the next-section request primarily loads the accumulated accepted claim list. Keeping critique in an archive does not ensure it is included in every future prompt. The design should explicitly solve this retrieval problem.

Consequences:

- A new section is assimilated with prior knowledge available, but every accepted addition remains in the cumulative list.
- There is no guarantee that contradiction, scope, or rejection history will be retrieved when needed later.
- As accepted memory grows, subsequent input grows. With roughly equal additions per section, cumulative input across many sections can grow approximately quadratically; this is an architectural observation, not a measured cost benchmark.
- Checkpoint history is valuable and should remain immutable. A bounded working view can be added without deleting that history.

## What the current forward trial does

[FoundationRules](../src/trade_theorist/forward/prospective.py) checks immutable learning ancestry and records the knowledge supplied to its request. Its behavior is nevertheless implemented as fixed rules:

- Index makes the initial bounded broad-fund allocation when its required public facts are present.
- Value abstains because daily bars do not establish valuation.
- Trend applies the frozen completed-close breakout condition against the preceding 20-session highs.
- The council receives three initial opinions, but its initial allocation policy remains fixed and Index-led.

The saved trial includes a fixed-probability control forecast and one matured result. It does not contain a live model learning new theories from observations. Evaluation and accounting record outcomes, but no automatic outcome-to-`Learner` feedback updates the foundation memory. Foundation versions remain frozen.

See [forward observation](../docs/step-11-forward-observation.md), [completion evidence](../examples/step-11/observation-completion.json), and [Step 12 audit](../docs/step-12-readiness-audit.md).

## Can the present learning model learn from forecasts?

Its provenance and versioning are a strong base. Its current source-section learner is designed for reading; simply feeding a trading retrospective through it would omit important safeguards. An outcome learner additionally needs the original prediction, exact information cutoff, resolution rule, benchmark, dependence group, error attribution, proposed belief change, and a later test of that change.

The missing capability is a **closed learning loop**: resolve a forecast, propose a specific memory revision, validate it, freeze a new version, and compare that version prospectively with its predecessor. The model should be allowed to conclude that one noisy outcome justifies no revision.

## Where the evidence blockage stands

The current [Step 13 brief](../tasks/active/STEP-13-paper-portfolios.md) is blocked after Step 12: **5 of 60 sessions and 1 of 30 matured forecasts**, leaving 55 sessions and 29 forecast resolutions against the selected floors. Fifty-five trading sessions are roughly eleven trading weeks, with holidays and missing observations potentially extending elapsed time. Nonoverlapping longer-horizon forecasts can take substantially longer.

Step 11 completed a finite observation window. The two finite jobs are disabled. Step 15 concerns later scheduling; Step 17 specifies a disclosure interface/source plan, not a functioning disclosure learning programme. The current sequence therefore needs an explicit continuation programme to collect and resolve more evidence; nothing creates those observations merely by moving to another coding task.

These counts belong to the existing trial. New model-driven Characters, different targets, or new regimes cannot automatically inherit that trial's observations as equivalent confirmations. Even reaching 60/30 would trigger review, not prove a predictive edge.

The [adapted design](ADAPTED_DESIGN.md) proposes named collection and learning side-steps and a revised separation of engineering permission from research maturity. **That proposal has not changed the active hold.**
