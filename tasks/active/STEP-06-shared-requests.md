# Step 06: Implement one shared market-data request budget

- Status: implemented and verified offline, 2026-09-06
- Recommended model / effort: Sol / high
- Historical coverage: [TASK-014](../TASK-014-high-Sol.md)
- Queue: [ordered remaining work](../README.md)
- Implementation guide: [Step 06 API, reproduction and recovery](../../docs/step-06-shared-requests.md)
- Design inputs: [Shared request budget](../../docs/market-data-request-budget.md)

## Why this position

Add shared admission, cache reuse and visible delays before any new qualification or prospective traffic.

## Starting evidence

Step 01 contracts and Step 04 commands are available; the base adapter already exists.

## Finished state

Durable shared admission covers every actual transport attempt, with merged cache misses, full cooldown handling, bound resume state and nonsecret usage telemetry proven offline.

## Implementation and acceptance

Implement the [shared request-budget contract](../../docs/market-data-request-budget.md). Step 06 owns one quota coordinator across all callers of the same Alpaca Market Data account quota, including manual sample collectors. Extend the versioned contracts and existing store, ingestion, heartbeat and command interfaces; do not create per-Character or per-process allowances.

Use a configurable 200/min hard maximum with an initial 180-attempt rolling-60-second operating ceiling and smooth pacing. All pages, retries and ambiguous outbound attempts consume that same ceiling and a finite work-item budget. Cache lookup, compatible in-flight request merging and multi-symbol batching precede admission; admission wraps every actual transport attempt. Persist quota/cooldown state and reject duplicate coordinator ownership. A restart cannot mint a new allowance. Reports must qualify account-wide guarantees when outside programs do not cooperate.

Correct the existing no-op default sleeper and truncated server wait: `_delay` currently caps even a valid long `Retry-After` at 30 seconds. Production waits or defers must respect the full server cooldown, handle header case and valid numeric/date formats, reject nonfinite delays, add bounded fallback jitter and cap retries. A 429 updates shared cooldown even on the final attempt. Test sleepers remain explicit offline dependencies.

Bind resume state to the full canonical query, atomically checkpoint accepted pages, and preserve later-symbol coverage across pagination. Cache hits make zero provider calls; three consumers of one missing window share one fetch sequence. Ship validated policy/query/work telemetry contracts without keys or account secrets; doctor reports missing coordinator/policy readiness. Verify the applicable Basic feed entitlement separately from the request limit; no silent SIP/IEX or time-window fallback.

Complete this step with recorded-transport tests of the implemented coordinator and adapter. Step 07 integrates the forward consumer; Step 08 then performs the independent adversarial preflight. Passing Step 08 is required before Step 09's account-backed sample, not before this engineering step can finish. The prior small credential check does not establish rate behavior, complete coverage or rights.

## Validation and handoff

Completed 2026-09-06. The [implementation guide](../../docs/step-06-shared-requests.md)
is the bounded handoff for a fresh task: exact APIs, commands, field meanings,
owner recovery, sharing semantics and the file/test map. The
[original recorded fixtures and validation evidence](../../examples/step-06/validation.json)
contain no account data.

- Added request policy/query/telemetry contracts, additive migration 005, durable
  quota ownership and admission, shared cache/in-flight work, atomic page resume
  and coverage. Production uses one HTTP attempt per admission; all adapter retry
  paths are either coordinated or explicitly offline.
- Extended adapter and revision-ingestion entry points, heartbeat preparation,
  v1/v2 doctor, nonsecret config and `market-recorded --fixture`. Updated schema
  export, field classification, installed-package check, READMEs and the active queue.
- Focused coordinator/adapter checks passed; the coordinator module has 24 tests.
  Related operation, heartbeat and ingestion checks also passed. Final full suite:
  **271 tests, 27/27 modules, 80.8 seconds**. It was repeated after the final compatible
  subset-sharing fix; quiet complete logs remain under `.local/test-logs/`.
- Clean wheel installation passed v1/v2 workflows, protected serving, migration 005,
  recorded collection and zero-call cache reuse with external sockets trapped.
  The recorded collector used two cumulative physical fixture attempts. Logs are
  under `.local/installed-logs/`; portable evidence is linked above.
- Schema generation and the **1,623-field** classification check passed; the diff
  whitespace check passed. No account calls, model calls, orders or recurring jobs
  were used. No real market coverage, rights or account capacity is claimed.

Next: **Step 07 only when requested**. Bind the existing shared-work references,
budgets, deadlines and expected coverage into forward manifests and experiment
snapshots. Step 08 independent preflight and Step 09 account-backed qualification
remain pending. A stopped owner/missing policy is reported separately from the
readiness of the private saved-data UI. Preserve quota registry and store together;
never create a fresh principal to bypass recovery or an exhausted work budget.

Use the [focused validation workflow](../../docs/development.md). Record changed files, actual checks, evidence artifacts and remaining blockers here. For code changes, run relevant tests and the full suite once after focused checks pass; for UI changes, verify keyboard and narrow/wide layouts too. Original synthetic acceptance never substitutes for required real-source or elapsed-time evidence.

Stop at this step's finished state. The default next item is [Step 07](STEP-07-forward-integration.md); do not start it automatically. Follow the queue's blocker rule for independent work. Preserve historical completion claims. No account call, order, paid subscription, public market-data deployment or recurring work is authorized merely by this task brief.
