# TASK-004: Implement ordered learning and the reference Character

> Historical task ID, retained for traceability. Remaining work is governed by [Step 10](active/STEP-10-pilot-readiness.md). Original status and evidence below describe the earlier scope; old dependencies and next-task wording are not the active execution order.

- Status: complete — software, fixture demonstration and real foundational source review verified (2026-09-05)
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

## Implementation evidence

Source-scope extension (2026-09-05): the [owner-adopted Microstructure revision](../decisions/records/ADR-002-microstructure-reading-scope.md) requires ordered completion of papers and accepted excerpts. The engine now pins these scopes in the curriculum, requires excerpt authority and reviewed declared coverage, and preserves scope in checkpoints. Generic samples/fixtures cannot become complete reading. Supplied transcripts can be loaded by exact hash and sequential page markers. This changes no frozen Bogle artifacts and performs no new Character learning.

Delivered `src/trade_theorist/learn/`, Index Steward's [design-prior constitution](../characters/index_steward/constitution.md) and unchanged ordered [curriculum](../characters/index_steward/curriculum.yaml), plus original two-section material, recorded outputs, cited checkpoints/memory, authored assimilation/adversarial review and preregistered fixture theories in `examples/learning/`. Fixture identity is separate from the real Character. The foundation remains Bogle; no summary or alternate source was substituted.

Tests pass for frozen priors, pinned source/constitution/curriculum hashes, exact locators and short supporting passages, ordered resume, duplicate prevention, changed-material rejection, source rights/recency, sample/full-book separation, interrupted response reuse, malformed citation rejection, ambiguous-call suppression and persistent usage caps. The two-section offline demo reruns without new responses or duplicate effects. See [workflow and evidence](../docs/foundation-implementation.md).

**Real deliverable completed:** the owner supplied the 2017 tenth-anniversary ePDF, ISBN 9781119404521, and requested this bounded reading. The related hardcover candidate remains in the catalog audit. Exact PDF hash, identity pages, 305-page coverage, introduction and all 20 chapters were checked. The full PDF is copied locally under an ignored source folder. It is not redistributed in the public repository.

The [source-grounded review](../characters/index_steward/checkpoints/bogle-2017-reading-review.json) records 46 claims (26 accepted, 17 qualified, three rejected). The validated public bundle contains 21 ordered checkpoints, original assimilation/adversarial deltas, consolidated memory and one preregistered theory. The prior remains immutable; [constitution v1](../characters/index_steward/constitution.v1.md) adds the resulting beliefs. `learn --character index_steward` verifies the published chain and reports `foundation_complete`, with positions 2–4 unread and evaluation `not_run`.

The reviewed-transcript adapter imports the current Codex session's attributed analysis. It does not claim a new independent generation, exact unavailable authoring parameters, zero original authoring cost, or forward performance evidence. A separate non-trading learning scope avoids inventing a paper policy. Requests now exclude future chapter text, citations resolve to specific pages, and sections need not invent a theory merely to retain a learning delta.

Acceptance evidence: 48 tests passed; the real run stopped after two sections and resumed with exactly 19 new imports; a completed rerun used zero new imports and retained all 48 records. Public export immutability, citation consistency, bundle references and SQLite/event-chain integrity passed. [Reproduction and limitations](../docs/index-steward-foundation.md). No remaining blocker for this bounded task; later books, other specialists and market/paper operation remain separate tasks.
