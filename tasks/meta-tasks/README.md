# Architecture meta-tasks

Meta-tasks are bounded architecture reviews. They may amend the task graph, decision
records, contracts and documentation, but they do not silently relabel historical work
as complete or launch market-data, model, paper-order or live-order activity.

## Start here

[META-001](META-001-high-Astra.md) is complete within its bounded architecture scope.
Read [START-HERE](START-HERE.md): the exact next task is TASK-024, additive v2 contracts
and persistence, followed by TASK-025's accounting integration. The [impact report](../../docs/meta-001-impact.md)
records findings, executable reference evidence and pending implementation.

Existing v1 evidence is preserved. The exporter now refuses nonfixture sources;
production FIFO/TWR, private v2 UI and broker attribution remain implementation tasks.
TASK-018 now packages the private local observatory; public Pages deployment is retired.

The owner-approved defaults are recorded in [APPROVALS.md](APPROVALS.md). Any new
choice discovered by META-001 must be added there unchecked with a recommendation; the
meta-task may not silently expand the recorded approval.

## Meta-task index

| Meta-task | Outcome | Model / effort | Status |
| --- | --- | --- | --- |
| [META-001](META-001-high-Astra.md) | Local-first UI, data-publication boundary, Character sub-ledgers and roadmap repair | GPT-6 Astra / high | Complete (2026-09-06); next TASK-024 |

## Required completion pattern

Every meta-task must leave:

1. an impact report separating preserved, amended, retired and newly required work;
2. versioned decision records and explicit unresolved owner choices;
3. an updated dependency graph without circular prerequisites;
4. a `START-HERE.md` with the exact next task, inputs, acceptance evidence and blockers;
5. repository validation evidence; and
6. no credentials, raw licensed market data, account identifiers or invented results.
