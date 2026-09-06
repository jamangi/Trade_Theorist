# Step 08: Adversarially verify the shared data path

- Status: pending; remaining scope as of 2026-09-06
- Recommended model / effort: Astra / high
- Historical coverage: [TASK-016](../TASK-016-high-Astra.md)
- Queue: [ordered remaining work](../README.md)
- Design inputs: [Shared request budget](../../docs/market-data-request-budget.md)

## Why this position

Both limiter and consumer exist; verify actual dispatch and deadline behavior before an account sample.

## Starting evidence

Steps 06 and 07 pass focused checks. Use fake clocks and recorded transports.

## Finished state

A dated preflight report verifies actual transport timestamps, concurrent/restarted callers, retries, pagination, shared snapshots and cutoff behavior, with blocking failures resolved or explicitly retained.

## Implementation and acceptance

Verify the implemented [request-budget contract](../../docs/market-data-request-budget.md) against Steps 06 and 07 using fake clocks and recorded transports. The earlier handful of authorized read-only calls does not satisfy this preflight. Record a distinct pass/fail artifact; it is not the Step 12 final audit or paper promotion.

Reproduce concurrent manual/scheduled callers and adapter instances, rolling-window boundaries, idle bursts, cache misses merged across Characters, mixed-query isolation, every page/retry/ambiguous attempt, exhausted work budgets, process death/restart and clock jumps. Verify shared 429 cooldown on final retry, `Retry-After: 120` despite a 30-second fallback cap, HTTP-date/lowercase/missing/invalid/nonfinite headers, real production wait wiring and query-bound pagination resume. Assert against actual transport dispatch timestamps, not only the limiter's own counters. A late-page symbol must not disappear from the opportunity set.

Confirm waits/deadlines produce visible incomplete coverage or abstention; data cutoffs and shared snapshot identity remain intact. Verify separate Market Data and paper Trading quota policies, no hidden SDK retry bypass, and zero Alpaca calls by result-only consumers. Stress testing is offline, not an account load test. Reports distinguish cooperating callers from unknown outside account traffic.

## Validation and handoff

Use the [focused validation workflow](../../docs/development.md). Record changed files, actual checks, evidence artifacts and remaining blockers here. For code changes, run relevant tests and the full suite once after focused checks pass; for UI changes, verify keyboard and narrow/wide layouts too. Original synthetic acceptance never substitutes for required real-source or elapsed-time evidence.

Stop at this step's finished state. The default next item is [Step 09](STEP-09-vendor-qualification.md); do not start it automatically. Follow the queue's blocker rule for independent work. Preserve historical completion claims. No account call, order, paid subscription, public market-data deployment or recurring work is authorized merely by this task brief.
