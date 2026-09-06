# TASK-013: Create the one-command demo and operating interface

> Historical task ID, retained for traceability. Remaining work is governed by [Step 04](active/STEP-04-commands.md). Original status and evidence below describe the earlier scope; old dependencies and next-task wording are not the active execution order.

- Status: v1 offline interface implemented and verified; private v2 command integration pending after META-001
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: medium
- Dependencies: TASK-003, TASK-004, TASK-010, TASK-011, TASK-012
- Design: [operations.md](../docs/operations.md)

## Scope

META-001 adds a follow-up after TASK-012's private v2 read model: commands must choose the schema/projection version explicitly, keep the v1 fixture demo working, use a private bundle root outside Git for real inputs, and report missing rights, migrations and reconciliation clearly. Doctor inspects prerequisites without exposing secrets or making account calls. TASK-018 owns hardened loopback serving; `--fixture` is not a license or a way to publish a private database. Preserve prior implementation evidence below.

Implement doctor, library check, learn, ingest, heartbeat, evaluate, and export commands with plain status and resumable blockers. Provide a pinned Windows setup path, nonsecret example config, private data-root choice, and a synthetic demo with recorded/scripted opinions. Document exactly which features are available.

## Deliverables

CLI, quickstart, sample config, offline demo fixture, operating runbook.

## Acceptance

From a clean setup, run the demo without accounts/network/model calls and reproduce both dashboard views. Doctor names missing source/policy prerequisites without leaking credentials. A failed phase gives a concrete resume action.

## Usage rationale

Documentation and conventional command wiring can use medium effort once the engine is stable.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.

## Implementation and evidence

Added doctor, complete demo, permitted-CSV ingestion, bounded fixture heartbeat,
evaluation and atomic local export commands. Existing library inspection/checks
remain available; learn can inspect readiness or resume an explicit permitted plan
with reviewed recorded responses. Missing real prerequisites produce plain blockers
and safe retry instructions. Nonsecret config and explicit private-root selection
are documented in the [Windows quickstart](../docs/quickstart.md) and
[operating runbook](../docs/runbook.md).

A fresh virtual environment installed pinned dependencies and the built wheel, then
ran the isolated demo without source-path imports. The demo itself uses no account,
network or external model; it reproduces both views, bounded mail, risk rejection,
independent portfolios, costs/dividends and mature/pending/stale evidence. Tests
confirm interruption/resumption, unchanged repeated demo state, CSV deduplication,
reviewed-learning reuse, redacted errors and actionable doctor blockers.

No bounded fixture blocker. Real-provider heartbeat orchestration remains gated by
unfinished learning, vendor/calendar qualification and real paper approval/readiness.
No live endpoint, scheduled work, paid model call or deployment was started.
