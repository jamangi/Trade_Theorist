# TASK-017: Start forward paper portfolios and optional broker adapter

- Status: planned
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: high
- Dependencies: TASK-007, TASK-008, TASK-014, TASK-016
- Design: [evaluation.md](../docs/evaluation.md)

## Scope

Run both portfolio modes against fresh permitted data under the approved paper policy and preregistered fill assumptions. Optionally implement a paper-only broker adapter if separately selected and authorized; local simulated sleeves remain canonical for comparative experiments. Preserve distinct broker-versus-local results and reconciliation.

## Deliverables

paper run manifests and reports; optional paper adapter contract tests; discrepancy report.

## Acceptance

No live host/credentials are accepted; orders cannot bypass policy; asynchronous/partial fills reconcile exactly; omitted broker dividends do not silently distort benchmark comparisons. Results remain insufficient until the declared sample matures.

## Usage rationale

The risky contracts have been reviewed; Sol handles the bounded operational adapter and validation.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.
