# Step 02: Prove FIFO, flow-adjusted returns and attribution

- Status: implemented and verified 2026-09-06; Step 03 remains pending
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

## Implementation evidence

Added the separate production `adapters/trader_user_sim/v2.py` command/fill path,
`evaluate/ledger_v2.py` FIFO/flow reducer, `evaluate/portfolio_v2.py` private reports,
and `adapters/trader_user_sim/broker_v2.py` offline update/account reconciliation.
Typed frozen plans, execution terms/receipts, costs, account checks and performance
records extend `schema_v2.py` / `contracts_v2.py`; additive migration 004 gives plans,
terms and result revisions durable uniqueness. V1 modules, database defaults and
migrations 001–003 retain their original meaning/checksums. The existing storage
upgrade test now expects the explicit v2 ceiling of four.

The [implementation guide](../../docs/step-02-accounting.md) records the APIs,
funding/risk denominators, correction semantics, baseline construction, private
inputs and supported corporate actions. Cash-in-lieu, fractional settlement under
a whole-share plan, pending-order split adjustment and ambiguous broker revisions
remain explicit gaps requiring reconciliation. No automatic risk-halt clearing,
account transport, new UI or real evidence claim is introduced.

`scripts/build_step_02_fixtures.py` writes original synthetic evidence in
[`examples/accounting-v2/`](../../examples/accounting-v2/): before/after stale
reports, a resolvable typed input bundle, and side-by-side v1/v2 migration/replay
evidence. Golden values match: cash **1188**, reserved **100**, FIFO basis **343**,
realized **28**, income **3**, equity **1548**, dollar gain **48**, TWR **0.05750570**
and drawdown **0.01901141**. Stale dependent values are null with reasons. The
independent baseline matches flow timing/costs and yields TWR **0.20542373**.
Before the flow, v1 average-cost basis/realized **333/18** and v2 FIFO **343/28**
produce the same **1078** equity. V1 event/record hashes and replay survive explicit
side-by-side conversion; unsupported legacy history creates no fabricated lots.

## Actual validation

- New accounting and broker tests cover the golden vector, withdrawals/refunding,
  missing boundary/scheduled marks, multiple instruments, FIFO residuals, partial
  fills/reservations/fees, dividend timing, split gaps, costs/baseline mismatch,
  flow-neutral halts, as-known/restated corrections, isolation, duplicate/crash
  recovery, cancellations, late cumulative updates, quarantine, timeouts and resets.
- Focused `scripts/check.py test_accounting_v2 test_broker_v2 test_simulation
  test_risk test_evaluation test_meta_contracts` passed all six modules. The final
  two-module run passed in **4.9 seconds** after adding reservation/refunding and
  corrected execution-mark regressions.
- Final full suite: **205 tests across 23/23 modules passed in 29.4 seconds**.
  The suite was rerun after the final execution-mark correction fix; all original
  v1 tests remain included. Complete module logs stay in ignored `.local/test-logs/`.
- The fixture builder and CLI bundle validator passed. Generated v2 schema matches
  its source; field inventory drift check passed with **1,272 classified fields**.
  `git diff --check` passed.

The existing sequential test-process runner and compact fixture builder avoid
dumping generated bundles/test output into the session. Development documentation
now maps v2 modules to focused tests and the bounded accounting guide. Memory
exhaustion was not reproduced; its original cause remains unmeasured.

No bounded Step 02 blocker remains. The queue now points to Step 03's private
Individual/Monarchy views, which have not been started. Real-source rights,
participant qualification, elapsed-time evidence and paper operation retain their
separate later gates.
