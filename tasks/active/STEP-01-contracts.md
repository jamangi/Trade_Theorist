# Step 01: Version the portfolio contracts and storage

- Status: implemented and verified 2026-09-06; synthetic contract/storage scope
- Recommended model / effort: Sol / high
- Historical coverage: [TASK-024](../TASK-024-high-Sol.md)
- Queue: [ordered remaining work](../README.md)
- Design inputs: [Performance v2](../../docs/portfolio-performance-v2.md), [rights](../../docs/data-rights-matrix.md)

## Why this position

Give calculations durable identities and typed events before adding new accounting interpretations. The stable singular mode name is already correct. FIFO is a chosen lot-relief convention; external-flow events are needed because owner funding must not become performance. Preserve v1 semantics and establish the v2 boundary before calculations or UI integration.

## Starting evidence

Existing v1 schema, persistence, risk and evaluation are implemented; META-001 architecture is approved. Use original synthetic data.

## Finished state

Typed production v2 records and a checked side-by-side synthetic migration exist. Old v1 readers, hashes and replay results remain valid; no old balances are silently relabeled FIFO.

## Scope

Introduce additive production v2 schemas and persistence contracts at the earliest affected boundary, while retaining v1 readers, record hashes, migration checksums and historical results. The META-001 schemas are synthetic acceptance envelopes; convert the design into operational record schemas, not a table of expected values.

Define portfolio/experiment/Character identity, stable `character_portfolio`/`council` modes, execution basis, funded segments, effective/observed times, typed cash-flow/lot/fee/distribution/correction/mark events, projection revision, private read-model publication class and source rights. Define private Monarchy internal-order/client-ID mapping plus an outbox/update contract with unique constraints. An Individual simulated order has no broker client ID. This task creates no submission transport, paper order, external request or automatic migration of owner data.

## Files and deliverables

Read [ADR-004](../../decisions/records/ADR-004-local-observatory.md), the [performance contract](../../docs/portfolio-performance-v2.md), [rights matrix](../../docs/data-rights-matrix.md), and [reference fixtures](../../examples/meta-001/performance-v2.fixture.json). Review src/trade_theorist/schema.py, src/trade_theorist/contracts.py, src/trade_theorist/storage.py, and src/trade_theorist/migrations/. Add a separate v2 schema module/JSON output and a forward-only migration using the next free migration number (003 at META-001's audit). Add a v2 schema export command, fixtures and targeted contract/storage tests. Keep explicit version dispatch and refuse unknown schema versions. Update the field-classification inventory with every new field; unknown/dynamic fields remain denied for public output.

Provide a dry-run migration command/report that reads an explicitly selected synthetic database, identifies event versions and conversion gaps, and writes a side-by-side destination only on an explicit apply action. Store source-chain hash, conversion version, limitations and destination lineage. Re-running the same input is idempotent; conflicting identity fails. Do not modify installed migrations or auto-run on an existing private owner database. Runtime FIFO arithmetic belongs to Step 02.

## Acceptance

Schema tests reject mode/basis mismatches, cross-portfolio references, Individual broker mappings, leaking internal names in client IDs, missing flow timestamps, unknown field classes and duplicate/conflicting submission mappings. Test preservation of old v1 record/event hashes and replay results; crash rollback, duplicate migration application and newer-version refusal. Raw old balances are not relabeled FIFO/TWR. Unconvertible history yields an explicit gap, not fabricated lots.

Run `.venv/Scripts/python.exe scripts/check.py test_contracts test_storage test_meta_contracts test_export`, add and run the new v2 contract/storage modules, then run the full suite once. Run `.venv/Scripts/python.exe scripts/export_field_classification.py --check` after intentionally regenerating/reviewing the inventory. Record real command results here. No credentials or source permissions are needed for this bounded synthetic task.

## Validation and handoff

Use the [focused validation workflow](../../docs/development.md). Record changed files, actual checks, evidence artifacts and remaining blockers here. For code changes, run relevant tests and the full suite once after focused checks pass; for UI changes, verify keyboard and narrow/wide layouts too. Original synthetic acceptance never substitutes for required real-source or elapsed-time evidence.

Stop at this step's finished state. The default next item is [Step 02](STEP-02-accounting.md); do not start it automatically. Follow the queue's blocker rule for independent work. Preserve historical completion claims. No account call, order, paid subscription, public market-data deployment or recurring work is authorized merely by this task brief.

## Implementation evidence

Added operational `schema_v2.py` / `contracts_v2.py`, generated
`schemas/contracts-v2.json`, explicit `storage_v2.py` and additive migration 003.
V1 storage defaults, installed 001/002 checksums, hashes and average-cost replay
remain unchanged. Typed identities, funded segments, events, lot/relief revisions,
private projection metadata, source rights, opaque Monarchy mappings and atomic
outbox/update contracts have reference checks and database uniqueness constraints.

`migrate-v2` defaults to an explicitly selected synthetic read-only preview. Apply
preserves the v1 database side by side, publishes only after validation, records
source/destination lineage and reuses exact repeats. Unsupported history has explicit
gaps and no fabricated lots or relabeled FIFO/TWR. `export-v2-schema` and the fixture
builder provide reproducible outputs. Every new record/storage field is classified.

See [implementation and operating detail](../../docs/step-01-contracts.md),
[operational bundle](../../examples/contracts-v2/bundle.json),
[migrated bundle](../../examples/contracts-v2/migrated.bundle.json) and
[checked migration report](../../examples/contracts-v2/migration-report.json).

Targeted validation passed all six requested/new modules in 6.4 seconds. New tests
cover contract dispatch, mode/basis/owner isolation, private rights/classes,
flow/mark/correction timestamps, duplicate fees, submission identity, late updates,
quarantine, process-crash rollback, migration repeat/conflict/newer-version refusal,
and preservation of an average-cost sale (18 realized, never relabeled FIFO's 28).
Final full suite: **178 tests across 21/21 modules passed in 24.1 seconds**.
`scripts/export_field_classification.py --check` passed with **1,048 declared
fields classified** after intentional regeneration/review; CI now checks drift too. Both operational and
migrated v2 bundles passed the CLI validator; `scripts/build_step_01_fixtures.py`
reproduced the checked migration artifacts. `git diff --check` passed.

No bounded Step 01 blocker remains. Step 02 owns arithmetic/reconciliation and has
not been started. No owner database, account, order transport, UI or public-data
publication was changed.
