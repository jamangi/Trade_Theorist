# TASK-016: Audit leakage, costs, recovery, and paper readiness

- Status: planned
- Recommended model: GPT-6 Astra (gpt-6-astra)
- Recommended effort: high
- Dependencies: TASK-011, TASK-013, TASK-014, TASK-015
- Design: [evaluation.md](../docs/evaluation.md)

## Scope

Review the completed implementation against clock barriers, simulated accounting, source rights, public exports, model usage, crash recovery, hard limits, and baseline fairness. Review the proposed numeric paper policy and obtain a recorded owner decision before paper execution. Distinguish engineering readiness from statistical evidence.

## Deliverables

audit report with reproduced findings; resolved defects; explicit paper-stage decision or blockers.

## Acceptance

Use adversarial cases spanning publication lag, revised filings, splits, stale quotes, repeated runs, unavailable sources, and injected instructions. Record all unresolved limitations. No paper promotion solely because the dashboard looks complete.

## Usage rationale

A separate focused reasoning pass is justified at the stage boundary; this task does not mandate a separate subagent.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.

## Two-stage rate-control review (2026-09-06)

**Offline rate preflight:** after 014 implements the [request-budget contract](../docs/market-data-request-budget.md), verify it with fake clocks and recorded transports before forward operation or a larger coordinator-backed sample. The owner separately authorized a handful of read-only calls that established paper authentication and delayed historical SIP access; they do not satisfy this preflight. This narrow subgate needs 014's new software and the existing fixture controls from 015, not vendor qualification or completed real forward sessions. Record a distinct preflight pass/fail artifact; it is not full TASK-016 completion or paper promotion.

Reproduce concurrent manual/scheduled callers and adapter instances, rolling-window boundaries, idle bursts, cache misses merged across Characters, mixed-query isolation, every page/retry/ambiguous attempt, exhausted work budgets, process death/restart and clock jumps. Verify shared 429 cooldown on final retry, `Retry-After: 120` despite a 30-second fallback cap, HTTP-date/lowercase/missing/invalid/nonfinite headers, real production wait wiring and query-bound pagination resume. Assert against actual transport dispatch timestamps, not only the limiter's own counters. A late-page symbol must not disappear from the opportunity set.

Confirm waits/deadlines produce visible incomplete coverage or abstention; data cutoffs and shared snapshot identity remain intact. Verify separate Market Data and paper Trading quota policies, no hidden SDK retry bypass, and zero Alpaca calls by result-only consumers. Stress testing is offline, not an account load test. Reports distinguish cooperating callers from unknown outside account traffic.

**Final readiness audit:** retain the full dependencies above. After the preflight permits a separately authorized 014 sample and 015 forward work, assess measured headroom, provider responses, usage telemetry, all existing financial/data gates and real forward evidence. Account access remains separately authorized. Do not add full TASK-016 as a prerequisite of 014 or 015; the staged gate is documented in the [task index](README.md).
