# Step 09: Qualify permitted data and a bounded workload

- Status: completed 2026-09-07 UTC; private delayed daily SIP qualified
- Recommended model / effort: Sol / high
- Historical coverage: [TASK-014](../TASK-014-high-Sol.md)
- Queue: [ordered remaining work](../README.md)
- Design inputs: [Provider qualification](../../docs/data-and-learning.md), [rights](../../docs/data-rights-matrix.md), [ADR-003](../../decisions/records/ADR-003-alpaca-market-data-qualification.md)

## Why this position

Offline controls are proven; now establish whether rights, entitlement and coverage support the intended experiment.

## Starting evidence

[Step 08 passed offline](../../docs/step-08-offline-preflight.md), with [independent final evidence](../../examples/step-08/preflight.json). Live Trading quota verification remains a Step 13 blocker, outside this Market Data qualification. The [standing owner decision](../../decisions/APPROVALS.md) now covers free account calls and private local storage/replay; repeated sample-specific permission is unnecessary.

## Finished state

A vendor/rights decision and bounded quality/workload report establish actual supported use and coverage, or state why the intended experiment remains blocked.

## Implementation and acceptance

Recheck official provider terms and capability requirements for the intended universe, cadence, time window and use. Save retrieval dates, versions and applicability. Distinguish authentication from entitlement and each storage/replay/model-processing/reporting right. Local reporting is not permission by itself.

Record applicable rights and finite sample scope before dependent use; standing owner authorization now covers this sample and later free private account use. Route all sample requests through Step 06 with Step 08 preflight evidence. Measure attempts, retries/pages, waits, coverage, gaps, revisions, resume and actual headroom under the existing 180/200 policy. No silent SIP/IEX, timeframe or universe substitution.

Deliver a vendor decision, capability/quality report and nonsecret workload evidence. Reingestion must be idempotent. Demonstrate required coverage or mark the experiment blocked. The prior tiny delayed SIP sample is historical evidence, not comprehensive qualification. Paid plans, alternate vendors and provider communication retain separate authority gates.

When rights or entitlement cannot support the design, record the blocker and a concrete bounded alternative for the relevant owner decision. Do not relax clocks, source permissions or the shared ceiling to claim success.

## Validation and handoff

Use the [focused validation workflow](../../docs/development.md). Record changed files, actual checks, evidence artifacts and remaining blockers here. For code changes, run relevant tests and the full suite once after focused checks pass; for UI changes, verify keyboard and narrow/wide layouts too. Original synthetic acceptance never substitutes for required real-source or elapsed-time evidence.

Stop at this step's finished state. The default next item is [Step 10](STEP-10-pilot-readiness.md); do not start it automatically. Follow the queue's blocker rule for independent work. Preserve historical completion claims. No account call, order, paid subscription, public market-data deployment or recurring work is authorized merely by this task brief.

## Completed qualification and handoff

Completed 2026-09-07 UTC under the owner's standing free-account authorization
and private-local storage/reuse interpretation. The earlier blocked review is
preserved in [dated evidence](../../examples/step-09/qualification.blocked-review.json),
not an outstanding permission request.

Start with the [compact implementation guide](../../docs/step-09-vendor-qualification.md).
It contains the scope, measured results, private-store location, reproducible
commands and remaining engineering work. Evidence:

- [Current selection](../../examples/step-09/qualification.json): Alpaca selected
  for private delayed raw daily SIP, VTI pilot with QQQ/SPY qualification controls.
- [Actual operational evidence](../../examples/step-09/account-sample.json): six
  HTTP 200 requests, first retrieval five pages with resume, second one page;
  30/30 expected instrument/session pairs each, zero retries/429s/quarantine.
  Exact caching made no additional calls; persisted replay added no duplicates.
  Minimum actual send gap 0.4825 seconds; rolling-minute peak six under 180/200.
  Header remaining=199 is recorded but does not establish account-wide headroom.
- [Executed protocol](../../examples/step-09/sample-plan.json): ten sessions,
  August 24–September 4, 2026, fixed SIP/raw/1Day scope, 12-attempt maximum and
  one ten-minute deadline. Actual use was six attempts. Raw data remains private
  outside Git under the same durable quota owner; no automatic purge was imposed.
- [Source review](../../examples/step-09/sources.json): twelve official sources,
  dates/versions and historical retrieval limitations. Personal-use terms and
  research/backtesting guidance support the recorded owner interpretation;
  no decisive contrary evidence for private local use was found.
- [Scoped capability](../../examples/step-09/source-capability.alpaca-conditional.json)
  now enables private storage/replay. Broader unqualified capabilities remain
  explicit. Public redistribution/external model data transfer are outside scope.

The rehearsal exposed duplicate additions when replaying an older receipt after
a newer one. `RevisionBook.append` now recognizes every previously seen exact
payload in a series. Real persisted replay verified zero additions; the second
retrieval retained 30 new receipt/provenance records with zero changed bar values.
Transport diagnostics are bounded and expose only timing/status/rate headers.
Earlier per-instrument quality fixes and regression evidence remain preserved.

Validation: **311 tests across 31 modules passed in 90.8 seconds**, field inventory
passed for **1,869 fields**, and the clean installed v1/v2, collector, forward and
protected local serving checks passed ([evidence](../../examples/step-09/installed-check.json)).
No orders, paid subscriptions, provider messages or external model calls occurred.

Next is Step 10 participant readiness; it was not started. Before Step 11, qualify
required dividend/split evidence for raw-price ETF total returns and implement the
reviewed real-source forward path (currently fixture-only). Step 13 still needs
Trading quota/adapter and attribution implementation. These are engineering and
experiment requirements, not renewed owner-authorization gates.
