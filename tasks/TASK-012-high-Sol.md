# TASK-012: Build the two-tab performance dashboard

- Status: planned
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: high
- Dependencies: TASK-010, TASK-011
- Design: [dashboard.md](../docs/dashboard.md)

## Scope

Implement a read-only dashboard for council and individual portfolios with equity/drawdown history, readiness, learning, holdings, decisions, advice, costs, and evidence grades. Add expandable answers to all six README success questions using saved records. Use fixture exports until real results exist; visibly label them.

## Deliverables

dashboard source and local preview; export schema consumer; accessible empty/error states.

## Acceptance

Walk through both tabs on narrow and wide screens and with keyboard only; verify six answers and evidence links, historical version selection, pending outcomes, stale data, no-trade cases, and no cross-regime ranking. No model call on opening a panel.

## Usage rationale

A specific product contract allows Sol to focus on implementation and visual verification.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.
