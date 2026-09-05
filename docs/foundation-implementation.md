# Foundation implementation: tasks 001–004

Tasks 001–003 are implemented. Task 004's ordered-learning software and fixture demonstration are implemented; real Index Steward learning remains blocked. The [catalog audit](../library/catalog/ACCESS_REPORT.md) records twelve slots, eleven exact edition candidates, one unresolved edition, and individual access/permission blockers. Nothing has been purchased, no third-party book text has been ingested, and no model API or broker is connected.

## Windows setup and checks

From the repository root, using Python 3.11 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\trade-theorist.exe validate schemas/fixtures/accepted/bundle.json
.\.venv\Scripts\trade-theorist.exe foundation-demo --data-root "$PWD\.local\foundation-demo"
```

Dependency installation requires network access once. The tests and foundation demo then run offline without credentials or model spending. The demo is limited to storage and ordered learning; the two-portfolio observatory, broker simulator, mail delivery and dashboard belong to tasks 005–013. The first run consumes two **recorded fixture responses** and commits two partial checkpoints, two theory cards and their test registrations. Repeating the command reuses the same checkpoints and consumes zero new responses. Private event history retains extraction, authored assimilation, adversarial review and memory deltas. The section-two example qualifies section one's equal-gross assumption, preserving both cited claims in memory.

`examples/learning/` contains the original material, saved responses keyed by complete request hashes, and readable JSON checkpoints/theories. They demonstrate mechanisms only and are separate from `characters/index_steward/`, which contains the approved design prior and real curriculum with **not_ready** status. Synthetic evaluation dates in 2099 ensure fixture registrations precede their toy outcomes; they are not scheduled runs.

## Private storage and recovery

For actual private metadata caches, licensed inputs and future model outputs, configure an absolute directory outside all Git checkouts:

```powershell
$env:TRADE_THEORIST_DATA_ROOT = Join-Path $env:LOCALAPPDATA 'TradeTheorist\private'
.\.venv\Scripts\trade-theorist.exe library report
.\.venv\Scripts\trade-theorist.exe library check
.\.venv\Scripts\trade-theorist.exe learn --character index_steward
```

The last command currently reports the foundational source blocker and exits 2. `library check` checks only known publisher URLs with ten-second timeouts, no automatic redirects and no response bodies. It caches checks for seven days and appends review requests for URL/validator changes, redirects, failed access and missing change validators. `--force` bypasses cache immediately before planned ingestion. The dated publisher inspection in Git is separate from local automated HEAD results; rerunning the metadata-generation script does not claim a new audit.

`Store(root)` rejects relative paths and directories inside a Git checkout. Only `Store(root, synthetic=True)` allows fixture storage in the ignored `.local` directory and it rejects non-fixture records and real learning material. Private data is not encrypted by this package; use an account-protected directory and the host's access controls. Databases, backups, keys, environment files, large outputs and generated mail are ignored by Git.

SQLite migrations have recorded checksums and reject unknown database versions or changed applied migration files. Writers use `BEGIN IMMEDIATE`, WAL and full synchronization. Nested operations use savepoints. Immutable-record and event tables reject SQL updates/deletes. IDs deduplicate identical writes and reject changed payloads. Events form a global SHA-256 chain over canonical JSON; `Store.verify()` checks records, references, SQLite integrity and the chain. This detects inconsistencies, not a malicious administrator who can rewrite the database and all hashes. Corrections must append new records/events.

```python
from pathlib import Path
from trade_theorist.storage import Store

with Store() as store:
    print(store.verify())
    backup = store.backup(store.root / "backup-001.sqlite3")

# Choose a new, empty private directory. Existing databases are never overwritten.
with Store.restore(backup, Path(backup).parent / "restored-001") as restored:
    print(restored.verify())
```

`run_phase()` holds a writer transaction around deterministic local effects. Completed phase output is reused, changed input hashes require a new run, and failed phase effects roll back. Phase transitions, failure codes and model usage are immutable events; the initial manifest remains unchanged. `replay(experiment_id, reducer, initial_state)` derives state from saved ordered events. Tests demonstrate exact Decimal replay, deduplication, nested rollback, actual abrupt process exit, concurrent writers and backup restoration. External model calls never run inside a long-held SQLite write transaction.

The checked-in run manifest is a synthetic contract specimen referencing the design baseline commit. Each actual foundation-demo invocation appends executing Git commit, package version, Python source-tree hash and recorded-output hash in `run.provenance`; it does not claim that the example manifest describes the current checkout. Frozen input/response events and their hashes are the replay authority. A changed implementation must be reviewed before using an old experiment for further work.

## Ordered learning API

The Python API is `Learner(Store, BoundedModel)`. Register the complete reference bundle first. `freeze()` checks the pinned constitution and curriculum hashes, foundation identity, earlier-book completion, source permissions, access recency, scope and section order, and saves the prior and entire supplied material privately. `step()` advances one section, validates locators and short quotations, and commits checkpoint, test registration, theory and delta atomically. Every section keeps the previous checkpoint hash and cited consolidated memory. Partial samples and fixture material can never become full-book completion or unblock the next approved book. Restarting does not skip or duplicate sections.

For a real source, the acquisition operator must register the correct edition, actual permitted passages in source order, scoped rights evidence and independently verified coverage. The API does not acquire books, bypass access controls, infer a full book from a sample, or infer permissions from HTTP success. The real curriculum remains blocked until that prerequisite exists. Substantive extraction/assimilation review is still necessary: a matching quote is evidence of available text, not a proof that the model interpreted it faithfully. Consolidation is an append-only cited memory view; explicit amendments and retirement policies can be layered on it later.

`BoundedModel` accepts a provider callable receiving a bounded request and `max_output_tokens`, returning `{response, usage}`. Requests pin source, constitution, prior memory, model, prompt, sampling settings and output schema; source content is labeled untrusted evidence and no tools are supplied. `RecordedProvider` requires an exact input hash and is the only bundled provider. No paid provider is enabled. A real provider adapter must enforce the output cap and report usage correctly.

Before calling a provider, the adapter persists an immutable budget and conservative input-byte/output-token reservation. Completed responses are cached; malformed semantic responses are retained privately and rejected without repeated calls. A timeout or crash after reservation is ambiguous and cannot auto-retry. Its reservation remains charged against the cap and unknown cost remains null. A new explicitly allocated budget is required for another attempt; changing an existing budget's caps is rejected. This bounds automatic retries but cannot undo a provider charge made before an interrupted response arrives.

Public logs accept only fixed status codes, recognized phases and hash-format run IDs. Prompts, responses, free-form exception messages and arbitrary fields never enter public logs. Detailed model provenance and outputs remain in the private database. No public export or scheduled operation is introduced by these tasks.

## Acceptance evidence and remaining work

The automated suite covers all contract kinds and each required field, rejected fixtures, explicit v0 migration, foreign references, future/ineligible observations, paper-policy completeness, source access/scope, changed materials, chapter ordering, quote verification, response reuse after interruption, ambiguous failures, usage exhaustion, URL caching/review, immutable storage and recovery. `pip check` verifies the installed dependency set. The foundation demo was run twice: two sections on the first run and zero new responses on the second, with the same checkpoint IDs and event-chain tip when code was unchanged.

Complete the unresolved edition/access/permission reviews before claiming real Character learning. Acquire the approved Bogle foundation with permitted machine ingestion/private storage, verify its full section coverage and then run the reviewed adapter with a pinned real experiment. Task 005 may use the verified fixture interface under the queue's partial-dependency rule; it may not report real specialists trained. Tasks 005–023 have not been launched here.
