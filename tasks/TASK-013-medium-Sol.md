# TASK-013: Create the one-command demo and operating interface

- Status: planned
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: medium
- Dependencies: TASK-003, TASK-004, TASK-010, TASK-011, TASK-012
- Design: [operations.md](../docs/operations.md)

## Scope

Implement doctor, library check, learn, ingest, heartbeat, evaluate, and export commands with plain status and resumable blockers. Provide a pinned Windows setup path, nonsecret example config, private data-root choice, and a synthetic demo with recorded/scripted opinions. Document exactly which features are available.

## Deliverables

CLI, quickstart, sample config, offline demo fixture, operating runbook.

## Acceptance

From a clean setup, run the demo without accounts/network/model calls and reproduce both dashboard views. Doctor names missing source/policy prerequisites without leaking credentials. A failed phase gives a concrete resume action.

## Usage rationale

Documentation and conventional command wiring can use medium effort once the engine is stable.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.
