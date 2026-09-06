# TASK-021: Add microstructure and risk specialist research

> Historical task ID, retained for traceability. Remaining work is governed by [Step 16](active/STEP-16-microstructure.md). Original status and evidence below describe the earlier scope; old dependencies and next-task wording are not the active execution order.

- Status: planned
- Recommended model: GPT-6 Astra (gpt-6-astra)
- Recommended effort: high
- Dependencies: TASK-003, TASK-004, TASK-011, TASK-014, TASK-016
- Design: [evaluation.md](../docs/evaluation.md)

## Scope

Prepare Market Microstructure Mechanic and Probabilistic Risk Skeptic curricula/checkpoints under verified source permissions. Add quotes, spreads, execution-quality measurements and stress scenarios before serious intraday simulation. Keep the Skeptic's advice distinct from the deterministic governor.

## Deliverables

specialist artifacts, quote-data requirements, execution realism review, preregistered intraday experiment proposal.

## Acceptance

No intraday performance claim from daily bars or a single-exchange volume proxy alone; stress spread/latency/gaps; Skeptic cannot alter its own hard limits. Source gaps leave Characters unready.

Source update (2026-09-05): the owner [accepted](../decisions/records/ADR-002-microstructure-reading-scope.md) Harris's 113-page draft excerpts as the limited foundation, followed by Johnson and five supplied papers. Johnson's page-indexed transcript is available; no new OCR is needed. Missing original books are retired targets. The Skeptic has four local candidates, including the unresolved Against the Gods edition and Marks's annotated volume. Use the [inventory](../library/catalog/INVENTORY_REPORT.md), [adopted packet](../docs/microstructure-alternatives.md) and [completion criteria](../docs/character-training.md). Read the supplied foundation first, retain omissions as unknown, and report progress out of seven declared Microstructure sources. Scope acceptance removes acquisition blockers but does not create checkpoints or grant readiness.

## Usage rationale

Market execution assumptions and risk-model weaknesses need deeper reasoning; this is after the useful daily pilot.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.

## Data-volume feasibility under Basic (2026-09-06)

Before quote/trade collection, estimate pages, payload volume, cadence, repair/retry work and completion time against TASK-014's [shared operating ceiling](../docs/market-data-request-budget.md). Batch and reuse missing windows; prefer a narrower preregistered universe or slower cadence when the workload cannot fit. Do not silently remove instruments mid-trial or bypass the limiter for research.

Evaluate shared streaming only if actual feed entitlement and separate connection/symbol/subscription limits support the experiment. Streaming is not a loophole for real-time SIP under Basic; reconnects need bounded backoff and any REST gap repair uses shared admission. Start with daily REST until a measured need justifies streaming. Acceptance reports whether data arrives before the thesis expires and rejects intraday claims when Basic delay/coverage is inadequate. This adds a data feasibility requirement without changing accepted reading scope.

## META-001 follow-up (2026-09-06)

Retain the approved microstructure/risk curriculum and high-volume request budget. Evaluate execution hypotheses on matched opportunity sets, horizons, costs and execution bases using v2 accounting. Separate broker-paper execution studies from simulated Character rankings.

See [the impact record](../docs/meta-001-impact.md) and [next task](meta-tasks/START-HERE.md).
