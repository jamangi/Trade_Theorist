# ADR-003: Alpaca market-data qualification remains conditional

- Date checked: 2026-09-06
- Status: conditional adapter implemented; vendor selection deferred
- Decision owner: repository owner for any subscription or license acceptance

## Decision

Alpaca remains the first vendor candidate, but it is not selected as the production
market-data source. The repository now contains a feed-pinned, transport-injected
bars adapter and recorded-response tests. No credentials, account call, license
acceptance or purchase occurred.

A real forward experiment remains blocked until an account-authorized sample proves
the required symbol/session coverage and the owner verifies contract rights for the
intended private storage, internal replay and any derived or public reporting. Unknown
rights are recorded as unavailable, not inferred from API access.

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
| Shared request-rate enforcement | Not implemented; required TASK-014 follow-up and TASK-016 offline preflight before account calls |
| SIP whole-market coverage | Documented product capability; account entitlement not sampled |
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
2. the owner authorizes account use and, if necessary, a paid plan;
3. an authorized bounded sample is collected through that coordinator with credentials outside Git, verifying applicable feed entitlement, observed rate behavior and headroom under the 200/min ceiling;
4. the generated quality report demonstrates the frozen universe, sessions, feed and
   revision behavior without synthesized gaps; and
5. license evidence explicitly covers intended retention, replay and reporting.

The initial 180-attempt operating ceiling and cache/pacing design are engineering recommendations, not evidence of measured account capacity. Market Data limits, recent SIP entitlement and paper Trading API limits are distinct; the request-budget contract links the current primary sources. No quota extension or account authorization is granted by this amendment.
