# TASK-017: Start forward paper portfolios and optional broker adapter

> Historical task ID, retained for traceability. Remaining work is governed by [Step 13](active/STEP-13-paper-portfolios.md). Original status and evidence below describe the earlier scope; old dependencies and next-task wording are not the active execution order.

- Status: planned
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: high
- Dependencies: TASK-007, TASK-008, TASK-014, TASK-016, TASK-025
- Design: [evaluation.md](../docs/evaluation.md)

## Scope

META-001 fixes the initial physical submission scope to **Monarchy only**, after separate order authorization. Individual portfolios remain independent internal simulations and never receive Alpaca client IDs. Use TASK-024/025's durable opaque mapping/outbox/update contracts. Do not encode local experiment/portfolio/Character IDs in `client_order_id`; resolve the opaque ID through the internal order to the final recommendation. Unknown submissions halt/reconcile instead of blind retry. Preserve partial fills through cancellation and reject unexplained aggregate account changes. Apply the [v2 performance contract](../docs/portfolio-performance-v2.md) and [ADR-004](../decisions/records/ADR-004-local-observatory.md), including a separately identified simulated Monarchy control for fair decision comparisons.

Run both portfolio modes against fresh permitted data under the approved paper policy and preregistered fill assumptions. Optionally implement a paper-only broker adapter if separately selected and authorized; local simulated sleeves remain canonical for comparative experiments. Preserve distinct broker-versus-local results and reconciliation.

## Deliverables

paper run manifests and reports; optional paper adapter contract tests; discrepancy report.

## Acceptance

No live host/credentials are accepted; orders cannot bypass policy; asynchronous/partial fills reconcile exactly; omitted broker dividends do not silently distort benchmark comparisons. Results remain insufficient until the declared sample matures.

## Usage rationale

The risky contracts have been reviewed; Sol handles the bounded operational adapter and validation.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.

## Shared evidence and separate order quotas (2026-09-06)

Council and individual portfolios consume the same eligible immutable market snapshot through TASK-014's [shared request controls](../docs/market-data-request-budget.md). They do not independently poll Alpaca for the same data. Prices for a later fill can require a new time-eligible snapshot; do not reuse an old decision snapshot as a fresh executable quote. Request-budget delays retain freshness gates and explicit abstention/pending status.

If an optional paper Trading API adapter is authorized, use the same coordination machinery with a separately verified quota policy for orders, account/assets/status queries, reconciliation and cancellations. Do not combine it with the Market Data budget or create separate budgets merely because credentials differ. Prioritize risk-reducing/cancellation/reconciliation work within the order pool; never exempt it from quota checks. Ambiguous order submissions require idempotent client IDs and reconciliation before retry, not the market-data GET retry policy.

Acceptance includes both modes sharing one market download, metered reconciliation/status calls, separate quota accounting and no duplicate paper orders after timeout. All TASK-016 final gates remain required.
