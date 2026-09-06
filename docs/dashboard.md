# Dashboard and owner experience

Status: the v1 two-tab fixture dashboard is implemented and now restricted to synthetic exports. Its existing labels remain Council/Character portfolios until TASK-012's follow-up. The approved v2 design below uses Individual/Monarchy, a private read model and local-only packaging under [ADR-004](../decisions/records/ADR-004-local-observatory.md). Public GitHub Pages deployment is retired from TASK-018. See [prior browser evidence](task-011-013-implementation.md), [local fixture setup](quickstart.md), and [the migration starting point](../tasks/meta-tasks/START-HERE.md).

## At a glance

The header shows data-as-of time, last successful heartbeat, experiment window, information regime, paper/fixture label, quality status, usage, and any halt. “No data yet,” “Awaiting outcomes,” “Stale data,” “Character not ready,” and “Failed heartbeat” are distinct states. Never animate stale values as though they were current.

**Monarchy tab:** selected lead and version; portfolio equity, cash, after-cost TWR versus cash and index, flow-neutral drawdown, exposure, turnover, latest decision; adviser recommendations and governor result. Explain: one selected lead decides after bounded advice and deterministic risk checks. Keep internal mode `council`. Show whose objections were accepted or left unresolved; lead history remains accessible. Separate broker-paper and matched simulated-control series, with aggregate Alpaca values only in reconciliation details.

**Individual tab:** one row/card for every Character with readiness, curriculum progress, fictional equity, after-cost TWR, baseline difference, drawdown, exposure, trades/abstentions, matured forecasts, calibration sample, and evidence grade. Keep internal mode `character_portfolio`. Expand for FIFO lots/relief, average remaining basis, realized/unrealized P/L, available/reserved/total cash, distributions/receivables, external flows, mark provenance, decisions, mail and learning history. Filters include window, experiment, Character version, horizon, advice and execution basis. Do not rank hindsight with forward results or simulations with broker fills; do not total capital across alternative experiments.

Each row has an accessible **Explain this result** button. Its panel provides short answers to the six success questions, with “not yet known” when evidence is missing. Use cached summaries generated when source records change, not a new model call on every click.

| README success question | Required answer | Evidence link |
| --- | --- | --- |
| What did each Character believe at the time? | Dated belief and relevant active theory | Frozen constitution/memory/checkpoint version |
| Which sources and reasoning steps produced that belief? | Concise claim-to-evidence rationale | Source/edition locators, learning deltas, authored decision explanation |
| What evidence would have changed its mind? | Preregistered invalidation and unanswered question | Theory version and objection/message IDs |
| What action—or abstention—did it recommend using only then-available information? | Action, sizing, horizon, reason, and information-regime qualification | Recommendation, snapshot cutoff, eligibility audit |
| How did that decision perform after realistic costs and against fair baselines? | Outcome with costs, baseline, window, and fill limitations | Ledger, execution model, evaluation run |
| Is the apparent edge stable out of sample, or better explained by luck, leakage, or hidden risk? | Evidence grade, sample size, uncertainty, regime/contamination flags, open limitations | Preregistration, all-trial registry, holdout/forward review |

The fourth answer must admit when only historical availability is controlled and model contamination remains possible. The sixth defaults to “insufficient evidence,” never an invented explanation of skill. Display decision quality and realized profit separately.

## Information layout

```text
Trade Theorist        PAPER / FORWARD        Data as of …       Health …
[Individual] [Monarchy]        [Window] [Experiment] [Execution basis]
Equity · After-cost TWR / baselines · Flow-neutral drawdown · Evidence grade
Equity and drawdown over time, with a readable table alternative
Character / role | Ready? | Net result | Risk | Evidence | Explain this result
Expanded: Decisions | Beliefs | Learning | Mail | Historical versions
Lab notebook: what changed, what failed, what is still unknown
```

Charts share the same date range and comparable scales. Include keyboard-operable tabs and disclosure buttons, focus indicators, table alternatives, readable contrast, and text/status icons alongside color. Support narrow screens and reduced motion. Every metric defines its units, horizon, and calculation in a tooltip or help panel.

## Controls and publication

Owner workflow on the local app: **Check setup → Check library → Import/refresh data → Run next heartbeat → View report**. Show missing prerequisites and estimated/limited usage before model work. Provide a no-model demo for understanding the pipeline. A run view distinguishes queued, running, partial, failed, and completed phases and gives a resumable action.

The v2 report runs over a generated private bundle served by a loopback-only service; no public host is required. TASK-018 owns Host/Origin/path/asset controls. The read-only UI describes local owner commands without a fake trading/run button. Later authenticated write controls need a separately scoped design. Show recurring operating expense, unknown charges and reconciliation state alongside trading outcomes; definitions come from [performance v2](portfolio-performance-v2.md).

Private exports use an allowlist, distinct schema/publication class, build/source IDs, generation time, eligible cutoffs and content hash. Browser code receives no credentials, general filesystem access, books or raw source responses. Include only permitted fields needed for owner inspection; every unknown field fails closed under the [rights matrix](data-rights-matrix.md). Preserve as-known and restated historical versions separately; atomic handoff keeps the previous valid local report on failure. Real raw or reconstructable data is never routed into the legacy synthetic/public format.

Acceptance includes a mobile/keyboard walkthrough, correct zero-data/stale/unready states, six expandable answers, execution-basis and mode separation, cash/flow/lot identities checked against the golden fixture, and a checked private bundle with local access controls. Private UI rendering makes no Alpaca or model call. A convincing mockup alone does not satisfy the working dashboard task.
