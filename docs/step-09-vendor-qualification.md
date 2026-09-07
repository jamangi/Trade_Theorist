# Step 09: qualified private delayed daily SIP

Completed 2026-09-07 UTC. **Alpaca is selected for the declared private local
delayed daily-bars scope.** Six real requests produced two complete retrievals,
30/30 expected symbol/session pairs each, without retries, throttles, quarantine
or duplicate replay observations. Start with [the current decision](../examples/step-09/qualification.json)
and [allowlisted account evidence](../examples/step-09/account-sample.json).
The [earlier blocked review](../examples/step-09/qualification.blocked-review.json)
is historical; its owner-authorization/private-storage blockers are superseded.

## Standing authorization and rights interpretation

The owner explicitly pre-approves **any free Alpaca account use**, including data
retrieval and paper trades at the agent's discretion, particularly within rate
limits. [APPROVALS.md](../decisions/APPROVALS.md) is the durable authority. Do not
request the same authorization again. Choose finite workloads and paper-risk
settings; record them and preserve shared admission and attributable ledgers.

The owner also directs the project to assume private local storage, reuse and
experiments are permitted unless decisive contrary evidence appears. We adopt
that operating interpretation, supported by personal/noncommercial language in
the [Terms](https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf),
research databases/backtesting in Alpaca's [historical-data guide](https://alpaca.markets/learn/fetch-historical-data),
and repeatable research artifacts in its [agent-workflow announcement](https://alpaca.markets/blog/alpaca-launches-skills-library-for-ai-agents/).
No decisive contrary evidence for this private-local use was found.

The [source register](../examples/step-09/sources.json) preserves the customer
agreement's reproduction wording and the unavailable exchange PDFs. This is an
owner-approved interpretation, not a negotiated licence or provider ruling. The
same general ambiguity is no longer a blocker. Reopen only for material new
evidence or expanded use. Paid services, live capital, public redistribution and
external transmission of market data are outside this free/private-local decision.
No automatic purge was imposed; the old 30-day proposal was not a provider rule.

## Actual bounded sample

The [authorized protocol](../examples/step-09/sample-plan.json) keeps VTI as the
daily pilot; QQQ/SPY are qualification controls. It pins SIP, raw daily bars,
`asof=2026-09-04` and ten sessions from August 24 through September 4. The
[FAQ](https://docs.alpaca.markets/us/docs/market-data-faq) documents the 15-minute
historical restriction; we retain a 20-minute margin. No current-SIP subscription
was required or purchased.

| Measurement | Actual result |
| --- | --- |
| First retrieval | Five pages; committed one page, then resumed the same full query |
| Second retrieval | One page, later frozen freshness bound, same market scope |
| HTTP attempts | 6 of the chosen 12-attempt maximum; all HTTP 200 |
| Coverage | 30/30 pairs each; zero missing pairs or quarantined rows |
| Retries / throttles | 0 / 0 |
| Minimum observed send gap | 0.4825 seconds |
| Peak sends in rolling 60 seconds | 6, under the retained 180 operating / 200 hard limits |
| Exact-query cache checks | Zero additional requests |
| Immediate and restored-book replay | Zero duplicate additions and zero quarantine |
| Changed economic bars | 0; 30 later receipt/provenance records are counted separately |
| Rate headers | Limit 200; remaining 199 on all six responses; reset values in evidence |

This small workload does not establish maximum account capacity or control of
unknown outside callers. Remaining-header semantics are not established as
account-wide headroom; `verified_rate_headers` remains false. The coordinator
enforces its own conservative limits. Independent send timestamps come from
`http.client.send` immediately before socket sending; the hook records times only.
Transport diagnostics retain at most 200 timing/status/allowlisted-header entries.

Prices, raw responses, request tokens, normalized observations and detailed reports
stay outside Git. Published evidence was built from an explicit operational-field
allowlist; it contains no prices, credentials, account IDs or private locators.

## Reproduce and continue

Use `.venv/Scripts/python.exe` for `python` on Windows. These checks are offline:

```text
python scripts/check.py test_live_qualification test_ingest test_alpaca_adapter test_market_requests test_request_preflight
python scripts/export_field_classification.py --check
python scripts/check.py
python scripts/check_installed.py --wheelhouse .local/wheelhouse
```

The separate live command is `python scripts/qualify_step_09.py`. It reads only
paper key/secret/base-URL fields from ignored `.env`, uses the production transport
and coordinator, and prints counts/status only. The stable private root is
`%LOCALAPPDATA%/TradeTheorist/alpaca-market-data`; its `step-09` directory holds the
manifest, resume references, normalized records, diagnostics and detailed report.
The permanent registry binds `quota:alpaca-owner-market-data` to this root. Reuse
that owner for cooperating callers; never reset it to obtain a fresh allowance.

Both query budgets and the common ten-minute deadline are frozen. Rerunning uses
the same queries/cache; it does not extend an expired workload or create a new
trial. New windows need new recorded work within the same owner under standing
authorization. Preserve the committed dated evidence during later checks.

The rehearsal exposed duplicate revisions when an older saved receipt was replayed
after a newer one. `RevisionBook.append` now recognizes any previously seen exact
payload in that series. Receipt/provenance is part of identity, so a genuinely
later observation is retained even if its price repeats. The real sample verified
replay after restoring the persisted revision book. Earlier per-instrument quality
repairs and original regression evidence remain in place.

Validation: **311 tests across 31 modules passed in 90.8 seconds**, 1,869 declared
fields passed classification, and clean installed v1/v2, collector/cache, forward
and protected-local-serving checks passed. [Installed evidence](../examples/step-09/installed-check.json)
is committed. Read targeted failing logs rather than full observation files.

## Remaining roadmap scope

Next is [Step 10 participant readiness](../tasks/active/STEP-10-pilot-readiness.md).
Step 09 bars qualification is complete; it does not establish Character readiness
or prospective elapsed performance. Raw-price ETF total returns still need
qualified dividend/split evidence; the production transport is currently bars-only.
`ForwardRound` is fixture-only and needs reviewed real-source integration before
Step 11. Delistings, historical membership, quotes, intraday execution quality and
historical point-in-time revision completeness are outside this sample.

Standing permission covers paper activity; Step 13 still needs its separate
Trading quota/adapter and attribution implementation. These are engineering/data
requirements, not recurring owner-permission requests. No paper strategy, scheduler
or later numbered step was started here.
