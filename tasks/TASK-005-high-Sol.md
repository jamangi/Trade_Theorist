# TASK-005: Create pilot specialists and structured recommendations

> Historical task ID, retained for traceability. Remaining work is governed by [Step 10](active/STEP-10-pilot-readiness.md). Original status and evidence below describe the earlier scope; old dependencies and next-task wording are not the active execution order.

- Status: implemented and verified (2026-09-06)
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: high
- Dependencies: TASK-004
- Design: [architecture.md](../docs/architecture.md)

## Scope

Create Value Rationalist and Systematic Trend Operator constitutions and ordered curricula. Reuse the learning protocol without sharing formative consolidated memories. Implement a bounded recommendation/forecast adapter that pins model, prompt, knowledge version, portfolio state, evidence, and expiry. Give each Character readiness state and explicit abstention.

## Deliverables

characters/ pilot artifacts; src/theorize/; recorded independent opinions and malformed-output fixtures.

## Acceptance

Demonstrate three independent fixture opinions and one real learned checkpoint per ready Character; blocked sources leave real readiness false. Missing citations, invalid quantities, and unsupported certainty are rejected. No claim that all four books were learned after one checkpoint.

Source update (2026-09-05): Value and Trend foundation PDFs are present in the [current inventory](../library/catalog/INVENTORY_REPORT.md). Prepare and register the actual editions before learning. This task starts specialist learning; later books require additional ordered runs under the [full-curriculum completion criteria](../docs/character-training.md).

## Usage rationale

Reuse the reviewed learning design; Sol handles distinct artifacts and structured output plumbing.

## Implementation evidence

Created separate [Value Rationalist](../characters/value_rationalist/README.md) and [Systematic Trend Operator](../characters/systematic_trend_operator/README.md) constitutions, resolved ordered curricula and immutable source records. Exact PDF hashes, page counts, title pages and reviewed page layouts were verified. A bounded reviewed import produced one genuine, cited checkpoint from Graham's introduction and one from Faith's first chapter. Neither Character is promoted: both report `partial_foundation`, `real_readiness: false`, zero books completed and fixture-only recommendation readiness. The PDFs and extracted text remain private; public artifacts contain original analysis and citation hashes.

Implemented `src/trade_theorist/theorize/` with a provider-neutral recommendation adapter. Requests pin Character/knowledge version, portfolio state, snapshot, evidence, model, prompt and expiry; the model receives no tools. The adapter rejects malformed output, missing active citations, negative quantities, stale forecast resolutions, evidence outside the frozen view, overlong expiry and absolute certainty. Explicit abstention is enforced by the base contract.

The checked-in fixture bundle demonstrates three independent opinions over one synthetic snapshot. The companion pins record shows distinct request hashes and contains no live-data or performance claim. Tests validate the two public learning chains, tamper detection and malformed recommendation cases. See the combined [implementation record](../docs/task-005-006-implementation.md).

Remaining learning scope: both foundation books beyond the reviewed opening section and all curriculum positions 2–4. This does not block the bounded fixture interface but does block real/historical-qualified recommendations.
