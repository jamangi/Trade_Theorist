# Step 07: shared evidence before paired decisions

Implemented with original offline evidence on 2026-09-06. Start with the
[queue](../tasks/README.md), [Step 07 brief](../tasks/active/STEP-07-forward-integration.md)
and this guide. The next step is independent [Step 08 preflight](../tasks/active/STEP-08-offline-preflight.md).

## Reproduce and inspect

Use the existing Python environment (`.venv/Scripts/python.exe` on Windows):

```text
python scripts/check.py test_forward_shared test_forward_shadow test_market_requests
python scripts/build_step_07_fixtures.py
python -m trade_theorist.cli forward-fixture --output-root C:/TradeTheorist/forward-fixture
python scripts/export_field_classification.py --check
```

The script regenerates [compact acceptance evidence](../examples/step-07/acceptance.json),
a manifest, a frozen snapshot and a private report under `examples/step-07`.
The command writes the same original evidence to the selected output directory.
Both use temporary SQLite stores, explicit fake clocks and recorded responses.
Neither uses an account, external model, broker or real elapsed observation window.
Repeated fixture generation reproduces identities; runtime resumption uses the
original durable store, as tested separately. No large JSON dump is needed to check
the four scenario summaries.

## Bounded implementation map

| File / interface | Responsibility |
| --- | --- |
| `forward/shared.py: freeze_round` | Preregister one paired decision round against existing v2 portfolios, funded segments, Character versions, accounting plans and baseline |
| `ForwardRound.prepare` | Submit one common query to the Step 06 owner, defer or seal one immutable snapshot for every participant |
| `ForwardRound.execute` | Reserve finite Character usage, run recorded opinions on identical copies, publish the entire paired result atomically |
| `ForwardRound.report` | Read saved private progress/results; no transport or Character execution |
| `heartbeat.run_forward_round` | V2 heartbeat entry through the same orchestration; no separate request budget |
| `forward/schema.py`, `forward/validation.py` | Additive v2 records and typed cross-experiment comparison checks |
| `forward/fixtures.py`, `tests/test_forward_shared.py` | Original scenarios and focused interruption/deadline/reference tests |
| `market_requests.Coordinator.evidence` | Immutable private observation IDs and bodies from the existing shared cache |

New record types are `forward_manifest`, `forward_progress`, `forward_snapshot`,
`forward_reservation` and `forward_result`. They use the existing append-only v2
record chain and migration 005 quota store; no new SQL migration is needed. Export
the additive schema with `scripts/export_schemas_v2.py`. V1 forward helpers and
legacy heartbeat phases retain their behavior. Existing accounting and private UI
projections continue to read their own record types.

## Preregister, prepare, decide

`freeze_round` accepts participant triples `(portfolio_id, accounting_plan_id,
funded_segment_id)` and a baseline pair `(portfolio_id, accounting_plan_id)`.
Supply the canonical market query, observation-window start/end, data deadline,
decision deadline, request cap, separate model budget and numeric stopping rule.
The coordinator's clock records registration; registration must precede the window.
The manifest pins the complete quota policy and hash, query/work identity, planned
snapshot ID, expected sessions, and Character/portfolio/segment/plan/policy hashes.

All participants must be original fixture identities, with `fixture_only` Character
readiness, simulated execution and permitted original-source private rights. The
paired group contains Individual and Monarchy modes. Ownership and experiment
references are checked independently for each participant. Baseline construction,
fees, slippage, spreads, mark conventions and cash-flow schedules must match;
paired risk policies also match. Baseline and participant identities must already
exist at registration. A fixture label cannot enable the production HTTP transport.
Real eligibility remains a later gate.

`prepare` runs before any Character callback. The initial page estimate is based
on expected symbol/session rows and page size, with the configured retry allowance
shown separately. It is an estimate, never a guaranteed call count or entitlement.
Actual admission is owned by Step 06. If a pending shared work item's original cap
exceeds the round's frozen request cap, the round abstains without driving it.
Completed compatible cache entries still cost zero new requests. A shared work
item cannot obtain a fresh allowance from another Character or round.

This implementation preregisters **complete coverage only**. Unfinished pagination
defers everyone; an exhausted budget or exhausted incomplete page sequence seals
an empty abstention snapshot. Early symbols never reach a Character on their own.
A recoverable cooldown preserves the planned snapshot ID and original cutoff.
After the data deadline, late completion cannot replace a sealed abstention.

Eligible snapshots select only requested sessions and the latest received revision
for each symbol/event within the frozen information cutoff. Conflicting revisions
with the same receipt time cause abstention. Immutable observation IDs and receipts
remain in the private snapshot. Feeds, adjustment, rights, freshness, revision policy
and cutoff cannot change on resume. The market query remains the full Step 06
identity; experiment snapshots remain specific to their preregistered round.

`execute` accepts `RecordedDecisions` only. Every participant receives a separate
copy of the same sealed snapshot, including the same ID and content hash. Actions
are recorded opinions; they create no orders or fills. The model-call and token
limits are distinct from HTTP attempts. The reservation covers all callbacks and
their declared output ceilings before execution starts. If any callback fails,
exceeds its limit or misses the decision deadline, all paired outcomes abstain.
No earlier Character result is published while later callbacks remain unfinished.
Commit-time deadline checks roll back a provisional success and save abstention.

The reservation survives interruption. If execution was reserved but no result
committed, resumption records `execution_ambiguous` without invoking the Characters
again. Unknown calls/tokens are `null`; reserved amounts remain visible. Committed
snapshots and results are immutable and idempotent. Preserve the Step 06 quota
registry and database together when restarting; recovery cannot create allowance.

## Read the evidence honestly

`forward_progress` reports estimates, actual attempts/retries/429s, pages, cache
hits, subscriber reuse, queue/sleep time, incomplete pages and deadline misses.
`physical_work_ref` identifies the single charged parent. Count physical attempts
once per distinct parent ID; do not sum copied counters across Characters or round
reports. A cache read may report earlier cumulative physical usage while adding
zero new calls. Model reservation/usage appears separately in `forward_result`.

Deferred progress references the planned snapshot ID; the snapshot record does
not yet exist. A terminal preparation creates it exactly once, as `ready` or
`abstained`. A ready data snapshot may still have an abstained decision result if
Character execution fails. Reports retain both facts. Saved reports never trigger
catch-up downloads, revise information cutoffs, infer matured forecasts or count
synthetic clock advances as real sessions. Promotion remains false.

Step 08 independently challenges this integrated path before Step 09 account/rights
qualification. Steps 10–11 establish actual eligible participants and prospective
observations; Step 12 audits real evidence. Do not enable a production provider or
broker by changing fixture labels. Multi-round scheduling, real model adapters,
paper execution and performance claims are outside this step.

Final test counts, installed-package evidence and remaining gates are recorded in
the [Step 07 handoff](../tasks/active/STEP-07-forward-integration.md).
