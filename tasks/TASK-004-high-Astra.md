# TASK-004: Implement ordered learning and the reference Character

- Status: partial — software and fixture demonstration complete (2026-09-05); real learning blocked
- Recommended model: GPT-6 Astra (gpt-6-astra)
- Recommended effort: high
- Dependencies: TASK-001, TASK-002, TASK-003
- Design: [data-and-learning.md](../docs/data-and-learning.md)

## Scope

Implement prior freeze, extraction with locators, assimilation, adversarial review, append-only deltas, consolidated memory, and preregistered theory output. Add a model adapter with bounded usage and a recorded-output fixture path. Instantiate Index Steward from its approved first source when permitted access exists; otherwise demonstrate mechanics with labeled fixtures and report the real learning blocker.

## Deliverables

src/learn/; Index Steward constitution and curriculum; real source-grounded checkpoint when accessible; fixture-only demonstration otherwise.

## Acceptance

Resume without reordering or duplicating chapters; claims trace to actual available source passages; partial reading is labeled; unacquired text cannot be reported read. Do not mark real learning complete while source access is blocked.

## Usage rationale

Faithful assimilation and the distinction between authored beliefs and unsupported model knowledge need deeper judgment.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.

## Implementation evidence and real-learning blocker

Delivered `src/trade_theorist/learn/`, Index Steward's [design-prior constitution](../characters/index_steward/constitution.md) and unchanged ordered [curriculum](../characters/index_steward/curriculum.yaml), plus original two-section material, recorded outputs, cited checkpoints/memory, authored assimilation/adversarial review and preregistered fixture theories in `examples/learning/`. Fixture identity is separate from the real Character. The foundation remains Bogle; no summary or alternate source was substituted.

Tests pass for frozen priors, pinned source/constitution/curriculum hashes, exact locators and short supporting passages, ordered resume, duplicate prevention, changed-material rejection, source rights/recency, sample/full-book separation, interrupted response reuse, malformed citation rejection, ambiguous-call suppression and persistent usage caps. The two-section offline demo reruns without new responses or duplicate effects. See [workflow and evidence](../docs/foundation-implementation.md).

**Blocked real deliverable:** no permitted full-book file for *The Little Book of Common Sense Investing* is registered. Its publisher offers a purchase route and a sample link; neither establishes machine-ingestion/private-storage permission. Obtain a permitted exact edition, verify full section coverage and run a reviewed adapter before claiming a real checkpoint or trained Index Steward. Real status remains `not_ready`; the whole task is not marked complete. Its implemented fixture interface is ready for downstream fixture engineering under the task index's explicit partial-dependency rule.
