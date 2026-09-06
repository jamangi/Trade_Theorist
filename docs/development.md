# Focused development and quiet validation

Start with [the active ordered queue](../tasks/README.md) and the requested active STEP brief. Original TASK files preserve historical evidence; they are not the active execution order. Read the brief's linked design documents.
Use `rg --files src tests scripts` for the implementation map, then targeted symbol
searches and short file slices. Do not print the entire library, schema fixture
bundles, book transcripts or all test files to find a small interface. Generated
examples can be rebuilt and validated without reading their complete JSON output.

Relevant implementation and validation paths:

| Work | Implementation | Tests |
| --- | --- | --- |
| Simulation/accounting | `src/trade_theorist/adapters/trader_user_sim/` | `test_simulation` |
| Independent policy | `src/trade_theorist/risk.py` | `test_risk` |
| Persistence/recovery | `src/trade_theorist/storage.py` | `test_storage` |
| Input contracts | `src/trade_theorist/contracts.py`, `schema.py` | `test_contracts` |
| Production v2 contracts/storage | `schema_v2.py`, `contracts_v2.py`, `storage_v2.py`, `migrate_v2.py` in the package | `test_contracts_v2`, `test_storage_v2` |
| Persistent v2 FIFO/TWR | `adapters/trader_user_sim/v2.py`, `evaluate/ledger_v2.py`, `evaluate/portfolio_v2.py` in the package | `test_accounting_v2` |
| Offline v2 broker reconciliation | `adapters/trader_user_sim/broker_v2.py` in the package | `test_broker_v2` |
| Market evidence | `src/trade_theorist/ingest/market.py` | `test_ingest` |
| Alpaca qualification | `src/trade_theorist/adapters/alpaca_market_data/` | `test_alpaca_adapter` |
| Prospective evidence gate | `src/trade_theorist/forward/`, `ingest/tool_policy.py` | `test_forward_shadow` |
| Mail/heartbeat | `src/trade_theorist/council/`, `heartbeat/` | `test_council`, `test_heartbeat` |
| Metrics/forecast review | `src/trade_theorist/evaluate/` | `test_evaluation` |
| Sanitized dashboard exports | `src/trade_theorist/export.py`, `dashboard/` | `test_export` |
| Private v2 dashboard | `src/trade_theorist/export_v2.py`, `dashboard/private.html`, `dashboard/private.js` | `test_export_v2`; [browser checklist](step-03-private-dashboard.md) |
| Offline demo/operating CLI | `src/trade_theorist/operations.py`, `cli.py` | `test_operations` |

Use the environment's Python (on Windows, `.venv/Scripts/python.exe`):

```text
python scripts/check.py test_simulation test_risk
python scripts/check.py test_evaluation test_export test_operations
python scripts/check.py test_contracts_v2 test_storage_v2
python scripts/check.py test_accounting_v2 test_broker_v2
python scripts/check.py test_export_v2 test_export
python scripts/check.py
```

Commands naming modules run only those modules; the last runs the complete suite.
Each module runs sequentially in its own process, releasing its Python memory on
exit. Standard output and errors go directly to ignored `.local/test-logs/` files,
without accumulating captured output in the parent. Console output is one result
per module plus a final summary; any failure returns a failing exit status. Read
only the failing module's log, starting with its first traceback. The runner does
not suppress tests, assertions, warnings or failure details in those logs. CI uses
the same command and uploads the logs on failure.

During tasks 007–008, the complete suite took about six seconds locally. We did not
reproduce an out-of-memory failure or measure a root cause. These changes reduce
console/context volume and cross-module retained memory; they do not establish
that the old test runner caused the reported problem. `Store.record()` now reads
one immutable record, and `Store.iter_events()` streams optional experiment/kind/
portfolio selections. Verification streams the event chain once rather than
materializing it twice. Whole-record bundle validation still loads record history;
further optimization should follow a measured workload rather than weaken contract
checks. Historical orders in an individual portfolio also still grow with activity.

After focused tests pass, run the full suite once before delivery. Repeat only if
further edits or an unresolved failure justify it. Record the validation results
and any real-data blockers in the task files; do not open their dependents implicitly.

For Step 02, `python scripts/build_step_02_fixtures.py` rebuilds and verifies the
golden and v1/v2 side-by-side artifacts without printing their full JSON bundles.
Use `python scripts/export_field_classification.py --check` to check schema/field
inventory drift. [The accounting guide](step-02-accounting.md) gives the API map,
math and unsupported cases, so subsequent work can begin with one bounded document.

## Continue without conversation history

The owner clarified that the reported memory issue is repeated “Optimizing the
conversation” without progress, rather than a demonstrated Python RAM failure.
Treat repository documentation as the handoff, not a cached conversation. Start
with `tasks/README.md`, the requested active brief, and its implementation guide.
Read only the relevant implementation slices and failing logs. Rebuild generated
fixtures to validate them instead of printing the full JSON.

For substantial work, maintain a short working note under `tasks/active/` with
current decisions, files, exact next action and checks already run. Replace it with
the final task evidence before delivery. Keep the queue and root README's next step
current, and push authorized completed work so a fresh task can reproduce it from
main. Historical TASK files retain evidence; they need not be reread as a transcript.
