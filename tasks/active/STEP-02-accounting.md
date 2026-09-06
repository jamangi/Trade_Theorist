# Step 02: Prove FIFO, flow-adjusted returns and attribution

- Status: pending; remaining scope as of 2026-09-06
- Recommended model / effort: Astra / high
- Historical coverage: [TASK-025](../TASK-025-high-Astra.md)
- Queue: [ordered remaining work](../README.md)
- Design inputs: [Performance v2 and broker attribution](../../docs/portfolio-performance-v2.md)

## Why this position

Prove the numbers on the new event contract before a UI presents them or asynchronous broker fills arrive.

## Starting evidence

Step 01's contracts and synthetic migration evidence pass.

## Finished state

The persistent v2 engine matches the golden vector and passes flow, stale-mark, partial-fill and isolation tests. Offline broker updates resolve to exactly one internal order; no submission transport runs.

## Scope

Implement the production v2 projections over Step 01's typed events: FIFO lot relief, partial fills, cash reservations, funding/deposits/withdrawals, dividend receivables/payment, splits, corrections, eligible marks, component P/L, exact external-flow TWR and flow-neutral drawdown. Retain v1 average-cost projections as historical records. Do not replace all existing simulation modules or change Character learning.

Integrate a separate v2 simulator/evaluator path (for example `src/trade_theorist/adapters/trader_user_sim/v2.py` and `src/trade_theorist/evaluate/portfolio_v2.py`) with the trusted governor. Define how external flows change risk denominators without disguising losses or silently resetting halts. Frozen funding policy must explicitly permit the flow; reference fixtures do not approve real paper funding.

Individual and Monarchy simulated comparisons share a preregistered execution model; any Monarchy paper ledger has a distinct ID and execution basis. Implement offline broker update reconciliation against the durable mapping/outbox without submitting orders. Preserve cumulative fills through partial cancellation, conflicting updates, unknown timeouts, corrections, account resets and unexplained aggregate activity. No new API request path belongs in this task.

## Deliverables

Versioned engine and evaluation projections, side-by-side conversion/replay reports, golden-vector integration tests, private read-model input records, and explicit supported/unsupported corporate-action behavior. Report after-cost TWR, flow-neutral drawdown, cash/broad-market baselines with matching flow timing, recurring operating expense and evidence grade. Do not rank across execution bases or stitch changing Character versions into a frozen trial.

## Acceptance

Replay [the META-001 golden fixture](../../examples/meta-001/performance-v2.fixture.json) through the **production persistence and reducer**, not the reference test helper: cash 1188, reserved 100, FIFO basis 343, realized gain 28, income 3, equity 1548, dollar gain 48, TWR 0.05750570 and drawdown 0.01901141 before the stale mark. The stale step invalidates dependent current values. Match original v1 expectations on its unchanged path.

Add withdrawals, full withdrawal/new funded segment, missing flow-boundary NAV, multiple instruments, per-lot rounding residuals, partial fills/fees, split cash-in-lieu unsupported status, ex/pay timing, mark corrections and as-known versus restated reports. Repeated persisted commands/updates must be idempotent; an interrupted projection must recover without a second cash movement. Assert no cross-portfolio contamination, no double fee/dividend, and no promotion when execution comparability or evidence is missing.

Run the new v2 integration tests plus `scripts/check.py test_simulation test_risk test_evaluation test_meta_contracts`; run the full suite once after focused checks pass and record counts/results. No real account, subscription, publication or capital is needed.

## Validation and handoff

Use the [focused validation workflow](../../docs/development.md). Record changed files, actual checks, evidence artifacts and remaining blockers here. For code changes, run relevant tests and the full suite once after focused checks pass; for UI changes, verify keyboard and narrow/wide layouts too. Original synthetic acceptance never substitutes for required real-source or elapsed-time evidence.

Stop at this step's finished state. The default next item is [Step 03](STEP-03-dashboard.md); do not start it automatically. Follow the queue's blocker rule for independent work. Preserve historical completion claims. No account call, order, paid subscription, public market-data deployment or recurring work is authorized merely by this task brief.
