# Architecture meta-tasks

Meta-tasks are bounded architecture reviews. They may amend the task graph, decision
records, contracts and documentation, but they do not silently relabel historical work
as complete or launch market-data, model, paper-order or live-order activity.

## Start here

Run [META-001](META-001-high-Astra.md) with GPT-6 Astra at high reasoning effort
before implementing public deployment or paper-account portfolio attribution. It must
inspect the repository as it exists on `main`, reconcile the local/private data boundary
with the dashboard plan, define Character performance precisely, and produce
`START-HERE.md` naming the first bounded implementation task after the review.

The current expectation is that contracts introduced around TASK-002 and TASK-007 may
need additive revisions, while the first user-visible repair affects TASK-012's dashboard
boundary. META-001 must verify that rather than assume it. Preserve stable task IDs and
historical evidence; prefer versioned migrations or new repair tasks over rewriting what
earlier commits actually proved.

The owner-approved defaults are recorded in [APPROVALS.md](APPROVALS.md). Any new
choice discovered by META-001 must be added there unchecked with a recommendation; the
meta-task may not silently expand the recorded approval.

## Meta-task index

| Meta-task | Outcome | Model / effort | Status |
| --- | --- | --- | --- |
| [META-001](META-001-high-Astra.md) | Local-first UI, data-publication boundary, Character sub-ledgers and roadmap repair | GPT-6 Astra / high | Ready; defaults approved |

## Required completion pattern

Every meta-task must leave:

1. an impact report separating preserved, amended, retired and newly required work;
2. versioned decision records and explicit unresolved owner choices;
3. an updated dependency graph without circular prerequisites;
4. a `START-HERE.md` with the exact next task, inputs, acceptance evidence and blockers;
5. repository validation evidence; and
6. no credentials, raw licensed market data, account identifiers or invented results.
