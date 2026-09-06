# TASK-015: Run forward shadow observations

- Status: controls implemented; real observations blocked
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

The bounded control implementation is complete; actual forward observation requires
the stated prerequisites and real elapsed sessions. TASK-016 and ongoing runs were not
implicitly launched.
