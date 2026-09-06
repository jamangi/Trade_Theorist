# TASK-014: Qualify a vendor and implement one market-data adapter

- Status: adapter implemented; production qualification blocked
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

## Implementation evidence (2026-09-06)

Implemented the feed-pinned Alpaca bars adapter, recorded-response tests, conditional
capability record, quality report and [ADR-003](../decisions/records/ADR-003-alpaca-market-data-qualification.md).
Pagination/resume, bounded 429/5xx retries, raw adjustment, response validation,
idempotence, revisions, quarantine, gaps and fail-closed entitlement denial are tested.

Production qualification remains blocked: no Alpaca credentials or account-authorized
sample were supplied, required coverage is therefore unproved, and private storage,
internal replay and reporting rights require owner/contract verification. No paid plan
was authorized or purchased. No alternative vendor was selected. See the detailed
[implementation record](../docs/task-014-015-implementation.md).

The bounded software task is complete; the real vendor decision is intentionally not.
No dependent run or ongoing spend was launched.
