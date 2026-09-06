# Step 03: Build the private Individual and Monarchy views

- Status: pending; remaining scope as of 2026-09-06
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

Filter by execution basis and Character version. Monarchy paper results and its matched simulated control remain separately identified; never rank Individual simulations against broker fills as a reasoning contest. Give real empty/unready states for untrained Characters. Validate mobile/keyboard use, all six answers and no network/model calls on interaction. This is a pending follow-up, not a new claim about the v1 browser tests.

Walk through both tabs on narrow and wide screens and with keyboard only; verify six answers and evidence links, historical version selection, pending outcomes, stale data, no-trade cases, and no cross-regime ranking. No model call on opening a panel.

## Validation and handoff

Use the [focused validation workflow](../../docs/development.md). Record changed files, actual checks, evidence artifacts and remaining blockers here. For code changes, run relevant tests and the full suite once after focused checks pass; for UI changes, verify keyboard and narrow/wide layouts too. Original synthetic acceptance never substitutes for required real-source or elapsed-time evidence.

Stop at this step's finished state. The default next item is [Step 04](STEP-04-commands.md); do not start it automatically. Follow the queue's blocker rule for independent work. Preserve historical completion claims. No account call, order, paid subscription, public market-data deployment or recurring work is authorized merely by this task brief.
