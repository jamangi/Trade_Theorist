# TASK-020: Add scheduled operation with bounded usage

- Status: planned
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: medium
- Dependencies: TASK-013, TASK-014, TASK-016, TASK-017
- Design: [operations.md](../docs/operations.md)

## Scope

Add an optional private scheduler aligned to market sessions, with overlap prevention, catch-up rules, usage ceilings, backups, and meaningful-change notifications. Preserve manual heartbeat controls. Configure recurring work only when explicitly requested; implementation alone must not start an unattended service.

## Deliverables

scheduler integration, recovery/backup runbook, disabled-by-default example schedule.

## Acceptance

Two triggers cannot overlap; market holidays do not create stale trades; unchanged state produces no unnecessary model work or notification; missed runs resume without fabricated historical decisions; backup restore reconciles.

## Usage rationale

Use ordinary scheduling and state machines; there is no reason to spend a high-reasoning agent on every tick.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.

## Shared admission across jobs (2026-09-06)

Submit all scheduled and manual downloads to TASK-014's [quota coordinator](../docs/market-data-request-budget.md); never instantiate a fresh limiter per job. Prevent duplicate ownership across processes. Prioritize fresh decision-critical snapshots over background backfill, with bounded queue age/fairness so postponed work does not silently starve. Persist budget/cooldown and page checkpoints across cancellation/restart; a deferred job resumes without replenishing its attempt budget.

Acceptance: simultaneous manual and scheduled triggers preserve the combined rolling-window limit and merge matching requests. Retried pages consume shared allowance. Queue/deadline exhaustion gives a visible deferred/expired outcome. Resuming after market time passes cannot invent a historical decision or weaken freshness. Notify only on meaningful status changes under the existing notification policy; no model call is needed to wait for quota.
