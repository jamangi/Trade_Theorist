# Step 02: Persistent FIFO accounting and offline attribution

Implemented 2026-09-06. [The active brief](../tasks/active/STEP-02-accounting.md)
records validation and the Step 03 handoff. This is an explicit v2 path; the v1
average-cost simulator, evaluator, databases and migration checksums remain intact.

## Entry points and durable inputs

- `V2Store` explicitly opens the v2 store, now through additive migration 004.
  It adds uniqueness constraints for frozen plans, order execution terms and
  performance revisions without rewriting migrations 001–003.
- `SimulatorV2(store, portfolio_id).command(id, records)` atomically validates
  typed inputs, applies the reducer and records an immutable command receipt.
  An identical retry returns that receipt; changed inputs under the same ID fail.
- `fill_order(command_id, order_id, mark_id, quantity, at=...)` explicitly advances
  a simulated partial or complete fill. The frozen `eligible-next-event-v2` model
  requires a new eligible raw event after order creation, the order's execution
  interval and limit, adverse spread/slippage, and per-share fees rounded per fill.
  Partial quantity is a declared replay input; this step does not model queue
  priority, volume participation or automatic liquidity availability.
- `evaluate(store, portfolio_id, effective_cutoff=..., receipt_cutoff=...)` saves
  a typed `performance_result`, projection, FIFO lots and reliefs in one transaction.
  Source IDs/hashes, frozen plan, revision, costs, baseline hash and both cutoffs
  make the private read-model inputs inspectable. Repeating the same evaluation
  reuses its saved result. An interrupted command/projection leaves no partial
  write or second cash movement.
- `correct(command_id, target_id, payload, observed_at=...)` appends a correction
  and replacement at the original effective time. Earlier receipt cutoffs retain
  the original as-known result; later cutoffs explicitly restate it. A withdrawn
  mark becomes missing; unresolved accounting corrections become gaps. A correction
  never silently clears a saved risk halt.

The implementation is in `adapters/trader_user_sim/v2.py`,
`adapters/trader_user_sim/broker_v2.py`, `evaluate/ledger_v2.py` and
`evaluate/portfolio_v2.py` under `src/trade_theorist/`. Schema declarations and
the generated field inventory cover every new record. Each replayed source must
permit private replay, and each reported source must permit the private read model.
No browser, public export, CLI workflow or submission transport is added here.
Step 03 can consume these records while keeping owner, funded segment, mode and
execution basis visible and separate.

## Arithmetic and funding policy

Cash movements and reservations use cents. FIFO basis/proceeds allocations retain
28 decimal places, with the final relief consuming the exact remaining residual.
Acquisition fees enter basis, disposal fees reduce realized P/L, and neither is
charged a second time as an operating expense. Partial fills release only their
own proportional reservation, rounded to cents; cancellation releases the remainder
without reversing confirmed fills. Separate fees must reference a fill whose fees
were declared separate. Closed-position hit rate and individual lot-relief win rate
are distinct samples and include later attributable disposal fees.

For an active segment:

```text
equity = cash + eligible marked holdings + unpaid dividend receivables
unrealized = marked holdings - remaining FIFO basis
strategy P/L = equity - initial funding - net external contributions
             = realized + unrealized + income - unallocated trading expenses
```

The accounting plan freezes allowed flows by segment, type, exact time and amount
before the experiment window. Each grant can be used once. Withdrawals cannot spend
reserved cash. Initial funding agrees with frozen policy capital; later grants do
not automatically raise deployed-capital limits. Fixture grants approve no real
funding. A complete withdrawal requires settled unreserved cash; refunding needs
an ended predecessor and a distinct preregistered funded segment. Returns are not
stitched across those segments or changing Character versions.

At each external flow, link the pre-flow equity divided by the previous post-flow
equity into a wealth factor, then reset the local denominator to pre-flow equity
plus the signed flow. At the report endpoint, multiply by the final local ratio
and subtract one for exact TWR. Held instruments need explicitly referenced,
eligible flow-boundary marks; absent evidence makes TWR null, even when current
cash and equity are otherwise known. A full withdrawal preserves the last return
without dividing by zero.

Drawdown tracks the peak of this flow-neutral wealth on the frozen mark schedule.
The trusted governor receives equivalent NAV denominators derived from wealth;
deposits therefore do not hide losses. Orders and simulated fills are independently
checked. Missing valuation or a loss threshold halts admission, and the command
persists that halt so a later correction, deposit or funded segment cannot erase it.
Existing accepted orders and fills are not re-admitted during historical replay;
restated marks change valuation without retroactively rewriting execution. Actual
attributed paper fills remain accounting evidence even when they breach risk.

Stale, missing or ineligible marks make dependent current values null with reasons.
An absent intermediate required valuation also invalidates drawdown and volatility;
endpoint TWR can still recover if no unknown flow boundary intervened. Volatility
is unannualized sample deviation of scheduled linked returns; turnover is gross
traded notional divided by mean scheduled equity. A terminal cutoff is also sampled.

## Corporate actions and explicit limits

Dividend entitlement is recognized once using actual ex-date holdings and an
explicit raw ex-date mark. Payment moves the receivable to cash without recognizing
income again. Splits preserve total lot basis and adjust shares using an explicit
post-split mark. Submit each corporate action together with its mark in one command
to avoid exposing a transient unadjusted valuation to admission checks.

Fractional orders/fills follow the frozen plan. Fractional-share split holdings are
supported when enabled. Whole-share splits that require fractional cash settlement,
explicit cash-in-lieu, and splits with pending orders record a gap and halt; they
do not invent settlement proceeds or automatically adjust broker orders. Pending
orders require explicit cancellation/replacement reconciliation. A separate
acquisition fee arriving after its lot has been relieved requires an explicit fill
correction. These gaps require reviewed reconstruction before operational use;
this step does not provide an automatic halt-clear or corporate-action adjudicator.

## Offline broker reconciliation

`BrokerReconcilerV2` accepts only an isolated Monarchy paper ledger. Persisted
updates resolve through exactly one durable submission mapping/internal order.
It derives incremental fills from cumulative quantity/notional/fees, deduplicates
identical updates and preserves partial executions after cancellation or rejection.
An earlier observation received late can split an already recorded aggregate fill
through explicit corrections; total cash/basis are unchanged and earlier as-known
reports remain available.

Conflicting identities, unknown mappings, decreasing cumulative totals, unrecognized
replacements, and fee/notional-only revisions require reconciliation. Confirmed
cash movements remain; gaps are visible. A timeout keeps the existing mapping and
reservation, marks the outbox unknown, and does not resubmit. Aggregate account
snapshots compare cash and positions without importing them as funding. Account
resets and unexplained activity halt the ledger instead of becoming performance.
A later matching snapshot does not clear the recorded halt. All operations are
offline; no broker client, network request or order submission runs.

## Baselines, costs and evidence

The zero-interest cash baseline has zero return under identical external flows.
The broad-market baseline is an independently funded portfolio, evaluated through
the same reducer. Matching requires identical flows, market evidence, window,
universe, costs, fractional policy, execution model, mark schedule and execution
basis. Missing or mismatched baseline evidence is null with a blocker. The fixture
baseline buys nine units at the next eligible event, retains the later contribution
as cash, and includes its own fees, dividend and split; its day-11 TWR is 0.20542373.

Recurring model/data/hosting costs are separate from trading TWR; economics dollar
P/L deducts them once. Learning/development costs remain one-time costs. An explicit
unknown cost produces a null cost/economics value; an empty registered cost ledger
totals zero and does not establish a real economic advantage. Every result carries
an evidence grade and review blockers. Promotion is always false in this path;
descriptive matched comparisons are not a skill or forward-readiness decision.

## Reproducible evidence

Run `python scripts/build_step_02_fixtures.py` to rebuild
[`examples/accounting-v2/`](../examples/accounting-v2/). It checks the actual store,
production reducer, typed bundle, replay chain and side-by-side v1 conversion:

| Before stale mark | Expected v2 value |
| --- | ---: |
| Cash / reserved | 1188 / 100 |
| FIFO basis / realized / income | 343 / 28 / 3 |
| Equity / strategy dollar P/L | 1548 / 48 |
| TWR / flow-neutral drawdown | 0.05750570 / 0.01901141 |

`before-stale.json` and `after-stale.json` are private-read-model shaped original
synthetic examples; `bundle.json` contains their typed evidence, and
`side-by-side.json` records preserved v1 hashes/results and explicit conversion gaps.
Before the external flow, the same fills yield v1 average-cost basis 333 / realized
18 and v2 FIFO basis 343 / realized 28, with identical equity 1078. Historical
average-cost holdings are not fabricated into FIFO lots during conversion.

Use the [quiet validation workflow](development.md); rebuild/validate the examples
without dumping the large bundle into a session. The full source bundle remains
available on disk for targeted inspection. This work did not reproduce or establish
the cause of the reported memory exhaustion; the existing per-module process/log
runner already bounds console output and releases test-process memory between modules.
