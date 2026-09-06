# TASK-002: Build durable storage and reproducible run records

> Historical task ID, retained for traceability. Remaining work is governed by [the ordered queue](README.md). Original status and evidence below describe the earlier scope; old dependencies and next-task wording are not the active execution order.

- Status: complete (2026-09-05)
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: high
- Dependencies: TASK-001
- Design: [architecture.md](../docs/architecture.md)

## Scope

Build a small Python package, SQLite migrations, single-writer transactions, private data-root configuration, append-only event APIs, hashes, and phase checkpoint/resume. Add ignore rules for private data, credentials, generated mail, and local artifacts. Persist prompts/responses privately with model and source versions.

## Deliverables

src/ persistence package; migration files; synthetic fixture store; bounded log redaction.

## Acceptance

Replay saved events to the same derived state; duplicate events do not duplicate effects; restore a backup; interrupted writes are atomic; secret fixtures are absent from public logs.

## Usage rationale

The contract is defined; careful conventional implementation and recovery checks fit Sol.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.

## Implementation evidence

Delivered the installable Python package, two checksummed SQLite migrations, single-writer transactions/savepoints, private-root configuration, immutable records and hash-chained events, phase resume, bounded public logging, backup/restore and a synthetic fixture store. Prompts, responses, source/model/prompt versions and usage reservations persist privately; actual demo code provenance is saved separately from the checked-in specimen manifest.

Storage tests pass for exact Decimal replay, duplicate IDs, changed-payload rejection, update/delete triggers, concurrent writers, nested rollback, abrupt child-process termination, failed/completed phase resume, backup restore and future database-version rejection. Secret fixtures are absent from public logs and failed-phase messages. `foundation-demo` ran twice: two committed sections on the first run and zero new recorded responses on the second. See [setup and recovery](../docs/foundation-implementation.md). No production data store or paid model provider is configured.

## META-001 follow-up (2026-09-06)

The completed v1 persistence remains valid. TASK-024 owns additive migrations, identity/attribution constraints and a synthetic side-by-side conversion report; no existing private database is automatically migrated.

See [the impact record](../docs/meta-001-impact.md) and [next task](meta-tasks/START-HERE.md).
