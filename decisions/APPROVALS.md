# Owner approvals

This register holds choices that materially affect product behavior, financial risk, legal exposure, or the meaning of an experiment.

## Standing Alpaca authorization — 2026-09-07

The owner explicitly pre-approved **any free use of the Alpaca account**, including
obtaining data and engaging in paper trades at the agent's discretion, particularly
within Alpaca's rate limits. This supersedes earlier per-sample/per-paper-action
permission gates in this register and active task briefs. Do not ask again for
the same authorization. Agents choose and document finite workloads and paper-risk
parameters appropriate to the task; keep shared quota enforcement and attribution.
This approval does not spend real capital or purchase paid plans/services, and does
not itself launch a paper strategy or create recurring work.

The owner also explicitly directs the project to assume private local storage,
reuse and experiments are permitted, citing Alpaca's personal-use Terms and the
owner's interpretation, unless decisive contrary evidence is found. The follow-up
[Step 09 rights decision](../docs/step-09-vendor-qualification.md) records the public
research/backtesting documentation supporting that interpretation. Record this as
an owner-approved operating interpretation, not a separately negotiated provider
licence. Do not repeatedly gate ordinary private local use on the same unresolved
general wording. Reopen the question only for material new evidence or expanded use.
Public redistribution and transfer of market data to external model services are
outside this private-local decision. No automatic data purge is authorized.

The Step 09 bounded historical SIP sample is covered now. Paper trading is likewise
owner-authorized; the roadmap's remaining implementation, readiness and quota
verification work describes engineering prerequisites, not another request for
owner permission. Paid subscriptions and live-capital actions remain separate.

**Owner decision recorded 2026-09-05:** the owner explicitly approved all recommended defaults in the original register, including the Lead Character default, and requested the additional research-system design and task backlog. Checked items below record that approval. Where the default was to defer a selection or require a later gate, the approved action is that deferral/gate—not an invented vendor, broker, budget, or live authorization. Items with no concrete recommended value remain open. See [ADR-001](records/ADR-001-research-observatory.md).

New numerical suggestions in the [architecture](../docs/architecture.md), discussion caps, and evaluation sample floors are proposals introduced after that approval. They are not silently included in it. Design and fixture implementation may proceed; actual paper trading requires the numeric policy and operating responsibilities below to be recorded.

## Product and capital policy

- [x] **Primary success metric.** Approved risk-adjusted, after-cost performance over a predeclared evaluation window as the primary objective, with profitable calendar months as a secondary consistency measure.
  - Recommended default: compare net return, maximum drawdown, and calibration against cash and a broad-market index over multiple regimes; never force a trade to satisfy a monthly target.
- [x] **Passive and active budgets.** Approved the default separation of protected long-term capital from the active experiment; no real-money amount selected.
  - Recommended default: keep protected long-term capital outside the active experiment; assign only a separately approved, loss-tolerant research budget to trading.
- [x] **Initial asset universe.** Approved the default instrument classes below; exact eligible symbols belong in each preregistered experiment.
  - Recommended default: liquid U.S.-listed equities and unleveraged ETFs only; no options, futures, crypto, shorting, margin, leveraged/inverse ETFs, penny stocks, or illiquid securities.
- [x] **Lead Character.** Approved Index Steward as the first council lead.
  - Recommended default: Index Steward is the initial capital-allocation lead; Systematic Trend Operator operates in shadow mode until it earns lead eligibility out of sample.

## Character design

- [x] **Pilot curricula.** Approved the proposed first three Characters and book order: Index Steward, Value Rationalist, and Systematic Trend Operator.
- [x] **Constitution changes.** Approved the versioned amendment/fork policy below.
  - Recommended default: append a versioned amendment with rationale and provenance; never overwrite history. A change to the first-book foundation creates a fork unless explicitly approved as an amendment.
- [x] **Leadership cadence.** Approved scheduled review and the evidence gate below; numeric minimum sample still belongs in the experiment policy.
  - Recommended default: scheduled quarterly review after a minimum sample and at least one predeclared out-of-sample window; no switching in reaction to a single recent win or loss.
- [x] **Merged Character experiment.** Approved the prerequisites below, not an immediate merge.
  - Recommended default: only after specialist baselines exist; pre-register curriculum order, memory access order, conflict rules, and weights.

## Data, books, and provenance

- [x] **Book acquisition and storage policy.** Approved the metadata/notes and private-source policy below; individual source permissions still require evidence.
  - Recommended default: store catalog metadata, page-level citations, original analysis, and short necessary quotations in the repository; keep licensed source files in access-controlled storage outside Git and respect license/copyright terms.
- [x] **External research policy.** Approved the source-quality and provenance policy below.
  - Recommended default: primary filings, exchange/broker specifications, official statistics, and peer-reviewed work outrank commentary; every derived claim retains provenance and retrieval time.
- [x] **Market-data vendor and license.** The original deferral below is superseded for Alpaca private delayed daily SIP by the [completed Step 09 decision](../docs/step-09-vendor-qualification.md). Broader requirements still need matching qualification.
  - Recommended default: postpone selection until schemas and evaluation needs are defined; require corporate actions, delistings, historical constituents, quotes, and publication timestamps where applicable.
- [x] **Alpaca account-backed sample.** On 2026-09-06 the owner supplied regenerated paper credentials and authorized a bounded read-only check. Authentication and a small delayed historical SIP daily-bar sample passed; no order was submitted and no credential or account identifier was retained. [ADR-003](records/ADR-003-alpaca-market-data-qualification.md) records the exact scope.
- [x] **Alpaca private data use and scoped selection.** The standing 2026-09-07 owner interpretation covers private local storage, replay, experiments and owner reporting. Step 09 selected Alpaca for the bounded delayed daily SIP scope after six successful metered requests. Public redistribution is outside this decision; successful access alone was not the rights basis.
- [ ] **Paid market-data subscription.** Authorize a specific plan and price before any purchase or paid SIP request. No subscription or spend is authorized by prior market-data deferral.

## Public-official analysis

- [x] **Subject scope.** Approved the default public-filer scope below.
  - Recommended default: begin with U.S. House and Senate members using official public records; do not infer protected traits or expand to private individuals.
- [x] **Product claim.** Approved describing this as delay-aware disclosure analysis rather than trade copying.
  - Recommended default: yes. Reports may appear weeks after execution, disclose value ranges rather than exact amounts, and may cover spouses or dependents; the system must represent those uncertainties.
- [x] **Ethics and reputational review.** Approved an explicit policy against harassment, unsupported allegations of misconduct, and claims that a disclosed trade proves motive or inside information.

## Execution and safety

- [x] **Broker and jurisdiction.** Approved deferring selection until paper-trading performance warrants integration, with current legal, tax, brokerage, and market-rule review for the owner's location and account type. No broker, account, or jurisdiction-specific execution setup has been selected.
- [x] **Live-capital gate.** Approved requiring a separate written decision before any real-money credential is created or any live order endpoint is enabled. No live capital is authorized.
  - Recommended default: historical replay and paper trading only until that approval.
- [x] **Human authorization model.** Approved the human-confirmation default below; no live pilot or automation is authorized by this entry.
  - Recommended default: human confirmation for a tiny-capital pilot; automation is a later, separate approval with independent kill switch and daily/position loss caps.
- [x] **Paper-risk policy authority.** The standing approval delegates selection of finite free-paper workloads and risk parameters to the agent. Record deployed paper capital, exposure, loss/drawdown, turnover, order-frequency and freshness settings before the run; no repeated owner confirmation is required. The [proposed pilot parameters](../docs/architecture.md#proposed-pilot-parameters) are a starting point, not measured performance. Live-capital limits remain unapproved.
- [x] **Free-account operator authority.** The owner authorizes agents to use the configured account for free data and paper activity. Document kill-switch, reconciliation and recovery responsibilities when implementing paper operation; protect credentials and retain owner control. This is an implementation duty, not a renewed permission gate.

## Additional owner-requested direction

- [x] **Finite Step 11 automation (2026-09-07).** The owner requested task briefs,
  roadmap updates, implementation of 11A/11B and pushing the finished work to
  online main. This authorizes the named Windows observation task at September 15,
  00:30 UTC with a 13:00 UTC fallback, plus a 17:00 UTC local deadline check, within
  the original 00:20:01–22:00 UTC window. Local failure warnings and zero-request
  scheduled rehearsal are included. These finite jobs run as the normal owner
  using interactive sign-in without stored Windows passwords. Existing budgets,
  inputs and stopping rules remain fixed. This supplements the standing exclusion
  of recurring work for this finite schedule only; it does not authorize weekly
  trials, new model spend, broker orders or general Step 15 recurrence.
- [x] **Private backup planning (2026-09-07).** Add Step 11C's backup/restore brief
  and connect it to Steps 12/15. The owner has a private server described as
  “lightrail” and proposed backups under the existing non-public-use interpretation.
  No exact endpoint/login, remote transfer or recurring backup configuration is
  established by this entry. Local restore design can precede server access.

- [x] Adopt the supplied five-paper Microstructure replacement sequence, retain the supplied Harris draft excerpts as the limited foundation, and use the two supplied OCR transcripts. No further material search is required for this revised plan. [ADR-002](records/ADR-002-microstructure-reading-scope.md) records exact order, scope and the distinction between material availability and completed learning.

- [x] Preserve the council and plan a separate mode where each Character controls a fictional portfolio.
- [x] Design inspectable discussion, learning, data acquisition, dashboards, and explicit historical-hindsight experiments without replacing the original boundaries.
- [x] Turn the adapted roadmap into implementation task files with model/effort recommendations and update the root README.
- [x] Publish this design and decision update to the online repository's `main` branch. This records authorization; completion is established by the resulting Git commit, not by this checkbox.

## Decisions the system must never make for the owner

Without explicit owner approval, no model or Character may:

- move from research to live capital;
- increase the approved budget, leverage, or loss limits;
- add a new asset class or jurisdiction;
- disable monitoring, reconciliation, or the kill switch;
- promote itself to lead or change its own evaluation criteria;
- treat target profit as guaranteed income.
