# TASK-014: Qualify a vendor and implement one market-data adapter

- Status: planned
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: high
- Dependencies: TASK-001, TASK-006
- Design: [data-and-learning.md](../docs/data-and-learning.md)

## Scope

Evaluate Alpaca first against the source capability checklist using current official terms and an authorized sample. Record storage/replay/public-display permissions and missing historical features. Keep final vendor selection deferred until this evidence exists; use an alternative only through a recorded choice. Build pagination, rate limiting, retries, resume and feed identity.

## Deliverables

vendor comparison/decision record; one qualified market-data adapter; quality report.

## Acceptance

Reingestion is idempotent; entitlement denial does not silently switch feeds; gaps and revisions are preserved. Demonstrate actual required coverage or mark the dependent experiment blocked. Obtain explicit authorization before any paid subscription.

## Usage rationale

Requires focused provider research plus conventional ingestion code; use Sol and escalate only unresolved contract ambiguity.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.
