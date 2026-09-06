# Step 07: Connect forward decisions to shared snapshots

- Status: pending; remaining scope as of 2026-09-06
- Recommended model / effort: Sol / high
- Historical coverage: [TASK-015](../TASK-015-high-Sol.md)
- Queue: [ordered remaining work](../README.md)
- Design inputs: [Shared request budget](../../docs/market-data-request-budget.md), [evaluation](../../docs/evaluation.md)

## Why this position

Integrate metered data with deadlines and identical opportunity sets before adversarial review.

## Starting evidence

Step 06 controls, Step 02 accounting and existing forward fixtures pass.

## Finished state

Offline forward orchestration consumes the shared data service, freezes equal eligible snapshots and records finite budgets, deadlines and truthful defer/abstention outcomes.

## Implementation and acceptance

Consume Step 06's [shared coordinator and cache](../../docs/market-data-request-budget.md), not independent Character transports. Extend the frozen forward manifest with quota-policy/version ID, finite request/work budget, deadline, expected coverage, shared work references and frozen snapshot identity. Keep API request budgets separate from model/token budgets. Report estimates and actual attempts, retries, cache hits, shared-fetch reuse, wait duration, incomplete pages and deadline misses; count shared physical requests once at the coordinator.

Plan a common snapshot before Character execution. Freeze only complete eligible coverage, or explicitly apply the preregistered partial-coverage policy equally to all paired consumers. A budget stopping pagination must not favor symbols on early pages. Quota waiting never relaxes evidence cutoffs; late data produces visible defer/abstention, not different data for a later Character. Reuse observations without crossing feed, entitlement, revision or decision-time boundaries.

Acceptance: identical Character/mode requests share one fetch sequence; subsequent eligible cache reads cause zero Alpaca calls; exhausted budget and delayed completion retain identical snapshot IDs and honest status. This step finishes on offline integration evidence. Account-backed work later requires Step 08 preflight and Step 09 sample/rights qualification; Step 12's final audit follows the real forward trial.

Use v2 execution-basis and portfolio identities and private reports. Validate frozen Character versions, baseline/cost/flow policies and stopping-rule fields with original synthetic records. This is offline integration; real eligibility and prospective observations remain Steps 10 and 11.

## Validation and handoff

Use the [focused validation workflow](../../docs/development.md). Record changed files, actual checks, evidence artifacts and remaining blockers here. For code changes, run relevant tests and the full suite once after focused checks pass; for UI changes, verify keyboard and narrow/wide layouts too. Original synthetic acceptance never substitutes for required real-source or elapsed-time evidence.

Stop at this step's finished state. The default next item is [Step 08](STEP-08-offline-preflight.md); do not start it automatically. Follow the queue's blocker rule for independent work. Preserve historical completion claims. No account call, order, paid subscription, public market-data deployment or recurring work is authorized merely by this task brief.
