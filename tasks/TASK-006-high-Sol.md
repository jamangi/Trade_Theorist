# TASK-006: Implement time-aware ingestion and historical snapshots

- Status: implemented and verified (2026-09-06)
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: high
- Dependencies: TASK-001, TASK-002
- Design: [data-and-learning.md](../docs/data-and-learning.md)

## Scope

Build synthetic and permitted CSV adapters, session calendars, deduplication, quarantine, revision retention, and snapshot freezing. Implement separate forward-ingestion eligibility and archived historical-publication eligibility. Preserve raw versus adjusted prices and instrument identity. Disable current web for restricted historical runs through tool access, not a prompt alone.

## Deliverables

src/ingest/; source capability records; historical fixture market and snapshots.

## Acceptance

Reject future/revised evidence, undocumented publication dates, missing sessions, malformed bars, and mixed adjustment conventions. A backfill creates a new revision. A fixture with a delisting cannot silently drop the failed instrument.

## Usage rationale

Temporal logic is substantial but bounded by the schemas; Sol can implement and validate explicit cases.

## Implementation evidence

Implemented `src/trade_theorist/ingest/` with an exact-column permitted CSV adapter, explicit session calendars, source-capability validation, row quarantine, identity checks, normalized fixed-point OHLCV, batch adjustment consistency, deduplication and append-only revision chains. Snapshot freezing has distinct `publication_and_ingestion` and `archived_publication` rules, selects the latest revision knowable at the cutoff and halts on missing expected sessions. Delisting events remain in snapshots and coverage instead of allowing failed instruments to disappear.

The shared contract now rejects event/publication/ingestion clock inversions, undocumented availability, malformed revision linkage, future events, known superseded observations and unsupported recommendation certainty. Restricted historical construction removes network-capable tools through a code allowlist and rejects callers that provide them; this is not delegated to prompt text.

`examples/ingest/` contains deterministic daily bars, a later correction, a source-capability record, before/after snapshots and explicit coverage. The fixture bundle validates as a complete reference graph. Tests cover malformed bars, mixed adjustment bases, missing sessions, delisting retention, exact duplicate suppression, new backfill revision, point-in-time revision selection, archived eligibility and restricted tool access. See the combined [implementation record](../docs/task-005-006-implementation.md).

Remaining blocker for non-fixture use: no market-data vendor or license has been approved. The adapter accepts only supplied/permitted CSV and synthetic data; no network feed, account or scheduled process was added.
