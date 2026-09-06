# TASK-009: Implement event-backed mail and bounded deliberation

- Status: implemented and verified (2026-09-06; fixture deliberation)
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: high
- Dependencies: TASK-001, TASK-002, TASK-005
- Design: [discussion.md](../docs/discussion.md)

## Scope

Implement immutable message bodies, delivery/read/expiry events, experiment isolation, conversation summaries, private authored reflections, and generated Markdown mailbox views. Gate peer visibility until initial opinions are committed. Enforce one question, two recipients, one reply each, and one final revision per Character with configured caps.

## Deliverables

src/council/; generated readable mail examples; targeted disagreement fixture.

## Acceptance

Two recipients have independent read states; duplicate delivery has no effect; timeout preserves objections; late replies cannot alter committed recommendations; unsafe titles cannot escape export directories; summaries link source events.

## Usage rationale

Conventional event processing with well-defined semantics fits Sol at high effort.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.

## Implementation and validation

Implemented `src/trade_theorist/council/` with immutable message records and
hash-chained open, initial-commit, delivery, per-recipient read, expiry, reflection,
final-commit and closure events. Peer opinions and mail remain hidden until every
initial opinion is committed. Configured bounds enforce one question, no more than
two recipients, one reply per addressed adviser, one final revision per Character,
message/reflection word ceilings and a total-message ceiling. Late replies remain
visible but cannot influence the frozen final decision; timeout retains unresolved
objections.

Markdown mailboxes are generated views with source-event links. Titles never
become paths; all paths are contained under the requested absolute export root.
Exports use a staged atomic handoff and preserve the prior valid tree on injected
failure. Private authored reflections appear only in their author's view and are
explicitly distinguished from hidden reasoning.

Evidence: the full suite passes 109 tests. Targeted cases cover two independent
read states, duplicate delivery, immutable body/title reuse, question/reply/final
caps, late and expired mail, timeout objections, reflection access, experiment
isolation, path traversal attempts, linked summaries and atomic failure. The
targeted disagreement and readable outputs are in `examples/heartbeat/`. See
[implementation details](../docs/task-009-010-implementation.md).

No bounded fixture blocker remains. This is internal Character mail—not email or
messaging to people. No external delivery, model spend or ongoing run was started.
