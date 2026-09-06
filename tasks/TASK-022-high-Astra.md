# TASK-022: Define the disclosure-analysis interface

- Status: planned
- Recommended model: GPT-6 Astra (gpt-6-astra)
- Recommended effort: high
- Dependencies: TASK-001, TASK-006, TASK-011, TASK-014, TASK-016
- Design: [data-and-learning.md](../docs/data-and-learning.md)

## Scope

Specify the separate Trader Analyzer package contract for official House/Senate data and the Event Detective. Preserve transaction, public-availability, ingestion, amendments, ownership ambiguity, and disclosed value ranges. Recheck current official access/use requirements before implementation; distinguish EDGAR company facts from congressional reports.

## Deliverables

Analyzer contract and fixture adapter; Event curriculum/source plan; delay-aware evaluation cases.

Source update (2026-09-05): all four Event title slots have local files; Quality of Earnings now has a supplied transcript with 231 sequential PDF page markers; use it without generating replacement OCR. Expectations Investing shares a file with Value, but learned interpretation must remain Character-specific. This task provides a source plan, not complete Event learning; see the [continuation map](../docs/character-training.md).

## Acceptance

A transaction cannot influence a decision before public availability; unknown publication time stays ineligible; value ranges never become exact amounts; no unsupported motives or allegations. Show only contract-level fixtures until trustworthy ingestion exists.

## Usage rationale

Ambiguous public disclosures and temporal interpretation warrant Astra high and a narrow scope.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.

## Reuse event market windows (2026-09-06)

Retrieve market windows around disclosures through TASK-014's [cache and shared limiter](../docs/market-data-request-budget.md). Coalesce compatible overlapping windows across events and Characters, fetching only missing coverage. Cache reuse must preserve original publication/ingestion clocks and revision identity; later-retrieved history does not become forward-eligible evidence retroactively.

Official filing/disclosure sources retain their own verified quotas, provenance and retry rules; do not charge them to Alpaca's pool or assume Alpaca's 200/min applies to them. Acceptance: repeated eligible event windows cause no new Alpaca call, missing windows are batched/metered, and deadline or coverage gaps remain visible without changing the disclosure cutoff.
