# TASK-010: Connect both modes through a resumable heartbeat

> Historical task ID, retained for traceability. Remaining work is governed by [the ordered queue](README.md). Original status and evidence below describe the earlier scope; old dependencies and next-task wording are not the active execution order.

- Status: implemented and verified (2026-09-06; fixture heartbeat)
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

## Implementation and validation

Implemented `src/trade_theorist/heartbeat/` with an experiment lock and ten ordered
phases covering snapshot freeze, portfolio mark, prior mail, independent opinions,
deliberation, final decisions, policy gate, simulation queue, evaluation handoff
and atomic export. Phase inputs are pinned by the immutable run-manifest hash.
Transactional phase completion reuses saved outputs, while completed model work is
cached only by its complete experiment/input/version hash. The bounded usage
reservation is durable before provider admission, and ambiguous calls are not
silently retried.

The checked fixture produces three council opinions, two inactive initial
recommendations, a mailbox exchange, one final decision and an independent
turnover rejection. A separate individual sleeve queues one simulated order.
Their experiments, portfolios, event streams and private reflection evidence stay
separate. All outputs are engineering fixtures without real-readiness or
performance claims.

Evidence: 109 tests pass. A recovery matrix crashes after every one of the ten
durable phases and resumes with exactly one order, three completed council calls,
five deliveries and ten completions. Additional tests cover concurrent lock
exclusion, changed plans, pre-call usage ceilings, exact response reuse,
cross-mode isolation, risk rejection, evaluation handoff and reproducible exports.
Run `python scripts/build_task_009_010_fixtures.py`; see
[implementation details](../docs/task-009-010-implementation.md).

No bounded fixture blocker remains. Honest outcome scoring belongs to Task 011.
Real operation still requires qualified data, completed Character learning,
owner-approved paper policy and readiness review. No live endpoint, scheduled
heartbeat, paid provider call or dependent task was launched.
