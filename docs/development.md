# Focused development and quiet validation

Start with [the active ordered queue](../tasks/README.md) and the requested active STEP brief. Original TASK files preserve historical evidence; they are not the active execution order. Read the brief's linked design documents.
Use `rg --files src tests scripts` for the implementation map, then targeted symbol
searches and short file slices. Do not print the entire library, schema fixture
bundles, book transcripts or all test files to find a small interface. Generated
examples can be rebuilt and validated without reading their complete JSON output.

Relevant implementation and validation paths:

Finite observation operations: `src/trade_theorist/observation_job.py`,
`scripts/run_step_11_job.py`, `scripts/install_step_11_tasks.ps1` and
`test_observation_job`; [11A/11B handoff](step-11-automation.md).
Preserve Step 11's frozen runtime files while its window is active. The launcher
lives outside that hash set. The native Windows scheduled rehearsal is a separate
read-only deployment check; passing unit tests does not prove account/path binding.

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
| Shared admission/cache/recovery | `market_requests.py`, `request_contracts.py`, `request_operations.py` | `test_market_requests`; [bounded handoff](step-06-shared-requests.md) |
| Alpaca qualification | `src/trade_theorist/adapters/alpaca_market_data/` | `test_alpaca_adapter` |
| Per-instrument qualification quality | `quality_report` in the Alpaca adapter; `examples/step-09/` | `test_quality_qualification`; [bounded rights/quality handoff](step-09-vendor-qualification.md) |
| Private account qualification and persisted replay | `scripts/qualify_step_09.py`; transport diagnostics; `RevisionBook` | `test_live_qualification`, `test_ingest`; [Step 09](step-09-vendor-qualification.md). Rehearsal is offline; live command prints counts only and keeps raw data outside Git. |
| Prospective evidence gate | `src/trade_theorist/forward/`, `ingest/tool_policy.py` | `test_forward_shadow` |
| Cited pilot participant readiness | `learn/readiness.py`, `scripts/review_step_10.py` | `test_pilot_readiness`; [scope, versions and next learning units](step-10-pilot-readiness.md) |
| Shared v2 forward integration | `forward/shared.py`, `forward/validation.py`, `forward/schema.py` | `test_forward_shared`; [bounded handoff](step-07-forward-integration.md) |
| Foundation continuations and real forward trial | `learn/continuation.py`, `forward/prospective.py`, `forward/trial.py`, `forward/observe.py` | `test_foundation_continuations`, `test_prospective_trial`; [Step 11 handoff](step-11-forward-observation.md) |
| Private corporate-action requests | `adapters/alpaca_market_data/actions.py`, `market_requests.py`, `request_contracts.py` | `test_corporate_actions`, `test_market_requests`, `test_live_qualification` |
| Independent shared-path preflight | `tests/preflight_support.py`, `tests/preflight_worker.py`, `scripts/run_step_08_preflight.py` | `test_request_preflight`; [findings and concise reproduction](step-08-offline-preflight.md) |
| Mail/heartbeat | `src/trade_theorist/council/`, `heartbeat/` | `test_council`, `test_heartbeat` |
| Metrics/forecast review | `src/trade_theorist/evaluate/` | `test_evaluation` |
| Sanitized dashboard exports | `src/trade_theorist/export.py`, `dashboard/` | `test_export` |
| Private v2 dashboard | `src/trade_theorist/export_v2.py`, `dashboard/private.html`, `dashboard/private.js` | `test_export_v2`; [browser checklist](step-03-private-dashboard.md) |
| Offline demo/operating CLI | `src/trade_theorist/operations.py`, `cli.py` | `test_operations` |
| Private v2 commands and read-only diagnostics | `src/trade_theorist/operations_v2.py`, `cli.py` | `test_operations_v2`; [installed-package check](step-04-commands.md) |
| Protected bundles and local serving | `private_bundle.py`, `local_server.py`, `export_v2.py` | `test_local_server`; [launch/browser/installed checklist](step-05-local-package.md) |

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

Step 08 adds a separate quiet audit command:
`python scripts/run_step_08_preflight.py --output .local/preflight-logs/recheck.json`.
It prints one result per case; independent transport traces go to the JSON and
tracebacks to ignored logs. Preserve the committed baseline and final artifacts.
Use the guide's finding table and case map before opening any large trace.
