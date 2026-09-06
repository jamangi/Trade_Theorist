# Remaining-work crosswalk

Date: 2026-09-06. Baseline: b60f301, completed META-001. This is an execution-plan refactor, not an engine migration. The [active sequence](README.md) supersedes the old recommended traversal.

| Historical TASK | Active step(s) | Treatment |
| --- | --- | --- |
| [001](TASK-001-high-Astra.md) | Implemented foundation; reuse | Historical interfaces/evidence retained; no new work implied |
| [002](TASK-002-high-Sol.md) | Implemented foundation; reuse | Historical interfaces/evidence retained; no new work implied |
| [003](TASK-003-medium-Sol.md) | Implemented foundation; reuse | Historical interfaces/evidence retained; no new work implied |
| [004](TASK-004-high-Astra.md) | [10](active/STEP-10-pilot-readiness.md) | 10 exposes existing real-readiness prerequisite, not full-curriculum completion |
| [005](TASK-005-high-Sol.md) | [10](active/STEP-10-pilot-readiness.md) | 10 exposes existing real-readiness prerequisite, not full-curriculum completion |
| [006](TASK-006-high-Sol.md) | Implemented foundation; reuse | Historical interfaces/evidence retained; no new work implied |
| [007](TASK-007-high-Astra.md) | Implemented foundation; reuse | Historical interfaces/evidence retained; no new work implied |
| [008](TASK-008-high-Astra.md) | Implemented foundation; reuse | Historical interfaces/evidence retained; no new work implied |
| [009](TASK-009-high-Sol.md) | Implemented foundation; reuse | Historical interfaces/evidence retained; no new work implied |
| [010](TASK-010-high-Sol.md) | Implemented foundation; reuse | Historical interfaces/evidence retained; no new work implied |
| [011](TASK-011-high-Astra.md) | Implemented foundation; reuse | Historical interfaces/evidence retained; no new work implied |
| [012](TASK-012-high-Sol.md) | [03](active/STEP-03-dashboard.md) | Only pending private v2 follow-up; v1 implementation retained |
| [013](TASK-013-medium-Sol.md) | [04](active/STEP-04-commands.md) | Only pending private v2 follow-up; v1 implementation retained |
| [014](TASK-014-high-Sol.md) | [06](active/STEP-06-shared-requests.md), [09](active/STEP-09-vendor-qualification.md) | 06 shared controls; 09 rights, coverage and authorized qualification |
| [015](TASK-015-high-Sol.md) | [07](active/STEP-07-forward-integration.md), [10](active/STEP-10-pilot-readiness.md), [11](active/STEP-11-forward-observation.md) | 07 offline integration; 10 participant prerequisite; 11 elapsed trial |
| [016](TASK-016-high-Astra.md) | [08](active/STEP-08-offline-preflight.md), [12](active/STEP-12-readiness-audit.md) | 08 offline preflight; 12 final evidence/paper audit |
| [017](TASK-017-high-Sol.md) | [13](active/STEP-13-paper-portfolios.md) | Remaining scope carried forward |
| [018](TASK-018-medium-Sol.md) | [05](active/STEP-05-local-package.md) | Remaining scope carried forward |
| [019](TASK-019-medium-Sol.md) | [14](active/STEP-14-research-notebook.md) | Remaining scope carried forward |
| [020](TASK-020-medium-Sol.md) | [15](active/STEP-15-scheduler.md) | Remaining scope carried forward |
| [021](TASK-021-high-Astra.md) | [16](active/STEP-16-microstructure.md) | Remaining scope carried forward |
| [022](TASK-022-high-Astra.md) | [17](active/STEP-17-disclosures.md) | Remaining scope carried forward |
| [023](TASK-023-high-Astra.md) | [18](active/STEP-18-governance-review.md) | Remaining scope carried forward |
| [024](TASK-024-high-Sol.md) | [01](active/STEP-01-contracts.md) | Remaining scope carried forward |
| [025](TASK-025-high-Astra.md) | [02](active/STEP-02-accounting.md) | Remaining scope carried forward |

There are 18 active steps, each containing its remaining implementation and acceptance brief. Sequence numbers are separate from historical task identities. Existing filenames, links and completion evidence remain valid. The former 24 → 25 → 12 → 13 → 18 is now 01 → 02 → 03 → 04 → 05.

The later chain explicitly separates shared controls, consumer integration, preflight, authorized qualification, participant readiness, real observation, final audit and paper operation. These were existing obligations; separating them neither expands authority nor weakens gates. Step 10 adds no universal book count or all-seven-curricula requirement. Optional broker submission and scheduling remain optional.

The later ordering expresses product priority, not new dependencies: notebook fixtures need no paper account; microstructure and disclosure work need no scheduler. Each brief states the actual starting evidence and the queue describes how to handle blocked real-world gates.

Normative detail remains [performance v2](../docs/portfolio-performance-v2.md), [private rights](../docs/data-rights-matrix.md), [request budgets](../docs/market-data-request-budget.md) and [ADR-004](../decisions/records/ADR-004-local-observatory.md). No approved risk limits, source access, live-capital exclusion or real elapsed evaluation requirement is removed.

## Validation

Documentation checks passed: 18 contiguous active steps with purpose, starting evidence, finished state and forward handoff; all 25 original task bodies preserved exactly beneath their new navigation notices; every historical ID mapped; 577 local targets/anchors checked across 78 documentation files; Git whitespace checks passed. The affected paths are 55 Markdown files, including new active briefs and the historical index.

Remaining-scope review retained the two new accounting tasks, private UI/command/packaging follow-ups, all shared-rate and staged-audit requirements, forward/paper boundaries, and notebook/scheduler/specialist/disclosure/governance outcomes. The new real-readiness step exposes an existing prerequisite. Default delivery priorities are distinguished from hard evidence gates.

Runtime code is unchanged. No new runtime test suite was necessary or claimed; META-001's earlier 154-test result remains historical evidence. This refactor does not implement FIFO/TWR, launch reading, call an account or deploy a UI.
