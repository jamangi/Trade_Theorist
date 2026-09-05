# TASK-020: Add scheduled operation with bounded usage

- Status: planned
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: medium
- Dependencies: TASK-013, TASK-016, TASK-017
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
