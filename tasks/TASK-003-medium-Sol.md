# TASK-003: Inventory book access and build the library catalog

> Historical task ID, retained for traceability. Remaining work is governed by [the ordered queue](README.md). Original status and evidence below describe the earlier scope; old dependencies and next-task wording are not the active execution order.

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

Latest update (2026-09-05): [ADR-002](../decisions/records/ADR-002-microstructure-reading-scope.md) adopts the five supplied papers and limited Harris draft. Inventory v2 contains 30 active PDFs covering 31 positions and two registered transcripts. Missing original books are retired acquisition targets. File verification covers all 32 artifacts; transcript records bind text to source PDF hashes and sequential page coverage. The earlier audit below is historical.

Validation for this revision: all 32 fingerprints matched at 2026-09-06 00:10 UTC (September 5 locally). The transcript loader confirmed 595/231 sequential pages, retaining blank text pages. All 57 tests and the dependency check passed, including excerpt-to-paper progression, missing authority/scope/coverage rejection and changed transcript detection. Bogle remains one completed book with three unread.

Earlier owner-requested refresh (2026-09-05): the [all-Character inventory](../library/catalog/INVENTORY_REPORT.md) registers 25 local PDF fingerprints across 28 ordered slots, with two missing titles, a partial Harris draft, two OCR requirements and actual edition differences. `library report` now shows this current inventory; `library verify-files` checks the owner's existing directory without copying text or promoting readiness. The original publisher audit below and pilot.json are retained as historical evidence. No additional Character was trained by the refresh.

Refresh verification: all 25 registered local files matched their sizes and SHA-256 hashes on 2026-09-05 at 23:00 UTC; both unacquired titles remained reported separately. All 53 tests and the dependency check passed. New coverage tests include shared-title deduplication, wrong order, fabricated material states, changed/missing files, path containment and reproducible reports. Index Steward's published foundation still validates as one book completed and three unread.

The [pilot catalog](../library/catalog/pilot.json) covers all twelve approved positions with eleven exact edition candidates and one explicit unresolved edition. ISBN identities are deduplicated independently of Character order. The [access report](../library/catalog/ACCESS_REPORT.md) links dated publisher evidence, legal acquisition routes and separate access/reading/ingestion/storage/redistribution states. The Intelligent Investor format remains unresolved; the publisher marks the fifth Buffett edition unavailable. The Harriman URL redirect is recorded for review. No book purchase or full-text ingestion occurred.

The cached checker uses bounded HEAD requests, never upgrades rights from HTTP 200, and appends human-review requests on changed URLs/metadata, redirects and uncertain results. Tests pass for catalog coverage/deduplication, missing evidence, sample/full-text separation, cache reuse and changed URLs/ETags. A manual live HEAD run on 2026-09-05 at 20:41–20:42 UTC returned HTTP 200 for all twelve metadata URLs; five lacked change validators and were queued for review. This does not contradict an unavailable book listing and grants no full-text access. The private cache remains outside Git.
