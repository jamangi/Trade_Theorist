# Step 13: Operate attributable paper portfolios

- Status: pending; remaining scope as of 2026-09-06
- Recommended model / effort: Sol / high
- Historical coverage: [TASK-017](../TASK-017-high-Sol.md)
- Queue: [ordered remaining work](../README.md)
- Design inputs: [Performance and attribution](../../docs/portfolio-performance-v2.md), [request budget](../../docs/market-data-request-budget.md)

## Why this position

Exercise paper operation only after its stage decision; optional broker submission follows Monarchy-only attribution.

## Starting evidence

Step 12 gates pass and the precise paper run is authorized. Broker submission requires separate selection and authority.

## Finished state

The selected approved paper workflow has private manifests, comparable simulated series and, only if separately selected, a reconciled Monarchy broker-paper series. Sample immaturity and discrepancies stay visible.

## Scope

META-001 fixes the initial physical submission scope to **Monarchy only**, after separate order authorization. Individual portfolios remain independent internal simulations and never receive Alpaca client IDs. Use Steps 01 and 02's durable opaque mapping/outbox/update contracts. Do not encode local experiment/portfolio/Character IDs in `client_order_id`; resolve the opaque ID through the internal order to the final recommendation. Unknown submissions halt/reconcile instead of blind retry. Preserve partial fills through cancellation and reject unexplained aggregate account changes. Apply the [v2 performance contract](../../docs/portfolio-performance-v2.md) and [ADR-004](../../decisions/records/ADR-004-local-observatory.md), including a separately identified simulated Monarchy control for fair decision comparisons.

Run both portfolio modes against fresh permitted data under the approved paper policy and preregistered fill assumptions. Optionally implement a paper-only broker adapter if separately selected and authorized; local simulated sleeves remain canonical for comparative experiments. Preserve distinct broker-versus-local results and reconciliation.

## Deliverables

paper run manifests and reports; optional paper adapter contract tests; discrepancy report.

## Acceptance

No live host/credentials are accepted; orders cannot bypass policy; asynchronous/partial fills reconcile exactly; omitted broker dividends do not silently distort benchmark comparisons. Results remain insufficient until the declared sample matures.

## Shared evidence and separate order quotas (2026-09-06)

Council and individual portfolios consume the same eligible immutable market snapshot through Step 06's [shared request controls](../../docs/market-data-request-budget.md). They do not independently poll Alpaca for the same data. Prices for a later fill can require a new time-eligible snapshot; do not reuse an old decision snapshot as a fresh executable quote. Request-budget delays retain freshness gates and explicit abstention/pending status.

If an optional paper Trading API adapter is authorized, use the same coordination machinery with a separately verified quota policy for orders, account/assets/status queries, reconciliation and cancellations. Do not combine it with the Market Data budget or create separate budgets merely because credentials differ. Prioritize risk-reducing/cancellation/reconciliation work within the order pool; never exempt it from quota checks. Ambiguous order submissions require idempotent client IDs and reconciliation before retry, not the market-data GET retry policy.

Acceptance includes both modes sharing one market download, metered reconciliation/status calls, separate quota accounting and no duplicate paper orders after timeout. All Step 12 final gates remain required.

## Validation and handoff

Use the [focused validation workflow](../../docs/development.md). Record changed files, actual checks, evidence artifacts and remaining blockers here. For code changes, run relevant tests and the full suite once after focused checks pass; for UI changes, verify keyboard and narrow/wide layouts too. Original synthetic acceptance never substitutes for required real-source or elapsed-time evidence.

Stop at this step's finished state. The default next item is [Step 14](STEP-14-research-notebook.md); do not start it automatically. Follow the queue's blocker rule for independent work. Preserve historical completion claims. No account call, order, paid subscription, public market-data deployment or recurring work is authorized merely by this task brief.
