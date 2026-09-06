# TASK-015: Run forward shadow observations

- Status: base forward controls implemented; request-budget integration pending; real observations blocked
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: high
- Dependencies: TASK-005, TASK-008, TASK-010, TASK-011, TASK-013, TASK-014
- Design: [evaluation.md](../docs/evaluation.md)

## Scope

Freeze a prospective experiment with actual eligible Character versions, allowed public-research retrieval, timestamps, horizon, and identical opportunity sets. Commit recommendations before outcomes; keep shadow mode free of broker orders. Surface readiness, gaps, usage, and immature outcomes in reports.

## Deliverables

forward shadow run manifests, provenance audit, dashboard reports with honest sample status.

## Acceptance

Demonstrate future information cannot be supplied via repository/mail/retrieval tools; preserve publication and ingestion times. Do not report completed forward evidence before elapsed real sessions and forecast horizons. Source or policy blockers remain visible.

## Usage rationale

Primarily operational integration; Sol high can maintain provenance and accurate status.

## Implementation evidence (2026-09-06)

Implemented frozen forward manifests, qualified evidence envelopes, publication and
ingestion cutoffs, opportunity-set equality, pre-outcome commit enforcement, shadow
status reports and a forward-only tool allowlist. Tests demonstrate that generic
repository, mail and retrieval outputs cannot enter a decision; late output from an
otherwise qualified adapter is also rejected. Broker access is absent and reports
record zero broker orders.

The checked-in pilot manifest is blocked and reports zero real sessions and zero
performance. No eligible `ready` Character version exists in the immutable contracts,
the Alpaca sample/rights gate in TASK-014 remains open, and no paid SIP plan is
authorized. The offline provenance audit tests mechanics only. See the
[implementation record](../docs/task-014-015-implementation.md).

The original bounded control implementation is complete; the request-budget integration below remains pending. Actual forward observation also requires the stated prerequisites and real elapsed sessions. TASK-016 and ongoing runs were not implicitly launched.

## Required follow-up: budgeted shared snapshots (2026-09-06)

Consume TASK-014's [shared coordinator and cache](../docs/market-data-request-budget.md), not independent Character transports. Extend the frozen forward manifest with quota-policy/version ID, finite request/work budget, deadline, expected coverage, shared work references and frozen snapshot identity. Keep API request budgets separate from model/token budgets. Report estimates and actual attempts, retries, cache hits, shared-fetch reuse, wait duration, incomplete pages and deadline misses; count shared physical requests once at the coordinator.

Plan a common snapshot before Character execution. Freeze only complete eligible coverage, or explicitly apply the preregistered partial-coverage policy equally to all paired consumers. A budget stopping pagination must not favor symbols on early pages. Quota waiting never relaxes evidence cutoffs; late data produces visible defer/abstention, not different data for a later Character. Reuse observations without crossing feed, entitlement, revision or decision-time boundaries.

Acceptance: identical Character/mode requests share one fetch sequence; subsequent eligible cache reads cause zero Alpaca calls; exhausted budget and delayed completion retain identical snapshot IDs and honest status. Real account-backed work requires the new 014 controls, the 016 offline rate preflight and 014 sample/rights qualification. The full 016 audit remains later, after forward evidence; no cyclic dependency on its final completion is introduced.
