# Implementation task index

Status (2026-09-06): TASK-001–008 are implemented and verified within their recorded scope. Index Steward's owner-supplied Bogle foundation is complete; Value and Trend each have one real opening checkpoint but remain partial and ineligible for real recommendations. Time-aware permitted-CSV ingestion, three independent fixture opinions, isolated simulation portfolios and deterministic risk controls are implemented. TASK-009–023 remain planned. See [completed Index learning](../docs/index-steward-foundation.md), [tasks 005–006 evidence](../docs/task-005-006-implementation.md), [tasks 007–008 evidence](../docs/task-007-008-implementation.md) and the individual task records. Use the [focused reading and quiet validation workflow](../docs/development.md). Task numbers are stable; filenames show recommended effort and model.

The [inventory](../library/catalog/INVENTORY_REPORT.md) covers all 31 active positions across seven Characters, including the [accepted Microstructure draft/paper sequence](../decisions/records/ADR-002-microstructure-reading-scope.md). Both scans have supplied transcripts; no more material search or replacement OCR is required. Learning starts in 004, expands in 005 and reaches microstructure/risk in 021; 022 only plans Event sources. Complete curricula still require additional ordered reading runs. Mean-Reversion learning is not yet assigned. See the [continuation map](../docs/character-training.md). Completing 005–006 did not launch their dependents.

## How to use the queue

Open one task, check its dependencies and source-access/policy prerequisites, implement its bounded deliverables, and record acceptance evidence before marking it complete. IDs in dependency lists refer to the linked rows below. Tasks can be independent in the dependency graph; this does not automatically request parallel agents or create new Codex tasks.

For fixture engineering, a dependency's implemented and verified software interface is sufficient even if its real-source learning deliverable is still blocked. Record that partial status explicitly; do not mark the whole prerequisite complete. Real-data and forward tasks require the actual source-grounded readiness and policy deliverables, not just the fixture interface. This lets the offline demo progress without pretending unavailable books have been read.

Use **Sol** for most implementation and **Astra** for contract design, learning fidelity, accounting, risk, evaluation, and stage reviews. The requested “Astral” is written **Astra**, matching the available GPT-6 Astra model. These assignments are project judgments, not measured guarantees. Current model names are documented in the [OpenAI model catalog](https://developers.openai.com/api/docs/models) and [Sol page](https://developers.openai.com/api/docs/models/gpt-5.6-sol), checked 2026-09-05. Recheck availability when starting a task; do not silently substitute a model. Reasoning effort is the run setting, not an estimate of calendar duration.

No blanket maximum effort. Start at the listed level; escalate a narrow unresolved reasoning problem with a recorded reason. Deterministic data fetching, tests, arithmetic, and report rendering run as scripts. Do not create recurring model work from this queue. Development model assignments do not determine competing Characters' runtime models.

## Queue

| Task | Outcome | Model / effort | Depends on |
| --- | --- | --- | --- |
| [TASK-001](TASK-001-high-Astra.md) | Define validated contracts and experiment policy | Astra / high | — |
| [TASK-002](TASK-002-high-Sol.md) | Build durable storage and reproducible run records | Sol / high | 001 |
| [TASK-003](TASK-003-medium-Sol.md) | Inventory book access and build the library catalog | Sol / medium | 001 |
| [TASK-004](TASK-004-high-Astra.md) | Implement ordered learning and the reference Character | Astra / high | 001, 002, 003 |
| [TASK-005](TASK-005-high-Sol.md) | Create pilot specialists and structured recommendations | Sol / high | 004 |
| [TASK-006](TASK-006-high-Sol.md) | Implement time-aware ingestion and historical snapshots | Sol / high | 001, 002 |
| [TASK-007](TASK-007-high-Astra.md) | Build fictional portfolios and the simulation ledger | Astra / high | 001, 002, 006 |
| [TASK-008](TASK-008-high-Astra.md) | Implement independent policy enforcement | Astra / high | 001, 002, 007 |
| [TASK-009](TASK-009-high-Sol.md) | Implement event-backed mail and bounded deliberation | Sol / high | 001, 002, 005 |
| [TASK-010](TASK-010-high-Sol.md) | Connect both modes through a resumable heartbeat | Sol / high | 005, 006, 007, 008, 009 |
| [TASK-011](TASK-011-high-Astra.md) | Build honest evaluation and evidence grades | Astra / high | 006, 007, 008, 010 |
| [TASK-012](TASK-012-high-Sol.md) | Build the two-tab performance dashboard | Sol / high | 010, 011 |
| [TASK-013](TASK-013-medium-Sol.md) | Create the one-command demo and operating interface | Sol / medium | 003, 004, 010, 011, 012 |
| [TASK-014](TASK-014-high-Sol.md) | Qualify a vendor and implement one market-data adapter | Sol / high | 001, 006 |
| [TASK-015](TASK-015-high-Sol.md) | Run forward shadow observations | Sol / high | 005, 008, 010, 011, 013, 014 |
| [TASK-016](TASK-016-high-Astra.md) | Audit leakage, costs, recovery, and paper readiness | Astra / high | 011, 013, 015 |
| [TASK-017](TASK-017-high-Sol.md) | Start forward paper portfolios and optional broker adapter | Sol / high | 007, 008, 014, 016 |
| [TASK-018](TASK-018-medium-Sol.md) | Publish validated reports on GitHub Pages | Sol / medium | 012, 013, 014, 016 |
| [TASK-019](TASK-019-medium-Sol.md) | Add belief timelines and the research notebook | Sol / medium | 004, 009, 011, 012, 013 |
| [TASK-020](TASK-020-medium-Sol.md) | Add scheduled operation with bounded usage | Sol / medium | 013, 016, 017 |
| [TASK-021](TASK-021-high-Astra.md) | Add microstructure and risk specialist research | Astra / high | 003, 004, 011, 016 |
| [TASK-022](TASK-022-high-Astra.md) | Define the disclosure-analysis interface | Astra / high | 001, 006, 011, 014, 016 |
| [TASK-023](TASK-023-high-Astra.md) | Review governance and preregister later experiments | Astra / high | 011, 017, 019 |

## Delivery milestones

1. **Contracts and persistence:** 001–002; catalog work 003 can start after contracts.
2. **First useful offline observatory:** 004–013 using recorded/scripted fixture opinions where source access is blocked. Both portfolio modes, one conversation, honest scorecards, six explanation panels, and a no-account demo must work. Fixture delivery does not complete real Character learning requirements.
3. **Prospective research:** 014–015 after the required trained Characters and data rights are ready. The duration of a forward trial is real elapsed market time; implementation cannot compress it.
4. **Paper readiness and public report:** 016 review, then 017 paper portfolios and 018 Pages publication. Public fixture reports may demonstrate the UI, but must not impersonate achieved forward results.
5. **Human context and reliable operation:** 019 adds richer observable learning; 020 adds optional scheduling after operational gates. Neither is required to gather the first shadow observations.
6. **Later research:** 021 before serious intraday work; 022 before disclosure-driven signals; 023 before merged Characters or revised governance. These are explicit follow-on tasks, not prerequisites for the useful daily pilot.

The first end-to-end fixture path is 001 → 002, with 003–009 prerequisites converging on 010 → 011 → 012 → 013. The first real paper path additionally requires verified learning, 014 → 015 → 016 → 017. Missing books or a vendor decision must not prevent fixture engineering, but must prevent claims that the dependent real experiment is complete.

## Reconciliation with the original roadmap

| Original milestone | Updated task(s) | What is preserved or added |
| --- | --- | --- |
| Resolve owner choices | [Approval register](../decisions/APPROVALS.md), 001, 014, 016 | Existing defaults approved; deferred selection and unspecified values stay explicit |
| Define schemas | 001 | Adds time, mail, portfolios, policy, and dashboard contracts |
| Index Steward plus one book | 003–004 | Same formative source and sequential protocol; rights/readiness are visible |
| Value and Trend specialists | 005 | Same curriculum order and separate formative memories |
| Theory validator and append-only manifests | 001–002 | Validation and durability move earlier, before data or agent activity |
| Historical decisions and forecasts | 006–013 | Adds realistic accounting, qualified replay, mail, and visible results |
| Live shadow then paper after review | 014–017 | Preserves stage ordering, adds dated evidence and numeric paper-policy gate |

## Decisions still needed at their point of use

Exact permitted editions/source access; vendor selection and license coverage; complete numeric paper-risk policy and operational ownership; actual experiment universe, benchmarks, costs and sample criteria. These do not block this design publication. They are identified in the relevant task and [approval register](../decisions/APPROVALS.md). No real-money implementation is included in this queue.
