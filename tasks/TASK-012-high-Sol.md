# TASK-012: Build the two-tab performance dashboard

> Historical task ID, retained for traceability. Remaining work is governed by [Step 03](active/STEP-03-dashboard.md). Original status and evidence below describe the earlier scope; old dependencies and next-task wording are not the active execution order.

- Status: v1 fixture dashboard implemented and verified; private v2 follow-up pending after META-001
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: high
- Dependencies: TASK-010, TASK-011, TASK-025
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

## Implementation and evidence

Implemented the packaged dashboard with Council/Character tabs, historical report
selection, experiment/advice/horizon filters, equity/drawdown charts and exact table
alternatives. It shows holdings, returns/baselines, costs, readiness, learning
provenance, decisions/governor rejections, considered mail and unresolved objections.
Each result has six expandable answers and working allowlisted evidence links.
Schema and content hashes are checked before rendering; panels read saved data only.

Browser checks covered both tabs in nominal 1280px and 390px local frames, no page
horizontal overflow, arrow-key tabs, Tab focus, historical selection, six keyboard
disclosures, evidence dialogs/Escape, stale Trend, pending forecasts, no-trade council,
empty filters and missing-report recovery. See [validation details and browser
environment notes](../docs/task-011-013-implementation.md).

No bounded fixture blocker. The local demo visibly claims fixture mechanics only;
no cross-regime ranking, model call or trading control exists in the page. Public
website deployment was not started. That old TASK-018 outcome is now retired by [ADR-004](../decisions/records/ADR-004-local-observatory.md).

## META-001 follow-up

Reuse the implemented layout, six answers and accessibility behavior with a distinct `private-owner-v2` read model after TASK-025. Display Individual/Monarchy while retaining `character_portfolio`/`council` internally. Surface FIFO lots, total/available/reserved cash, dividend receivables, TWR and flow-neutral drawdown, external flows, recurring cost, mark freshness and reconciliation status. Private schema fields obey the [rights matrix](../docs/data-rights-matrix.md); no raw/real values enter the legacy fixture exporter.

Filter by execution basis and Character version. Monarchy paper results and its matched simulated control remain separately identified; never rank Individual simulations against broker fills as a reasoning contest. Give real empty/unready states for untrained Characters. Validate mobile/keyboard use, all six answers and no network/model calls on interaction. This is a pending follow-up, not a new claim about the v1 browser tests.
