# TASK-007: Build fictional portfolios and the simulation ledger

> Historical task ID, retained for traceability. Remaining work is governed by [the ordered queue](README.md). Original status and evidence below describe the earlier scope; old dependencies and next-task wording are not the active execution order.

- Status: implemented and verified (2026-09-06; fixture execution)
- Recommended model: GPT-6 Astra (gpt-6-astra)
- Recommended effort: high
- Dependencies: TASK-001, TASK-002, TASK-006
- Design: [evaluation.md](../docs/evaluation.md)

## Scope

Implement separate council and per-Character portfolios, cash reservations, orders, next-eligible-event fills, costs, corporate actions, marks, and reconciliation behind a Trader User simulation adapter. Seed fixture portfolios equally; require a recorded real paper policy for nonfixture paper execution. No live endpoint implementation.

## Deliverables

src/adapters/trader_user_sim/; event-derived portfolio state; versioned execution assumptions.

## Acceptance

Use hand-calculated buy/sell/fee/dividend/split examples; prevent negative cash, duplicate fills, same-close lookahead, and mixing holdings across modes. Missing quotes/bars never produce invented fills. Equity reconciles after restore.

## Usage rationale

Accounting and timing errors can invalidate all apparent performance; invest in strong reasoning and adversarial examples.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.

## Implementation and validation

Implemented `src/trade_theorist/adapters/trader_user_sim/` with event-derived cash,
reservations, orders, raw next-open fills, fees, average cost basis, dividend
entitlement/payment, splits, cancellation/expiry, marks and reconciliation. Policy,
calendar and execution assumptions are pinned. Four checked-in fixture portfolios
have separate experiment/portfolio IDs and equal $10,000 seeds. Nonfixture execution
requires recorded paper policy and explicit nonfixture execution assumptions.

Evidence: `python scripts/check.py test_simulation test_risk test_storage` passes;
hand calculations cover buy/sell fees and slippage, dividend entitlement after a
sale, splits and restored equity. Adversarial cases prevent negative cash, reserved
cash reuse, duplicate fills, short positions, same-close/future fills, adjusted-bar
mixing, stale opening marks, clock reversal and cross-mode/owner execution. An
interruption after a fill rolls back the complete transaction. The fixture rebuild
produces cash $8,997.90 and equity $10,017.90 in each isolated portfolio.

See [implementation/API and boundaries](../docs/task-007-008-implementation.md) and
[quiet validation workflow](../docs/development.md). No bounded fixture blocker.
Final full-suite validation: 97 tests passed across 11 modules in 6.4 seconds;
existing/new fixture bundles validate and the diff whitespace check passes.
Real vendor/calendar qualification, complete real paper approval and readiness
review remain later prerequisites; no live endpoint, ongoing run or dependent task
was launched. Arbitrary corrections and fractional cash-in-lieu are unsupported
and rejected explicitly.

## META-001 follow-up (2026-09-06)

The completed v1 simulator uses proportional average-cost relief. TASK-025 adds production FIFO lots, flow-aware accounting and corporate-action/correction projections after TASK-024. Earlier results retain their accounting version.

See [the impact record](../docs/meta-001-impact.md) and [next task](meta-tasks/START-HERE.md).
