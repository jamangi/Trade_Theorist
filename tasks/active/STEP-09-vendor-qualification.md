# Step 09: Qualify permitted data and a bounded workload

- Status: review delivered 2026-09-07 UTC; real qualification blocked with explicit evidence and next actions below
- Recommended model / effort: Sol / high
- Historical coverage: [TASK-014](../TASK-014-high-Sol.md)
- Queue: [ordered remaining work](../README.md)
- Design inputs: [Provider qualification](../../docs/data-and-learning.md), [rights](../../docs/data-rights-matrix.md), [ADR-003](../../decisions/records/ADR-003-alpaca-market-data-qualification.md)

## Why this position

Offline controls are proven; now establish whether rights, entitlement and coverage support the intended experiment.

## Starting evidence

[Step 08 passed offline](../../docs/step-08-offline-preflight.md), with [independent final evidence](../../examples/step-08/preflight.json). Live Trading quota verification remains a Step 13 blocker, outside this Market Data qualification. Applicable rights and explicit authorization are required before each dependent real use or bounded account sample.

## Finished state

A vendor/rights decision and bounded quality/workload report establish actual supported use and coverage, or state why the intended experiment remains blocked.

## Implementation and acceptance

Recheck official provider terms and capability requirements for the intended universe, cadence, time window and use. Save retrieval dates, versions and applicability. Distinguish authentication from entitlement and each storage/replay/model-processing/reporting right. Local reporting is not permission by itself.

Establish applicable rights before dependent use; obtain specific bounded sample authority before calls. Route all sample requests through Step 06 with Step 08 preflight evidence. Measure attempts, retries/pages, waits, coverage, gaps, revisions, resume and actual headroom under the existing 180/200 policy. No silent SIP/IEX, timeframe or universe substitution.

Deliver a vendor decision, capability/quality report and nonsecret workload evidence. Reingestion must be idempotent. Demonstrate required coverage or mark the experiment blocked. The prior tiny delayed SIP sample is historical evidence, not comprehensive qualification. Paid plans, alternate vendors and provider communication retain separate authority gates.

When rights or entitlement cannot support the design, record the blocker and a concrete bounded alternative for the relevant owner decision. Do not relax clocks, source permissions or the shared ceiling to claim success.

## Validation and handoff

Use the [focused validation workflow](../../docs/development.md). Record changed files, actual checks, evidence artifacts and remaining blockers here. For code changes, run relevant tests and the full suite once after focused checks pass; for UI changes, verify keyboard and narrow/wide layouts too. Original synthetic acceptance never substitutes for required real-source or elapsed-time evidence.

Stop at this step's finished state. The default next item is [Step 10](STEP-10-pilot-readiness.md); do not start it automatically. Follow the queue's blocker rule for independent work. Preserve historical completion claims. No account call, order, paid subscription, public market-data deployment or recurring work is authorized merely by this task brief.

## Delivered review and blocked-use outcome

The permitted blocked finished state is delivered on 2026-09-07 UTC / September 6
America/Chicago. **Real vendor qualification has not passed.** Read the
[bounded guide](../../docs/step-09-vendor-qualification.md) before opening evidence:

- [Current decision and quality/workload report](../../examples/step-09/qualification.json):
  candidate retained; each right is distinguished; zero new account calls, with
  unmeasured coverage/retries/waits/revisions/headroom recorded as null.
- [Official-source review](../../examples/step-09/sources.json): ten sources,
  displayed versions/locators and retrieval date; current customer footer
  V26.2026.07, general personal-use language and two unavailable linked agreements.
- [Concrete proposed sample](../../examples/step-09/sample-plan.json): ten sessions,
  QQQ/SPY/VTI historical raw daily SIP, at most 12 total attempts through the same
  coordinator and one ten-minute deadline. Not authorized or executed; VTI remains
  the pilot opportunity set. Storage/replay scope is proposed for 30 days.
- [Current conditional capability](../../examples/step-09/source-capability.alpaca-conditional.json)
  and [original quality regression evidence](../../examples/step-09/quality-regression.json).
  Historical access, initial pilot and Step 08 acceptance artifacts are preserved.

Code repair: the Alpaca adapter module's `quality_report` now checks each instrument/session
pair, blocks missing scope/quarantine/mixed data, retains generator revision counts,
and defaults sample authority to unverified. Six new tests reproduce the issues;
existing ingestion proves original duplicate/revision handling (1 initial, 0
duplicate, 1 changed revision). This is not real-source reingestion evidence.

Validation: focused quality/adapter/ingestion/coordinator/forward tests passed;
full suite passed once, **309 tests across 30 modules in 87.2 seconds**. Existing
field inventory check passed (**1,869 declared fields**; unknown fields denied).
No package/dependency/migration/UI changes required a new installed or browser check.

Remaining concrete blockers: match accepted account/subscriber terms to private
storage/replay and the proposed retention, authorize the exact sample after those
rights are established, and measure real quality/workload. AI processing and public
reporting have separate unresolved scopes. Raw-price ETF total-return claims also
need qualified actions/dividends, and the fixture-only forward path needs reviewed
real integration before Step 11. No provider was contacted and no permission was
inferred from absent documentation or an unanswered clarification.

Next independent task is Step 10's saved-evidence readiness review; it may retain
conditional data criteria. Step 11 stays blocked. Neither the sample nor Step 10
was started. README/queue, ADR-003, rights matrix and development map now point here,
so continuation does not depend on conversation history.
