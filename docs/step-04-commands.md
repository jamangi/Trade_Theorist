# Step 04: explicit private commands

Implemented 2026-09-06. Start with the [Windows quickstart](quickstart.md) to run
both versions. This is the bounded handoff for a fresh task; no conversation history
or large generated JSON read is needed. Step 05 is next and owns protected serving.
No account transport, order submission or recurring run was added.

## Command contract

Operating commands accept `--projection-version 1|2`. CLI selection overrides config
`projection_version`; the compatibility default is v1. Config `schema_version`
remains 1 and describes the config format. Invalid versions, unknown fields and
malformed path types fail with bounded diagnostics. Demo is always synthetic.

| V2 command | Inputs and behavior |
| --- | --- |
| `demo` | Dedicated absolute data root and optional output root. Atomically seed original production-ledger fixtures with a recipe receipt; export separately. Defaults are in the quickstart. |
| `doctor` | Existing data and output roots. Read-only SQLite snapshot; migration checksums, chain verification, rights inventory, saved-result validation, missing/halted reconciliation and accounting gaps. No credential values or account calls. |
| `evaluate` | Existing migrated v2 root, `--portfolio`, explicit UTC `--as-of`, optional UTC `--receipt-cutoff` (defaults to as-of). Optional `--experiment` asserts portfolio membership. Saves/reuses production FIFO/TWR results, including gap/halt states. |
| `export` | Existing migrated v2 root, `--output-root`, explicit UTC `--as-of`. Read-only database; all permitted saved results created by cutoff, with exact effective/receipt versions and shared comparison lineage. Rejects `--experiment` rather than silently ignoring it. |
| `ingest`, `heartbeat` | V2 orchestration is not implemented; return an actionable boundary before opening storage. V1 commands and existing production v2 APIs remain available. |

`validate <report.json>` recognizes the private v2 read-model schema and content
hash as well as the v1 allowlist. Doctor/export additionally verify stored lineage
and replay. The bundle root must not equal or contain the data root. Real storage
and bundles belong outside every Git checkout, including worktrees with a `.git`
file. Export checks actual lineage even with `--fixture`; fixture selection grants
no rights. Original synthetic bundles may remain in ignored repository paths.

## Prerequisites and recovery

Exit 0 means completion (doctor may say `ready_with_gaps`); 2 names a prerequisite;
1 identifies a failed phase with a resume action. Raw exception/account values are omitted.

| Condition | Action |
| --- | --- |
| Missing database | Select existing v2 evidence or run demo in a new dedicated root. Doctor/export never initialize storage. |
| Missing migrations | Require verified migrations 001–004. Preview `migrate-v2 --source <absolute research.sqlite3> --synthetic` for supported synthetic v1 input, then explicitly apply to a separate destination. This does not convert arbitrary v1 trades or owner data. For an already-v2 store needing additive migration, back up and explicitly open `V2Store` with the matching package after review; command preflight never silently upgrades it. |
| Changed/unknown migrations or broken chain | Use the matching package and review/restore verified evidence; doctor never repairs it. |
| Missing rights | Record reviewed private storage/replay/read-model permissions for the referenced lineage. Doctor inventories all rights; export checks those used by its cutoff. |
| Reconciliation/valuation gaps | Inspect gaps, reconcile saved broker/account evidence through the offline API, and evaluate again. Gaps can limit accounting/admission without blocking inspection. Doctor describes saved evidence, not current account truth. |
| Interrupted seed | Repeat demo with the same roots. The entire seed and receipt commit together or roll back together. |
| Interrupted evaluation | Repeat the same portfolio and both cutoffs. Successful immutable results are reused; no orders are created. |
| Interrupted export | Fix output access/rights/integrity, then repeat at the same cutoff. The previous entry remains until atomic replacement; demo retries reuse committed seed/evaluations. |

Saved-data inspection does not require a trained Character, profitable record or
paper-trading approval. Delayed SIP is useful historical input; request coordination/
qualification remain separate work. Real browser serving is pending Step 05. This
step neither treats unresolved vendor rights as a prohibition nor treats access
alone as proof of every permission.

## Reproduce with bounded output

Use the environment's Python (`.venv/Scripts/python.exe` on Windows):

```text
python scripts/check.py test_operations_v2 test_operations test_export_v2 test_storage_v2
python scripts/check_installed.py --wheelhouse .local/wheelhouse
python scripts/check.py
```

The installed check builds a wheel, creates a fresh virtual environment outside the
checkout, installs locked dependencies from the wheelhouse with `--no-index`, and
exercises v1/v2 demo, resume, evaluate, export, doctor and validate. A socket trap
rejects connections; imports must come from the installed package. Both demos have
zero model calls. No server starts. Logs, report artifacts and `evidence.json` stay
in ignored `.local/installed-logs/`; only one success line or a failed phase's bounded
log tail reaches the console.

Dependency acquisition is separate: where downloads are permitted,
`python -m pip download -r requirements.lock -d .local/wheelhouse` prepares wheels
for that Python/platform. The check itself never downloads. The development
environment must already contain the locked build dependencies.

Read only a failing module's log under `.local/test-logs/`. Run the full suite once
after focused checks pass. Actual checks are in the [Step 04 brief](../tasks/active/STEP-04-commands.md).

| Responsibility | File / tests |
| --- | --- |
| Version/config routing, artifact validation | `src/trade_theorist/cli.py`; `tests/test_operations_v2.py`, existing `test_operations.py` |
| Read-only diagnostics, private commands, atomic demo receipt | `src/trade_theorist/operations_v2.py`; `tests/test_operations_v2.py` |
| Existing accounting, read model and fixtures | `evaluate/portfolio_v2.py`, `export_v2.py`, `fixtures_dashboard_v2.py`; `test_accounting_v2`, `test_export_v2`, `test_storage_v2` |
| Clean install and concise evidence | `scripts/check_installed.py`; `.local/installed-logs/evidence.json` |

No dashboard asset or schema change was needed. Step 03's browser evidence remains
in its guide. Begin Step 05 with this guide and its brief; implement its server
protections rather than enabling the generic v1 preview for real bundles.
