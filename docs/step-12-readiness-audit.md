# Step 12: reproduced readiness audit

**2026-09-15 — audit complete; paper stage held at forward shadow.** The original
Step 11 observation is valid within its narrow scope. Its **5 completed sessions
and 1 matured forecast** do not meet the retained **60-session/30-forecast** review
floors. Passing engineering checks is not evidence of profitable reasoning.
Step 13 remains blocked and was not started.

The [evidence verification](../examples/step-12/evidence-verification.json),
[validation results](../examples/step-12/validation.json) and
[policy decision](../examples/step-12/paper-policy-decision.json) make this decision
reviewable. The [original handoff](step-12-audit-handoff.md) remains the locator
for private source evidence; its September 15 scheduler snapshot is historical.

## Reproduced evidence

The completion launcher returned `already_complete` on September 15 at 10:07 UTC,
without a collector. The separate audit traps Python socket connections and opens
SQLite read-only. It instantiates no account coordinator, provider or model client.
It verifies the pinned completion report rather than trusting a movable pointer.

| Check | Reproduced result |
| --- | --- |
| Frozen trial, runtime, qualifications and learning ancestry | Original manifest and all frozen input checks pass |
| Database integrity, v1/v2 chains and references | 248 v2 records; unchanged before/after audit |
| Production accounting replay | All 35 stored results: cash, reserves, available funds, funding/flows, FIFO basis, realized result, income, fees, receivables, expenses, equity, unrealized result, P/L, TWR, drawdown, halt and valuation history |
| Scientific history retention | All 7 immutable reports hash correctly and every embedded performance record equals its stored original |
| Observation | 5 real sessions, 1 matured forecast, no immature/unscorable forecasts or source gaps |
| Original operational receipt | Successful observation, zero unfinished predecessors; no unfinished launcher runs found during audit |
| Opinions | 3 independent opinions and 1 subsequent council opinion; one shared snapshot; pinned requests/ancestry and bounded advice |
| Baselines | All 4 strategy portfolios match their separately funded simulated market control; cash is explicitly zero-interest |
| Underlying evidence | Saved decision download equals sealed snapshot; original outcome queries, observation hashes, session membership and receipt clocks reproduce settlement and forecast score |
| Request budgets | 3 trial attempts of 12 permitted; each of 3 fixed jobs used 1 of 4. Account total 11 includes earlier workloads |
| Audit activity | Zero account/provider/model calls and zero broker orders |

The audit checks the durable request journal against its **logical clock** bounds;
those values are not UTC transport timestamps. Calendar/receipt clocks establish
prospective ordering separately. Step 09's independently measured six sends per
rolling minute, no throttles and complete coverage remain the limited real
headroom sample. Step 11 added two action-qualification requests, one initial
download and two outcome downloads. No account capacity/load-test claim follows.
The coordinator retains its 180/minute operating ceiling and 200/minute hard
ceiling; unknown outside callers remain outside its guarantee.

## Adversarial and engineering review

The full regression suite and independent Step 08 preflight were rerun. Synthetic
tests establish specific controls; they do not count toward forward sample floors.
The base environment discovered 401 tests across 40 modules; 394 passed and 7
optional recovery cases skipped. The dedicated recovery environment then passed
all 19 cases in its two modules, including all skipped cases, with the recorded
age binary hash. Thus all 401 distinct tests are covered. This uses local synthetic
encryption/receiver tests, not a fresh remote transfer or physical-key ceremony.

| Requirement | Reproduction and scope |
| --- | --- |
| Golden accounting, costs and corporate actions | `test_accounting_v2`: production persisted FIFO/TWR compared to the independent META-001 golden values; stale marks yield null valuations, contributions/withdrawals do not manufacture return, splits and dividend receivables/payments preserve economics, costs count once |
| Preserved migrations | `test_storage_v2`: unchanged v1 tables/hash history, preview/apply/rollback, repeat migration, crash recovery, average-cost legacy preservation and explicit conversion gaps |
| Publication lag and revisions | `test_ingest`, `test_forward_shadow`, `test_evaluation`: publication/receipt cutoffs, unavailable or superseded data, missing sessions and late forecast receipts. These are synthetic timestamp/revision cases; no real disclosure adapter is qualified |
| Splits across a forecast | New `test_readiness_audit`: a post-entry split makes the raw-close forecast unscorable and prevents completion; existing tests cover fractional settlement, pending orders and action gaps |
| Injected instructions | New rehashed request containing a broker tool and instruction to read credentials is rejected by the sealed request validator. Existing tool/roster/future-evidence tests pass. This is a tools-free deterministic runtime, not an LLM prompt-injection certification |
| Repeated work and failure | `test_prospective_trial`, `test_heartbeat`, `test_observation_job`, `test_private_backup`: repeat runs do not repeat decisions, fills or requests; deadlines cannot backfill a trial; interrupted/overlapping processes preserve receipts and charges |
| Shared requests | All 14 independent `test_request_preflight` cases pass: actual mock-transport dispatch traces, clock jumps, killed processes, cooldown/429 formats, ambiguous attempts, cache/resume binding and equal snapshots |
| Hard limits and stale quotes | `test_risk`, `test_accounting_v2`: exposure/cash/turnover/frequency, pending reservations, age/spread, loss/drawdown and durable halts. The present shadow policy is not the future paper policy |
| Attribution and execution basis | `test_broker_v2`, `test_storage_v2`, `test_export_v2`: Monarchy-only opaque mapping, atomic outbox, partial fill/cancel/reconciliation and matched simulated control; cross-basis comparisons rejected. Broker transport remains unimplemented |
| All trials and uncertainty | `test_evaluation`: failed/repeated/immature/hindsight runs remain visible and cannot promote; zero trades is a valid result, missing observations are not zero risk |
| Privacy and local server | `test_export`, `test_export_v2`, `test_local_server`: fixture-only public export, no private-source relabeling, allowlisted fields/assets, secret rejection, host/origin/traversal/symlink/hardlink/binding checks, atomic bundle publication and conservative retention |
| Install and schema classifications | Clean offline wheel install and private workflow checks; 1,983 declared fields classified, unknown fields denied |

The new replay checks deliberately bypass `evaluate()`'s saved-result cache.
Returning a cached report would only prove equality to itself. The existing backup
verifier already recalculates six accounting scalars; Step 12 additionally checks
returns, drawdowns, receivables and valuation history directly from ledger state.
New adversarial tests reject rehashed false metrics, source lists and halt/history
changes. This closes an audit-coverage gap without rewriting historical results.
The command also replaces a stale successful output with a sanitized failure
when the original installation cannot be located; that failure path is tested.

## Rights, source quality and privacy

The September 7 standing owner decision still covers free Alpaca private local
storage/replay and paper activity. The September 15 review of Alpaca's
[Terms](https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf)
retains personal/noncommercial use and restrictions on publication/distribution;
no decisive new conflict with the recorded private-use interpretation was found.
That is an operating interpretation, not a negotiated licence. Public redistribution
and external-model transmission of market data remain outside it.

The [current FAQ](https://docs.alpaca.markets/us/docs/market-data-faq) still distinguishes
delayed historical SIP from subscription-dependent recent/latest SIP. Keep the
20-minute margin and explicit feed; successful access alone does not qualify quotes.
The [corporate-actions endpoint](https://docs.alpaca.markets/us/reference/corporateactions-1)
and existing qualification establish scoped receipts, not proof that no later
announcement/revision exists. Total-return vintages remain provisional.

Only counts, hashes, operational times, policy and original analysis are published.
Raw bars, action rates, holdings, returns, account identity and credentials remain
private. The three first-book learning versions retain source hashes and original
contamination labels. The remaining curricula and theory evaluation are unfinished.

## Decisions, defects and remaining blockers

| ID | Finding and disposition | Responsible next work |
| --- | --- | --- |
| S12-01 | **Blocking evidence:** 5/60 sessions and 1/30 forecasts; one fixed variant and one uncalibrated control forecast cannot establish edge, calibration or regime robustness | A separately preregistered finite forward programme, then a fresh readiness review; never extend or tune the completed trial retrospectively |
| S12-02 | **Policy distinction resolved:** frozen shadow policy uses 10% daily loss, 20% drawdown, 100% turnover, one initial order and a four-day outer mark-age bound. These were not the architecture's proposed 2%/10%/20% paper controls | Future paper implementation must instantiate and test the selected policy below; Step 11 files stay frozen |
| S12-03 | **Operational gap:** verified local/remote recovery evidence dates to September 7 and contains 177 records/9 attempts, versus 248/11 now. Observation-inclusive remote recovery is not established | Owner-controlled fresh private backup/restore; remote refresh uses attended FIDO PIN/touch. Do not activate the old restored quota owner or erase the 2 later spent attempts |
| S12-04 | **Execution limitation:** after-receipt daily-close research fills do not prove executable prices, intraday stops or broker fills. No qualified quote/order transport or separate Trading quota is implemented | Step 13 engineering only after its stage prerequisites; retain separate broker and simulated series |
| S12-05 | **Research uncertainty:** provisional action completeness, unsupported/ambiguous action ordering, no delisting/membership or intraday qualification, unknown full operating/authoring costs, incomplete curricula | Preserve nulls/gaps; qualify expanded scope explicitly. No inferred profitability or advice benefit |
| S12-06 | **Audit coverage repaired:** prior completion verification replayed six ledger scalars; hash equality alone did not recalculate return/history fields | Expanded read-only replay and adversarial metric/request tests added |
| S12-07 | **Documentation repaired:** active brief still requested another owner policy approval and contained pre-collection wording | Standing delegated authority recorded; current queue and Step 13 blocker made explicit |
| S12-08 | **Storage defect fixed:** an exception in connection setup occurred before the cleanup handler, leaving SQLite open while its traceback survived. A deterministic failure-injection test failed for all three setup pragmas before the fix, then passed with explicit closure and unchanged persisted records | Setup now closes its connection before propagating the original error; no automatic retries or account-state resets were added |
| S12-09 | **Residual Windows recovery uncertainty:** one full-suite run hit `disk I/O error` opening WAL immediately after killing a synthetic worker, then a locked-file cleanup error. The focused rerun passed. The handle leak above is reproducible; the underlying transient I/O cause is not established | Preserve failed-run evidence; deployment recovery still requires receipt/lock/database checks. A passing rerun does not prove every Windows termination timing is reliable |

The storage startup cleanup change leaves the explicit Step 11 runtime hash set,
manifest, scientific reports and accounting algorithms unchanged. `storage.py`
is a transitive dependency outside that original hash set; the new audit's broader
source inventory records its exact changed bytes. The original hash check is
therefore scoped provenance, not a claim to hash every dependency or Python itself.
Broader paper operation is not engineering-ready merely because its
individual offline components pass. In particular, a multi-session paper controller
must enforce loss checks on declared session boundaries and preserve halts across
restarts; the finite trial's one initial decision does not demonstrate that workflow.

## Selected paper policy and operational ownership

The agent selects the [documented numeric policy](../examples/step-12/paper-policy-decision.json)
under the existing owner delegation, with **stage held** and no deployment.
USD10,000 fictional cash per separate portfolio; VTI only; long/cash-only;
20% company, 40% sector, 100% diversified ETF/gross exposure ceilings; **2% daily
loss, 10% peak drawdown, 20% one-way session turnover and one new order/session**.
The one-order ceiling is more conservative than the earlier five-order proposal.
Buys reserve all costs and outstanding commitments. Reductions remain policy-checked;
halts do not invent liquidation prices and never auto-reset.

Use the latest completed exchange session, zero stale sessions, a four-day outer
mark-age limit for weekends/holidays and a 20-minute delayed-SIP margin. That
mark rule never substitutes for the separately selected **60-second executable
quote age and 10-basis-point spread ceiling**. Broker-paper use requires actual
quote qualification. Simulated costs remain 5 basis points slippage plus 1 basis
point half-spread, zero commission, explicit raw corporate actions and no double
charge of fund expenses. Unknown full operating costs remain unknown.

The owner retains kill-switch/reset, incident and recovery authority. An authorized
running agent checks policy/entry conditions, records receipts and reconciles each
session; discrepancies halt new risk and go to the owner. Preserve partial fills,
opaque submission identity and spent requests through recovery. No passive monitor
or recurring job is implied. Dates and finite data budgets must be separately frozen
before a new run. Clearing sample floors will still require a dependence-aware,
all-variant review rather than automatic promotion.

## Operations disposition

Both exact Step 11 tasks were idle and [disabled at 10:18 UTC](../examples/step-12/scheduler-disposition.json).
This retires redundant future starts after verified completion, before the
08:00/noon Chicago triggers; it does not claim those triggers executed or that
the 17:00 expiry had already elapsed. Task definitions and original receipts are
preserved. No running collector was terminated and no recurring job was added.

The [backup review](../examples/step-12/backup-review.json) reverified the original
local bundle against its published manifest hash, including offline accounting and
quota preservation. It contains 71 fewer v2 records and 2 fewer spent attempts than
the current store. This is a concrete recovery freshness gap, not observed data loss.
No new backup, remote contact, key ceremony or restored-account activation occurred.

## Reproduction and next handoff

From the existing checkout with access to its pinned private installation:

```powershell
.venv/Scripts/python.exe scripts/run_step_12_audit.py --output .local/step-12-recheck.json
.venv/Scripts/python.exe scripts/check.py test_readiness_audit test_accounting_v2 test_storage_v2 test_prospective_trial
.venv/Scripts/python.exe scripts/run_step_08_preflight.py --output .local/step-12-preflight-recheck.json
.venv/Scripts/python.exe scripts/export_field_classification.py --check
.venv/Scripts/python.exe scripts/check.py
.venv/Scripts/python.exe scripts/check_installed.py --wheelhouse .local/wheelhouse
```

Use the handoff's resolved `local_app_data`; a missing installation is a blocker,
not a reason to initialize a replacement store. The audit accepts an explicit
`--local-app-data` and fails closed, replacing its output with a sanitized failure
if verification fails. Exit zero means saved evidence verified, **not promotion**.
The output pins code/test byte hashes. Reports and requests remain unchanged.

Step 13 is the next dependent stage, blocked by the decision above. Independent
Step 14 work may be considered under the queue's blocker rule if its own inputs
are met. This task starts neither. Preserve the completed five-session trial and
use this report, policy decision, validation artifact and scheduler disposition
for continuation without conversation history.
