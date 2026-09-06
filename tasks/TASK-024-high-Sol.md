# TASK-024: Add v2 portfolio identity, event and private-read-model contracts

- Status: planned; exact next implementation task after META-001
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: high
- Dependencies: TASK-001, TASK-002, TASK-007, TASK-008, TASK-011
- Architecture gate: completed [META-001](meta-tasks/META-001-high-Astra.md)
- Design: [performance v2](../docs/portfolio-performance-v2.md), [rights matrix](../docs/data-rights-matrix.md), [ADR-004](../decisions/records/ADR-004-local-observatory.md)

## Scope

Introduce additive production v2 schemas and persistence contracts at the earliest affected boundary, while retaining v1 readers, record hashes, migration checksums and historical results. The META-001 schemas are synthetic acceptance envelopes; convert the design into operational record schemas, not a table of expected values.

Define portfolio/experiment/Character identity, stable `character_portfolio`/`council` modes, execution basis, funded segments, effective/observed times, typed cash-flow/lot/fee/distribution/correction/mark events, projection revision, private read-model publication class and source rights. Define private Monarchy internal-order/client-ID mapping plus an outbox/update contract with unique constraints. An Individual simulated order has no broker client ID. This task creates no submission transport, paper order, external request or automatic migration of owner data.

## Files and deliverables

Review `src/trade_theorist/schema.py`, `contracts.py`, `storage.py`, and current migration files. Add a separate v2 schema module/JSON output and a forward-only migration using the next free migration number (003 at META-001's audit). Add a v2 schema export command, fixtures and targeted contract/storage tests. Keep explicit version dispatch and refuse unknown schema versions. Update the field-classification inventory with every new field; unknown/dynamic fields remain denied for public output.

Provide a dry-run migration command/report that reads an explicitly selected synthetic database, identifies event versions and conversion gaps, and writes a side-by-side destination only on an explicit apply action. Store source-chain hash, conversion version, limitations and destination lineage. Re-running the same input is idempotent; conflicting identity fails. Do not modify installed migrations or auto-run on an existing private owner database. Runtime FIFO arithmetic belongs to TASK-025.

## Acceptance

Schema tests reject mode/basis mismatches, cross-portfolio references, Individual broker mappings, leaking internal names in client IDs, missing flow timestamps, unknown field classes and duplicate/conflicting submission mappings. Test preservation of old v1 record/event hashes and replay results; crash rollback, duplicate migration application and newer-version refusal. Raw old balances are not relabeled FIFO/TWR. Unconvertible history yields an explicit gap, not fabricated lots.

Run `.venv/Scripts/python.exe scripts/check.py test_contracts test_storage test_meta_contracts test_export`, add and run the new v2 contract/storage modules, then run the full suite once. Run `.venv/Scripts/python.exe scripts/export_field_classification.py --check` after intentionally regenerating/reviewing the inventory. Record real command results here. No credentials or source permissions are needed for this bounded synthetic task.

## Usage rationale

Reuse approved architecture and schema tools; Sol high is appropriate for careful additive migration work. Escalate an unresolved accounting interpretation narrowly rather than reconstructing the entire product. Complete this contract/persistence boundary before TASK-025 calculations or private UI changes.
