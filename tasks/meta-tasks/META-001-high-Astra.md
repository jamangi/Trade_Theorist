# META-001: Pivot to a local-first observatory and formalize Character performance

- Status: complete (2026-09-06), within the bounded architecture/reference-contract scope below
- Recommended model: GPT-6 Astra (`gpt-6-astra`)
- Recommended effort: high
- Authority: repository owner's 2026-09-06 request to reconcile Alpaca data limits,
  local UI, Individual/Monarchy modes and portfolio attribution
- Owner policy: all recommended defaults in [APPROVALS.md](APPROVALS.md) approved on
  2026-09-06
- Does not authorize: paid subscriptions, new account calls, paper orders, live orders
  or public Alpaca data

## Objective

Audit and, where justified, amend the architecture and task graph so Trade Theorist is
local/private by default, offers an aesthetic and comprehensive single-page owner UI,
and measures each Character and the lead-led council without relying on Alpaca's
aggregate account statistics for strategy attribution.

Produce a precise task starting point. Recover architectural integrity at the earliest
affected contract without erasing valid completed work or pretending a design change was
already implemented.

### Refinements adopted for this execution

Optimize the next implementation path for credible prospective, after-cost advantage over frozen baselines, not feature count or a profitable-looking dashboard. Track recurring operating cost separately from trading return, preserve failed trials, and require independent initial opinions and scheduled knowledge-version changes. Waiting can be a good decision; no monthly trade quota or automatic promotion follows a gain.

Separate **decision comparison** from **execution comparison**. Individual simulated fills and Monarchy broker fills have different assumptions. Compare Characters and council using a matched simulated execution basis; show any Monarchy paper result as a separately identified reconciliation/execution series. Never overwrite hypothetical fills with broker fills or pool those ledgers. If no matched control exists, show results descriptively without ranking decision skill across execution bases.

Account for unsettled distribution receivables and use flow-adjusted return/drawdown. An external deposit is not profit; a dividend payment settles an existing receivable rather than recognizing income twice. Audit the actual internal mode spelling before making migrations, even if older prose names it differently.

Deliver an executable, original synthetic contract fixture and focused regression checks, plus a prioritized migration task. This remains a bounded architecture review: reference-contract tests do not imply a production ledger migration, a private UI implementation, or broker reconciliation is complete. Apply small protective corrections when the audit exposes a current publication escape; queue the full runtime migration explicitly. Finish with a deliverable/evidence table separating implemented protection, tested contract arithmetic, and pending integration. Stop expanding the review once the earliest repair and measurable acceptance are concrete.

## Starting facts to verify

1. TASK-012 already implements a local read-only two-tab fixture dashboard. TASK-018
   still proposes public GitHub Pages deployment. Determine which implementation and
   export contracts are reusable under a private-first boundary.
2. The repository already models separate `portfolio_id`, cash, holdings, fills and
   append-only ledger events. Inspect actual schemas, storage, simulation, evaluation,
   dashboard and tests before proposing replacements.
3. Current Alpaca terms describe personal/non-commercial use, and Alpaca's support page
   states that Alpaca API data cannot be redistributed. Do not infer private retention,
   internal replay, post-subscription retention or derived-publication rights merely
   from successful API access. Record primary-source versions and distinguish documented
   permission, documented restriction, reasonable design assumption and unanswered
   question.
4. Alpaca supports a caller-supplied `client_order_id` and documents different IDs as a
   way to track parallel strategies in one account. The ID is attribution metadata, not
   a subaccount: account cash, buying power, net positions and equity remain aggregate.
5. A Character proposes a recommendation. It never owns credentials or invokes Alpaca
   directly. A deterministic allocator/risk gate creates an internal order, and only a
   separately authorized broker adapter may submit it.

Primary evidence to recheck at execution time:

- [Alpaca Terms and Conditions](https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf)
- [Alpaca redistribution policy](https://alpaca.markets/support/redistribute-alpaca-api)
- [Alpaca Market Data API plans](https://docs.alpaca.markets/us/docs/about-market-data-api)
- [Alpaca order IDs](https://docs.alpaca.markets/us/docs/working-with-orders)
- [Alpaca paper-trading limitations](https://docs.alpaca.markets/us/docs/paper-trading)

## Target product model

### Local/private owner interface

Use a single-page HTML/JS application that runs locally from validated saved records.
The browser receives neither broker credentials nor unrestricted filesystem access.
Choose and document one safe delivery pattern: a generated private static bundle, or a
loopback-only local service with explicit origin/access controls. It must work without a
public host and default to refusing non-loopback binding.

The visible primary tabs are:

- **Individual:** one independently funded virtual portfolio for every eligible
  Character, including readiness, equity, after-cost return, benchmark difference,
  drawdown, exposure, holdings, decisions, abstentions, forecasts and evidence quality.
- **Monarchy:** the existing council mode: a selected lead receives bounded advice,
  makes the final decision, and remains subordinate to deterministic risk policy.

Retain stable internal mode identifiers unless a versioned migration proves a change is
necessary. Explain the visible metaphor accessibly; do not allow a label change to alter
council governance or lead eligibility.

Public publishing is disabled for real Alpaca-backed artifacts by default. A future
derived-only public summary must be a separate owner decision with a field-level rights
matrix and tests proving it contains no reconstructable raw market data. Synthetic demo
artifacts and ordinary source code are a distinct publication class.

### Attribution and execution

Use this owner-approved initial paper arrangement:

1. Every Character commits a decision against the same immutable eligible snapshot.
2. Every Individual portfolio applies its own decision to a separate internal virtual
   cash/position ledger under the same risk and fill rules.
3. Monarchy commits the lead's post-discussion decision to its own internal portfolio.
4. Only Monarchy's approved order is submitted to the shared Alpaca paper account.
5. For each Monarchy internal order separately authorized for broker submission,
   generate an opaque, unique, nonsecret `client_order_id` and durably map it to that
   internal order. The internal order already identifies its experiment, portfolio and
   originating final recommendation. Individual-only simulated orders receive no Alpaca
   client ID. Preserve every broker order/fill update against the mapping.
6. Broker fills reconcile into Monarchy's ledger. Alpaca account values are shown only
   as aggregate reconciliation evidence, never as an Individual Character's return.

If the audit recommends physically submitting multiple Character strategies through one
account, explicitly model shared buying-power interference, opposing-order netting,
partial fills and allocation. Do not claim independent broker portfolios from tags. A
cleaner later alternative is genuinely separate paper accounts or sequential isolated
experiments, subject to provider support and owner approval.

## Canonical portfolio and performance contract

Specify, version and test at least:

- portfolio, experiment, mode, Character and Character-version identity;
- initial funding plus every external contribution/withdrawal with effective time;
- available cash, reserved cash and total cash;
- immutable order, fill, fee, distribution, split, correction and mark events;
- open tax-neutral accounting lots with instrument, side, remaining quantity, fill time,
  fill price, fees and source order;
- weighted-average cost as a convenience view and FIFO lot relief as the proposed
  realized-gain convention;
- current eligible mark with price, event time, receipt time, feed, revision, source and
  stale/missing status;
- realized P/L, unrealized P/L, cash income, trading costs and total equity without
  double counting;
- exposure, turnover, maximum drawdown, trade/abstention counts, forecast calibration,
  evidence grade and reconciliation status;
- frozen cash and broad-market baselines using the same evaluation window and cost
  convention; and
- after-cost time-weighted return as the primary strategy-return measure when external
  flows exist, with money-weighted return only as a separately labeled secondary view.

Define formulas and null behavior. At minimum:

`total cash = available cash + reserved cash`

`equity = total cash + eligible distribution receivables + sum(open quantity × eligible mark)`

The initial long-only cash model has no borrowing liability. Any future liability support requires an explicit contract extension and subtracts liabilities from equity. Reservations are part of total cash, not additional wealth. An unvalued asset or receivable makes dependent equity unavailable.

Dollar strategy P/L must remove net external contributions. Time-weighted return must
split subperiods at external cash flows. Stale or missing marks make dependent values
unavailable rather than zero. Average entry price alone is not sufficient evidence:
lot history, fees, partial sells, dividends, splits and corrections must survive.

Include a hand-worked acceptance fixture with multiple buys at different prices, a
partial sell, a fee, a dividend, a split, an external deposit and a stale mark. Reconcile
the arithmetic to the append-only events and prove that repeated execution is idempotent.

## Required repository audit

Inspect at least:

- root vision/map and ADR-001/ADR-003;
- contracts and persistence from TASK-001/002;
- simulation, risk, ledger and portfolio isolation from TASK-007/008;
- evaluation and export logic from TASK-011;
- local UI/export contracts from TASK-012/013;
- Alpaca qualification, forward evidence and readiness from TASK-014/015/016;
- paper execution and reconciliation from TASK-017;
- public Pages scope in TASK-018; and
- downstream assumptions in TASK-019–023.

For each affected artifact or task, classify it as **preserve**, **amend**, **retire** or
**replace/add**, with a reason and migration effect. Preserve stable task IDs and their
historical status. If completed work needs revision, describe its old proven scope and
add a versioned repair task or explicit follow-up rather than rewriting history.

## Deliverables

1. A dated impact report and dependency diagram.
2. A versioned architecture decision for the local/private UI and publication boundary.
3. A field-level data-rights matrix covering local raw input, private derived state,
   repository-safe evidence, possible public summaries and prohibited/default-denied
   output.
4. Versioned portfolio/performance and broker-attribution contracts, with migration and
   reconciliation rules.
5. Updated dashboard design for Individual and Monarchy, including all existing evidence
   and accessibility requirements.
6. Updated affected task files and task index. Explicitly retire, replace or defer
   TASK-018's public deployment outcome based on the approved boundary.
7. Updated [meta approvals](APPROVALS.md) containing exact recommendations and any
   questions the owner must decide.
8. `tasks/meta-tasks/START-HERE.md` naming one exact next bounded implementation task,
   its prerequisites, files, acceptance commands, migration order and blockers.
9. Passing repository checks and targeted tests for any contracts or runtime behavior
   changed during the meta-task.

## Acceptance

The following are contract and roadmap obligations unless a deliverable explicitly records runtime implementation. Existing protection changes and the synthetic reference fixture must have executable tests; production migration, private UI packaging and broker reconciliation remain separately tracked tasks. No complete-system claim can be inferred from the meta-task's completion.

- No real Alpaca-backed dashboard requires public hosting, and real raw/reconstructable
  market data cannot enter a public or Git export by default.
- Every persisted/exported field has a publication classification and fail-closed default.
- Individual and Monarchy portfolios cannot share cash, lots, P/L or performance despite
  sharing observations.
- Every submitted Monarchy paper order and update can be traced from an opaque
  `client_order_id` to exactly one internal order, and from there to exactly one
  portfolio, experiment and originating final recommendation, without exposing those
  local identifiers, Character commentary or secrets to Alpaca. Individual simulated
  orders have no broker mapping or Alpaca client ID.
- Aggregate broker equity and positions are never presented as independent Character
  performance.
- Performance formulas, external-flow handling, lots, costs, corporate actions, stale
  marks, baselines and evidence grades are explicit and tested.
- Existing valid fixture/dashboard work is reused where possible; no earlier completion
  claim is falsified and no future result is invented.
- The updated graph has no circular dependency and `START-HERE.md` lets a fresh task begin
  safely without rediscovering this discussion.
- No account call, order, subscription, deployment or public data publication occurs as
  part of META-001.

## Completion evidence (2026-09-06)

Executed against main at `7681a34`, using the already-approved defaults. The [impact report](../../docs/meta-001-impact.md) records preserved/amended/retired/new work and the revised dependency diagram. [ADR-004](../../decisions/records/ADR-004-local-observatory.md), the [rights matrix](../../docs/data-rights-matrix.md), [performance/attribution contract](../../docs/portfolio-performance-v2.md), synthetic schemas/fixtures and reference tests complete the design evidence. The legacy exporter now refuses nonfixture inputs and outputs, with regression coverage.

The full suite passed **154 tests in 19 modules**. Both new JSON Schemas validate, all 632 declared field classifications match the generated inventory, and the 25-task graph is acyclic and consistent with its index. Local Markdown targets/anchors and Git whitespace checks passed. The current UI assets are unchanged; no new browser-rendering claim is made.

[START-HERE](START-HERE.md) names **TASK-024** as the next bounded implementation task, then TASK-025. Production FIFO/TWR integration, private v2 UI and broker submission remain pending; reference arithmetic is not evidence of those implementations or trading performance. No new blocking approval was necessary for this review, and no account call, order, subscription or deployment occurred.
