# Owner approvals

This register holds choices that materially affect product behavior, financial risk, legal exposure, or the meaning of an experiment. Recommended defaults are supplied so development can stay concrete, but no unchecked item is approved merely because it appears here.

## Product and capital policy

- [ ] **Primary success metric.** Approve risk-adjusted, after-cost performance over a predeclared evaluation window as the primary objective, with profitable calendar months as a secondary consistency measure.
  - Recommended default: compare net return, maximum drawdown, and calibration against cash and a broad-market index over multiple regimes; never force a trade to satisfy a monthly target.
- [ ] **Passive and active budgets.** Decide whether long-horizon index investing is external household finance or an explicit portfolio sleeve in the future Trader User.
  - Recommended default: keep protected long-term capital outside the active experiment; assign only a separately approved, loss-tolerant research budget to trading.
- [ ] **Initial asset universe.** Select instruments the pilot may simulate.
  - Recommended default: liquid U.S.-listed equities and unleveraged ETFs only; no options, futures, crypto, shorting, margin, leveraged/inverse ETFs, penny stocks, or illiquid securities.
- [ ] **Lead Character.** Choose whether the Index Steward is the first lead or only a benchmark.
  - Recommended default: Index Steward is the initial capital-allocation lead; Systematic Trend Operator operates in shadow mode until it earns lead eligibility out of sample.

## Character design

- [ ] **Pilot curricula.** Approve the proposed first three Characters and book order: Index Steward, Value Rationalist, and Systematic Trend Operator.
- [ ] **Constitution changes.** Decide how a foundational belief may be amended.
  - Recommended default: append a versioned amendment with rationale and provenance; never overwrite history. A change to the first-book foundation creates a fork unless explicitly approved as an amendment.
- [ ] **Leadership cadence.** Approve how a shadow Character may become lead.
  - Recommended default: scheduled quarterly review after a minimum sample and at least one predeclared out-of-sample window; no switching in reaction to a single recent win or loss.
- [ ] **Merged Character experiment.** Decide when specialists may be combined.
  - Recommended default: only after specialist baselines exist; pre-register curriculum order, memory access order, conflict rules, and weights.

## Data, books, and provenance

- [ ] **Book acquisition and storage policy.** Approve how legally obtained books are made available to the system and what derived text may be retained.
  - Recommended default: store catalog metadata, page-level citations, original analysis, and short necessary quotations in the repository; keep licensed source files in access-controlled storage outside Git and respect license/copyright terms.
- [ ] **External research policy.** Decide which sources can update a Character and how source quality is ranked.
  - Recommended default: primary filings, exchange/broker specifications, official statistics, and peer-reviewed work outrank commentary; every derived claim retains provenance and retrieval time.
- [ ] **Market-data vendor and license.** Choose a point-in-time data source whose terms permit storage, replay, and the intended use.
  - Recommended default: postpone selection until schemas and evaluation needs are defined; require corporate actions, delistings, historical constituents, quotes, and publication timestamps where applicable.

## Public-official analysis

- [ ] **Subject scope.** Decide which public filers the Trader Analyzer may study.
  - Recommended default: begin with U.S. House and Senate members using official public records; do not infer protected traits or expand to private individuals.
- [ ] **Product claim.** Approve describing this as delay-aware disclosure analysis rather than trade copying.
  - Recommended default: yes. Reports may appear weeks after execution, disclose value ranges rather than exact amounts, and may cover spouses or dependents; the system must represent those uncertainties.
- [ ] **Ethics and reputational review.** Approve an explicit policy against harassment, unsupported allegations of misconduct, and claims that a disclosed trade proves motive or inside information.

## Execution and safety

- [ ] **Broker and jurisdiction.** Select these only after paper-trading performance warrants integration; obtain current legal, tax, brokerage, and market-rule review for the owner's location and account type.
- [ ] **Live-capital gate.** Approve a separate written decision before any real-money credential is created or any live order endpoint is enabled.
  - Recommended default: historical replay and paper trading only until that approval.
- [ ] **Human authorization model.** Decide whether every future live order requires confirmation or whether tightly bounded automation can eventually be approved.
  - Recommended default: human confirmation for a tiny-capital pilot; automation is a later, separate approval with independent kill switch and daily/position loss caps.
- [ ] **Risk limits.** Approve maximum deployed capital, position size, sector exposure, daily loss, total drawdown, turnover, order frequency, and stale-data thresholds before paper trading.
- [ ] **Secrets and operational ownership.** Choose who may access brokerage credentials, activate the kill switch, reconcile the ledger, and respond to incidents.

## Decisions the system must never make for the owner

Without explicit owner approval, no model or Character may:

- move from research to live capital;
- increase the approved budget, leverage, or loss limits;
- add a new asset class or jurisdiction;
- disable monitoring, reconciliation, or the kill switch;
- promote itself to lead or change its own evaluation criteria;
- treat target profit as guaranteed income.
