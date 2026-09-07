# Step 08: Adversarially verify the shared data path

- Status: completed offline 2026-09-06; live Trading quota verification explicitly retained as blocked below
- Recommended model / effort: Astra / high
- Historical coverage: [TASK-016](../TASK-016-high-Astra.md)
- Queue: [ordered remaining work](../README.md)
- Design inputs: [Shared request budget](../../docs/market-data-request-budget.md)

## Why this position

Both limiter and consumer exist; verify actual dispatch and deadline behavior before an account sample.

## Starting evidence

Steps 06 and 07 pass focused checks. Use fake clocks and recorded transports.

Start with the [Step 07 bounded handoff](../../docs/step-07-forward-integration.md)
and its [original acceptance evidence](../../examples/step-07/acceptance.json).
The integrated path is `ForwardRound.prepare/execute`, reached through
`heartbeat.run_forward_round`; inspect Step 06 admission separately. Write a new
independent preflight artifact rather than relabeling those implementation tests.

## Finished state

A dated preflight report verifies actual transport timestamps, concurrent/restarted callers, retries, pagination, shared snapshots and cutoff behavior, with blocking failures resolved or explicitly retained.

## Implementation and acceptance

Verify the implemented [request-budget contract](../../docs/market-data-request-budget.md) against Steps 06 and 07 using fake clocks and recorded transports. The earlier handful of authorized read-only calls does not satisfy this preflight. Record a distinct pass/fail artifact; it is not the Step 12 final audit or paper promotion.

Reproduce concurrent manual/scheduled callers and adapter instances, rolling-window boundaries, idle bursts, cache misses merged across Characters, mixed-query isolation, every page/retry/ambiguous attempt, exhausted work budgets, process death/restart and clock jumps. Verify shared 429 cooldown on final retry, `Retry-After: 120` despite a 30-second fallback cap, HTTP-date/lowercase/missing/invalid/nonfinite headers, real production wait wiring and query-bound pagination resume. Assert against actual transport dispatch timestamps, not only the limiter's own counters. A late-page symbol must not disappear from the opportunity set.

Confirm waits/deadlines produce visible incomplete coverage or abstention; data cutoffs and shared snapshot identity remain intact. Verify separate Market Data and paper Trading quota policies, no hidden SDK retry bypass, and zero Alpaca calls by result-only consumers. Stress testing is offline, not an account load test. Reports distinguish cooperating callers from unknown outside account traffic.

## Validation and handoff

Use the [focused validation workflow](../../docs/development.md). Record changed files, actual checks, evidence artifacts and remaining blockers here. For code changes, run relevant tests and the full suite once after focused checks pass; for UI changes, verify keyboard and narrow/wide layouts too. Original synthetic acceptance never substitutes for required real-source or elapsed-time evidence.

Stop at this step's finished state. The default next item is [Step 09](STEP-09-vendor-qualification.md); do not start it automatically. Follow the queue's blocker rule for independent work. Preserve historical completion claims. No account call, order, paid subscription, public market-data deployment or recurring work is authorized merely by this task brief.

## Completion and fresh-task handoff

Completed 2026-09-06 America/Chicago (final artifact timestamp is 2026-09-07 UTC).
Read [the bounded guide](../../docs/step-08-offline-preflight.md) first. It maps each
case and remaining boundary without reading the large traces or prior conversation.

- [Baseline](../../examples/step-08/baseline.json): eight passes, four failures on
  main `5e7140e`. Preserved independently from Step 06/07 acceptance.
- [Final audit](../../examples/step-08/preflight.json): 14 cases pass. Actual
  recorded transport timings, a real-wait mocked HTTP boundary, five forcibly
  terminated process boundaries, full server cooldowns, merged/cache/resume
  behavior, paired cutoffs/abstention, result-only consumers and additive upgrade.
- Fixed admission/send descheduling bursts, oversized verified-header overflow
  losing cooldown, mutable active policy and mutable forward manifest. Migration
  006 adds settlement time; migration 005 and prior accounting records stay intact.
- Changed implementation: `market_requests.py`, `forward/shared.py`, migration
  `006_market_settlement.sql`; independent tests/helpers and audit runner;
  installed-wheel migration check; field inventory; README/queue/guides.
- Focused checks passed: independent audit plus `test_market_requests`,
  `test_forward_shared`, `test_storage`, `test_storage_v2`, `test_alpaca_adapter`.
  Full suite passed once: **303 tests, 29 modules, 87.5 seconds**. Field inventory:
  **1,869 classified fields**, unknown fields denied. Clean installed v1/v2,
  shared collector/cache, protected local serving and forward fixtures passed;
  migration 006 and settled attempts are checked explicitly. Portable
  [installed-check evidence](../../examples/step-08/installed-check.json) is committed.

**Retained blocker:** live paper Trading quota verification is unavailable because
its live adapter/policy does not exist. Market Data rejects Trading policies and
URLs; offline broker reconciliation cannot prove broker request admission. Step 13
must implement and verify this after its stage decision. The scoped offline
Market Data preflight passes; no live Trading or paper-promotion pass is claimed.

Step 09 remains next and was not started. Applicable source rights and separate
bounded-sample authorization precede dependent real calls. Unknown outside
account traffic and real account headroom are not measured. No account calls,
external model calls, orders, subscription or recurring work occurred.
