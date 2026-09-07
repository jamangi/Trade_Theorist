# Step 06: one durable request owner

Implemented offline on 2026-09-06. Start here after the [queue](../tasks/README.md)
and [Step 06 brief](../tasks/active/STEP-06-shared-requests.md). Next is
[Step 07](../tasks/active/STEP-07-forward-integration.md). No conversation history
or large fixture dump is needed.

## What to use

| Interface | Purpose |
| --- | --- |
| `market_requests.Coordinator` | One account-principal owner; `submit`, `run`, `resume`, `telemetry`, `observations`, `normalize`, `usage` |
| `request_contracts.py`; `schemas/market-requests-v1.json` | Strict version-1 policy, full query and nonsecret work telemetry; accounting versions remain separate |
| `RequestStore`; migration `005_market_requests.sql` | Additive SQLite quota, attempts, work, immutable observations, windows and atomic page checkpoints |
| `AlpacaBarsAdapter.fetch_shared` | Explicit-feed adapter entry through the owner |
| `heartbeat.prepare_market_data` | Preparation callback before a heartbeat transaction; Step 07 owns decisions and snapshot eligibility |
| `Coordinator.normalize` | Complete raw downloads through existing CSV revision ingestion; requires matching feed and storage/replay rights |
| `request_operations.status`; `doctor --quota-root --quota-policy` | Read-only policy, migration, principal binding and owner diagnostics; no repair or account call |
| `market-recorded --fixture` | Manual original-fixture collector through the same owner; no network transport |
| `tests/test_market_requests.py`, `test_alpaca_adapter.py` | Small recorded transports, fake clocks and process-lock checks |

Read only the relevant method and test when making a change. The broader design
is [market-data-request-budget.md](market-data-request-budget.md).

## Reproduce without an account

Use the existing environment; on Windows replace `python` below with
`.venv/Scripts/python.exe`. Generated pages contain original invented prices,
not downloaded market data. Pick one absolute fixture quota root and keep it.

```text
python scripts/check.py test_market_requests test_alpaca_adapter test_operations test_operations_v2
python scripts/export_request_schemas.py
python scripts/build_step_06_fixtures.py
python scripts/export_field_classification.py --check
python -m trade_theorist.cli market-recorded --fixture --quota-root C:/TradeTheorist/request-fixture --quota-policy examples/step-06/policy.json --query examples/step-06/query.json --responses examples/step-06/responses.json --max-attempts 5 --deadline 2099-01-01T00:00:00Z
```

The collector completes two recorded pages: AAPL on page one, MSFT on page two.
Repeating the same command reuses completion, with two cumulative physical recorded
attempts and zero account calls. `fixture_only` is explicit. The displayed resume
record binds the work ID and full query hash; it contains no provider token.
For a deferred recorded download, supply the remaining responses beginning at its
next uncommitted page. The durable store owns the actual token. A restart defers
new transport for at least 60 seconds; repeat after `not_before`, without deleting
state. Exhausted work retains its original budget and deadline.

`doctor` accepts `--quota-root` and `--quota-policy`, or nonsecret config fields
`quota_root` and `quota_policy_path`. Missing setup, mismatched policy, damaged or
missing state, and a stopped owner are explicit blockers under `market_requests`.
Private saved-data inspection keeps its own readiness status. A successful local
coordination check does not certify source rights or authorize real requests.

## Coordinator contract

Construct one owner for a stable **nonsecret quota ID**, not an API key, Character,
feed or run. Production requires `SingleAttemptTransport(key, secret)` with keys
supplied privately in memory. It sends one bounded, timed historical-bars GET per
invocation, without SDK retries or redirects. There is no real-fetch CLI. Supplying
a transport does not grant authorization; account qualification remains Step 09.
`AlpacaBarsAdapter.pages` is now explicitly offline-only. Fake clocks, jitter and
alternate registry paths require `synthetic=True`.

All cooperating consumers share the same owner object and private SQLite store.
A second process fails closed; this step does not add IPC or a background service.
The OS lock lives under `%LOCALAPPDATA%/TradeTheorist/quota-owners` (home fallback).
A permanent principal-to-root binding prevents starting the same allowance in an
empty replacement directory. Preserve **both** registry and database during backup
and recovery. Policy changes currently fail closed: use an explicit reviewed
transition before changing a running principal's policy, never a fresh quota ID.
This guarantee covers cooperating callers using the same principal and registry;
other OS accounts, hosts or unrelated programs require operational coordination.
The 20-attempt headroom is not a guarantee against their traffic.

The default policy admits at most 180 attempts in any rolling 60 seconds, below
the configurable 200 hard maximum. Lower configured limits win. Dispatch is paced
at least one third of a second apart, more slowly for lower ceilings. Idle time
does not accumulate burst permits. Every page, retry and ambiguous attempt is
charged durably **before** transport and against its finite work budget. Neither
waiting nor transport holds a database write transaction. A crash before page
commit preserves the charge; the next attempt can refetch but cannot refund it.

In-process admission uses monotonic time. Restart preserves logical time, waits a
full recovery window and honors any longer remaining cooldown without trusting
wall-clock downtime. Wall-clock jumps cannot refill admission. Completion deadlines
use both elapsed and UTC bounds; waiting never changes an information cutoff.
A transport already in progress can finish after the work deadline. Its attempt
stays charged and the work becomes `expired`; it cannot support an on-time decision.
Numeric or HTTP-date `Retry-After` is case insensitive and uncapped, including on
the final 429. Invalid/nonfinite headers use bounded exponential backoff plus
jitter. Very large finite waits retain their full internal deadline; only the
display timestamp saturates at year 9999. Waits exceeding a run's wait allowance
return `deferred`, with `not_before`, instead of sleeping indefinitely.

`verified_rate_headers` defaults false: Market Data reset-header meaning is not
assumed from Broker API documentation. When separately verified and enabled,
headers can lower the durable limit or extend cooldown; higher hints never raise
the configured ceiling. Feed entitlement is independent: SIP end must be at least
900 seconds old and the selected feed must be permitted in policy. No feed or
time-window fallback exists. The fixture policy's rights references demonstrate
structure only; production references require the applicable independent review.

## Sharing, coverage and continuation

Full canonical identity pins endpoint, symbols, interval, timeframe, feed,
adjustment/as-of, sharing and rights scopes, revision policy, freshness, information
cutoff, expected sessions and page size. Canonical symbol order is immaterial.
Identical pending requests join one work item: three consumers receive one download
and one physical charge. Compatible pending subsets (including different page
sizes) retain their own full-query IDs and reference the parent's `shared_work_id`.
Running a subset progresses the same parent download and filters its frozen IDs;
the subset owns no additional transport allowance. Its own earlier deadline still
applies. A subscriber retains the parent's original limits and remaining budget;
it cannot top up attempts or reset retries. Parent failure propagates, and a subset
cannot treat an unfinished parent page sequence as complete.
Compatible completed windows are reused, including overlapping intervals and
symbol subsets; remaining identical intervals are batched across missing symbols.
Queued independent work rechecks the cache before its first transport attempt.

Page contents and checkpoint commit together. Observations are immutable, and the
completed work freezes their IDs. An exhausted page sequence records the fetched
window, but `complete` additionally requires every requested symbol/session.
Missing coverage is `incomplete`, never an invented bar or proof of no opportunity.
Partial downloads expose telemetry and resume state; `normalize` refuses them.
Experiment-specific revision persistence and information eligibility remain the
existing ingestion caller's responsibility. Normalization returns accepted and
quarantined records; inspect both and save accepted records transactionally with
the experiment's existing revision history.

Telemetry contains one physical-attempt total per shared work item, retries, 429s,
pages, cache hits, subscription count, queue lifetime, actual in-process sleep,
coverage, remaining attempts, deadline failure and deferred reason/time. Queue
lifetime uses the conservative persisted logical clock and excludes unmeasured
downtime. Subscription count counts submissions, not distinct people. Do not sum
the same work's attempts once per subscriber; `usage()` reconciles actual attempts.
Query hashes and tokens belong in private state; raw pages and credentials never
enter public exports. Schema and field classification deny unknown public fields.

Step 07 must bind this work to frozen run manifests and shared experiment snapshots,
including original deadlines, budgets, expected coverage and abstention behavior.
Step 08 independently challenges the integrated path; Step 09 then qualifies a
separately authorized, bounded account workload. This engineering evidence does
not replace any of those gates.

## Validation

The focused suite covers shared consumers, later-symbol pages, cache batching,
concurrent submission, rolling/paced admission, downward headers, timeout charging,
atomic rollback/restart, full final-429 cooldown, clock jumps, deadlines, denied
feeds, strict resume, malformed coverage, production transport and private doctor.
The installed-package check also exercises the recorded collector and cache under
a network trap, proving migration 005 ships in the wheel. Final counts and checks
are recorded in the [Step 06 handoff](../tasks/active/STEP-06-shared-requests.md).
