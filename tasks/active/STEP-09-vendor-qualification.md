# Step 09: Qualify permitted data and a bounded workload

- Status: pending; remaining scope as of 2026-09-06
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
