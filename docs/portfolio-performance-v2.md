# Portfolio and performance contract v2

> Subsequent queue refactor (2026-09-06): [ordered remaining work](../tasks/README.md) now starts at Step 01. Original TASK references below remain stable historical/contract references; [the crosswalk](../tasks/CROSSWALK.md) gives their active steps.

Date: 2026-09-06. Status: versioned design with implemented production contracts, accounting and offline reconciliation. [Step 01](step-01-contracts.md) implements operational v2 contracts and explicit persistence with a checked synthetic migration boundary. [Step 02](step-02-accounting.md) integrates persistent FIFO/TWR with a separate simulator/evaluator and proves the golden vector and offline broker attribution. [Step 03](step-03-private-dashboard.md) adds the private owner read model and verified browser views. Private command integration, hardened real-data serving and real operational readiness remain pending. Existing `raw-next-open-ledger-v1` results keep their original average-cost meaning.

## Identity and execution basis

Every projection identifies contract version, experiment, portfolio, mode, owning Character/version, execution basis, reporting currency, policy, source event IDs/hash, effective cutoff, receipt cutoff, mark policy, accounting method and report revision. Retain `character_portfolio`/`council`; baseline is a portfolio role. `simulated` and `paper_broker` are execution bases, separate from modes. An Individual paper-broker portfolio is invalid under the current arrangement.

Neither Character identity nor symbol alone keys a position. Partition orders, lots, marks, cash and returns by experiment and portfolio. A shared observation ID is permitted; a shared balance is not. An experiment with changing Character versions either ends a frozen comparison window or explicitly records a new longitudinal segment. Show the segment boundaries rather than stitching incompatible minds into one claimed fixed-strategy backtest.

For a fair decision comparison, use identical simulated fill rules for Individual and a Monarchy control. Monarchy's real paper fills remain a separate series and ledger. Do not add those series, replace the control's fills, or credit an Individual with the broker's aggregate equity. Execution divergence is measured separately and may explain apparent return differences.

## Canonical events and lots

Persist immutable funding/contribution/withdrawal, order/reservation/release, fill, fee, dividend entitlement/payment, split, correction, mark and halt events. Each has a stable idempotency key, effective time, observed time, ordering sequence, portfolio identity and source/provenance. Monetary calculations use decimal arithmetic. Money is rounded at actual cash-event boundaries; preserve basis-allocation residuals until the final lot relief, so no cents disappear across partial sales. Fees represented in fills must not also be applied as duplicate standalone fees.

Maintain FIFO lots with `lot_id`, originating fill/order, instrument, acquisition time, original/remaining quantity, original/remaining cost basis (including acquisition fees), and corporate-action lineage. A sale records relieved lot IDs, relieved quantities, allocated basis, proceeds and disposal fees. FIFO realized P/L is net proceeds minus relieved basis. Weighted-average remaining basis per share is a display convenience. It is not the amount to relieve when FIFO sells the oldest shares.

Reservations reduce **available** cash and leave **total** cash unchanged. Release/fill/cancel affects only the reservation tied to the order. Do not erase unfilled quantities on a partial fill. Reject sales beyond owned/unreserved shares, withdrawals exceeding available cash, missing identity, duplicate IDs with changed content, and unknown event types. An exact duplicate delivery is a no-op.

Dividends establish an entitlement receivable once, based on the holdings eligible under the frozen corporate-action policy. Payment converts receivable to cash without new income. The ex-date price and mark provenance must be explicit; never credit a receivable while retaining an unadjusted cum-dividend mark as if it were current. Splits change quantity and per-unit basis/marks while preserving total basis and equity. Fractional cash-in-lieu requires an explicit event and price; no invented payment. Pending-order changes and corporate actions are reconciled against actual provider behavior.

Corrections append a reference to the corrected event with reason, source evidence, observed time and a new projection revision. Rebuild affected lots, flows and dependent reports deterministically; keep the original as-known report accessible. Never edit old cash/fill history. A late broker correction cannot become information available to an earlier decision.

## Marks and components

A mark includes instrument, price, event/receipt/publication times, feed, adjustment basis, observation revision/source, eligibility cutoff and status `eligible/stale/missing`. Quotes/bars need their own mark policy. Stale or missing holdings make dependent valuation null with a reason; show last-known values only with their original timestamp and an unmistakable stale label. Do not zero a held instrument or use a later backfill to silently repair an earlier as-known report.

For the long-only cash pilot:

```text
total_cash = available_cash + reserved_cash
equity = total_cash + distribution_receivables + marked_holdings
net_external_flows = contributions - withdrawals       # after initial funding
strategy_P/L = equity - initial_funding - net_external_flows
unrealized_P/L = marked_holdings - remaining_FIFO_basis
strategy_P/L = realized_P/L + unrealized_P/L + income - unallocated_expenses
```

Acquisition/disposal fees already affect basis/realized P/L, so the last identity must not subtract them again. Report gross cost totals for explanation, not a second charge. Any future liability is a separate contract extension that subtracts from equity. Unknown receivable valuation, unsupported corporate actions or unreconciled cash differences block a fully reconciled value.

## Return, drawdown, and null behavior

At each external flow, obtain time-eligible NAV immediately before the flow `V−` and after it `V+ = V− + flow`. Split the period there. With subperiod start-after-flow `B_i` and end-before-next-flow `E_i`, `TWR = product(E_i / B_i) - 1`. Initial funding starts the series; it is not a return. An actual dated withdrawal uses a negative flow. No positive starting NAV or missing flow-boundary marks makes the affected linked return unavailable; do not substitute endpoint return or an approximate flow-adjusted method under the TWR label.

Compute drawdown from the chained, flow-neutral wealth index, not raw equity that jumps when money is deposited. Preserve the full declared mark schedule. Missing intermediate required marks invalidate schedule-dependent drawdown/volatility even if endpoint return can be computed for a no-flow subperiod. Missing current marks invalidate current equity/unrealized P/L/TWR. A complete withdrawal terminates the funded segment; new funding begins a new segment, not a divide-by-zero recovery. Report this explicitly.

Dollar P/L, TWR and owner money-weighted return answer different questions. Money-weighted return is optional and must disclose timing, solver and unavailable/nonunique-solution cases. Do not add it merely to make a poor TWR look better. Compare against zero-interest cash and a frozen broad-market total-return benchmark with matching flow timing, period, costs and eligible instruments. Show benchmark construction and why a cash-only Character may rationally abstain. Baseline contributions/withdrawals mirror the strategy's amounts and timestamps or the comparison must be labeled unmatched.

Turnover retains its existing documented gross-traded-notional convention with a specified equity denominator and sampling schedule. Closed-position hit rate stays separate from FIFO lot-relief win rate; do not inflate sample count by splitting one sale into many lots. Forecast calibration uses preregistered event/horizon and matured observations. Insufficient samples, heterogeneous regimes, dependent observations and trial multiplicity remain visible.

Show recurring model/data/hosting expense and attributable strategy dollar P/L side by side; a separate experimental-economics view can deduct known recurring operating costs once. One-time research/learning costs and speculative live scaling belong in separately labeled totals or scenarios. Do not alter approved trading TWR with a hidden cost allocation or assume a larger future portfolio can earn the same percentage without impact.

## Hand-worked reference

All figures below are original fictional values for one instrument. No market data is used. The executable vector is [the performance fixture](../examples/meta-001/performance-v2.fixture.json), validated against [its schema](../schemas/meta-001/performance-v2.schema.json). The test reducer is a reference specification only; TASK-025 must match it through the actual persistent implementation.

| Step | Total cash | Shares | FIFO basis | Receivable | Eligible mark | Equity | Realized P/L |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Initial funding | 1,000 | 0 | 0 | 0 | — | 1,000 | 0 |
| Buy 2 at 100, fee 2 | 798 | 2 | 202 | 0 | 100 | 998 | 0 |
| Buy 2 at 120, fee 2 | 556 | 4 | 444 | 0 | 120 | 1,036 | 0 |
| Sell 1 at 130, fee 1; relieve 101 | 685 | 3 | 343 | 0 | 130 | 1,075 | 28 |
| Dividend ex-date, 1/share; mark becomes 129 | 685 | 3 | 343 | 3 | 129 | 1,075 | 28 |
| Pay dividend | 688 | 3 | 343 | 0 | 129 | 1,075 | 28 |
| 2-for-1 split | 688 | 6 | 343 | 0 | 64.5 | 1,075 | 28 |
| Eligible mark 65, before deposit | 688 | 6 | 343 | 0 | 65 | 1,078 | 28 |
| External deposit 500 | 1,188 | 6 | 343 | 0 | 65 | 1,578 | 28 |
| Reserve 100 | 1,188 (1,088 available) | 6 | 343 | 0 | 65 | 1,578 | 28 |
| Eligible mark 60 | 1,188 | 6 | 343 | 0 | 60 | 1,548 | 28 |
| Mark becomes stale | 1,188 | 6 | 343 | 0 | unavailable | unavailable | 28 |

Before the stale mark: income 3, fees 5 already included, unrealized gain 17, dollar strategy gain `1548 - 1000 - 500 = 48 = 28 + 17 + 3`. Remaining FIFO lots are 2 split-adjusted shares with basis 101 and 4 shares with basis 242. Average remaining basis is `343 / 6`; it does not change the first lot's relief.

TWR is `(1078 / 1000) × (1548 / 1578) − 1 = 0.05750570` rounded to eight places. The flow-neutral peak-to-final drawdown is `1 − 1548 / 1578 = 0.01901141`. The naive `1548 / 1000 − 1 = 54.8%` would incorrectly credit the deposit. At the stale step current equity, unrealized P/L, strategy P/L and current return are null, while known cash, realized P/L and lot quantities remain available.

## Broker attribution contract v1

[The attribution schema](../schemas/meta-001/broker-attribution-v1.schema.json) and [synthetic fixture](../examples/meta-001/broker-attribution-v1.fixture.json) specify an internal order and its private mapping. Generate a random opaque 32-hex-character client ID after policy approval and before submission; do not encode experiment, Character, portfolio, recommendation or secret identifiers in it. Persist the mapping and an outbox entry atomically. Individually simulated orders have no mapping or client ID. One internal paper order has one submission identity; replacement is a new explicitly related order, not a mutation of that identity.

Updates resolve through the client/broker ID mapping to one internal order and originating final recommendation. Store effective/observed timestamps, provider event identity, cumulative quantity/notional/fees, incremental fill identity and status. Deduplicate exact updates; quarantine conflicting duplicate IDs, unknown mappings, impossible quantities, decreasing cumulative values or unrecognized replacements for reconciliation. Out-of-order observations cannot erase already confirmed fills. Cancellations and rejections leave prior partial fills intact.

On timeout, persist `unknown` and reconcile; no blind resubmission or assumption of cancellation. Broker account resets, manual activity or unexplained aggregate differences halt new submissions until attributed. Initial Monarchy broker cash must be reconciled to the approved experiment funding; a pre-existing account balance is not an unexplained windfall. Broker omissions (such as dividends) require explicit reconciliation adjustments and separately labeled economic-versus-broker values, not duplicated cash income.

Official [order documentation](https://docs.alpaca.markets/us/docs/working-with-orders) describes client IDs and warns about resubmitting timed-out orders. The [paper documentation](https://docs.alpaca.markets/us/docs/paper-trading) describes simulation omissions. The mapping supports inspection; it does not create independent subaccounts. No submission adapter is implemented or invoked by META-001.
