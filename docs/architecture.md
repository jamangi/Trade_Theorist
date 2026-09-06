# Architecture and experiment modes

Status: target architecture extending the original README. Tasks 001–008 now implement contracts, SQLite, ordered learning, partial Value/Trend specialists, bounded opinions, point-in-time permitted-CSV ingestion, isolated simulation portfolios and independent risk enforcement. The heartbeat below remains planned. See [foundation](foundation-implementation.md), [tasks 005–006](task-005-006-implementation.md) and [tasks 007–008](task-007-008-implementation.md). Preserve the Trade Theorist / Trader Analyzer / Trader User boundary.

## Two portfolio views, one research engine

| Mode | Who decides? | Capital | Discussion | Meaning |
| --- | --- | --- | --- | --- |
| Council | Index Steward initially leads; Value and Trend submit shadows | One separately identified fictional portfolio | Independent opinions, then bounded advice | Tests governed team decisions |
| Character portfolios | Each eligible Character leads its own sleeve | Equal initial fictional cash per Character | Optional mail under the same rules | Tests each Character's decisions with declared advice access |

Use a shared observation snapshot and execution model, but separate `experiment_id`, `portfolio_id`, holdings, cash, and ledger. Index Steward's own sleeve is distinct from the council portfolio and from the mechanical buy-and-hold benchmark. Do not pool their returns or count identical money twice. A Character can still abstain, provide execution advice, or remain unready; each gets a dashboard row regardless of whether it trades. A not-yet-trained Character displays `not_ready`, not invented performance.

The approved council leadership remains unchanged. Leading a research sleeve grants no eligibility to lead the council. The Risk Skeptic can offer advice in either mode, but the hard governor is deterministic policy outside every Character, including the Skeptic.

Both modes reuse the same preparation and independent opinion where inputs genuinely match. Final decisions usually differ because holdings and mail differ; do not reuse across different input hashes. Each Character receives a view of its own portfolio and only the evidence allowed by its experiment. No unrestricted repository-reading tool belongs inside a Character run: future outcomes and other Characters' private notes may be present there.

## Modules and storage

| Module | Responsibility | Durable output |
| --- | --- | --- |
| `ingest` | Fetch, normalize, deduplicate, timestamp, quarantine | Immutable source revisions and snapshot indexes |
| `learn` | Source registration and ordered checkpoints | Knowledge deltas, memory versions, citations |
| `theorize` | Structured forecasts and independent opinions | Validated theory and recommendation records |
| `council` | Mail delivery, deadlines, final decisions | Events, conversations, read receipts |
| `evaluate` | Costs, baselines, mature outcomes, comparisons | Reproducible scorecards and evidence summaries |
| `adapters/trader_user_sim` | Apply policy-approved simulated orders | Append-only orders/fills/cash/position events |
| `export` | Build allowlisted public reports | Versioned dashboard JSON and readable artifacts |
| `cli` | Doctor, ingest, learn, heartbeat, evaluate, export | Run manifest and clear status |

SQLite is the single-writer operational store for the local pilot; database migrations are versioned. Keep raw licensed payloads and the database under a configured private data root outside Git. Use ordinary JSON snapshots first; introduce partitioned Parquet only when measured volume warrants it. `/market/` is an optional local view of snapshot manifests, never a second independently editable source of truth.

Persist event IDs, schema version, UTC timestamps, input hashes, code commit, policy version, source revisions, Character version, model identifier, prompt version, sampling settings, usage, and parent run. Simulated ledger writes are transactional and use fixed-point decimal money. Record model output once; replay saved outputs for reproducibility because regenerating language is not guaranteed deterministic.

## Minimum contract set

Every record has an ID and schema version. Unknown enum values and missing required provenance fail validation.

| Record | Essential fields beyond identity |
| --- | --- |
| Source | Author, edition, locator, rights evidence, retrieval time, availability status, storage permission |
| Checkpoint | Character/version, curriculum position, prior hash, source IDs, accepted/rejected claims, memory delta |
| Observation | Instrument ID, event/publication/ingestion timestamps, feed, revision, units, payload hash, quality |
| Snapshot | Cutoff, experiment clock policy, ordered observation IDs, exclusions, hash |
| Theory | README theory-card fields plus version and test-registration ID |
| Recommendation | Character/version, portfolio, snapshot, action, quantity/target, horizon, confidence event, invalidation, citations, expiry, abstention reason |
| Message | Protocol fields in [discussion](discussion.md), with immutable body and evidence IDs |
| Policy | Universe, numeric limits, clock/freshness rules, execution assumptions, approval reference |
| Fill/ledger event | Order and decision IDs, portfolio, quantity, price, fees, timestamps, simulation model version |
| Evaluation | Window, eligible sample, benchmark, cost model, metrics/null reasons, evidence status, source run IDs |
| Run manifest | Experiment, mode, versions, clocks, input/output hashes, phase status, usage, failure and resume state |

## Heartbeat transaction

A heartbeat is an explicit application action, initially owner-triggered. It is not a continuously running agent or a newly scheduled Codex automation.

1. Acquire an experiment lock; establish unique heartbeat ID, market cutoff, and usage cap.
2. Optionally ingest; validate session coverage and freeze an immutable snapshot. With ingestion disabled, freshness checks still apply.
3. Mark existing holdings and resolve already-due outcomes only from eligible observations. Missing marks produce stale/unknown equity, not zero prices.
4. Deliver eligible mail; load pinned knowledge, active theories, allowed evidence, and prior portfolio state.
5. Commit independent opinions, run at most one discussion round, and commit final recommendations or explicit abstentions.
6. Validate schema, expiry, funds, approved universe, exposure, and hard policy. Model text cannot change policy.
7. Queue eligible simulated orders for the next permitted execution event. Never fill using an observation that predates the decision or shares a bar whose close was used to decide.
8. Append execution events when their event time arrives; reconcile cash/positions; compute available outcomes.
9. Export a complete report atomically. Keep the previous valid report if export fails. Release lock.

Each phase has `pending/running/complete/failed` state. Retrying an ID reuses committed outputs and cannot duplicate mail, model charges for completed calls, orders, or fills. An ambiguous model-call failure may incur a charge; record it and cap retries. Partial work is visible and never reported as a complete experiment. Learning promotions occur between frozen evaluation windows, not as silent in-window memory updates.

## Proposed pilot parameters

These are new design proposals, not retroactively approved defaults: $10,000 fictional cash per portfolio; daily-session decisions; long-only, cash-only; maximum 20% equity per individual company and 40% per sector; an explicit diversified, unleveraged broad-market ETF exception allowing up to 100%; 100% maximum gross exposure; five new orders/session; 20% one-way turnover/session; 2% daily equity-loss and 10% peak drawdown halt on new risk. Buys reserve cash including modeled costs. Reductions remain policy-checked. Halts do not imply an executable liquidation price and never auto-reset.

An eligible daily snapshot must cover the latest completed expected session; missing sessions halt affected decisions. Quote-based fills require a configured maximum quote age and spread bound. Session-calendar rules, tradable symbols, sector mapping, costs, and benchmark fund must be frozen before a run. If an input needed for a limit is unknown, the order is rejected. These values require an explicit paper-policy record before paper trading; fixture tests can use clearly named test policy. They do not authorize any real capital.

## Delivery boundary

GitHub Pages will host exported public reports; the local/private runner owns data, keys, and writes. No database credentials or model API keys enter the browser. A future authenticated control service can trigger runs; the first dashboard is read-only. The proposed implementation sequence is in [tasks](../tasks/README.md).
