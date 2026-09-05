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

Source update (2026-09-05): all four Event title slots have local files; Quality of Earnings needs OCR. Expectations Investing shares a file with Value, but learned interpretation must remain Character-specific. This task provides a source plan, not complete Event learning; see the [continuation map](../docs/character-training.md).

## Acceptance

A transaction cannot influence a decision before public availability; unknown publication time stays ineligible; value ranges never become exact amounts; no unsupported motives or allegations. Show only contract-level fixtures until trustworthy ingestion exists.

## Usage rationale

Ambiguous public disclosures and temporal interpretation warrant Astra high and a narrow scope.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.
