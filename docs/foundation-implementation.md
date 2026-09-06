# Foundation implementation: tasks 001–004

Tasks 001–004 are implemented, including [Index Steward's real foundational reading](index-steward-foundation.md). The owner supplied the 2017 Bogle ePDF; its introduction and all 20 chapters have cited checkpoints. The [catalog audit](../library/catalog/ACCESS_REPORT.md) keeps thirteen edition records for twelve slots, including the earlier hardcover candidate. Other source blockers remain. No book was purchased and no model API or broker is connected.

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

`examples/learning/` contains original synthetic material, saved responses keyed by request hashes, and JSON checkpoints/theories. It remains separate from the real [Index Steward](../characters/index_steward/README.md), which now has a completed first source. Synthetic evaluation dates in 2099 ensure fixture registrations precede their toy outcomes; they are not scheduled runs.

## Private storage and recovery

For actual private metadata caches, licensed inputs and future model outputs, configure an absolute directory outside all Git checkouts:

```powershell
$env:TRADE_THEORIST_DATA_ROOT = Join-Path $env:LOCALAPPDATA 'TradeTheorist\private'
.\.venv\Scripts\trade-theorist.exe library report
.\.venv\Scripts\trade-theorist.exe library check
.\.venv\Scripts\trade-theorist.exe learn --character index_steward
```

The last command validates the published completion and reports `foundation_complete`, one book read, three unread and no performance evaluation. Without a completion record it reports the source blocker and exits 2. `library check` checks publisher URLs with ten-second timeouts, no automatic redirects and no response bodies. It caches metadata for seven days and appends review requests. It cannot establish local possession, renew local authorization, or change learning status. The generation script preserves the dated original audit and the separately recorded acquisition.

`library report` now defaults to the [all-Character local inventory](../library/catalog/characters.json); use `--catalog library/catalog/pilot.json` to inspect the historical publisher scope. `library verify-files --books-root <local-books-directory>` checks the supplied PDF fingerprints without extracting text. See the [library guide](../library/README.md). The learning command continues to use its frozen pilot source so the completed Bogle run stays reproducible.

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

The Python API is `Learner(Store, BoundedModel)`. Register a reference bundle first. `freeze()` checks constitution/curriculum hashes, foundation identity, earlier-book completion, source permissions, access recency, scope and section order, and saves the prior and material privately. It can preserve an externally frozen, empty-memory design prior with its original predictions and timestamp. Each model request receives only the current section and earlier memory; the full material is pinned by hash. `step()` validates short quotations against a section or its exact marked PDF page and atomically commits a checkpoint and delta. A theory and test are optional, but must be promoted together. Every section retains the previous checkpoint hash and cited memory. Samples and fixtures cannot become full-book completion; restarting cannot skip or duplicate sections.

For a real source, register the correct edition, available passages in source order, scoped authorization and reviewed coverage. A `learning_session` can hold source learning without inventing a market universe or paper policy; market records are prohibited in that scope. The API does not infer book access from a sample or permissions from HTTP success. A matching quote establishes availability, not faithful interpretation. The Bogle run includes substantive extraction, assimilation and challenge, with a readable constitution amendment and preserved intermediate states.

`BoundedModel` accepts a callable receiving a bounded request and `max_output_tokens`, returning `{response, usage}`. Requests pin source, constitution, prior memory, model, prompt, sampling settings and output schema; source content is untrusted evidence and no tools are supplied. `RecordedProvider` requires an exact input hash. `ReviewedTranscriptProvider` deterministically imports a separately attributed review and verifies source/Character inputs. Its zero tokens/cost describe import only; original authoring usage and settings may be unknown. No paid provider is enabled.

Before calling a provider, the adapter persists an immutable budget and conservative input-byte/output-token reservation. Completed responses are cached; malformed semantic responses are retained privately and rejected without repeated calls. A timeout or crash after reservation is ambiguous and cannot auto-retry. Its reservation remains charged against the cap and unknown cost remains null. A new explicitly allocated budget is required for another attempt; changing an existing budget's caps is rejected. This bounds automatic retries but cannot undo a provider charge made before an interrupted response arrives.

Public logs accept only fixed status codes, recognized phases and hash-format run IDs. Prompts, private responses and arbitrary exception messages never enter public logs. Bogle's reviewed public export selects original claims, citations and learning records, excluding material and request events. JSON exports reject changed content and preserve existing bytes when a repeat has equivalent JSON key order. No scheduled operation was added.

## Acceptance evidence and remaining work

The automated suite covers all contract kinds and each required field, rejected fixtures, explicit v0 migration, foreign references, future/ineligible observations, paper-policy completeness, source access/scope, changed materials, chapter ordering, quote verification, response reuse after interruption, ambiguous failures, usage exhaustion, URL caching/review, immutable storage and recovery. `pip check` verifies the installed dependency set. The foundation demo was run twice: two sections on the first run and zero new responses on the second, with the same checkpoint IDs and event-chain tip when code was unchanged.

The 48-test suite and completed [Bogle import](index-steward-foundation.md) establish TASK-004's bounded deliverable. Remaining books, specialist learning and market/paper prerequisites are still explicit. Tasks 005–023 have not been launched here.

## Supplied transcripts and revised source scopes

The current inventory has 30 PDFs and two supplied transcripts. File verification checks all 32 artifacts. Transcript records bind text hashes to source PDF hashes. `pages_from_transcript(path, expected_sha256=..., expected_pages=...)` verifies text identity and sequential page markers, then returns private pages for a reviewed reading pass. It does not generate OCR or certify fidelity.

Materials can now declare `full_paper` or `approved_excerpt` as well as `full_book`. Papers and excerpts require matching scope in the pinned curriculum; excerpts also require nonempty `scope_authorization`. Completeness means reviewed coverage of the declared material, not omitted published pages. The next source requires a completed checkpoint for the exact preceding source and its declared scope. Generic samples and fixtures remain partial. Reviewed-material helpers accept `scope`, defaulting to `full_book` to preserve Bogle reproduction. [ADR-002](../decisions/records/ADR-002-microstructure-reading-scope.md) records the owner's decision.
