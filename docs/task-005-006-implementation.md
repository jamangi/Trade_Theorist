# Tasks 005–006: specialists, opinions and point-in-time ingestion

Implemented and verified 2026-09-06. These tasks add two partial real learning paths and deterministic offline infrastructure. They do not add a broker, live feed, portfolio accounting, scheduled process or performance evidence.

## Task 005 boundary

Value Rationalist and Systematic Trend Operator now have separate constitutions and ordered curricula. Their supplied foundation PDFs were checked by exact SHA-256, page count, title/edition text and rendered representative pages. The public [acquisition record](../library/catalog/specialist-foundations-2026-09-05.json) records scope and permissions without redistributing source text.

The bounded review covers:

- Value Rationalist: *The Intelligent Investor* introduction and its 2003 commentary, PDF pages 17–31;
- Systematic Trend Operator: *Way of the Turtle* chapter 1, PDF pages 25–32.

Each review was imported through the existing ordered-learning engine with an empty formative memory, frozen design prior, exact source/curriculum/constitution hashes, page-bound anchors, original assimilation and adversarial review. The public bundles exclude source passages, quotations, requests and private events.

Both statuses intentionally say `partial_foundation`, `real_readiness: false`, `recommendation_readiness: fixture_only`, zero books completed and no evaluation. Possessing the complete PDF is not the same as reading it. Later chapters and books must proceed in order.

`OpinionAdapter` constructs one tool-free independent request from a persisted Character, its exact checkpoint/theory, portfolio, snapshot, portfolio state, evidence allowlist, model, prompt and expiry. The output can contain a bounded forecast, but the durable trading-facing result is only a validated recommendation; it cannot execute. Active opinions require positive decimal quantity and citations. Wait/abstain requires a reason. Absolute certainty, unknown evidence, past forecast resolution and excessive expiry fail closed.

The [fixture opinion bundle](../examples/theorize/independent-opinions.bundle.json) contains three distinct Character opinions over identical synthetic inputs. The [request pins](../examples/theorize/independent-opinions.pins.json) expose hashes and versions without private prompts or a real-world claim.

## Task 006 boundary

`CSVMarketAdapter` accepts one exact, allowlisted daily-bar format. It preserves immutable instrument ID, source feed, event/publication/ingestion clocks, raw versus adjusted basis, fixed-point OHLCV, publication permission and payload hash. A row is either normalized or returned with a bounded quarantine reason and raw-row hash. A batch that mixes adjustment conventions is rejected rather than silently combined.

`RevisionBook` suppresses identical repeats and assigns a new contiguous revision when the same feed/instrument/event/kind/adjustment identity changes. The new observation points to its predecessor. Snapshot construction chooses the latest revision knowable at the cutoff:

- `publication_and_ingestion` requires both publication and local ingestion by cutoff;
- `archived_publication` uses the documented historical public-availability time, permitting a later archival import but not a revision whose publication date was later.

The pinned `SessionCalendar` supplies expected sessions. Missing bars halt freezing. A delisting observation ends later bar expectations but remains in the selected observations and coverage report, so a failed instrument cannot disappear from a historical universe.

Restricted historical runs receive a code-level tool allowlist. Web, browser, HTTP, live-market and broker capabilities are removed before the run; providing one raises an error. Prompt instructions are supplemental, not the access boundary.

The [synthetic CSV](../examples/ingest/market.synthetic.csv), [later correction](../examples/ingest/market-revision.synthetic.csv), [capability record](../examples/ingest/source-capability.synthetic.json) and [validated snapshot bundle](../examples/ingest/snapshots.bundle.json) are deterministic demonstrations only. A real source remains blocked on vendor/license approval and capability evidence.

## Verification

The complete suite passes 68 tests. New coverage includes three opinion pins, explicit abstention, malformed/missing citations, invalid quantities, unsupported certainty, stale forecasts, source-review tampering, malformed OHLCV, undocumented publication time, duplicate suppression, revision retention, cutoff selection, missing sessions, delisting retention, mixed adjustments, source capabilities and restricted tool construction.

Run locally:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m trade_theorist validate examples/theorize/independent-opinions.bundle.json
.\.venv\Scripts\python.exe -m trade_theorist validate examples/ingest/snapshots.bundle.json
.\.venv\Scripts\python.exe -m trade_theorist learn --character value_rationalist
.\.venv\Scripts\python.exe -m trade_theorist learn --character systematic_trend_operator
```

The two `learn` status commands intentionally exit 2 while real readiness is false.
