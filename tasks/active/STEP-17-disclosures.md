# Step 17: Define the delay-aware disclosure interface

- Status: pending; remaining scope as of 2026-09-06
- Recommended model / effort: Astra / high
- Historical coverage: [TASK-022](../TASK-022-high-Astra.md)
- Queue: [ordered remaining work](../README.md)
- Design inputs: [Data and learning](../../docs/data-and-learning.md), [training scope](../../docs/character-training.md)

## Why this position

Reuse proven timing and evidence contracts before introducing an ambiguous new signal source.

## Starting evidence

Steps 01, 02, 09 and 12 supply contracts and evidence. Microstructure and scheduling are not prerequisites.

## Finished state

A separate Analyzer fixture contract and Event source plan preserve public-availability timing, revisions and disclosure ambiguity. No complete Event curriculum or real signal is claimed.

## Scope

Specify the separate Trader Analyzer package contract for official House/Senate data and the Event Detective. Preserve transaction, public-availability, ingestion, amendments, ownership ambiguity, and disclosed value ranges. Recheck current official access/use requirements before implementation; distinguish EDGAR company facts from congressional reports.

## Deliverables

Analyzer contract and fixture adapter; Event curriculum/source plan; delay-aware evaluation cases.

Source update (2026-09-05): all four Event title slots have local files; Quality of Earnings now has a supplied transcript with 231 sequential PDF page markers; use it without generating replacement OCR. Expectations Investing shares a file with Value, but learned interpretation must remain Character-specific. This task provides a source plan, not complete Event learning; see the [continuation map](../../docs/character-training.md).

## Acceptance

A transaction cannot influence a decision before public availability; unknown publication time stays ineligible; value ranges never become exact amounts; no unsupported motives or allegations. Show only contract-level fixtures until trustworthy ingestion exists.

## Reuse event market windows (2026-09-06)

Retrieve market windows around disclosures through Step 06's [cache and shared limiter](../../docs/market-data-request-budget.md). Coalesce compatible overlapping windows across events and Characters, fetching only missing coverage. Cache reuse must preserve original publication/ingestion clocks and revision identity; later-retrieved history does not become forward-eligible evidence retroactively.

Official filing/disclosure sources retain their own verified quotas, provenance and retry rules; do not charge them to Alpaca's pool or assume Alpaca's 200/min applies to them. Acceptance: repeated eligible event windows cause no new Alpaca call, missing windows are batched/metered, and deadline or coverage gaps remain visible without changing the disclosure cutoff.

## Private architecture requirements

Keep disclosure windows and linked market context private under source-specific rights. Public availability of a filing does not license redistribution of joined market data. Reuse cached windows and retain transaction/publication/ingestion times and v2 evidence identity.
md).

## Validation and handoff

Use the [focused validation workflow](../../docs/development.md). Record changed files, actual checks, evidence artifacts and remaining blockers here. For code changes, run relevant tests and the full suite once after focused checks pass; for UI changes, verify keyboard and narrow/wide layouts too. Original synthetic acceptance never substitutes for required real-source or elapsed-time evidence.

Stop at this step's finished state. The default next item is [Step 18](STEP-18-governance-review.md); do not start it automatically. Follow the queue's blocker rule for independent work. Preserve historical completion claims. No account call, order, paid subscription, public market-data deployment or recurring work is authorized merely by this task brief.
