# Start here after META-001

Date: 2026-09-06. **Next bounded task: [TASK-024-high-Sol.md](../TASK-024-high-Sol.md)**, additive production v2 contracts and persistence. META-001 is complete; its [impact/evidence report](../../docs/meta-001-impact.md) records the checks and implementation boundary. Do not start by renaming the UI, enabling Alpaca calls or implementing all downstream tasks in one turn.

## Why this task first

The earliest affected boundary is TASK-001's v1 record contract, followed by TASK-002 persistence. The actual engine currently uses average-cost lots and endpoint returns, and its mode is singular `character_portfolio`. A label-only/private-path change would leave FIFO, external-flow return and paper attribution unproven. Preserve those old facts and add explicit versioning before calculation/UI integration.

## Inputs and exact scope

Read [ADR-004](../../decisions/records/ADR-004-local-observatory.md), [performance v2](../../docs/portfolio-performance-v2.md), [rights matrix](../../docs/data-rights-matrix.md), the [golden performance fixture](../../examples/meta-001/performance-v2.fixture.json), and [broker fixture](../../examples/meta-001/broker-attribution-v1.fixture.json). The owner defaults in [APPROVALS.md](APPROVALS.md) cover this direction.

Inspect `src/trade_theorist/schema.py`, `src/trade_theorist/contracts.py`, `src/trade_theorist/storage.py`, `src/trade_theorist/migrations/`, `scripts/export_schemas.py`, `tests/test_contracts.py`, `tests/test_storage.py` and `tests/test_meta_contracts.py`. Add v2 schema/version dispatch and a forward-only side-by-side persistence migration. Do not edit old migrations, overwrite owner data, implement broker submission or claim the reference-test reducer is a production ledger. Keep `council` and `character_portfolio` serialized values.

## Acceptance commands

From the repository root on Windows:

```powershell
.venv/Scripts/python.exe scripts/check.py test_contracts test_storage test_meta_contracts test_export
.venv/Scripts/python.exe scripts/export_field_classification.py --check
```

Add/run the new v2 schema/storage tests required by TASK-024; the commands above alone do not establish a new implementation. After focused checks pass, run `.venv/Scripts/python.exe scripts/check.py` once. Use existing quiet logs and inspect only failures. Record actual results and migration/dry-run evidence in TASK-024. The new field inventory must be regenerated and reviewed, never automatically made public.

## Migration order and independent work

1. **024:** typed v2 identities/events/rights and side-by-side persistence; preserve original hashes.
2. **025:** actual FIFO/flow-aware projection, matched execution comparisons and offline reconciliation; test against golden vectors.
3. **012 follow-up → 013 follow-up → 018:** private owner read model, Individual/Monarchy presentation and hardened local packaging. Synthetic acceptance needs no broker access.
4. **014 shared controls → 016 offline rate preflight → 014 coordinator-backed qualification → 015 forward observations → 016 final readiness → 017:** preserve the separate account/forward/paper gates. The preflight uses fixture controls; full final-review dependencies do not prevent that narrow earlier check.

Source-grounded Character learning can continue independently under its approved ordered curricula. Rate-limiter unit implementation can also proceed against fixtures; any integration with changed v2 contracts must use 024 outputs. Never treat a schema migration as permission to collect data or spend recurring model usage.

## Blockers and stop condition

There is **no new approval blocker for TASK-024's synthetic code/migration work**. Provider retention/replay/model-processing rights, eligible Character versions, exact paper limits/operator assignments and real elapsed evaluation windows remain blockers at the corresponding later gates. Do not read `.env`, call Alpaca, send mail to the provider, purchase anything, or deploy a real-data site to resolve this task.

Stop TASK-024 after its additive contract/storage implementation, checked synthetic migration and validation record. Hand off 025 as the next task; do not silently mark FIFO, TWR, private UI or paper integration complete.
