# TASK-010: Connect both modes through a resumable heartbeat

- Status: planned
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: high
- Dependencies: TASK-005, TASK-006, TASK-007, TASK-008, TASK-009
- Design: [architecture.md](../docs/architecture.md)

## Scope

Implement the ordered heartbeat phases, locks, frozen snapshots, portfolio-aware final decisions, risk gate, queued execution, evaluation handoff, and atomic export handoff. Reuse model outputs only for identical full input/version hashes. Track usage before admitting additional calls.

## Deliverables

src/ heartbeat orchestrator; council and individual experiment examples.

## Acceptance

One fixture heartbeat produces independent opinions, a mailbox exchange, a final decision, an abstention, and a risk rejection. Resume a crash between each durable phase without duplicate orders or completed model calls. Cross-mode holdings and private evidence remain isolated.

## Usage rationale

Integration uses already-defined components; Sol high provides enough attention without blanket flagship use.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.
