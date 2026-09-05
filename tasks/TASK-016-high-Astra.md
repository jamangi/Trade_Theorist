# TASK-016: Audit leakage, costs, recovery, and paper readiness

- Status: planned
- Recommended model: GPT-6 Astra (gpt-6-astra)
- Recommended effort: high
- Dependencies: TASK-011, TASK-013, TASK-015
- Design: [evaluation.md](../docs/evaluation.md)

## Scope

Review the completed implementation against clock barriers, simulated accounting, source rights, public exports, model usage, crash recovery, hard limits, and baseline fairness. Review the proposed numeric paper policy and obtain a recorded owner decision before paper execution. Distinguish engineering readiness from statistical evidence.

## Deliverables

audit report with reproduced findings; resolved defects; explicit paper-stage decision or blockers.

## Acceptance

Use adversarial cases spanning publication lag, revised filings, splits, stale quotes, repeated runs, unavailable sources, and injected instructions. Record all unresolved limitations. No paper promotion solely because the dashboard looks complete.

## Usage rationale

A separate focused reasoning pass is justified at the stage boundary; this task does not mandate a separate subagent.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.
