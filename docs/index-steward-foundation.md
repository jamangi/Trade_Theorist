# Index Steward: completed foundational reading

TASK-004 is complete as of 2026-09-05. The supplied file appears to be the correct 2017 tenth-anniversary edition of *The Little Book of Common Sense Investing*, by John C. Bogle: title page at PDF page 9, copyright and ePDF ISBN 9781119404521 at page 10, 305 PDF pages, introduction and all 20 chapters, acknowledgments and closing license pointer. Its publisher authenticity and acquisition history were not independently certified.

The file was copied to `library/sources/private/bogle-2017-common-sense-investing.pdf`, an ignored local folder. Its SHA-256 is `b5c2c3136dc2fda5b24a584b3ad23ffbc7ae9ed46c750155badfe1303d5e68e3`. The public repository receives original analysis, citations and code. The PDF, extracted pages, renders, requests and detailed private events are excluded. The owner's supplied-file request authorizes this bounded analysis and copy; it is not recorded as a publisher redistribution license. [Acquisition record](../library/catalog/bogle-2017-acquisition.json).

## What was read and retained

The design prior and predictions were frozen before reading the body. Codex read the introduction and chapters in source order, appending original review notes. Front matter and back matter were inspected separately. The cited text anchors were verified against their actual pages; representative identity pages and figures were rendered and visually checked. No other curriculum book was reported read.

The result contains 21 checkpoints, 26 accepted claims, 17 qualified claims, three rejected claims, each section's assimilation and adversarial review, append-only memory deltas, consolidated memory and one falsifiable theory with a prospective test registration. PDF locators are one-based; printed Arabic page numbers are PDF page minus 34. The [review transcript](../characters/index_steward/checkpoints/bogle-2017-reading-review.json) and [current Character](../characters/index_steward/README.md) are the main reading entry points.

Qualifications are substantive: cost arithmetic does not promise positive returns; hypothetical compounding examples remain hypothetical; survivor and cash-flow conventions matter; the book's current-at-publication figures are dated; advisory value differs from selection alpha; ETFs are vehicles; and allocation depends on liabilities and risk capacity. Claims involving correlation, allocation statistics, Social Security examples and current tax treatment are not promoted to executable inputs without independent verification. The author's home bias and skepticism of active/factor alternatives remain explicit tensions.

## What the run means

The authoring model was the current Codex GPT-6-family session. Exact model snapshot, original generation token counts, price and sampling settings were not exposed. Current model background knowledge and context carryover cannot be removed. Accordingly, this is an attributed source review labeled **hindsight-contaminated**, not an independently regenerated chapter experiment, a weight-training run, or prospective investment evidence.

`ReviewedTranscriptProvider` imports the already-authored transcript deterministically into the bounded learning engine, validating frozen source/constitution/curriculum inputs and section/page anchors. `recorded-codex-source-review-v1` names this import adapter. Its zero generation tokens and zero cost describe the local import only; they do not assert that the original Codex review was free. The recorded temperature/seed likewise describe deterministic playback, not unavailable original authoring settings. Import timestamps are actual persistence times; the earlier prior freeze and review-completion times are recorded separately.

The immutable Character record pins the initial `partial` state and original design constitution. Completion is derived from its ordered final checkpoint; the readable v1 constitution appends the resulting beliefs. The run manifest was frozen immediately before export and retains `export: pending`; the immutable `learning.public_export` event and public completion record establish the subsequent successful export. Code commit and source-tree hash identify the executing implementation, including uncommitted source at import time. Later maintenance provenance appends without replacing that history.

## Reproduce or inspect

Public review and structural validation need no PDF, credentials or paid provider:

```powershell
.\.venv\Scripts\python.exe -m trade_theorist learn --character index_steward
.\.venv\Scripts\python.exe -m trade_theorist validate characters/index_steward/checkpoints/bogle-2017.bundle.json
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

To verify source passages and replay the attributed review on a machine with the same authorized PDF, install the optional reader and use an external private directory:

```powershell
.\.venv\Scripts\python.exe -m pip install '.[learning]'
$bookData = Join-Path $env:LOCALAPPDATA 'TradeTheorist/private/index-steward-bogle-2017-v1'
.\.venv\Scripts\python.exe scripts/import_bogle_review.py --data-root $bookData --stop-after 2
.\.venv\Scripts\python.exe scripts/import_bogle_review.py --data-root $bookData
```

The importer defaults to the ignored source path; `--pdf` accepts another local path. It checks the exact PDF hash, page count, ordered coverage, original prior and review hashes, and every supporting anchor. The private store must remain outside Git. Recheck local access/authorization when its dated check expires; an HTTP success cannot renew it. This review does not require an ongoing schedule or another model service.

The original private run is resumable. A new private database creates new actual import timestamps and therefore a distinct run; its exports must go to a new directory using `--export-dir`, so the published historical checkpoints are never overwritten. The deterministic review contents remain the same, but a new import is not byte-identical historical provenance.

## Verification and remaining scope

The real import was interrupted after two sections, then resumed through the remaining 19. A completed rerun used zero new imports and kept all 48 records. SQLite integrity, references and event hashes passed. The 48-test suite covers section-only requests, page-bound citations, non-trading learning scopes, optional theory promotion, immutable exports, partial/resumed learning and published-completion integrity, alongside the original contract/storage/library checks.

The first source is complete; the other three Index Steward books and the other pilot Characters remain unread. The cost hypothesis has not been evaluated. It specifies a future comparison with failure/inconclusive conditions and must expire if prerequisites are not met before its window. No market-data feed, portfolio experiment, broker, scheduled job or downstream task was launched.
