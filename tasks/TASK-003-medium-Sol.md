# TASK-003: Inventory book access and build the library catalog

- Status: planned
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
