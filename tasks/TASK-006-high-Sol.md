# TASK-006: Implement time-aware ingestion and historical snapshots

- Status: planned
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

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.
