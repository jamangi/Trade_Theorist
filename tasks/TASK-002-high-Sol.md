# TASK-002: Build durable storage and reproducible run records

- Status: planned
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
