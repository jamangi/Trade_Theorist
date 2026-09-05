# TASK-011: Build honest evaluation and evidence grades

- Status: planned
- Recommended model: GPT-6 Astra (gpt-6-astra)
- Recommended effort: high
- Dependencies: TASK-006, TASK-007, TASK-008, TASK-010
- Design: [evaluation.md](../docs/evaluation.md)

## Scope

Implement net returns, drawdown, exposure, turnover, calibrated forecasts, cash/index baselines, null reasons, experiment registry, and separate rejected-decision counterfactuals. Add no-mail versus mail comparisons, holdout/forward review reports, trial counts, and explicit hindsight contamination labels.

## Deliverables

src/evaluate/; checked metric fixtures; six-answer evidence summary records.

## Acceptance

Match manual calculations; avoid duplicated dividends and costs; zero trades produce unavailable hit rate but valid cash return; immature forecasts stay pending; historical hindsight results cannot enter promotion rankings. A full counterfactual portfolio respects its own funds and order timing.

## Usage rationale

False evidence of skill is a central project risk; this warrants Astra's deeper review.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.
