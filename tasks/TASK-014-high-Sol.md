# TASK-014: Qualify a vendor and implement one market-data adapter

- Status: base adapter implemented; shared request controls pending; production qualification blocked
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: high
- Dependencies: TASK-001, TASK-002, TASK-006
- Design: [data-and-learning.md](../docs/data-and-learning.md)

## Scope

Evaluate Alpaca first against the source capability checklist using current official terms and an authorized sample. Record storage/replay/public-display permissions and missing historical features. Keep final vendor selection deferred until this evidence exists; use an alternative only through a recorded choice. Build pagination, rate limiting, retries, resume and feed identity.

## Deliverables

Vendor comparison/decision record; one qualified market-data adapter; quality report; shared quota coordinator, cache/query identity and request telemetry; versioned configuration and CLI/doctor integration for these controls.

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

The original bounded adapter implementation is complete; the additional request-control requirements below are pending. The real vendor decision is also incomplete. No dependent run or ongoing spend was launched.

## Required follow-up: shared request control (2026-09-06)

Implement the [shared request-budget contract](../docs/market-data-request-budget.md). TASK-014 owns one quota coordinator across all callers of the same Alpaca Market Data account quota, including manual sample collectors. Extend existing contracts, private persistence, ingestion and CLI interfaces from tasks 001/002/006/010/013 under this task; do not create per-Character or per-process allowances.

Use a configurable 200/min hard maximum with an initial 180-attempt rolling-60-second operating ceiling and smooth pacing. All pages, retries and ambiguous outbound attempts consume that same ceiling and a finite work-item budget. Cache lookup, compatible in-flight request merging and multi-symbol batching precede admission; admission wraps every actual transport attempt. Persist quota/cooldown state and reject duplicate coordinator ownership. A restart cannot mint a new allowance. Reports must qualify account-wide guarantees when outside programs do not cooperate.

Correct the existing no-op default sleeper and truncated server wait: `_delay` currently caps even a valid long `Retry-After` at 30 seconds. Production waits or defers must respect the full server cooldown, handle header case and valid numeric/date formats, reject nonfinite delays, add bounded fallback jitter and cap retries. A 429 updates shared cooldown even on the final attempt. Test sleepers remain explicit offline dependencies.

Bind resume state to the full canonical query, atomically checkpoint accepted pages, and preserve later-symbol coverage across pagination. Cache hits make zero provider calls; three consumers of one missing window share one fetch sequence. Ship validated policy/query/work telemetry contracts without keys or account secrets; doctor reports missing coordinator/policy readiness. Verify the applicable Basic feed entitlement separately from the request limit; no silent SIP/IEX or time-window fallback.

Acceptance requires recorded-transport tests for these controls and TASK-016's **offline rate preflight** before any account-authorized sample. The preflight does not require full TASK-016 completion or a real TASK-015 window. Once it passes, collect only the separately authorized bounded sample to qualify entitlement, coverage, rights and measured headroom. A source/permission blocker remains a blocker; this task update does not authorize account calls.
