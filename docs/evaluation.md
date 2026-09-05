# Experiments, fictional money, and fair evidence

Status: evaluation specification. There are no trained Characters or performance results in this revision.

## Separate three information regimes

| Regime | Information access | Legitimate claim |
| --- | --- | --- |
| Historical replay with restricted retrieval | Only archived evidence publicly available by the simulated cutoff; current web disabled | Tests pipeline and qualified historical behavior; pretrained model contamination remains possible |
| Historical hindsight sandbox | Historical price progression plus current internet or current-trained memories | Exploratory demonstration of reasoning with hindsight; excluded from clean performance rankings and promotion |
| Forward shadow / paper | Current public information retrieved and committed before subsequently observed outcomes | Primary evidence for prospective decision quality, subject to simulation and sample limits |

Hiding current market data does not hide future facts in model weights, curricula, personal notes, repository files, or current web pages. Record model/version, declared knowledge limitations, source dates, curriculum/checkpoint cutoff, retrieval policy, and contamination flags. A prompt saying “pretend it is 2010” is not an information barrier. Do not label historical LLM trials leakage-free merely because retrieval is restricted.

Store `event_at`, `published_at`, `ingested_at`, revision and supersession timestamps. Forward runs need both publication and ingestion no later than the decision. Historical archived replay may use material imported today only when historical availability is evidenced independently; preserve today's actual ingestion timestamp and record the replay eligibility rule. Unknown publication time cannot be guessed from a transaction date. For restatements and corporate actions, preserve vintages rather than overwriting the past.

## Preregister each experiment

Freeze experiment mode, Characters and versions, input universe and historical membership, initial cash, baseline funds, decision cadence, sizing rules, costs, fill model, data feeds, corporate-action handling, information regime, trial variants, metrics, sample requirements, start/end dates, and policy approval. Preserve all trials, including failures. Development windows, validation windows, and the final holdout must be distinct; tuning after viewing holdout results creates a new development sample.

Compare council and individual sleeves using the same opportunity set and risk policy, while displaying their actual exposure and investment horizon. Compare no-advice versus bounded-advice as separate frozen variants. Deterministic baselines: zero-yield cash initially, clearly labeled; broad-market buy-and-hold with dividends and the same cost convention. Add a Treasury-like return only with an actual dated return series. Do not simulate interest by inventing a constant “risk-free” rate.

An independent virtual portfolio with its own holdings and costs is required to score rejected recommendations as an investable strategy. A single rejected trade's later price move is only a local counterfactual and cannot be added to a portfolio return. Advice contribution is estimated by matched ablations, with explicit uncertainty; avoid assigning causal credit from a flattering narrative.

## Accounting and execution

Use an append-only ledger with separate funding, orders, reservations, fills, cancellations, fees, distributions, splits, corrections, and marks. Never reset a losing portfolio in place; create a new experiment. Reconcile each snapshot to events. Reports distinguish realized gain, unrealized gain, cash income, and total equity change; these must not double-count one another.

Start with next-session daily-bar simulation. A decision based on a closing bar cannot fill at that same close. Use the next eligible session open plus an explicitly configured adverse cost assumption, and label it bar-based simulation. Missing or halted sessions leave the order pending until expiry; no guessed fill. Do not mix split-adjusted prices with unadjusted shares or credit dividends twice. Prevent negative cash, unsupported shorting, duplicate fills, and buys beyond reserved funds. Handle corporate actions before relying on historical total returns.

Daily bars cannot establish intraday liquidity, queue priority, or executable spreads. A more realistic quote/fill adapter, Microstructure Character, and appropriate data must precede serious intraday claims. Broker paper fills are another simulation with different assumptions; report them separately. Alpaca explicitly describes omissions including market impact, latency slippage, and queue position in its [paper-trading documentation](https://docs.alpaca.markets/us/docs/paper-trading).

## Metrics and null behavior

| Measure | Calculation / interpretation |
| --- | --- |
| Net return | Ending equity / starting equity − 1 when there are no external flows; use a declared flow-adjusted method otherwise |
| Maximum drawdown | Largest `1 − equity / running_peak_equity` on the declared mark schedule |
| Volatility | Standard deviation of periodic returns with stated frequency; annualize only with explicit convention and sufficient observations |
| Turnover | Sum of absolute traded notional / mean equity over the window; convention shown |
| Exposure | Gross holdings value / equity; separate company, sector, and cash allocation |
| Hit rate | Winning closed positions / eligible closed positions after costs; no closed positions → unavailable |
| Calibration | Brier score `mean((p − y)^2)` for preregistered binary events with matured outcomes; show event definition, horizon, sample and reliability bins |
| Tail loss | Worst session and loss quantiles with sample count; small samples cannot support a precise ruin probability |
| Participation | Trades, explicit abstentions by reason, missed deadlines, pending forecasts, eligible sessions |
| Operating cost | Model usage, retrieval/storage expense, and latency separately from trading costs; also show net experimental economics when costs are attributable |

Stale or missing marks make dependent metrics incomplete. No trades can still yield a valid cash-portfolio return; it cannot yield a hit rate. No matured forecasts means calibration is unavailable. Empty portfolios and untrained Characters must never appear as zero-risk winners.

## Evidence and promotion

Use evidence states: fixture, hindsight-contaminated, historical-qualified, forward-insufficient, and forward-reviewed. Suggested first review floor is 60 forward market sessions and 30 matured preregistered forecasts, plus the completed declared window; these are research proposals, not statistical proof or automatic eligibility. Long-horizon Characters may need much longer. Report uncertainty using methods appropriate to dependence in returns, avoid treating correlated forecasts as independent, and disclose the number of tried variants.

Quarterly council leadership review remains the approved cadence. The reviewer checks after-cost relative performance, drawdown, calibration, data quality, rule breaches, horizon suitability, and regime coverage. A positive month or clearing the sample floor is insufficient. The owner authorizes promotion; policy cannot be rewritten by the contender. Paper-stage numeric policy and later live-capital decisions remain separately recorded in [approvals](../decisions/APPROVALS.md).

Every dashboard must answer all six README success questions from frozen records; see the exact [dashboard mapping](dashboard.md).
