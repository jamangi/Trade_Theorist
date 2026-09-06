# TASK-018: Publish validated reports on GitHub Pages

- Status: planned; public deployment paused pending META-001 local/private rights review
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: medium
- Dependencies: TASK-012, TASK-013, TASK-014, TASK-016
- Design: [dashboard.md](../docs/dashboard.md)

## Scope

Build an allowlisted export and GitHub Pages workflow from sanitized artifacts. Verify rights for each public field; omit restricted source content and private reflections. Document private-runner versus public-site responsibilities, update timing, retention, and rollback. Publishing the dashboard is this task, not the planning revision.

Do not begin this scope until [META-001](meta-tasks/META-001-high-Astra.md) decides
whether it is retired, replaced by local/private packaging, or retained only for a
separately approved synthetic or derived-only publication class. No real Alpaca-backed
artifact is approved for public deployment by this task file.

## Deliverables

Pages build/deploy workflow, inspected public report, README link and update instructions.

## Acceptance

Scan a deliberately secret-bearing private fixture to prove nothing sensitive is exported; validate links and both tabs at the deployed URL. A failed build retains the prior valid report; no browser keys or fake run button.

## Usage rationale

Static publishing and clear documentation need medium effort with a strict export contract.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.

## Result-only publication (2026-09-06)

Read persisted evaluations and allowlisted [request-budget telemetry](../docs/market-data-request-budget.md). Neither the exporter, Pages build nor public browser receives Alpaca credentials or makes Alpaca calls. Show rate-delayed/stale/incomplete status from saved records; missing data is not a reason to fetch from the dashboard. Acceptance runs the export with a provider-call trap and confirms zero Alpaca requests, including page refresh and history selection.
