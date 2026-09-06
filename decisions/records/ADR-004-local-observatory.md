# ADR-004: Private observatory, versioned accounting, and attributable execution

> Subsequent queue refactor (2026-09-06): [ordered remaining work](../../tasks/README.md) now starts at Step 01. Original TASK references below remain stable historical/contract references; [the crosswalk](../../tasks/CROSSWALK.md) gives their active steps.

Date: 2026-09-06. Status: accepted architecture under the [approved META-001 defaults](../../tasks/meta-tasks/APPROVALS.md). Production migration is pending. This decision supersedes ADR-001's active public-dashboard target and amends ADR-003's delivery boundary; it does not replace vendor qualification or authorize requests/orders.

## Decision

1. The owner UI is a single-page, read-only private application served by a minimal loopback-only service over a generated, validated private bundle. Serve only that bundle, not the database, `.env`, books or general filesystem. TASK-018 owns packaging and host/origin/path protections. A public host is unnecessary.
2. Display **Individual** and **Monarchy**. Preserve the actual serialized identifiers **`character_portfolio`** and **`council`**. The earlier approval's plural `character_portfolios` is a prose mismatch, not a reason to rewrite valid stored records. Monarchy describes selected-lead advice and existing deterministic risk governance.
3. Preserve existing v1 records, migrations, average-cost simulation results and fixture evidence. TASK-024, the next bounded implementation task, adds v2 contracts/persistence; TASK-025 adds the portfolio/performance projections. Do not silently reinterpret old realized P/L as FIFO or external funding as performance.
4. Independent Individual ledgers retain simulated executions. Only an explicitly authorized Monarchy paper order can receive an opaque broker client ID. Its internal order resolves the originating final recommendation, portfolio and experiment. Broker cash/positions are aggregate reconciliation evidence, not separate Character capital.
5. A Monarchy paper ledger and any matched Monarchy simulated control have distinct portfolio IDs and execution bases. The control is a research comparison, never a second submission. Without matched simulation, Individual-versus-paper performance is descriptive, not an attribution of superior reasoning. No new broker account or capital is implied.
6. Retire active GitHub Pages deployment under TASK-018 and replace its outcome with private packaging. Public original synthetic demonstrations/source documentation remain allowed. Real-data publication and unclassified derived fields are denied by default; a future proposal requires a separate owner and rights decision.

## Delivery boundary

The existing v1 exporter is now explicitly fixture-only. Its removal of raw bars was insufficient: `holding.value / holding.quantity` can reconstruct a mark, and returns/holdings may retain licensed information. It rejects non-synthetic stores, persisted non-fixture records, non-synthetic observation feeds and non-fixture output cards/private evidence. This protection does not certify intentionally mislabeled input. Fixture generation must continue to use original project data.

TASK-012's layout, interaction patterns, six explanation panels and accessibility work are reused. It is not renamed or rebuilt during this review. TASK-024 introduces contracts and TASK-025 integrates accounting; then 012 updates the private read model and labels; 013 updates commands; 018 packages the loopback UI. None of these depends on credentials for synthetic validation.

## Economic purpose

The next useful evidence is a version-frozen forward comparison against cash and broad-market baselines with identical opportunity sets, costs and execution assumptions. Show after-cost TWR, drawdown, uncertainty, horizon and operating expense; do not optimize activity or agreement. Separate recurring inference/data cost from one-time learning/development cost. A Character's more elaborate personality, completed books or recent win does not establish a trading edge.

The [impact report](../../docs/meta-001-impact.md), [performance contract](../../docs/portfolio-performance-v2.md), [rights matrix](../../docs/data-rights-matrix.md) and [START-HERE](../../tasks/meta-tasks/START-HERE.md) specify the evidence and implementation sequence. Open provider-rights and numeric paper-risk decisions block their dependent operations, not this review or offline repair.
