# Production v2 contract and storage boundary

Step 01 adds operational contracts and explicit persistence. It does not calculate
FIFO/TWR, serve the private UI, contact an account or submit an order. The META-001
arithmetic vectors remain an independent specification for Step 02.

## Version and identity

`schema_v2.py` generates `schemas/contracts-v2.json`. `contracts.validate` and
`validate_bundle` dispatch explicitly on version 1 or 2; mixed bundles and unknown
versions fail. V1 JSON, canonical hashing and the installed SQL migrations 001/002
are unchanged. The v1 writer rejects v2 records so old readers cannot consume new
accounting semantics accidentally.

`V2Store` explicitly opts into migration 003. The ordinary `Store` keeps its v1
schema ceiling and never automatically installs 003. Separate immutable v2 records
have their own hash chain. A v1 reader can still verify/replay the original tables
after an explicit upgrade. This API opt-in is not permission to upgrade owner data.
The supplied migration command accepts only explicitly selected synthetic input.

Experiments pin mode, execution basis, instrument universe, policy and Character
versions. Portfolios pin their owner, USD reporting currency, accounting/return
methods and role. The serialized modes remain `character_portfolio` and `council`;
baseline is a role. Individual portfolios require `simulated`. A Monarchy paper
ledger and its simulated control have different portfolio and experiment identities.
Source rights are an independent typed record, not inferred from evidence labels.

Funded segments have ordered identities and predecessor references. A full
withdrawal can end a segment through `segment_end`; later funding belongs to a new
segment. Character changes use a new frozen portfolio/experiment window rather
than rewriting the old owner's identity. Step 02 must enforce economic segment-end
conditions and validate funds/positions before emitting transitions.

## Canonical records

All v2 records declare a fixed field class and hashed source provenance. Internal
references resolve to typed records in the same experiment, portfolio and segment
where applicable. `provenance.source_event_ids` identifies external/legacy evidence;
`provenance.source_hash` pins it. These are not inferred references to v2 balances.

Ledger events have idempotency keys, per-portfolio ordering sequences and distinct
effective/observed times, with a recorded creation time. Typed payloads cover initial
funding, contributions, withdrawals, segment ends, orders, cash/share reservations,
releases, fills, allocated/unallocated fees, dividend entitlement/payment, splits,
cash-in-lieu, corrections, marks and halts. Amounts use decimal strings; cash-event
amounts require cents. Basis/relief allocations allow 28 fractional places so an
accounting implementation can preserve residuals until final relief.

Lots and lot relief are immutable projection records with originating fills,
orders, corporate-action lineage and revisions. Original acquisition quantity stays
original; a split can change remaining units when explicit action lineage exists.
No arithmetic reducer is implemented here. Step 02 owns cumulative fills, available
funds/shares, exact lot relief, distribution reconciliation and mark-boundary NAV.

Projection identities pin source event IDs and their ordered digest, effective and
receipt cutoffs, owner/policy, mark policy, methods, revision and predecessor. The
`source_chain_hash` on a projection is the digest of its explicitly ordered source
event records; the storage chain independently covers every persisted v2 record.
The result is a hash reference, not an untyped public payload. Unavailable results
carry explicit reasons. A conversion-gap portfolio cannot claim a completed result.
Publication class is always `private-owner-v2`; private replay/read-model rights
must be permitted. New public fields are not authorized by this schema.

## Attribution and recovery

An internal order points to its final decision, frozen snapshot hash and policy
approval. It never contains a broker client ID. `prepare_submission` is a local
persistence operation: for Monarchy paper orders only, it generates a random opaque
32-hex-character ID and atomically stores one mapping and one prepared outbox.
Repeated preparation returns the same mapping. No transport exists in this step.

Unique indexes prevent reusing client IDs, internal-order mappings, outbox revisions,
provider update IDs, fill IDs, segment ordinals and event keys/sequences. Outbox
revisions preserve the immutable order/request hash. An unknown submission cannot
transition back to prepared; it requires reconciliation, never blind resubmission.

Broker updates include effective/observed times, cumulative quantity/notional/fees,
incremental fill identity and status. Exact deliveries are no-ops; valid late older
updates remain available without overwriting newer fills. Conflicting identities,
unknown mappings/replacements, excess quantities or decreasing cumulative values
roll back and enter quarantine as a hash plus fixed reason, without persisting an
unvalidated payload. Bindings uniquely associate a broker order with one mapping.
Step 02/13 will consume this evidence for actual attribution and reconciliation.

## Synthetic migration

Use an **absolute database file**, not a directory. The default is read-only preview:

```powershell
.\.venv\Scripts\trade-theorist.exe migrate-v2 --source C:\fixtures\old\research.sqlite3 --synthetic
.\.venv\Scripts\trade-theorist.exe migrate-v2 --source C:\fixtures\old\research.sqlite3 --synthetic --destination C:\fixtures\new --apply
```

The source opens in SQLite read-only mode with a consistent snapshot. The converter
checks original v1 hashes, migration checksums, record versions and fixture evidence;
it refuses newer databases and unsupported simulation versions. It preserves the
entire v1 database in a separate destination, installs 003 there, and writes typed
identities/lineage transactionally. The final database appears only after validation.
Neither preview nor apply mutates the source or its installed migrations.

Only an isolated, timestamped initial funding event can cross the accounting
boundary directly. Traded histories, legacy accounting records, ambiguous receipt
times and other unsupported history produce explicit gaps. Existing balances,
realized profit and marks are never relabeled FIFO/TWR, and no lots are fabricated.
All original records/events remain readable under v1. The report stores source
chain/record/migration hashes, conversion version, destination identity and limits.
Exact repeat input is idempotent; changed source or unrelated destination fails.

An interrupted transaction publishes no destination database. Rerun the same command
after ordinary exceptions. If the process itself is terminated while staging, an
unpublished `.v2-stage-*` directory may remain; choose a fresh empty destination and
retain the abandoned staging directory for inspection. No automatic deletion of an
existing unrelated directory or owner history is performed.

## Reproducible evidence

```powershell
.\.venv\Scripts\python.exe scripts/export_schemas_v2.py
.\.venv\Scripts\python.exe scripts/build_step_01_fixtures.py
.\.venv\Scripts\python.exe scripts/check.py test_contracts test_storage test_meta_contracts test_export test_contracts_v2 test_storage_v2
.\.venv\Scripts\python.exe scripts/export_field_classification.py --check
```

`export-v2-schema <output>` also exports the schema without opening a database.
`examples/contracts-v2/` contains the original operational bundle, converted bundle
and checked preview/apply/repeat/gap report. Test databases and verbose test logs
remain local. The field inventory now includes every v2 record and storage column;
unknown/dynamic fields remain denied for public/Git export. No v2 exporter or browser
read model is added by this step.

Validation on 2026-09-06: all 178 tests in 21 modules passed in 24.1 seconds;
the targeted six-module run passed in 6.4 seconds. All 1,048 inventoried fields
passed the drift check, which is also enforced in CI. Both v2 bundles passed CLI validation and the fixture
builder verified the copied v1 hash chain/replay, duplicate apply and explicit gaps.
