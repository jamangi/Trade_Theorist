# Step 03: Private owner dashboard

Implemented 2026-09-06. This guide is the starting point for a fresh task without
conversation history. [The active brief](../tasks/active/STEP-03-dashboard.md)
records validation. [Step 04](../tasks/active/STEP-04-commands.md) is next.

## Reproduce the original fixture

Run from the repository root with the installed environment:

```powershell
.venv/Scripts/python.exe scripts/build_step_03_fixture.py
.venv/Scripts/python.exe -m http.server 8765 --bind 127.0.0.1 --directory .local/private-v2-demo
```

Open `http://127.0.0.1:8765/`; Ctrl+C stops the preview. This development server is
**only for the original synthetic fixture**, not real private bundles. Step 05
owns hardened Windows serving and Host/Origin/path controls. The builder uses a
temporary database and ignored `.local/private-v2-demo/`; no account/model is needed.

Select January 11 as known on January 11: equity 1548, total/available/reserved cash
1188/1088/100, FIFO basis 343, realized gain 28, income 3, TWR 0.05750570 and drawdown
0.01901141. January 12 is stale. January 11 known through January 13 has the explicit
correction (equity 1554), while the original stays selectable. Its baseline becomes
unavailable because the corrected market evidence no longer matches the baseline.

Broker paper shows partial fills, reconciliation, failed heartbeat and unknown
hosting cost. “Inspect simulated control” selects separate capital with matching
frozen decisions/assumptions; no cross-basis return ranking is made. Individual also
shows a no-trade cash portfolio and an unready version without invented results.
Learning notes are original fixture context, not real curriculum completion.

## Implementation map

| Work | Start here | Check |
| --- | --- | --- |
| Read model, lineage/rights, atomic export | `src/trade_theorist/export_v2.py` | `test_export_v2` |
| Private page and filters | `src/trade_theorist/dashboard/private.html`, `private.js` | Browser checklist below |
| Shared tables/charts/dialog/style | `src/trade_theorist/dashboard/app.js`, `style.css` | `test_export`, legacy browser smoke check |
| Authored context record | `inspection_context` in `schema_v2.py`, `contracts_v2.py` | `test_contracts_v2`, `test_export_v2` |
| Original fixture seed | `src/trade_theorist/fixtures_dashboard_v2.py` | Fixture builder |
| Browser schema | `schemas/private-owner-v2.json` | Generated-schema test |

`build_private(store, as_of=...)` reads an explicit `V2Store` without writes.
It verifies the store chain, source permissions, matching projection/source hashes
and core monetary values against read-only replay. `validate_private(report)`
checks the strict allowlist, hash, cutoffs, six connected answers and null reasons.
`export_private(store, destination, as_of=...)` validates before creating output,
writes immutable version assets, then atomically replaces the entry page. An
interrupted handoff preserves the previous valid entry; no retention deletion runs.

Private source rights are checked through typed references and source lineage,
including baseline evidence and authored context. Only necessary browser fields
are copied. Provider/client order IDs, credentials, raw records/responses and
filesystem paths are omitted. A fixture flag cannot authorize real-source output
inside Git: all sources must actually be original synthetic evidence for that
exception. Real private exports require a destination outside Git and must await
Step 05 before browser serving. Source rights remain a separate prerequisite.

Lots and reliefs belong to the exact saved projection. Marks use corrected reducer
state, including withdrawals; evidence panels are scoped to each report cutoff.
Historical selection retains effective and receipt cutoffs. Filters select frozen
Character version, portfolio window, advice, horizon, regime and execution basis.
Rows retain source order and never pool capital or imply promotion.

Optional `inspection_context` records contain saved authored beliefs/rationale,
invalidation, source/edition/locator citations, learning progress, advice disposition,
forecast samples and heartbeat status. Scope is portfolio + funded segment + frozen
Character version + as-known time + source rights. These are authored summaries,
not hidden model reasoning or automatic learning completion. Missing context stays
unknown; readiness comes from the frozen Character record. Step 04 can connect
existing learning/operations to this record without changing v2 accounting.

The private page reuses the existing layout and helpers. It loads its local report
and schema once; interactions use memory only. V1's fixture-only exporter/page
remain separate, with their original accounting meanings. No CLI workflow, model,
broker client, public publishing or real-data server is added in Step 03.

## Validate a change

```powershell
.venv/Scripts/python.exe scripts/check.py test_export_v2 test_export test_contracts_v2 test_accounting_v2 test_broker_v2
.venv/Scripts/python.exe scripts/export_schemas_v2.py
.venv/Scripts/python.exe scripts/build_step_03_fixture.py
.venv/Scripts/python.exe scripts/export_field_classification.py --check
```

Regenerate/review the field inventory after intentional schema changes. Run the
full `scripts/check.py` after focused checks pass. Inspect only failing logs under
`.local/test-logs/`; do not dump generated bundles into a conversation.

Browser checklist: both tabs at 1365×1000 and 390×844; arrow/Home/End tab keys;
keyboard filters and Explain; six answers and evidence dialog; Escape/focus return;
exact history table and horizontal scrolling; stale, corrected, pending, unknown
cost, failed-heartbeat, no-trade and unready states; Character-version selection;
paper/control separation; no requests on interaction. Smoke-check v1 when shared
assets change. Record results in the active brief, update the queue, and push main.
