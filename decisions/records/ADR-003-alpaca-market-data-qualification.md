# ADR-003: Alpaca market-data qualification remains conditional

- Date checked: 2026-09-06
- Status: delayed historical SIP sample passed; vendor selection deferred
- Decision owner: repository owner for any subscription or license acceptance

## Decision

Alpaca remains the first vendor candidate, but it is not selected as the production
market-data source. The repository contains a feed-pinned, transport-injected bars
adapter and recorded-response tests. On 2026-09-06 the owner authorized a bounded
read-only check using regenerated paper credentials. No credential value or account
identifier was retained, no order was submitted, and no purchase occurred.

The account authenticated successfully. Explicit `feed=sip` daily-bar requests ending
20 minutes before retrieval returned five sessions for each of VTI, SPY and QQQ. An
explicit latest SIP trade request returned HTTP 403. This proves delayed historical
SIP access for the sampled endpoint, symbols and window—not current SIP entitlement,
all-symbol coverage, quote/trade coverage, historical completeness or data rights.

A real forward experiment remains blocked until the owner verifies contract rights for
private storage, internal replay and any derived or public reporting and eligible
Character versions exist. Unknown rights remain unavailable rather than being inferred
from successful API access.

## Official evidence reviewed

- [Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq): the free
  stock feed is IEX; SIP access depends on subscription and recent SIP history can be
  denied. Alpaca documents an explicit `feed` parameter and warns that IEX represents
  only one venue. Therefore every adapter request pins its feed; defaults and fallback
  are prohibited.
- [Historical stock data](https://docs.alpaca.markets/us/v1.4.2/docs/historical-stock-data-1):
  Alpaca describes IEX as roughly 2.5% of market volume and SIP as consolidated U.S.
  exchange coverage. IEX is not accepted as evidence of whole-market opportunity
  coverage.
- [Historical bars API](https://docs.alpaca.markets/us/v1.1/reference/stockbarsingle-1)
  and [historical trades API](https://docs.alpaca.markets/us/reference/stocktradesingle-1):
  pagination uses `next_page_token`; requests expose feed and adjustment choices; the
  trades reference documents `asof` for symbol changes and 429 rate-limit responses.
- [Corporate Actions API](https://docs.alpaca.markets/us/reference/corporateactions-1):
  corporate-action events are available, but Alpaca warns that provider and processing
  delays can occur. This does not establish point-in-time revision history.
- [Alpaca disclosures](https://alpaca.markets/disclosures) and the current
  [customer agreement](https://files.alpaca.markets/disclosures/library/AcctAppMarginAndCustAgmt.pdf):
  exchanges retain market-data rights; reproduction, distribution, sale and commercial
  exploitation require permission. API functionality alone is not treated as private
  storage, internal replay or publication permission.

## Capability conclusion

| Requirement | Current conclusion |
| --- | --- |
| Explicit feed, bars, automation, pagination | Documented; adapter implemented |
| Shared request-rate enforcement | Subsequently implemented and independently verified offline in Steps 06–08; real account headroom remains unmeasured |
| Delayed historical SIP daily bars | Authorized sample passed for VTI, SPY and QQQ over five sessions |
| Current/latest SIP | HTTP 403 in the authorized check; not entitled |
| SIP whole-market coverage | Product capability documented; the small sample does not establish complete coverage |
| IEX whole-market coverage | Not sufficient |
| Provider publication timestamp on bars | Missing; forward receipt time is retained as the conservative first-demonstrated availability time |
| Point-in-time revisions | Not demonstrated |
| Corporate actions/dividends | Endpoint exists; timing/revision quality still needs sample validation |
| Delistings and historical constituents | Not demonstrated for the required experiment |
| Private storage/internal replay | Contract permission not established |
| Derived public display/raw redistribution | Not established; raw redistribution is restricted absent permission |

No alternative vendor was evaluated or silently selected. Selecting another provider
requires a new decision record using the same checklist.

## Promotion gate

Before status can change from conditional to selected:

1. TASK-014 implements the [shared request-budget contract](../../docs/market-data-request-budget.md), and TASK-016's narrow offline rate preflight passes (not its later full forward/paper review);
2. the owner authorizes a paid plan if a preregistered strategy requires current SIP;
3. a coordinator-backed follow-up sample verifies observed rate behavior and headroom under the 200/min ceiling;
4. the generated quality report demonstrates the frozen universe, sessions, feed and
   revision behavior without synthesized gaps; and
5. license evidence explicitly covers intended retention, replay and reporting.

The initial 180-attempt operating ceiling and cache/pacing design are engineering recommendations, not evidence of measured account capacity. Market Data limits, recent SIP entitlement and paper Trading API limits are distinct; the request-budget contract links the current primary sources. The manual check used only a handful of calls and was not a load test or substitute for the pending coordinator preflight.

The sanitized [account check](../../examples/ingest/alpaca-account-access.2026-09-06.json)
records the exact successful scope. Raw returned bars remain outside Git.

## Subsequent architecture decision (2026-09-06)

[ADR-004](ADR-004-local-observatory.md) supersedes public-hosting assumptions with a private local owner interface and versioned accounting repairs. It preserves this record's historical decisions and qualification evidence. The [rights matrix](../../docs/data-rights-matrix.md) keeps provider permission questions explicit; private deployment does not select a vendor or authorize account operations.

## Step 09 decision update (2026-09-07 UTC)

**Retain Alpaca as candidate; do not select production use yet.**
[The current review](../../docs/step-09-vendor-qualification.md) distinguishes
documented delayed-SIP fit from unknown current account access and applicable use
rights. General personal-use language supports that use; it does not by itself
resolve the proposed retention/replay/model-processing scope under all applicable
agreements. The source register records the customer PDF's V26.2026.07 footer and
the linked subscriber PDFs' retrieval failures.

Promotion gate 1 above is now satisfied offline by Steps 06–08. Gates 3–5 remain
unfulfilled; a paid/current SIP plan is unnecessary for the proposed older daily
window and was not purchased. The new [quality/workload decision](../../examples/step-09/qualification.json)
contains explicit nulls for unmeasured real metrics. The [sample proposal](../../examples/step-09/sample-plan.json)
has 12 total attempts and requires applicable storage/replay rights plus specific
authority before execution. No account sample ran in Step 09. Historical access
and initial blocked pilot artifacts remain unchanged.

Raw-bar ETF returns also require qualified distribution/action evidence; endpoint
availability is insufficient. Current forward integration remains fixture-only.
Step 10 may independently establish participant readiness, but neither its result
nor this review clears Step 11's data and real-integration requirements.
