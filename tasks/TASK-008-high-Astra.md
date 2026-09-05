# TASK-008: Implement independent policy enforcement

- Status: planned
- Recommended model: GPT-6 Astra (gpt-6-astra)
- Recommended effort: high
- Dependencies: TASK-001, TASK-002, TASK-007
- Design: [architecture.md](../docs/architecture.md)

## Scope

Implement deterministic universe, funds, position, sector, gross exposure, loss, drawdown, turnover, order-frequency, expiry, and freshness controls. Keep policy outside model output. Support the explicit diversified ETF exception without accidentally exempting single-company funds. Persist halts and require a recorded owner reset.

## Deliverables

risk policy validator and governor; fixture approved-policy records; clear rejection events.

## Acceptance

Exercise every limit, unknown sector, stale mark, policy text injection, attempted self-promotion, and attempted live endpoint. A halt survives restart; reductions remain checked. Incomplete numeric policy blocks paper readiness.

## Usage rationale

The governor must remain independent of persuasive advice and preserve safe failure behavior.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.
