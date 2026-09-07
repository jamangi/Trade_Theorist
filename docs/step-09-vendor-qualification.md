# Step 09: vendor and rights decision

Reviewed 2026-09-07 UTC / 2026-09-06 America/Chicago. **Alpaca remains the candidate
for delayed daily SIP; production qualification remains blocked.** The Step 09
finished state permits a documented blocked outcome. This review delivers that
decision, the missing-evidence register and a concrete sample proposal. It does not
claim that a new real sample passed.

Start here, then read [qualification.json](../examples/step-09/qualification.json).
[sources.json](../examples/step-09/sources.json) records ten official sources,
displayed versions/locators, retrieval date and two failed agreement retrievals.
The [sample plan](../examples/step-09/sample-plan.json) is proposed, not authorized
or executed. No credentials, account endpoints, market observations, model calls,
orders, paid plans or provider messages were used in this step.

## Scope and evidence

The historical [blocked pilot](../examples/forward-shadow/pilot-candidate.blocked.json)
declares **VTI at daily cadence**. Preserve that opportunity set. QQQ/SPY are useful
sample controls from the earlier access check, not newly approved trading assets.
The pilot's old start/end dates are not authority to backdate decisions or start a
trial. Step 10 reviews actual participants; any real trial needs new prospective
registration after all gates are satisfied.

| Question | Decision and evidence |
| --- | --- |
| Can delayed SIP support a daily pilot? | Documented candidate fit: the [FAQ](https://docs.alpaca.markets/us/docs/market-data-faq) permits unsubscribed historical SIP queries ending at least 15 minutes earlier. Keep a 20-minute safety margin; explicitly pin SIP. |
| Is current access verified? | No new check. The [historical sanitized evidence](../examples/ingest/alpaca-account-access.2026-09-06.json) records five sessions each for VTI/SPY/QQQ and a latest-SIP 403. Those facts are not current authentication or comprehensive qualification. |
| Is the limiter still missing? | No. Steps 06–08 implemented it and passed independent offline preflight. Retain 180 operating / 200 hard requests per rolling minute; the [Basic plan table](https://docs.alpaca.markets/us/docs/about-market-data-api) does not measure this account's headroom. |
| What would qualify bars? | Every declared instrument/session pair, explicit feed/raw adjustment, complete pagination, receipt/cutoff preservation, resolved quarantine and idempotent replay. [Bar documentation](https://docs.alpaca.markets/us/reference/stockbars) sorts by symbol before time; `asof` resolves names, not historical knowledge of revisions. |
| Can bars alone qualify total returns? | No. Dividends/splits need permitted, timely evidence. The [corporate-action reference](https://docs.alpaca.markets/us/reference/corporateactions-1) warns of availability delays. The current production transport admits only bars. Action retrieval requires a separately scoped shared-admission extension. |
| Are real forward decisions ready after a bars pass? | No. `ForwardRound` currently rejects real-source operation. Reviewed real integration, eligible immutable participants and actual prospective observations remain separate requirements. |

A current ETF watchlist is a forward scope, not survivor-free historical universe
coverage. Delisted instruments, historical constituents, quotes, intraday execution
quality and point-in-time corporate-action history are unqualified. No fallback to
IEX, adjusted returns, a new timeframe or a new vendor was selected.

## Rights: supported access versus unresolved uses

The [public Terms](https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf)
support personal, noncommercial access/use. They are **not a blanket prohibition
on private research**. They also refer to other agreements and restrict broader
distribution. The current [Customer Agreement](https://files.alpaca.markets/disclosures/library/AcctAppMarginAndCustAgmt.pdf)
has footer version **V26.2026.07**; section 30 restricts reproduction as well as
distribution/commercial exploitation. Which customer/subscriber terms apply to
this owner's paper-only/data use has not been established in this review.

The NASDAQ and NYSE subscriber documents linked from Alpaca's
[disclosure index](https://alpaca.markets/disclosures) returned HTTP 403 through the
reader. Their contents and versions are not inferred. No additional account-specific
evidence was supplied during this review. Engineering therefore retains these
use-specific states, rather than declaring all uses prohibited:

| Intended use | Current disposition |
| --- | --- |
| Personal noncommercial access | Supported by the general Terms, subject to the applicable agreement set. |
| Private persistent cache, backups and replay | Unresolved for the proposed retention/use; necessary before the durable coordinator collects a real sample. |
| Local AI inference or training | Not established for this use; resolve before model processing. |
| Sending observations/derived series to an external model service | Unapproved; model-service retention/training and transfer are separate questions. The proposed sample makes no model calls. |
| Private owner reports | Conditional on permitted underlying use; loopback hosting does not supply missing rights. |
| Public derived series or raw redistribution | Unapproved/restricted. The [redistribution support article](https://alpaca.markets/support/redistribute-alpaca-api) provides no general redistribution permission. |

Match the accepted agreements to the intended use first. New written permission
is necessary only where the applicable terms require it or leave a material issue
unresolved; an existing grant may suffice. No account access, acceptance of new
terms, provider outreach or purchase was performed to resolve this.

## Concrete next decision

The proposed one-time sample requests **QQQ/SPY/VTI, raw daily SIP bars for ten
sessions, 2026-08-24 through 2026-09-04**, with a frozen `asof` of September 4.
The [NYSE calendar](https://www.nyse.com/trade/hours-calendars) has no holiday within
that interval; September 7 is closed. A daily API aggregate is not thereby proven
to contain only regular-session trades.

Two work budgets sum to **at most 12 physical attempts**, including all pages,
retries and ambiguities, with one common completion deadline ten minutes after
start. First query: seven bars per page, at most eight attempts, explicit checkpoint
resume. Second: separately frozen freshness/cutoff, at most four attempts, to
observe the same period again. Exact-query cache reads and duplicate normalization
must add zero provider attempts/observations. Same owner/root, no quota reset.
An exhausted budget, long cooldown, unresolved quarantine or missing pair blocks
the sample; a small workload cannot establish maximum account capacity.

Before executing it, resolve **collection + private storage/replay with a proposed
30-day retention including backups**, then obtain authorization for that exact
bound. This proposal grants no retention or deletion permission. Keep raw data and
detailed results outside Git; separately review any nonsecret operational summary
before committing it. Model use and extended retention for the 60-session forward
trial require their own applicable scope.

For the owner or provider clarification, use this precise question: *Under the
agreements applicable to this Basic/paper-only account, may its sole owner retain
the specified delayed-SIP sample and backups for 30 days, normalize/replay it for
personal research and show derived results only to that owner? Which clauses and
deletion obligations apply? Separately, what scope permits local AI processing or
transfer to a named external model service for the later forward trial?* This is
an unsent question; do not contact the provider without authorization.

Until resolved, an original synthetic or independently licensed owner-supplied CSV
can exercise engineering. It cannot substitute for Alpaca qualification. A bars-only
price-observation exercise could avoid an unsupported total-return claim, but that
scope change needs an explicit decision and does not remove source-use requirements.

## Quality-report repair and validation

The old `quality_report` could mark a sample qualified when one symbol supplied
all aggregate session dates, despite another symbol being absent. It also ignored
quarantine as a blocker and lost revision counts when passed a generator. The
[original regression evidence](../examples/step-09/quality-regression.json) records
those pre-fix outcomes without vendor observations.

Callers now supply `expected_instruments` alongside `expected_sessions`. The report
lists `missing_pairs`, blocks absent/duplicate scope, mismatched feed/adjustment or
out-of-scope rows and unresolved quarantine, and preserves iterator revisions.
`sample_kind` defaults to `unverified`. A caller's explicit `authorized_account`
label is an evidence classification, not proof of authority: `coverage_status`
does not grant rights, select a vendor or enable real forward operation.

Use `.venv/Scripts/python.exe` for `python` on Windows:

```text
python scripts/check.py test_quality_qualification test_alpaca_adapter test_ingest test_market_requests test_forward_shared
python scripts/export_field_classification.py --check
python scripts/check.py
```

Read the small regression evidence and failing logs, not entire fixtures. The
active brief records final checks. Historical Step 08 and initial account/quality
artifacts remain unchanged; the new report records real metrics as **null / not
run**, rather than turning zero account calls into zero gaps or measured headroom.

Next: [Step 10](../tasks/active/STEP-10-pilot-readiness.md) may independently review
saved learning/readiness and state conditional data requirements. Step 11 remains
blocked by unresolved Step 09 qualification as well as its other entry criteria.
Neither next step nor the proposed sample was started automatically.
