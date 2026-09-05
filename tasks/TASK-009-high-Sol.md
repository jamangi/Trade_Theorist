# TASK-009: Implement event-backed mail and bounded deliberation

- Status: planned
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
