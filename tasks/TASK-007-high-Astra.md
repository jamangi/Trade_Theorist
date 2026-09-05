# TASK-007: Build fictional portfolios and the simulation ledger

- Status: planned
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
