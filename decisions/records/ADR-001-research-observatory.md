# ADR-001: Research observatory with council and Character portfolios

Date: 2026-09-05. Status: accepted direction under the owner's attached request; implementation remains planned.

## Context and authority

The owner explicitly approved all recommended defaults in the existing approval register, requested a Meadows-style discussion-system design, cheap scripted ingestion, inspectable learning and performance, separate fictional portfolios, implementation tasks with model/effort guidance, and publication of this repository update to `main`.

The starting repository contained only README.md and decisions/APPROVALS.md. There is no existing application infrastructure to migrate. Preserve its conceptual service boundaries and pilot curriculum order.

## Decisions

1. Keep Index Steward as the initial council lead and Trend as a shadow. Add an independently evaluated Character-portfolio mode without granting council promotion.
2. Share evidence infrastructure and simulation code, while separating portfolio accounting, experiment permissions, knowledge versions, and outcome histories.
3. Use event-backed, bounded mail with readable Markdown exports. Preserve independent initial opinions; do not require consensus or unrestricted chatter.
4. Prefer a local Python/SQLite implementation and scripts for recurring mechanical work. Keep simulated execution behind a Trader User adapter contract.
5. Use prospective shadow/paper evidence as the strongest initial test of LLM trading behavior. Preserve the requested hindsight sandbox with explicit contamination labels.
6. Design a read-only, two-tab GitHub Pages report with expandable answers to every README success question. Private computation and public exports are separate.
7. Preserve deferred vendor/broker selection and the separate live-capital gate. Approving a default to defer a choice does not select a vendor or authorize an account.

## New proposals versus approved defaults

The dollar amounts, numeric risk limits, discussion caps, sample floors, implementation stack, and task assignments introduced in this revision are design recommendations. The direction is authorized; new numeric paper policy must be explicitly recorded before paper runs. Existing items without a concrete recommended value (numeric limits and operational access assignments) are still unresolved. No book is declared acquired, no Character trained, no provider selected, and no application deployed by this decision.

## Tradeoffs and pruned alternatives

Two modes add evaluation state, but avoid replacing the original governance. SQLite and generated mail views reduce competing sources of truth. Reject folder moves as the canonical message database, continuous all-to-all debate, unrestricted current web in clean historical comparisons, forced daily trading, popularity-based capital allocation, and secret-bearing browser controls.

Defer merged Characters until specialist evidence exists; defer intraday claims until microstructure and quote handling exist; defer disclosure-driven signals until public-availability ingestion exists. Add belief timelines, question tracking, decision postcards, and failure reviews as event-derived views, not new autonomous services.

## Implementation and review

The [task index](../../tasks/README.md) replaces the original near-term sequence while preserving all seven original milestones. Each task defines dependencies, outputs, and observable acceptance. Revisit structure after measured queue, latency, cost, and outcome evidence from the first working cycle. The [systems model](../../docs/systems-model.md) records the initial hypotheses.

## Subsequent architecture decision (2026-09-06)

[ADR-004](ADR-004-local-observatory.md) supersedes public-hosting assumptions with a private local owner interface and versioned accounting repairs. It preserves this record's historical decisions and qualification evidence. The [rights matrix](../../docs/data-rights-matrix.md) keeps provider permission questions explicit; private deployment does not select a vendor or authorize account operations.
