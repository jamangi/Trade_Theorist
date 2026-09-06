# Trade Theorist

Trade Theorist is the research and reasoning component of a future decision-support system for trading. It creates versioned **Characters**: distinct investment minds formed by reading deliberately ordered curricula, distilling their reasoning, testing their theories, and recording how their decisions perform over time.

The premise is that reading order matters. A first book supplies a Character's foundational instincts; later books are interpreted through that foundation, either extending it, qualifying it, or creating explicit tension. Two Characters can therefore read some of the same material and still arrive at different conclusions.

This repository currently covers **Trade Theorist only**. It does not yet place trades, connect to a brokerage, or promise profitable results.

## Start here: the research observatory

**Current status (2026-09-06): tasks 001–013 implement the offline research observatory; tasks 014–015 add a conditional Alpaca adapter and prospective evidence controls.** Contracts, persistence, ordered learning, independent opinions, permitted ingestion, isolated simulation, risk controls, bounded council mail, resumable heartbeat, ledger-based evaluation and a read-only dashboard are implemented. A bounded read-only check authenticated to the paper account and returned delayed historical SIP daily bars for VTI, SPY and QQQ; current/latest SIP was not entitled. Run the [one-command offline demo](docs/quickstart.md) after setup. The [current inventory](library/catalog/INVENTORY_REPORT.md) covers all seven Characters. Index Steward's Bogle foundation is complete. Value Rationalist and Systematic Trend Operator each have one real, cited opening checkpoint, but neither has completed its first book or may issue real recommendations. Synthetic fixtures demonstrate both portfolio modes and evidence handling without claiming an edge. Production vendor selection and real forward observations remain blocked by shared request controls, license evidence, eligible Character versions and real elapsed sessions. No subscription, order or forward performance is claimed. The owner has approved the original recommended defaults, including Index Steward as initial council lead.

See [Index Steward's completed reading](docs/index-steward-foundation.md), the partial [Value](characters/value_rationalist/README.md) and [Trend](characters/systematic_trend_operator/README.md) Characters, the [tasks 009–010 implementation record](docs/task-009-010-implementation.md), and the [vendor/forward control record](docs/task-014-015-implementation.md). Source PDFs stay local; public artifacts contain metadata, original analysis and citation hashes. The separate fixture paths use only original synthetic data and saved opinions.

Two dashboard tabs share one research engine: **Council**, where a chosen lead decides with shadow advice, and **Character portfolios**, where each ready Character controls a separate fictional budget. Being a lead in a personal research portfolio does not grant council leadership. Neither mode requires a Character to trade when its best decision is to wait. See [tasks 011–013 and validation](docs/task-011-013-implementation.md) for evaluation, dashboard and operating-interface details.

| Read this | What you will find |
| --- | --- |
| [Systems model](docs/systems-model.md) | Meadows-style stocks, flows, feedback loops, delays, measures, and ways to refine the initial design |
| [Architecture](docs/architecture.md) | Two portfolio modes, shared data, independent risk controls, storage contracts, and the heartbeat sequence |
| [Discussion and Character life](docs/discussion.md) | Bounded mailbox conversations, readable exports, belief timelines, decision postcards, and a research notebook |
| [Data and learning](docs/data-and-learning.md) | Cheap scripted ingestion, provider qualification, dated book-access checks, and ordered learning |
| [Shared market-data request budget](docs/market-data-request-budget.md) | Required Task 14 follow-up: cache reuse, shared 200/min maximum with initial 180/min operating ceiling, and Task 16 preflight |
| [META-001 impact](docs/meta-001-impact.md) / [performance v2](docs/portfolio-performance-v2.md) / [rights matrix](docs/data-rights-matrix.md) | Completed architecture review, tested reference accounting and pending runtime repairs |
| [Evaluation](docs/evaluation.md) | Fictional-money accounting, fair baselines, historical contamination, and forward paper evidence |
| [Dashboard design](docs/dashboard.md) | At-a-glance performance and expandable answers to every success question below |
| [Operating design](docs/operations.md) | Future setup, no-account demo, manual heartbeats, recovery, and usage controls |
| [Implementation tasks](tasks/README.md) | 18 ordered remaining-work steps, with a crosswalk to 25 historical task IDs with Sol/Astra guidance, acceptance criteria, and roadmap mapping |
| [Approved defaults](decisions/APPROVALS.md) / [architecture decision](decisions/records/ADR-001-research-observatory.md) | What is approved, what remains deferred, and which new parameters are still proposals |

[META-001 is complete](docs/meta-001-impact.md). It adopts a private Individual/Monarchy UI, versioned accounting and opaque Monarchy-only broker attribution. The legacy exporter refuses nonfixture data. [Step 01: contracts and storage](tasks/active/STEP-01-contracts.md) and [Step 02: accounting](tasks/active/STEP-02-accounting.md) are implemented and verified: explicit v2 persistence, a checked synthetic migration, production FIFO/flow-adjusted returns and offline broker reconciliation preserve v1 results. See the [accounting guide and evidence](docs/step-02-accounting.md). [Step 03: private dashboard](docs/step-03-private-dashboard.md) now adds the verified Individual/Monarchy views, with a distinct private read model and preserved fixture UI. [Step 04: private commands](docs/step-04-commands.md) now adds explicit v1/v2 selection, read-only diagnostics, resumable private evaluation/export and a clean offline installation check. [Step 05: protected local packaging](docs/step-05-local-package.md) now adds a validated bundle manifest, protected loopback launch/stop and conservative retention. The [numbered execution sequence](tasks/README.md) continues with Step 06 shared request coordination. Start from those repository guides in a fresh task; no conversation history is required. Steps 06–13 separately cover shared requests, offline forward integration, preflight, qualification, participant readiness, real observation, final audit and paper operation. Those later steps remain pending; [the crosswalk](tasks/CROSSWALK.md) preserves original task identities and completed v1 evidence.

Learning reaches microstructure/risk specialists in Step 16 (historical TASK-021), and completing each curriculum still requires additional ordered runs. See [training scope and continuation](docs/character-training.md). The first full observatory release remains a clearly labeled offline demonstration. Forward paper experiments require a licensed vendor, eligible Characters and stage gates.

> [!WARNING]
> Trading can lose some or all deployed capital, and leverage can produce losses beyond the initial investment. “Make a profit each month” is an aspiration to evaluate, not a guarantee or a safe optimization target. Early development should use historical replay and paper trading. Live execution belongs behind explicit approval, legal/compliance review, and hard risk controls.

## The future three-part system

| Component | Responsibility | Produces | Must not do |
| --- | --- | --- | --- |
| **Trade Theorist** | Learns schools of thought, constructs falsifiable theories, debates opportunities, and makes timestamped recommendations | Theses, confidence, invalidation conditions, proposed actions, and abstentions | Send brokerage orders |
| **Trader Analyzer** | Ingests public transaction disclosures and market context, estimates reporting delay, and tests explanations for observed trades | Delay-aware observations and candidate rationales | Treat a delayed disclosure as a real-time signal or claim to know a filer's intent |
| **Trader User** | Applies portfolio and risk policy, obtains fresh quotes, and eventually simulates or executes approved orders | Orders, fills, positions, and an immutable ledger | Bypass exposure, loss, liquidity, or authorization limits |

A shared evaluator should compare all three components and their combinations under the same budget, opportunity set, timestamps, fees, slippage, and risk limits.

```text
books + research ──> Trade Theorist ──> recommendations ──┐
                                                        ├─> risk gate ─> paper broker ─> ledger
public disclosures ─> Trader Analyzer ─> observations ──┘                    │
                                                                             v
                                              baselines + counterfactual evaluation
```

The boundary between recommendation and execution is intentional. A persuasive theory is not permission to risk capital.

## What a Character is

A Character is not a fictional writing style or a single prompt. It is a reproducible, inspectable state of mind with:

- a **constitution**: foundational beliefs, favored evidence, risk philosophy, time horizon, and known biases;
- an ordered **curriculum** with a reason for every book's position;
- **learning checkpoints** that preserve what the Character believed before and after each source;
- consolidated **memory** that a fresh task can load without rereading the whole library;
- a versioned collection of **theory cards**;
- an append-only record of forecasts, recommendations, abstentions, and outcomes;
- a scorecard that separates luck, process quality, and realized performance.

Characters may borrow techniques from other schools, but imports remain labeled with their origin. This protects useful specialization. A deliberately merged Character should be created as a separate experiment rather than silently averaging the specialists into one generic voice.

### Character governance

The approved initial council operating model is **one lead Character plus shadow advisers**:

1. The lead and advisers independently submit a recommendation, confidence, and strongest objection.
2. Bounded discussion exposes relevant evidence and disagreement; the lead then makes the final recommendation by the deadline.
3. A risk governor—policy, not personality—can veto any action that violates hard limits.
4. All recommendations are recorded, including those not selected, so counterfactual performance can be measured.
5. Lead status is earned on a rolling, out-of-sample scorecard and can change only at scheduled reviews, not after one lucky trade.

This retains the speed advantage of one decision-maker without discarding disagreement data.

The additional **Character portfolios** experiment gives each ready specialist separate fictional cash and the final recommendation for its own portfolio, under the same independent policy gate. It tests specialists with declared advice access without replacing the council. All Characters commit independent initial opinions before current-round peer discussion; mail is bounded and consensus is optional. See [the architecture](docs/architecture.md) and [discussion protocol](docs/discussion.md).

## The smallest useful theory

Each theory should be reducible to a short causal chain without becoming a slogan. A theory card contains:

```yaml
position: "What the Character believes"
minimal_logic_chain:
  - "premise or observation"
  - "causal step"
  - "testable implication"
scope: "assets, market regime, and time horizon"
assumptions: []
predicted_observables: []
portfolio_implication: "buy, sell, size, wait, or abstain"
invalidation_conditions: []
strongest_counterarguments: []
rebuttals: []
confidence: 0.0
evidence_and_citations: []
character_and_version: ""
created_at: ""
```

A rebuttal does not erase a counterargument. Both survive in the record. If a theory cannot state what would invalidate it, it is philosophy or narrative—not yet a trading theory.

## Sequential learning protocol

Book order is part of the experiment and must be preserved.

1. **Register the source.** Record edition, author, publication details, curriculum position, intended lesson, and permitted storage/use. Prefer citations and concise notes over storing copyrighted books.
2. **Freeze the prior.** Before reading, save the Character's current beliefs and its predictions about the source.
3. **Extract faithfully.** Capture the author's claims, evidence, assumptions, definitions, and limits before critiquing them.
4. **Assimilate through the Character.** State what the existing constitution accepts, rejects, or reinterprets—and why.
5. **Run an adversarial pass.** Test the new claims against contrary evidence, alternative schools, data leakage, transaction costs, and regime dependence.
6. **Write the memory delta.** Append the change; do not silently rewrite earlier beliefs. Contradictions remain visible.
7. **Promote only reusable knowledge.** Update consolidated memory and theory cards with provenance back to source and checkpoint.
8. **Pre-register tests.** Specify prediction, horizon, benchmark, failure condition, and evaluation window before seeing outcomes.

Fresh tasks load the Character's constitution first, then its consolidated memory, active theories, and recent evaluation summary. Other schools' memories are loaded afterward and labeled as outside views. This gives the Character a stable bias without hiding contrary evidence.

## Candidate schools of thought

The sequences below are proposed curricula, not endorsements of every claim in every book. The first title is intentionally formative; later titles operationalize, broaden, or challenge the resulting mindset.

### 1. The Index Steward — evidence-first passive allocation

**Core position:** Most active strategies fail to overcome costs and uncertainty consistently, so low-cost diversification is the default use of long-horizon capital. Active trading must earn the right to displace that default.

1. **The Little Book of Common Sense Investing — John C. Bogle.** Installs low cost, broad diversification, long horizons, and humility as the constitution.
2. **A Random Walk Down Wall Street — Burton G. Malkiel.** Adds efficient-market skepticism toward forecasts and popular trading systems.
3. **The Four Pillars of Investing — William J. Bernstein.** Broadens the model across theory, history, psychology, and the investment business.
4. **The Psychology of Money — Morgan Housel.** Makes endurance, behavior, and personal risk capacity part of portfolio design.

**Trading behavior:** Usually abstains. Acts as the benchmark and as a skeptical capital-allocation gate for every active Character. This school can run in the background without being mixed into the active trading budget.

### 2. The Value Rationalist — price versus business value

**Core position:** A security is a claim on an underlying business; opportunity appears when price diverges materially from conservatively estimated value.

1. **The Intelligent Investor — Benjamin Graham.** Establishes margin of safety, Mr. Market, and investor-versus-speculator discipline.
2. **The Essays of Warren Buffett — Warren E. Buffett, arranged by Lawrence A. Cunningham.** Extends value from cheap assets to business quality, management, and capital allocation.
3. **Common Stocks and Uncommon Profits — Philip A. Fisher.** Forces the Graham-trained Character to incorporate qualitative growth and competitive durability.
4. **Expectations Investing — Alfred Rappaport and Michael J. Mauboussin.** Converts valuation into a test of which future expectations are already embedded in price.

**Trading behavior:** Patient, selective, and generally poorly suited to forced daily action. Intraday dislocations matter only when they change the price/value gap enough to justify costs and risk.

### 3. The Systematic Trend Operator — follow, size, and exit

**Core position:** Persistent price movement can be traded without predicting fundamentals, provided losses are cut, positions are sized consistently, and rules are followed.

1. **Way of the Turtle — Curtis Faith.** Establishes explicit rules, breakout logic, position sizing, and disciplined execution.
2. **Following the Trend — Andreas F. Clenow.** Reframes the intuition as a portfolio-level, testable systematic process.
3. **Trading Systems and Methods — Perry J. Kaufman.** Expands the design vocabulary and exposes parameter and implementation choices.
4. **Evidence-Based Technical Analysis — David Aronson.** Challenges the now-formed trend believer to demand statistical evidence and control data-mining bias.

**Trading behavior:** Frequent abstention in directionless markets; enters only on defined signals and treats exit and sizing as part of the thesis.

### 4. The Mean-Reversion Experimentalist — extremes tend to normalize

**Core position:** Some short-horizon deviations from a conditional norm are temporary, but only after the norm, catalyst, execution cost, and failure regime are defined quantitatively.

1. **Quantitative Trading — Ernest P. Chan.** Establishes research workflow, backtesting, implementation realism, and accessible statistical arbitrage concepts.
2. **Algorithmic Trading — Ernest P. Chan.** Deepens mean-reversion and momentum strategy design with explicit rationales.
3. **Machine Trading — Ernest P. Chan.** Adds regime awareness, feature construction, and a more modern research loop.
4. **Advances in Financial Machine Learning — Marcos López de Prado.** Introduces stronger defenses against leakage, invalid cross-validation, and misleading backtests.

**Trading behavior:** Demands data, executable prices, and a pre-registered test. Suspicious of any edge that disappears after spread, slippage, latency, borrow, and taxes.

### 5. The Market Microstructure Mechanic — understand how orders become prices

**Core position:** At intraday horizons, market structure, liquidity, order types, queue position, and adverse selection can dominate the apparent investment thesis.

1. **Trading and Exchanges (draft) — Larry Harris.** Uses the supplied 113-page draft excerpts to form an initial map of participants, orders, markets and liquidity. Omitted material remains explicitly unknown.
2. **Algorithmic Trading and DMA — Barry Johnson.** Turns that map into execution mechanics, benchmarks and algorithm design. The supplied transcript provides text indexed to the scan's PDF pages.
3. **How markets slowly digest changes in supply and demand — Jean-Philippe Bouchaud, J. Doyne Farmer and Fabrizio Lillo.** Adds persistent order flow, liquidity, market impact and price formation.
4. **Limit Order Books — Martin D. Gould, Mason A. Porter, Stacy Williams, Mark McDonald, Daniel J. Fenn and Sam D. Howison.** Tests order-book models against empirical properties and known limitations.
5. **Market Microstructure Knowledge Needed for Controlling an Intra-Day Trading Process — Charles-Albert Lehalle.** Connects market design to scheduling, routing and execution constraints.
6. **Optimal split of orders across liquidity pools: a stochastic algorithm approach — Sophie Laruelle, Charles-Albert Lehalle and Gilles Pagès.** Examines allocation across venues and routing assumptions.
7. **Realtime market microstructure analysis: online Transaction Cost Analysis — Robert Azencott, Arjun Beri, Yutheeka Gadhyan, Nicolas Joseph, Charles-Albert Lehalle and Matthew Rowley.** Adds execution monitoring and diagnosis of underperforming orders.

This owner-approved sequence replaces the two unavailable later books with five supplied papers. It retains the limited Harris draft as its foundation. See [versions, file evidence and scope](docs/microstructure-alternatives.md); completion will describe this revised curriculum, not the two missing books or the complete published Harris text.

**Trading behavior:** May reject an otherwise sound trade because the expected edge is smaller than its execution cost or because liquidity makes the observed price misleading.

### 6. The Probabilistic Risk Skeptic — survive uncertainty first

**Core position:** Outcomes mix skill, luck, and hidden risk. Survival, calibrated uncertainty, and avoidance of ruin come before maximizing headline return.

1. **Fooled by Randomness — Nassim Nicholas Taleb.** Makes luck, survivorship bias, and asymmetric exposure the foundational suspicion.
2. **Against the Gods — Peter L. Bernstein.** Adds the history and conceptual machinery of probability and risk.
3. **Thinking in Bets — Annie Duke.** Separates decision quality from outcome quality and makes belief updating operational.
4. **The Most Important Thing — Howard Marks.** Applies second-level thinking, cycles, defensive investing, and risk control to markets.

**Trading behavior:** Sizes down, seeks convexity, records uncertainty, and vetoes strategies with hidden ruin paths. Best implemented partly as an independent risk governor so no alpha-seeking Character controls its own limits.

### 7. The Event and Disclosure Detective — infer, do not merely copy

**Core position:** Public events and filings can reveal incentives or changing expectations, but the tradeable object is the market's remaining mispricing after publication—not the stale action itself.

1. **You Can Be a Stock Market Genius — Joel Greenblatt.** Establishes event-driven curiosity around spinoffs, restructurings, mergers, and unusual situations.
2. **Quality of Earnings — Thornton L. O'glove.** Trains skepticism toward reported figures and teaches forensic reading.
3. **Expectations Investing — Alfred Rappaport and Michael J. Mauboussin.** Frames the question as what the current price already assumes.
4. **The Art of Execution — Lee Freeman-Shor.** Focuses attention on what investors do after an initial position, not just the entry story.

**Trading behavior:** Treats a political figure's disclosed transaction as delayed evidence. It reconstructs the information available at the original trade and at disclosure time, generates multiple rationales, and tests whether any edge remains.

## Recommended pilot Characters

Start with three specialists rather than seven:

| Role | Character | Why it belongs in the pilot |
| --- | --- | --- |
| Lead candidate / baseline | **Index Steward** | Establishes the opportunity cost of activity and prevents “doing something” from being mistaken for value |
| Contrarian fundamental adviser | **Value Rationalist** | Supplies business reasoning and a long-horizon alternative to price-only explanations |
| Active strategy candidate | **Systematic Trend Operator** | Produces explicit, testable rules and is structurally different from the first two |

Add the **Market Microstructure Mechanic** before any serious intraday simulation, then add the **Probabilistic Risk Skeptic** as an independent governor. The **Event and Disclosure Detective** belongs at the interface with Trader Analyzer once trustworthy disclosure ingestion exists.

The first merged Character should be created only after each specialist has a meaningful out-of-sample record. Its curriculum order, starting weights, and conflict rules must be pre-registered so the merge cannot be tuned to past winners.

## Evaluation strategy

Profit is necessary to call a trading system economically useful, but “green every calendar month” is a dangerous sole objective: it can reward leverage, hidden tail risk, and overtrading. Use a hierarchy:

1. **Hard constraints:** no unauthorized live orders; no breach of capital, drawdown, exposure, leverage, liquidity, or data-freshness limits.
2. **Primary research objective:** positive net performance over a predeclared out-of-sample window relative to appropriate baselines and risk taken.
3. **Secondary objective:** monthly consistency, measured alongside drawdown and probability of ruin—not optimized in isolation.

Every evaluation should include (and explicitly disclose unavailable inputs):

- an uninvested cash or Treasury-like baseline appropriate to the period;
- a low-cost broad-market buy-and-hold baseline;
- identical starting cash and capital availability;
- point-in-time data with no future or revised information leakage;
- fees, spread, slippage, market impact, borrow availability, dividends, and corporate actions;
- both selected and rejected recommendations;
- return, volatility, maximum drawdown, turnover, exposure, hit rate, calibration, and tail loss;
- enough trades and market regimes to distinguish a process from a lucky month.

For model-driven historical experiments, restricting retrieval cannot remove future knowledge already present in model weights or later curricula. Keep the requested **hindsight sandbox** separate from historical replay with restricted evidence and from forward shadow/paper records. Use forward decisions committed before their outcomes as the primary prospective evidence. See [information regimes and scoring](docs/evaluation.md).

For public-official disclosures, preserve at least three timestamps: **transaction date**, **filing/publication date**, and **system ingestion date**. House and Senate rules generally allow covered transactions over $1,000 to be reported by the earlier of 30 days after notice or 45 days after the transaction. Therefore, backtests may act no earlier than the historical public-availability timestamp. See the official [House Periodic Transaction Report calculator](https://ethics.house.gov/periodic-transaction-report-calculator/) and [Senate financial disclosure guidance](https://www.ethics.senate.gov/public/index.cfm/financialdisclosure).

## Safety and promotion gates

Development advances one reversible stage at a time:

```text
offline unit tests
  -> historical replay
  -> walk-forward simulation
  -> live-data shadow recommendations
  -> paper trading
  -> tiny-capital, human-approved pilot
  -> bounded automation (separate approval)
```

Promotion requires predefined evidence, reproducibility, and owner approval. A later stage must never weaken these invariants:

- secrets are kept out of the repository and logs;
- research tasks cannot call brokerage execution endpoints;
- the execution service accepts only schema-valid, policy-compliant orders;
- stale, missing, conflicting, or anomalous data causes abstention;
- an independent kill switch cancels new activity;
- the ledger is immutable and reconciled against the broker;
- model, prompt, Character, theory, data, and code versions accompany every decision;
- simulated and live results are never mixed.

Day-trading and margin rules are jurisdiction-, broker-, account-, and time-dependent. They must be checked again when a broker and account type are selected. Current U.S. background is available from the SEC's [Investor.gov margin-rules bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/margin).

## Repository map

The design documents and task backlog accompany the Python implementation in `src/trade_theorist/`, versioned schemas, three Character directories, fixture opinions, ingestion snapshots, simulation portfolios, deterministic risk controls, council mail and the heartbeat. See [tasks 007–008](docs/task-007-008-implementation.md) for accounting and execution, [tasks 009–010](docs/task-009-010-implementation.md) for deliberation and recovery, [tasks 011–013](docs/task-011-013-implementation.md) for evaluation and the local dashboard, and [focused development](docs/development.md) for quiet tests with saved failure logs. Original synthetic exports are generated locally. [META-001](docs/meta-001-impact.md) retires public Pages deployment and replaces task 018 with private local packaging; [START-HERE](tasks/meta-tasks/START-HERE.md) gives the repair order.

```text
Trade_Theorist/
├── README.md                       # Vision, research method, and architecture map
├── decisions/
│   ├── APPROVALS.md                # Choices reserved for the owner
│   └── records/                    # Accepted architecture and policy decisions
├── docs/
│   ├── systems-model.md            # Stocks, flows, feedback, measures, and refinement
│   ├── architecture.md             # Modes, contracts, storage, heartbeat, and risk policy
│   ├── discussion.md               # Mail protocol and observable Character life
│   ├── data-and-learning.md        # Acquisition, source rights, and learning workflow
│   ├── evaluation.md               # Metrics, baselines, and promotion criteria
│   ├── dashboard.md                # Two tabs and six expandable evidence answers
│   └── operations.md               # Setup, usage, recovery, and future command interface
├── tasks/                          # Dependency-ordered implementation tasks
│   └── meta-tasks/                   # Architecture audits, approvals, and next-task handoff
├── library/
│   ├── catalog/                    # Source metadata, rights, editions, and status
│   └── notes/                      # Citation-linked notes; not unlicensed book copies
├── characters/
│   └── <character_id>/
│       ├── constitution.md         # Stable identity and epistemic rules
│       ├── curriculum.yaml         # Ordered sources and intended transformations
│       ├── checkpoints/            # Append-only belief state after each source
│       ├── memory/                 # Consolidated memory for fresh tasks
│       ├── theories/               # Versioned theory cards
│       ├── evaluations/            # Character-specific scorecards
│       └── mail/                   # Generated readable views of immutable mail events
├── schemas/                        # Machine-validated source, theory, and decision formats
├── src/trade_theorist/
│   ├── ingest/                     # Source ingestion and provenance
│   ├── learn/                      # Sequential reading and memory consolidation
│   ├── theorize/                   # Theory generation and adversarial review
│   ├── council/                    # Implemented bounded event-backed deliberation
│   ├── heartbeat/                  # Implemented locks, phase recovery, and call reuse
│   ├── forward/                    # Prospective manifests and future-information gate
│   ├── adapters/alpaca_market_data/# Conditional feed-pinned market-data adapter
│   ├── adapters/trader_user_sim/   # Isolated simulated-execution contract
│   ├── evaluate/                   # Implemented replay and counterfactual scoring
│   └── export.py                   # Implemented allowlisted dashboard export
├── tests/                          # Unit, integration, leakage, and safety tests
└── runs/                           # Reproducible manifests; large outputs stay external
```

Future Trader Analyzer and Trader User components should live in separate packages or repositories with explicit, versioned contracts. That separation reduces the chance that a research prompt can become an order by accident.

## Near-term roadmap

The original contract, library, learning, ingestion, simulation, risk, mail, heartbeat and fixture-demo work is retained. Its completion evidence and partial real-source status remain in the [historical index](tasks/LEGACY-INDEX.md).

1. **Steps 01–05:** version contracts and persistence, prove accounting, integrate the private UI and commands, then package the local observatory.
2. **Steps 06–08:** build shared request admission, connect forward snapshots, and pass offline adversarial preflight.
3. **Steps 09–13:** qualify permitted data, verify eligible Character versions, gather real prospective observations, audit readiness, and operate only the approved paper workflow.
4. **Steps 14–18:** add the notebook, optional scheduling, specialist/disclosure research, and an evidence-based governance review.

Each [active task](tasks/README.md) explains its place in this order and its actual entry conditions. Source rights, owner decisions and real elapsed time remain gates; independent fixture work may proceed under the queue's blocker rule. The [Definition of success](#definition-of-success) still maps to [six dashboard explanation panels](docs/dashboard.md).

## Definition of success

Trade Theorist succeeds when it can answer, reproducibly:

- What did each Character believe at the time?
- Which sources and reasoning steps produced that belief?
- What evidence would have changed its mind?
- What action—or abstention—did it recommend using only then-available information?
- How did that decision perform after realistic costs and against fair baselines?
- Is the apparent edge stable out of sample, or better explained by luck, leakage, or hidden risk?

The goal is not a chorus of confident personas. It is a small ecology of inspectable minds whose differences produce testable decisions—and a system disciplined enough to learn when none of them deserves the trade.
