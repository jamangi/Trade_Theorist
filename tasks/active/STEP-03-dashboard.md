# Step 03: Build the private Individual and Monarchy views

- Status: implemented and verified 2026-09-06; Step 04 remains pending
- Recommended model / effort: Sol / high
- Historical coverage: [TASK-012](../TASK-012-high-Sol.md)
- Queue: [ordered remaining work](../README.md)
- Design inputs: [Dashboard design](../../docs/dashboard.md), [rights](../../docs/data-rights-matrix.md)

## Why this position

Reuse the dashboard to inspect the proven numbers, mark eligibility and separate execution bases.

## Starting evidence

Step 02's production projections pass; preserve the implemented fixture UI.

## Finished state

A distinct private-owner-v2 read model and accessible Individual/Monarchy views explain the six success questions, execution bases, lots, flows, costs and unavailable values.

## Implementation and acceptance

Retain equity/drawdown history, readiness and learning provenance, holdings, decisions, advice, costs and evidence grades. Preserve historical version selection, pending outcomes, no-trade cases and no cross-regime ranking. Reuse the existing layout rather than discarding its tested behavior.

Reuse the implemented layout, six answers and accessibility behavior with a distinct `private-owner-v2` read model after Step 02. Display Individual/Monarchy while retaining `character_portfolio`/`council` internally. Surface FIFO lots, total/available/reserved cash, dividend receivables, TWR and flow-neutral drawdown, external flows, recurring cost, mark freshness and reconciliation status. Private schema fields obey the [rights matrix](../../docs/data-rights-matrix.md); no raw/real values enter the legacy fixture exporter.

Filter by execution basis and Character version. Monarchy paper results and its matched simulated control remain separately identified; never rank Individual simulations against broker fills as a reasoning contest. Give real empty/unready states for untrained Characters. Validate mobile/keyboard use, all six answers and no network/model calls on interaction. This follow-up has its own v2 validation below; it does not relabel the historical v1 browser tests.

Walk through both tabs on narrow and wide screens and with keyboard only; verify six answers and evidence links, historical version selection, pending outcomes, stale data, no-trade cases, and no cross-regime ranking. No model call on opening a panel.

## Validation and handoff

Use the [focused validation workflow](../../docs/development.md). Record changed files, actual checks, evidence artifacts and remaining blockers here. For code changes, run relevant tests and the full suite once after focused checks pass; for UI changes, verify keyboard and narrow/wide layouts too. Original synthetic acceptance never substitutes for required real-source or elapsed-time evidence.

Stop at this step's finished state. The default next item is [Step 04](STEP-04-commands.md); do not start it automatically. Follow the queue's blocker rule for independent work. Preserve historical completion claims. No account call, order, paid subscription, public market-data deployment or recurring work is authorized merely by this task brief.

## Start fresh from the repository

Read [the Step 03 reproduction/API guide](../../docs/step-03-private-dashboard.md).
It contains the exact original-fixture command, file/test map and browser checklist.
No cached conversation or generated JSON dump is needed. Next, implement only
[Step 04](STEP-04-commands.md): explicit v2/private command selection, actionable
prerequisites and documented operating integration. Step 05 still owns hardened
real-data serving. The development HTTP preview is for original synthetic data only.

## Delivered interfaces and behavior

- `export_v2.py`: strict private-owner-v2 allowlist, source rights/lineage checks,
  matching projection/hash validation, core monetary replay checks, exact lot/relief
  revisions, cutoff-scoped mark evidence, separate execution bases and atomic export.
  Real-source output inside Git is rejected independently of fixture flags.
- `dashboard/private.html` / `private.js`: Individual/Monarchy views over the
  existing layout and shared chart/table/dialog helpers. Filters cover saved report,
  portfolio window, Character version, advice, horizon, regime and execution basis.
  Lots, flows, cash components, receivables, TWR, drawdown, costs, freshness, readiness,
  pending forecasts, advice and six evidence answers are visible with null reasons.
- Optional typed `inspection_context` saves authored explanations, source citations,
  learning progress, advice, forecast sample and heartbeat status. Frozen Character
  readiness remains authoritative; missing context is unknown. Context cannot claim
  a future heartbeat. Existing Character learning behavior is unchanged.
- `fixtures_dashboard_v2.py` and `scripts/build_step_03_fixture.py` reproduce the
  original fixture from the production store/accounting path. Generated browser
  output stays under ignored `.local/private-v2-demo/`. Schema source/export and
  the field inventory are updated; v1 stays fixture-only and separately rendered.

The original vector remains 1548 equity, 1188/1088/100 total/available/reserved cash,
343 basis, 28 realized, 3 income, 0.05750570 TWR and 0.01901141 drawdown. The explicit
restated mark produces 1554 equity without replacing the original as-known view.
Paper and simulated-control portfolios have separate IDs, capital and returns;
control matching checks frozen owner content, decisions, policy, costs, window and
flow timing. There is no cross-basis difference score or ranking.

## Actual checks

- Focused accounting/export/contract checks passed. Final focused private/context
  run passed **2/2 modules in 8.3 seconds**.
- Final full suite passed **217 tests across 24/24 modules in 36.9 seconds**.
  The suite was repeated after the final future-heartbeat validation change.
- Original private fixture builder, generated schemas and field inventory check
  passed: **1,534 declared fields classified**. `git diff --check` passed.
- Browser walkthrough used **1365×1000** and **390×844**. Both tabs, arrow/Home/End
  selection, keyboard Explain, all six answers, evidence dialog/Escape, history
  table, Character-version selection, paper/control navigation, stale/corrected
  reports, pending outcomes, unknown costs, failed heartbeat, unready and no-trade
  states worked. Tables scroll within their regions; neither width had page-wide
  overflow. Browser console showed no application errors or warnings.
- The rebuilt v1 fixture page retained Council/Character tabs, keyboard switching,
  its original values and six-answer disclosure without browser console errors.
- Private builder tests trap network access and verify unchanged database hashes.
  Browser interactions use the loaded bundle. Source inspection confirms only two
  private fetches, both local report/schema at load, and only local assets; no
  account/model/remote-asset path is added.
- Tests cover denied context rights before output creation, unknown keys, bad hash,
  missing evidence, interrupted atomic handoff, absent evaluations/context, broker
  identifier omission, fixture-flag misuse, corrected/withdrawn marks and preserved
  historical values.

No bounded Step 03 blocker remains. This is original synthetic UI/accounting
acceptance, not real-source readiness or authorization for an account operation.
The root README, queue, rights status and development guide now point to the next
bounded work and explain how to resume without conversation history.
