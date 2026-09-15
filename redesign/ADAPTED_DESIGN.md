# Adapted design: close the learning loop without rebuilding the observatory

**Proposal, September 15, 2026. Written after [DESIGN.md](DESIGN.md).** This document preserves the existing research infrastructure and proposes a bounded route to the same first useful learning milestone. The current Step 12 decision and Step 13 hold remain active. Adopting this proposal would require an explicit recorded roadmap/policy revision; writing these documents does not perform that revision.

## 1. Recommendation

Build the learning laboratory as an extension of the existing observatory. Preserve the completed trials and learning checkpoints. Add a versioned, bounded working memory over those records, actual structured Character research calls, and an outcome-to-memory review loop.

Start with Index, Value, and Trend. Use one qualified evidence family, at most six active entity modules in total, a finite observation window, internal paper accounting, and a small manual review surface. Defer a new UI framework, autonomous tool building, broad disclosure ingestion, and broker integration until the first learning loop works.

This retains the fresh design's scientific requirements. It reduces the initial integration surface. It does not require rereading all three foundations or discarding the ledger, provenance, request budgets, or prior audit evidence.

## 2. A fair comparison of the two designs

Both approaches must reach the same **first engineering milestone**:

1. Three foundation-based Characters can make independently recorded, structured research responses from bounded, time-eligible packets.
2. At least one preregistered forecast family can be resolved by an explicit outcome rule, with benchmark and overlap metadata.
3. An outcome can produce a reviewed candidate memory patch with a reproducible parent/child lineage; a fresh process can load either version.
4. The parent and candidate can receive the same subsequent evidence under a fixed comparison allocation.
5. Recommendations can run through a bounded internal paper controller with matched controls, durable risk state, receipts, and recovery.
6. A finite study can collect observations and show due dates, missing evidence, and remaining work without all-day model use.

Fixture outcomes can prove this plumbing. One or several real forecast resolutions exercise it, but **demonstrating better reasoning is a later empirical milestone**. Waiting for real five-session or quarterly outcomes is not disguised as development time. A broker paper account, all seven trained Characters, complete curricula, broad disclosure coverage, and a redesigned dashboard are excluded from both first-milestone estimates.

### Development estimate

Assumption: one developer familiar with this Python repository, stable source/model access, the same limited first-milestone scope, and focused implementation plus verification. These are planning estimates, not measured delivery promises.

| Work package | Fresh construction, days | Adaptation, days | Why adaptation saves time |
| --- | ---: | ---: | --- |
| Contracts, durable records, source controls, and recovery | 6 | 2 | Existing hashes, source registry, persistence and recovery patterns |
| Bounded Character runtime and packet assembly | 4 | 3 | Existing model boundary, frozen ancestry and independent opinion records |
| Modular memory, patch review, and version comparison | 5 | 4 | New in both; current checkpoints supply the import baseline |
| Forecast resolution, paper controller, and finite runner | 6 | 3 | Existing evaluator, accounting, budgets and finite observation machinery |
| End-to-end verification and operator handoff | 5 | 2 | Existing fixtures, reference accounting and audit tools |
| **Central estimate** | **26** | **14** | **12 development days saved** |
| **Planning range** | **24–34** | **12–18** | Even 24 versus 18 leaves 6 development days |

That range targets a lead of at least one five-day development week. It is credible only with the exclusions above. If adapters reveal deeper storage or recovery changes, re-estimate rather than asserting the lead is guaranteed. At the end of the first two development days, compare actual integration findings with this budget. If adaptation is trending above 18 days, narrow optional presentation/ingestion work or reconsider the architecture; do not remove scientific or accounting checks to save the estimate.

The fresh design can later support more general research relationships and a broader interface. The adapted path should already be collecting bounded prospective evidence while that broader construction would still be underway. This is an opportunity, conditional on source qualification and elapsed-time dependencies.

## 3. Preserve, extend, defer

| Existing component | Treatment | Change required |
| --- | --- | --- |
| Constitutions, curricula, reviewed source notes, learning checkpoints | Preserve exact historical artifacts | Add derived working-memory manifests that cite them |
| Ordered book-learning engine | Keep its current contract and tests | Send completed deltas into the new memory compiler; no silent alteration of prior sections |
| Theory cards and preregistrations | Reuse concepts and original records | Add rival predictions, mechanism outcomes, case selection and dependence metadata |
| Bounded model interface | Reuse reservations and completed-output reuse | Qualify a real reasoning route and record actual usage; conservative failure handling |
| Shared snapshots and independent opinion sequence | Reuse | New runtime version consumes selected memory modules; old `FoundationRules` remains an explicit control |
| v1/v2 history and reference accounting | Preserve | Add adapters for new research records; do not rewrite completed evidence |
| Market-data cache and shared quota ownership | Reuse the existing owner | Add only admitted requests; no second collector or recreated quota state |
| Evaluation, portfolio baselines, and private exports | Reuse | Separate forecast learning, paper utility, and uncertainty displays |
| Mailbox and finite heartbeat/job machinery | Reuse bounded interfaces | Add research-request leases, dirty-module work, and outcome deadlines |
| Backup/recovery and audit machinery | Extend | Include new records and the latest observations; rehearse restore before unattended use |
| Full notebook/dashboard redesign | Defer | Begin with a compact private report and current UI links |
| Broker paper transport | Optional later work | Internal simulation is sufficient for the first milestone |
| All-source Analyzer and remaining specialist curricula | Separate finite work items | Neither is implicitly completed by this adaptation |

Relevant implementations: [learning engine](../src/trade_theorist/learn/engine.py), [model boundary](../src/trade_theorist/learn/model.py), [prospective runtime](../src/trade_theorist/forward/prospective.py), [architecture](../docs/architecture.md), [accounting](../docs/step-02-accounting.md), and [finite operations](../docs/step-11-automation.md).

## 4. Minimal new components

The names below describe proposed modules and records; they do not claim that these files or schemas already exist.

### A. Working-memory compiler

Read current source checkpoints without changing them. Produce a small core, selected theory modules, and entity capsules. Every assertion has a source/checkpoint or outcome reference, a scope, and a status. Separate quoted-author claims from adopted Character beliefs.

Import the three current foundations once. Retain the 43/138/83 accepted-or-qualified claims and their rejected alternatives in the archive; the working view need not repeat all of them in every prompt. Test the compiler on scope, contradiction, invalid application, and evidence-retrieval questions before a Character uses it. A compact summary alone is not proof that it retained the book's reasoning.

New books still pass through ordered reading. Source learning produces deltas; the compiler assimilates affected deltas with the prior modules. It does not reread all previous books on each call. A request for deeper study can retrieve a cited passage when access permits.

### B. Research runtime

Add a distinct runtime identity rather than replacing `FoundationRules` in a sealed trial. Assemble constitution, selected modules, current permissible facts, open questions, and response contract inside a hard context budget. Record the exact packet and model/prompt version.

Require a claim under test, forecast or justified abstention, horizon, evidence references, strongest alternative, invalidation condition, and optional research request. Numerical data and order checks remain deterministic. A persuasive response cannot bypass a source or risk gate.

Use a reviewed-response import path first if needed to exercise contracts. Label it manual authoring with unknown authoring cost; do not call it automatic or cost-free. Routine model-driven observation additionally requires a qualified model route and accurate usage reservations.

### C. Outcome learner

Link each matured forecast to its original mind and packet. Apply its frozen resolution contract before asking for interpretation. A proposal can add, qualify, weaken, split, retire, link, or make no change. Preserve the failed original forecast and any disagreement about attribution.

A bounded critic inspects the proposed patch against the source and strongest counterevidence. Structural checks reject unsupported references, future information, missing qualifiers, oversized modules, and changes to protected owner policy. Save a candidate version and test it against its predecessor on later common packets. One winning comparison is not a promotion rule.

### D. Bounded entity and request records

Begin with a maximum of six active entity capsules across three Characters, with no requirement that every slot be filled. Each has a fixed size ceiling, last-updated time, review trigger, shared fact references, Character-specific interpretation, and an expiring watch lease.

A Character can request a defined observation using an approved template, such as a future issuer filing or a permitted market window. It must explain which theory and rival prediction the evidence could distinguish. The policy service deduplicates shared factual work, applies existing source budgets, and returns an explicit decision. Deferred work remains visible. General tool creation and automatic paid-source acquisition are outside this slice.

### E. Private research companion store

Prefer an append-only research companion store for initial new mind, experiment, patch, and request records. It references existing evidence by ID plus content hash, avoiding immediate changes to the historical v1/v2 record contracts. This is a proposed architecture choice to confirm during the first two days.

There is still one market/account request owner. The companion store must not own separate provider quotas. Cross-store references are not atomic by magic: write source evidence durably first, then append an idempotent research receipt referencing its hash. Pending links cannot enter a decision packet until verified. Crash recovery resumes from stable IDs and never fabricates a missing source record.

Use the existing accounting store for its supported portfolio contracts through an explicit adapter. If this cannot represent a new runtime without changing old assumptions, add a versioned migration or separate new-run database with a documented shared request-owner interface; do not stretch an old schema silently. The old store and trial remain readable. Recovery bundles cover the stores together, their references, and all spent budgets.

## 5. Data and model-processing prerequisites

Current approval covers free Alpaca data/paper use and specified private research. It does **not** automatically establish permission to send licensed market observations to an external model or to publish derived memories. Source processing and destination rules must be recorded before packets are routed.

For each source, qualify access, storage, extraction, model processing, retention, and public export separately. A summary derived from restricted observations is not automatically unrestricted. If hosted processing is unavailable, use an approved local route or a packet whose inputs are independently permitted. Removing a ticker or reducing precision does not by itself settle permission.

The first slice can use a qualified official filing/fundamentals family while deterministic scripts retain private market processing, if the resulting packet is permitted. Value can investigate business premises while other Characters supply their own conditional questions or abstain. This does not make that one family sufficient to validate every school. Broader Trend and disclosure-attention experiments require their own source coverage.

Congressional reports have specific use restrictions; keep their qualification separate from SEC filings. The [fresh design's disclosure section](DESIGN.md#10-public-disclosures-as-evidence) supplies official sources, lag distinctions, cohort construction, and the need for an independently qualified attention measure. No real disclosure connector or roster is implemented by this proposal.

## 6. Make the missing evidence programme explicit

I recommend adopting the following side-steps. Their proposed IDs associate them with the blocked Step 13 rather than hiding essential work after it. The task queue and policy would be updated together only when this redesign is selected.

| Proposed side-step | Concrete action and exit evidence | Dependency / responsible role |
| --- | --- | --- |
| 13A: scope and gate revision | Record the selected design, study question, source/model rights, budget, and distinction between research operation and maturity. Reconcile the existing 60/30 policy explicitly | Owner selects direction; implementer records policy consistent with standing authority |
| 13B: recovery and runner readiness | Fresh observation-inclusive backup/restore; resolve or contain Windows crash/restart uncertainty; verify session-aware risk checks and durable halt state | Implementer/operator; required before new operational study |
| 13C: working memories and runtime | Import foundations, verify compact memory, qualify structured model calls and source routing, preserve frozen rules control | Implementer; 13A permissions; can develop offline alongside 13B |
| 13D: learning protocol | Freeze test family, selection/overlap groups, primary outcomes, corrections, memory patch/review rules, parent comparison and scoring | Research implementer; 13C; fixture results prove mechanics |
| 13E: finite observation lease | Register start/end dates, exchange sessions, forecast due dates, quotas, model ceilings, operator, missed-run response, and deadline review | Operator; 13A–13D; one explicit finite run |
| 13F: collection and resolution | Run scripted intake; admit bounded research calls; resolve due forecasts; update coverage and backlog; repair gaps or mark unresolved | Operator; 13E; elapsed market/filing time is an explicit dependency |
| 13G: consolidation and comparison | Review matured outcomes, write candidate modules, run future parent/candidate comparisons inside the budget, inspect compression losses | Research reviewer; first eligible outcomes from 13F; continues during the lease |
| 13H: maturity review / next lease | Assess evidence by theory and episode, uncertainty and all variants; approve or decline a bounded next phase, naming remaining blockers | Reviewer/operator; end or stop trigger of 13E; no automatic continuation |
| 13P: optional broker paper adapter | Implement and qualify order identity, quote timing, partial fills, reconciliation, cancellation and separate Trading quotas | Implementer; paper engineering gates; not a prerequisite for internal learning |

The operator is the owner or an explicitly authorized running agent/service. A prose task is not a scheduler. A finite job needs an installed runner and a machine available at its declared times. General recurrence remains a separate Step 15 scope.

### Two explicit choices for the 60/30 hold

**Recommended proposal:** allow a finite internal paper research study after engineering/source readiness, while retaining maturity requirements for claims, role promotion, and expansion. Set study-specific evidence requirements; if 60/30 remains a useful review floor, describe what population and overlap policy it counts. It is not a universal proof of reasoning quality.

**If the existing policy is retained unchanged:** 13E–13G collect additional forward-shadow evidence, and paper operation waits. Register another finite programme without modifying the completed Step 11 manifest. The current arithmetic gap remains 55 sessions and 29 resolutions, but comparable populations and horizons must be defined before combining results. New learned-model forecasts cannot simply relabel fixed-rule observations as their own evidence.

Either choice gives the hold an actual unblocking path. Neither permits counting fixture results, retrospective forecasts, or duplicated windows as new prospective confirmations. Engineering work for independent prerequisites can continue while outcomes mature.

### What paper operation accomplishes

It tests how a recommendation becomes exposure and eventually an accounting result. The current Step 13 intends attributable internal Character portfolios plus a council portfolio, with an optional separate council/Monarchy broker series. Preserve that separation and its matched simulated control. Individual portfolios remain internal; do not issue individual broker client IDs.

Broker paper operation can be interesting during a long evidence campaign. It should follow verified transport/reconciliation engineering, and it adds execution evidence rather than accelerating quarterly fundamentals or supplying independent market regimes. Existing free-Alpaca authority need not be requested again for an already covered action; a precise finite run and required engineering still have to exist.

## 7. Routine usage and owner experience

Adopt the [fresh design's initial usage envelope](DESIGN.md#8-bounded-routine-operation): at most 15 daily research calls plus six weekly consolidation/review calls for three Characters in a five-session week, totaling at most 138,000 input and 24,000 output tokens under the stated accounting assumptions. These are proposed ceilings, not observed consumption.

New reading campaigns and parent comparisons need visible allocations. Fit comparisons by replacing ordinary research calls on selected days or by declaring a separately funded finite comparison batch. Do not quietly double usage by running every historical mind every day. Council synthesis likewise consumes a declared allocation.

A routine tick should:

1. Collect only newly due, permitted observations using existing caches and request controls.
2. Resolve due outcomes and mark affected memory modules dirty.
3. Select a bounded set of useful research questions; abstain or defer when context/data is insufficient.
4. Record recommendations and research requests, then apply paper policy if this study permits operation.
5. Consolidate only in the scheduled maintenance allocation.
6. Save receipts, remaining budget, unresolved work, and the next due time; then exit.

Most archive growth is handled by append-only storage and scripted indexes. Fixed context ceilings and active-watch limits keep routine AI input bounded as history grows. They do not promise constant total compute, instant archive searches, or unlimited coverage. Large incoming batches create a visible backlog.

The first report should answer in plain language:

- What does each Character currently believe, and which version acted?
- What changed, why, and what evidence argues against the change?
- What will test it next, and when can that outcome resolve?
- Which hypotheses or regimes still lack evidence?
- How much resource budget remains, and which requests are waiting?
- Did the paper controller operate correctly, separately from whether the theory was useful?

## 8. Verification and acceptance

Use focused tests for the new contracts and integration, then the repository's required regression workflow. The most important cases are behavioral, not tests that merely repeat the implementation:

| Concern | Required demonstration |
| --- | --- |
| Historical integrity | Existing checkpoints, completed trial manifest, accounting outputs and reports retain their original hashes |
| Compact memory | A source-grounded probe still recovers a critical qualifier, contradiction, and failure case after compression |
| Time leakage | A later filing amendment or outcome cannot enter an earlier packet; retrospective imports retain their label |
| Honest learning | Failed forecasts remain failed; a new exception is a candidate hypothesis; parent/candidate scoring uses later common evidence |
| Independence | Initial opinions precede peer advice; common-event and overlap groups survive reports |
| Resource control | Large archive with fixed active workload fits the same model envelope; backlog and deferred questions are explicit |
| Requests | Duplicate watch requests share intake; expired leases stop new work; unpermitted destinations are rejected |
| Recovery | Crash between stores leaves a recoverable pending reference; no duplicate request, model charge assumption, or order follows restart |
| Source withdrawal | Derived modules are marked affected; an old mind cannot reactivate quarantined evidence silently |
| Paper operation | Session loss/freshness checks and halts persist across restart; controls use matching opportunities and fill assumptions |

Acceptance of the first milestone means the loop functions and is inspectable. It does not claim statistical maturity, causal identification, or a profitable system.

## 9. Later bounded extensions

Attach each extension to its own dependency and exit condition:

- **Reading campaigns:** one next curriculum source per Character per finite run, with exact scope and memory probes. Give full Event and Mean-Reversion learning explicit tasks; current source planning does not train them.
- **13D-disclosure:** qualify one disclosure family, freeze a cohort and controls, verify timestamps/identity/amendments, then run a new prospective test. Congressional use and attention measurements are named dependencies.
- **13P-broker:** add the optional paper adapter after internal operation and recovery are sound. Keep real and simulated fill evidence separate.
- **14-memory view:** extend the research notebook to show belief patches, versions, unresolved questions, and outcome links; avoid a new frontend for its own sake.
- **15-finite renewal:** automate approved bounded leases with expiry, missed-run handling, and quiet unchanged ticks. No endless automatic continuation based only on "still need more data."
- **16-specialists:** train and evaluate additional Characters before treating their advice as learned expertise.

## 10. Decision summary

Choose the adaptation if the priority is to start studying and testing real Character reasoning sooner while preserving the work already done. Choose the fresh design if replacing the architecture itself is worth delaying the first working learning loop.

My recommendation is the adaptation, with the fresh design as its destination rather than a requirement to rebuild everything first. The first decision is about the research loop and gate structure. Paper trading is a useful companion; memory learning and fair prospective tests are the essential work.
