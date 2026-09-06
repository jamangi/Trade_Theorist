# Tasks 007–008: simulation and independent policy

Implemented 2026-09-06. This is fictional-money engineering. The real paper-policy
template remains incomplete, and no live execution endpoint is implemented.

`trade_theorist.adapters.trader_user_sim.Simulator` reads an experiment, portfolio,
and its pinned policy from `Store`. Its explicit UTC session schedule and execution
assumptions are recorded once; changing them requires a new experiment. Council and
each Character sleeve have different experiment and portfolio identities, with
equal policy-defined starting cash. The portfolio owner alone can submit its final
recommendation. This does not promote any Character to council leadership.

## Runner interface

1. Persist validated experiment, policy, portfolio, observation, snapshot and
   recommendation records using the existing contracts. Instantiate
   `Simulator(store, experiment_id, portfolio_id, sessions)`; each schedule entry
   contains `session`, `open_at`, and `close_at` in UTC. Initialization is idempotent.
2. Pass ingestion's `Normalized(observation, payload)` objects to `mark(snapshot_id,
   items, at=...)`. The adapter verifies stored identity, payload hashes, raw price
   convention, availability, feed, calendar, and frozen-snapshot membership.
3. Call `submit(recommendation_id, at=..., price_cap="101")`. A buy reserves quantity
   times this maximum execution price, plus the recorded fee. The cap is a cash
   reservation bound, not a simulated exchange limit-order queue. Rejections have
   durable reason codes and the policy ID.
4. Call `process_bar(item, at=...)` when the complete raw daily bar is available.
   Execute it **before** later-session marks, decisions or actions. The fill's
   effective time is the scheduled open; its recorded time is the bar's availability
   time. Both the submission time and decision session must precede that open.
   This is retrospective daily-bar simulation, not a claim of receiving the full
   bar at the open. Publication and ingestion must have occurred before processing.
5. Apply corporate actions in effective-time order. `corporate_action` requires a
   stable economic action ID and documentary evidence from the trusted runner.
   `dividend_ex` fixes entitlement before ex-date trading, `dividend_pay` pays that
   entitlement even if shares were sold, and `split` adjusts shares while keeping
   total cost basis and cancels pending orders for new advice. The ex-date carry
   mark is adjusted to prevent double-counting the dividend receivable. Subsequent
   raw market prices replace that carry mark. No dividend is inferred from prices.
   If an action is processed retrospectively, supply its later `recorded_at`
   separately from effective `at`. The processing clock cannot move backward after
   outcomes have been observed, even when effective ledger times are earlier.
6. Mark the closing snapshot, then `reconcile(at=...)`. Missing or stale required
   marks produce null equity and unrealized gain with instrument-level reasons.
   A same-session opening mark is not accepted as a completed closing mark.

Missing bars do nothing; zero-volume bars and gaps above a buy's reservation do not
fill. Call `expire(at=...)` even when there is no bar to release expired reserves.
`cancel(order_id, at=...)` also releases reserves. No order can short holdings or
spend another pending order's cash. Costs are the raw open plus adverse slippage
and half the configured spread for buys, minus those costs for sells. Fill prices
have eight decimal places; USD notionals and fees settle to cents using half-up
rounding. Sub-cent orders are rejected. Fractional shares use average cost basis;
splits requiring more than eight quantity decimals fail closed pending explicit
cash-in-lieu support. Quote execution, total-return/adjusted bars, arbitrary
accounting corrections and unsupported corporate actions also fail closed.

## Policy and persistence

`risk.Governor` enforces universe, available cash, long-only positions, company and
sector concentration, diversified ETF weight, deployed capital, gross exposure,
daily loss, drawdown, turnover, session order counts, expiry and mark freshness.
Pending buys count toward exposure and turnover; pending sells never release buying
power early. The diversified exception requires an unleveraged ETF explicitly
classified as diversified with the diversified sector. A single-company ETF keeps
company/sector limits. Unknown sectors fail closed. `check_quote` implements age
and spread eligibility for future adapters; it does not enable quote fills.

Checks run again at the actual execution open, including actual-session turnover
and order count. Daily loss compares with the preceding carried equity when a new
session begins; drawdown uses the running observed equity peak. A threshold breach
persists a halt on buys. Reductions remain subject to cash, quantity, freshness,
expiry and activity checks; an existing exposure breach can be reduced without
requiring immediate full liquidation. Halts persist across a new adapter instance
and database backup/restore. `reset_halt` is a trusted runner/owner API requiring
the policy's kill-switch owner and a recorded approval reference, fresh reconciled
marks, and an explicit reset ID. The reset event records the previous loss anchors
and rebases monitoring to current equity; historical P&L remains intact. This is
an administrative API, not an authentication service or a model tool.

All effects and command results are appended transactionally to the existing
hash-chained `events` table as `kind="simulation"`. Payload version
`raw-next-open-ledger-v1` identifies the reducer and contains the portfolio ID,
effective UTC time and typed effect (`funding`, `order`, `fill`, `mark`,
`cancellation`, `dividend_ex`, `dividend_pay`, `split`, `halt`, `owner_reset`,
`rejection`, or `command`). Reservations are fields of admitted order events; fees
are fields of fill events, so neither can commit separately from its transaction.
The generic `ledger_event` record contract remains available for later interchange;
the operational reducer reads these versioned event envelopes directly. Order and
fill events retain decision/order/observation IDs, and the initialization command
pins policy, experiment, portfolio, session schedule and rounding assumptions.

Command identities deduplicate retries and reject changed inputs. Session and
instrument identify bar processing across revisions; revised bars cannot cause a
second fill. State is rebuilt from only this portfolio's streamed events, without
loading the book library or other portfolios. Cash, reservations, quantities and
equity reconcile after replay. Equity change equals realized gain plus unrealized
gain plus dividend income; fees are already included in basis/proceeds and are not
subtracted twice. SQLite transactions roll back interrupted partial fills.

## Evidence and remaining prerequisites

Final local validation: 97 tests across 11 modules passed in 6.4 seconds on Python
3.14.6/Windows; both the existing accepted contract bundle and new simulation bundle
validated, and `git diff --check` passed. CI retains Python 3.11/3.14 on Windows and
Ubuntu; those remote matrix results are separate from this local evidence.

Run `python scripts/check.py test_simulation test_risk test_storage` for focused
validation, or `python scripts/check.py` for the complete suite. The tests cover
hand-calculated buy/sell fees, adverse costs, split/dividend entitlement, restore,
rollback, gap/expiry/no-volume behavior, duplicate commands, policy injection,
self-promotion, live endpoint attempts, every implemented numeric control, unknown
sectors and stale marks. Paper-policy validation rejects each missing numeric
field and missing approval/ownership; nonfixture execution cannot use fixture policy.

`python scripts/build_simulation_fixtures.py` rebuilds four isolated, equally seeded
fixture portfolios and `examples/simulation/report.json`. Each starts at $10,000,
buys ten shares at $100.11 with a $1 fee, and closes at $102: cash $8,997.90,
holdings $1,020, equity $10,017.90. The checked-in policy approval is explicitly
fixture-only and all opinions are scripted arithmetic, not real trained opinions.

No remaining blocker for these bounded fixture tasks. Real learning for Value and
Trend remains partial; vendor/calendar qualification, complete owner-approved real
paper policy, readiness review, heartbeat orchestration and actual forward trials
remain their existing later tasks. No dependents, scheduled runs or paid model
calls were started.
