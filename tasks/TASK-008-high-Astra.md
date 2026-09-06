# TASK-008: Implement independent policy enforcement

- Status: implemented and verified (2026-09-06; fixture execution)
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

## Implementation and validation

Implemented `src/trade_theorist/risk.py` and integrated it at order admission and
execution. Controls cover universe, funds/reservations, long-only quantities,
company/sector/diversified ETF weights, deployed capital, gross exposure, daily
loss, drawdown, turnover, frequency, expiry and mark freshness. Quote age/spread
validation exists independently; quote execution remains unsupported. Single-company
funds receive no diversified exception. Rejections persist stable reason codes and
the pinned policy ID. Halts persist; only the trusted owner's recorded reset rebases
loss monitoring, without erasing historical results.

Evidence: `python scripts/check.py test_simulation test_risk test_storage` passes.
Tests exercise every implemented numeric control, unknown sectors, stale marks,
pending-order aggregation, checked reductions, fee affordability, policy prose and
extra-field injection, attempted council self-promotion and live execution. Halts
survive backup/restore. Missing numeric fields or paper approval/ownership block
readiness; real execution rejects fixture assumptions. Approved fixture policies
are recorded in `examples/simulation/` and have no real-paper authority.

See [implementation/API and boundaries](../docs/task-007-008-implementation.md).
Final full-suite validation: 97 tests passed across 11 modules in 6.4 seconds;
existing/new fixture bundles validate and the diff whitespace check passes.
No bounded fixture blocker. The actual owner-approved numeric paper policy remains
unresolved for later paper readiness; source learning and forward trials were not
advanced by these engineering fixtures. No dependent or ongoing run was launched.

## META-001 follow-up (2026-09-06)

Preserve the completed independent governor. TASK-025 integrates v2 equity, receivables, external flows and reservations without resetting loss limits or halts through deposits. New risk-policy values retain their owner gate.

See [the impact record](../docs/meta-001-impact.md) and [next task](meta-tasks/START-HERE.md).
