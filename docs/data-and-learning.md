# Data acquisition and the learning library

Status (2026-09-06): catalog, ordered learning and permitted-CSV point-in-time ingestion are implemented. The [current inventory](../library/catalog/INVENTORY_REPORT.md) records 30 PDFs and two transcripts covering all 31 active positions. Index Steward's Bogle foundation is complete; Value and Trend each have one partial opening checkpoint and remain ineligible for real recommendations. The owner adopted the limited Harris draft and five papers for Microstructure; missing original books are retired targets. No market-data vendor or subscription is selected. See [tasks 005–006 evidence](task-005-006-implementation.md).

## A cheap data path

Start with synthetic fixtures and an import adapter for owner-supplied, permitted CSV. Build the ledger and report before paying for coverage. Next, evaluate one daily market-data adapter for forward observation, then add archival coverage and quotes only when an experiment needs them. A current watchlist is acceptable for a forward pilot; using today's survivors for historical tests requires an explicit selection-bias label.

Ordinary scripts perform downloads, pagination, retries, normalization, hashing, database writes, validation, metrics, and exports. Models interpret a bounded set of new evidence and create reasoning records. Fetch once per instrument/session/feed, share the immutable observation across Characters, and use checkpoints to resume. Repeatedly asking an agent for the same market prices is not the ingestion design.

| Candidate / source | Useful role | Limitation or decision still needed |
| --- | --- | --- |
| Permitted CSV and synthetic fixtures | Immediate deterministic development | Fixtures demonstrate mechanics, not an edge; real CSV needs provenance and rights |
| Alpaca market-data API | Candidate for a small forward-data pilot | Feed entitlement, coverage, storage and display rights must be checked for the actual account |
| Alpaca paper environment | Optional later execution-adapter validation | Separate simulation, not a substitute for internal per-Character ledgers or evidence of real fills |
| SEC EDGAR APIs | Primary company filings and financial facts for Value/Event research | Preserve filing vintages; this does not provide stock prices or House/Senate transaction reports |
| Broader licensed archival vendor, to be selected | Delistings, historical membership, corporate actions, quote coverage | Obtain a requirements-matched sample and rights record before choosing or paying |

Alpaca distinguishes single-exchange IEX from consolidated SIP in its [historical-data guide](https://docs.alpaca.markets/us/docs/historical-stock-data-1). Its [FAQ](https://docs.alpaca.markets/us/docs/market-data-faq) distinguishes recent SIP access from older historical queries; test the exact requested interval rather than inferring all entitlements from “free.” Its [paper guide](https://docs.alpaca.markets/us/docs/paper-trading) describes paper-only IEX access and limitations including omitted dividends. A paper account's execution prices and the research feed can differ; record both. These are reasons to evaluate Alpaca first, not a completed vendor selection or redistribution grant.

The [SEC EDGAR API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) describes unauthenticated submissions and XBRL APIs and bulk downloads. Follow the SEC's current [developer access guidance](https://www.sec.gov/about/developer-resources). Resolve issuer IDs and filing accession numbers; do not join on mutable ticker alone or substitute a later restatement into an earlier decision.

## Adapter and quality contract

An adapter declares instruments, sessions, intervals, feed, adjustment basis, pagination behavior, revisions, and missing-data semantics. Preserve raw content hashes and vendor request metadata. Keep credentials in local environment/secret storage. Use request timeouts, bounded exponential retry with jitter, rate-limit responses, resume watermarks, and a quarantine table. Never silently fall back from one feed to another.

Validate duplicate identity, timestamp timezone, expected sessions, nonnegative prices/volume, OHLC consistency, instrument mapping, splits/dividends, and unexpected gaps. Distinguish exchange closure from missing records. Quality failure blocks only the affected universe when the experiment policy explicitly permits partial coverage; otherwise abstain for the run. A backfill is a new revision, not an invisible repair of a published experiment.

Each source needs a capability checklist: event/publication/ingestion times; point-in-time revisions; corporate actions and dividends; delisted instruments; historical constituents when needed; feed venue and quote coverage; storage retention; automated access; internal replay; derived-results publication; and raw redistribution. Missing capability narrows experiment claims or blocks that use. Public access and an API key do not prove publication rights. Export no vendor raw data by default, and withhold derived fields until their intended display is permitted.

## A library that distinguishes availability from permission

Build one catalog record per exact edition, deduplicated across curricula. Preserve each Character's separate ordered assignments. Fields: title, author, edition/ISBN, publisher, curriculum positions, official/library URLs, access class, `checked_at`, next check, rights evidence, allowed storage/use, private source locator, ingestion status, and blocker. Keep three independent states:

- **Access:** unknown, public full text, sample only, library loan, owned copy, purchase required, unavailable.
- **Permission:** unknown, metadata-only, reading/analysis permitted, machine ingestion permitted, redistribution permitted; record scope and evidence rather than inferring one from another.
- **Learning:** not started, prior frozen, extracting, adversarial review, checkpoint complete, blocked.

On a user-triggered library refresh, scripts check cached known URLs and changed metadata. A link returning HTTP 200 does not verify a full book or its license. Human/model review handles new editions, ambiguous permission, and curriculum changes. Recheck immediately before ingestion and on changed access; avoid daily model searches for unchanged books. Never bypass access controls or substitute a summary for a supposedly read book.

The [current catalog](../library/catalog/characters.json) separates actual edition evidence from frozen learning records. [ADR-002](../decisions/records/ADR-002-microstructure-reading-scope.md) revises Microstructure to seven ordered sources, including an explicitly accepted excerpt foundation. Other Characters retain their four-title order. The historical pilot catalog and Bogle acquisition remain unchanged. Register supplied editions and scope in the next Character version before learning. Completing the approved draft scope does not mean the full published book was read. See [training scope](character-training.md) and the [adopted packet](microstructure-alternatives.md).

Useful verified supplemental starting points are [Berkshire's shareholder-letter archive](https://www.berkshirehathaway.com/letters/letters.html), SEC filings, and Meadows' official essays. Berkshire's public letters are not the same edition or ordering as *The Essays of Warren Buffett*. They are not an automatic curriculum replacement. Project Gutenberg's [permission guidance](https://www.gutenberg.org/policy/permission) explains its U.S.-based scope; assess the individual work and jurisdiction rather than treating all old texts or translations as unrestricted.

## Learning workflow

“Training” initially means source-grounded learning artifacts and retrieval, not fine-tuning model weights. Register permitted source → freeze prior → extract claims with locators → assimilate through constitution → adversarial pass → append memory delta → consolidate cited memory → preregister tests. Preserve chunk/section progress and source hashes so a restart cannot reorder books or skip material silently.

For the first book, produce the Index Steward constitution, curriculum record, before/after checkpoint, small memory, and at least one falsifiable theory. Validate citation locators against the actual source and mark partial reading explicitly. Only then apply the protocol to Value and Trend, keeping formative memories separate. General model knowledge must be labeled as such; it cannot be passed off as a quotation or evidence of reading.

Learning status is visible independently from trading status. Frozen trials retain their knowledge version. Later amendments, retirements, and forks create new versions and future experiment windows. The owner sees reading progress, unresolved contradictions, and the next useful source without reopening every file.
