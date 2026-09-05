# Dashboard and owner experience

Status: product specification, not an implemented or published website. Target: one GitHub Pages site with two primary tabs, fed by a private runner's sanitized exports.

## At a glance

The header shows data-as-of time, last successful heartbeat, experiment window, information regime, paper/fixture label, quality status, usage, and any halt. “No data yet,” “Awaiting outcomes,” “Stale data,” “Character not ready,” and “Failed heartbeat” are distinct states. Never animate stale values as though they were current.

**Council tab:** selected lead and version; council equity, cash, net return versus cash and index, drawdown, exposure, turnover, latest decision; adviser recommendations and governor result. Show whose objections were accepted or left unresolved. Lead history remains accessible.

**Character portfolios tab:** one row/card for every Character with readiness, curriculum progress, fictional equity, after-cost return, baseline difference, drawdown, exposure, trades/abstentions, matured forecasts, calibration sample, and evidence grade. Expand a row for holdings, equity/drawdown history, decisions, mail, and learning history. Filters select date window, experiment, version, horizon, and advice access. Do not rank hindsight experiments with forward ones or total capital across mutually exclusive variants.

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
[Council] [Character portfolios]            [Window] [Experiment]
Equity · Net return / baselines · Drawdown · Exposure · Evidence grade
Equity and drawdown over time, with a readable table alternative
Character / role | Ready? | Net result | Risk | Evidence | Explain this result
Expanded: Decisions | Beliefs | Learning | Mail | Historical versions
Lab notebook: what changed, what failed, what is still unknown
```

Charts share the same date range and comparable scales. Include keyboard-operable tabs and disclosure buttons, focus indicators, table alternatives, readable contrast, and text/status icons alongside color. Support narrow screens and reduced motion. Every metric defines its units, horizon, and calculation in a tooltip or help panel.

## Controls and publication

Owner workflow on the local app: **Check setup → Check library → Import/refresh data → Run next heartbeat → View report**. Show missing prerequisites and estimated/limited usage before model work. Provide a no-model demo for understanding the pipeline. A run view distinguishes queued, running, partial, failed, and completed phases and gives a resumable action.

[GitHub Pages is static hosting](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages); it does not run the Python engine or store private database writes. The public report is read-only. Its help panel explains how the owner starts a run locally; it must not expose a nonfunctional “trade” or “run” control. Later authenticated controls are a separate design task.

Exports use an allowlist, schema version, build ID, source run IDs, generation time, redaction policy, and content hash. Keep private notes, account identifiers, raw licensed data, source books, prompts containing secrets, and credentials out. Public summaries can link to permitted repository artifacts; restricted evidence shows a provenance label and private-inspection instruction, not a broken public link. Preserve historical reports when allowed, with retention limits; publish atomically and keep the previous report if validation fails.

Acceptance includes a mobile/keyboard walkthrough, correct zero-data and stale-data states, all six expandable answers, separation of modes, and a checked public export. A convincing mockup alone does not satisfy the working dashboard task.
