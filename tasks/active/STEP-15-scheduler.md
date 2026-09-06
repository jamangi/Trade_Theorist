# Step 15: Add optional bounded scheduling and recovery

- Status: pending; remaining scope as of 2026-09-06
- Recommended model / effort: Sol / medium
- Historical coverage: [TASK-020](../TASK-020-medium-Sol.md)
- Queue: [ordered remaining work](../README.md)
- Design inputs: [Operations](../../docs/operations.md), [request budget](../../docs/market-data-request-budget.md)

## Why this position

Automate repetition only after manual operation and its failure handling are reviewed.

## Starting evidence

Step 13's selected manual workflow is verified, Step 12 gates hold, and Step 06's shared coordinator is available.

## Finished state

Disabled-by-default scheduling passes overlap, quota, queue, recovery and backup/restore checks. Manual controls remain; no unattended service starts merely from implementation.

## Scope

Add an optional private scheduler aligned to market sessions, with overlap prevention, catch-up rules, usage ceilings, backups, and meaningful-change notifications. Preserve manual heartbeat controls. Configure recurring work only when explicitly requested; implementation alone must not start an unattended service.

## Deliverables

scheduler integration, recovery/backup runbook, disabled-by-default example schedule.

## Acceptance

Two triggers cannot overlap; market holidays do not create stale trades; unchanged state produces no unnecessary model work or notification; missed runs resume without fabricated historical decisions; backup restore reconciles.

## Shared admission across jobs (2026-09-06)

Submit all scheduled and manual downloads to Step 06's [quota coordinator](../../docs/market-data-request-budget.md); never instantiate a fresh limiter per job. Prevent duplicate ownership across processes. Prioritize fresh decision-critical snapshots over background backfill, with bounded queue age/fairness so postponed work does not silently starve. Persist budget/cooldown and page checkpoints across cancellation/restart; a deferred job resumes without replenishing its attempt budget.

Acceptance: simultaneous manual and scheduled triggers preserve the combined rolling-window limit and merge matching requests. Retried pages consume shared allowance. Queue/deadline exhaustion gives a visible deferred/expired outcome. Resuming after market time passes cannot invent a historical decision or weaken freshness. Notify only on meaningful status changes under the existing notification policy; no model call is needed to wait for quota.

## Private architecture requirements

Package scheduled results through Step 05's local/private boundary. Scheduling does not grant publication, account-call or order authority. Preserve shared quotas, job leases, recorded delays and bounded cost; do not invent missed decisions retrospectively.
md).

## Validation and handoff

Use the [focused validation workflow](../../docs/development.md). Record changed files, actual checks, evidence artifacts and remaining blockers here. For code changes, run relevant tests and the full suite once after focused checks pass; for UI changes, verify keyboard and narrow/wide layouts too. Original synthetic acceptance never substitutes for required real-source or elapsed-time evidence.

Stop at this step's finished state. The default next item is [Step 16](STEP-16-microstructure.md); do not start it automatically. Follow the queue's blocker rule for independent work. Preserve historical completion claims. No account call, order, paid subscription, public market-data deployment or recurring work is authorized merely by this task brief.
