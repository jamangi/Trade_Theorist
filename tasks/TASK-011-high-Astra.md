# TASK-011: Build honest evaluation and evidence grades

- Status: implemented and verified (2026-09-06; fixture evaluation)
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

## Implementation and evidence

Implemented ledger-derived daily metrics, explicit null reasons, closed-position hit
rate, forecast registration/maturation and Brier reliability bins. Forecasts pin an
explicit probability, raw-price event, time and feed; late ingestion cannot score an
earlier report. Fees and dividends enter equity once. Cash/index baselines, all-trial
registry, matched no-mail/mail comparisons, independent counterfactual portfolios and
price-only counterfactual labels are available. Hindsight/historical results cannot
enter promotion review; forward review keeps complete-window/sample requirements
and an explicit recorded owner gate. Six cached evidence answers accompany exports.

Manual calculations and adversarial tests cover stale/missing observations, zero
trades, pending/unscorable forecasts, late data, idempotent reports, separate capital,
original counterfactual risk limits, failed-trial retention and external-flow rejection.
See [implementation and validation](../docs/task-011-013-implementation.md) and
[checked arithmetic](../examples/evaluation/metric-checks.json).

No bounded fixture blocker. This task creates no evidence of real skill or completed
forward trial, promotes no Character, and does not authorize paper/live execution.
