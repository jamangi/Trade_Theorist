# TASK-003: Inventory book access and build the library catalog

- Status: complete — inventory and checker (2026-09-05); acquisition/rights blockers recorded
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: medium
- Dependencies: TASK-001
- Design: [data-and-learning.md](../docs/data-and-learning.md)

## Scope

Catalog all twelve approved pilot curriculum slots, deduplicating exact editions while retaining Character-specific order. Verify official/publisher/library access today, recording access separately from machine-ingestion and redistribution permission. Add cached URL checks with checked-at dates and a human-review queue. Do not purchase or ingest unknown-rights full text.

## Deliverables

library/catalog/ metadata; access checker; report of missing editions, rights, and legal acquisition options.

## Acceptance

Every slot maps to an exact edition or explicit unresolved edition; every availability claim has dated evidence; a sample page cannot become full-book status; a changed URL triggers review.

## Usage rationale

Mostly bounded research and mechanical catalog work; escalate only ambiguous curriculum reasoning, not every URL check.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.

## Implementation evidence

The [pilot catalog](../library/catalog/pilot.json) covers all twelve approved positions with eleven exact edition candidates and one explicit unresolved edition. ISBN identities are deduplicated independently of Character order. The [access report](../library/catalog/ACCESS_REPORT.md) links dated publisher evidence, legal acquisition routes and separate access/reading/ingestion/storage/redistribution states. The Intelligent Investor format remains unresolved; the publisher marks the fifth Buffett edition unavailable. The Harriman URL redirect is recorded for review. No book purchase or full-text ingestion occurred.

The cached checker uses bounded HEAD requests, never upgrades rights from HTTP 200, and appends human-review requests on changed URLs/metadata, redirects and uncertain results. Tests pass for catalog coverage/deduplication, missing evidence, sample/full-text separation, cache reuse and changed URLs/ETags. A manual live HEAD run on 2026-09-05 at 20:41–20:42 UTC returned HTTP 200 for all twelve metadata URLs; five lacked change validators and were queued for review. This does not contradict an unavailable book listing and grants no full-text access. The private cache remains outside Git.
