# Step 08: independent offline preflight

Completed 2026-09-06 for the implemented shared Market Data and fixture forward
paths. [Final evidence](../examples/step-08/preflight.json) passes 14 independent
cases. [Baseline evidence](../examples/step-08/baseline.json) records eight passes
and four failures on main `5e7140e`, before fixes. This is an offline engineering
result, not account qualification, real elapsed forward evidence or paper promotion.

Start with this guide and the [active brief](../tasks/active/STEP-08-offline-preflight.md).
The default next task is [Step 09](../tasks/active/STEP-09-vendor-qualification.md);
it was not started. Read its rights and bounded-sample requirements before use.

## Findings and fixes

| Baseline defect | Resolution |
| --- | --- |
| A ten-second pause between admission and transport produced a zero-second gap between sends. | Pace from receipt/exception completion, and retain each rolling charge until at least 60 seconds after that completion. This conservatively bounds the actual send. |
| A 100-digit verified `X-RateLimit-Limit` overflowed SQLite's integer binding and rolled back a valid 120-second 429 cooldown. | Ignore non-reducing hints before binding them. Valid server cooldowns survive oversized headers. |
| A returned policy dictionary could change active feed-delay/entitlement settings. | `Coordinator.policy` returns a defensive deep copy. |
| A returned forward manifest could change frozen participants and model budgets. | `ForwardRound.manifest` returns a defensive deep copy. |

Migration `006_market_settlement.sql` adds nullable `market_attempts.settled` and
an index on `COALESCE(settled,dispatched)`. `dispatched` remains the original
**admission timestamp**, not a claimed wire measurement. New settlements use the
owner's logical monotonic clock. Old or interrupted attempts keep their charge;
restart still waits a full recovery window and any longer persisted cooldown.
Migration 005 and the v1/v2 accounting tables are unchanged. Slower responses now
reduce achievable throughput conservatively; 180/minute is a ceiling, not a target.

## What the independent evidence measures

`tests/preflight_support.py` defines original policy/query/clock/transport inputs.
The oracle calculates gaps and open-left, closed-right rolling 60-second windows
from transport-entry timestamps, independently of admission counters. Integer
nanoseconds avoid counting floating-point boundary noise twice. The production
case records the mocked HTTPS request boundary with real monotonic time and real
sleep. It makes no HTTP connection. Full traces stay in JSON; do not print them
into a task's context just to check success.

| Cases | Independent assertions |
| --- | --- |
| 01–02 | 365 sustained pages plus idle recovery at 180/minute; lower seven/minute policy; no burst after descheduling between admission and send. |
| 03–05 | Overlapping manual/scheduled/adapter consumers; one shared download; mixed-query isolation; full-query resume binding; each timeout, retry and page charged; exhausted budgets expose no partial evidence. |
| 06–07, 13 | Final-retry 429s preserve shared waits; numeric 120, HTTP-date, case variants, missing, invalid, negative, NaN and infinite headers; oversized hints; verified lower ceilings and a 120-second reset cannot increase capacity. |
| 08–09 | Parent forcibly terminates child processes during dispatch, transaction commit, committed-page checkpoint, persisted cooldown and owner-only state. Duplicate ownership is refused, charges reconcile, late-symbol resume survives, wall jumps cannot refill allowance. |
| 10 | Real production sleep wiring and exactly two mocked HTTP attempts; SDK transport injection, Trading URLs and Trading policies rejected by the Market Data boundary. |
| 11–12 | Original paired portfolio/council inputs, queued subset misses, late-page opportunity coverage, frozen common snapshot/hash/cutoff, uniform deadline/late-receipt/budget abstention, interrupted reservation never replayed, defensive manifest copy. Saved reports, private dashboard data and read-only request diagnostics add zero calls. |
| 14 | Migration 5→6 preserves old checksums and ambiguous charges; recovery remains conservative; current v1/v2 readers can open the additive store. |

The paired fixture reuses only `FixtureV2` to construct typed ledger inputs. It
does not reuse Step 07's setup, scenarios or acceptance output as its oracle.
The baseline covers cases 01–12; cases 13–14 additionally verify the fixes. Each
artifact records its own harness/source byte hashes and UTC run date. These are
independent implementation checks, not a separate human review or third-party audit.

## Reproduce with bounded output

Use `.venv/Scripts/python.exe` for `python` on Windows:

```text
python scripts/run_step_08_preflight.py --output .local/preflight-logs/recheck.json
python scripts/check.py test_request_preflight test_market_requests test_forward_shared test_storage test_storage_v2 test_alpaca_adapter
python scripts/export_field_classification.py --check
python scripts/check.py
python scripts/check_installed.py --wheelhouse .local/wheelhouse
```

The audit prints one result per case, writes full tracebacks directly to ignored
`.local/preflight-logs/`, and returns a failing exit code for any failure. Use a
new output path to preserve the committed baseline/final evidence. The ordinary
quiet runner also discovers the independent audit. Read only the failing log and
relevant test/method. No provider, SDK, external model or order is needed. Tests
trap socket connections; the installed smoke separately allows local UI serving.

The clean wheel check verifies migration 006 and two settled attempts, as well as
v1/v2 resume/export, protected loopback serving, shared collection/cache and forward
fixtures. Exact final test counts are in the active brief.

## Retained boundaries and blockers

- Guarantees cover cooperating callers bound to one durable quota owner. Unknown
  outside account traffic, provider headroom and actual account headers are unmeasured.
- **Live paper Trading quota verification is blocked:** no live Trading transport
  or executable Trading quota policy exists. Offline broker reconciliation is not
  that implementation. The tested Market Data boundary rejects Trading policy/URL
  use. Step 13 must implement and independently verify separate Trading admission
  before any broker operation; this does not block Step 09 Market Data qualification.
- Step 09 must establish applicable source rights and a separately authorized,
  bounded coordinator-backed sample. Historical delayed SIP access alone does not
  establish storage, replay, model-processing or reporting permission.
- Real forward operation still requires eligible participants and prospective
  elapsed observations (Steps 10–11), followed by the Step 12 final audit. All
  preflight prices/opinions are original fixtures; promotion remains false.
- The production HTTP timeout bounds socket I/O, not a guaranteed total wall-time
  cancellation. Late responses cannot become eligible evidence; no stronger
  cancellation or real-workload latency claim is made here.
