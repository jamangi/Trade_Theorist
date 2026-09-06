# Focused development and quiet validation

Start with the requested `tasks/TASK-...md` files and their linked design documents.
Use `rg --files src tests scripts` for the implementation map, then targeted symbol
searches and short file slices. Do not print the entire library, schema fixture
bundles, book transcripts or all test files to find a small interface. Generated
examples can be rebuilt and validated without reading their complete JSON output.

Relevant paths for tasks 007–015:

| Work | Implementation | Tests |
| --- | --- | --- |
| Simulation/accounting | `src/trade_theorist/adapters/trader_user_sim/` | `test_simulation` |
| Independent policy | `src/trade_theorist/risk.py` | `test_risk` |
| Persistence/recovery | `src/trade_theorist/storage.py` | `test_storage` |
| Input contracts | `src/trade_theorist/contracts.py`, `schema.py` | `test_contracts` |
| Market evidence | `src/trade_theorist/ingest/market.py` | `test_ingest` |
| Alpaca qualification | `src/trade_theorist/adapters/alpaca_market_data/` | `test_alpaca_adapter` |
| Prospective evidence gate | `src/trade_theorist/forward/`, `ingest/tool_policy.py` | `test_forward_shadow` |
| Mail/heartbeat | `src/trade_theorist/council/`, `heartbeat/` | `test_council`, `test_heartbeat` |
| Metrics/forecast review | `src/trade_theorist/evaluate/` | `test_evaluation` |
| Sanitized dashboard exports | `src/trade_theorist/export.py`, `dashboard/` | `test_export` |
| Offline demo/operating CLI | `src/trade_theorist/operations.py`, `cli.py` | `test_operations` |

Use the environment's Python (on Windows, `.venv/Scripts/python.exe`):

```text
python scripts/check.py test_simulation test_risk
python scripts/check.py test_evaluation test_export test_operations
python scripts/check.py
```

The first command runs only named modules; the second runs the complete suite.
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
