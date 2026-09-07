# Step 11A: Record and verify finite observation runs

- Status: implemented 2026-09-07; acceptance evidence below.
- Recommended model / effort: Sol / medium.
- Queue: [ordered roadmap](../README.md); early bounded part of [TASK-020](../TASK-020-medium-Sol.md).
- Starting evidence: the frozen [Step 11](STEP-11-forward-observation.md) trial and its private reports already exist. Elapsed observation is not required to build or rehearse this launcher.

## Purpose and finished state

Make every attempted launch inspectable, including failures and interrupted runs.
A successful process exit or a saved report alone must not claim trial completion.
The owner requested this early infrastructure, followed by Step 11B, on September 7.

## Scope and acceptance

Add an external launcher around the frozen runtime. Write flushed `start <date>`
and `end <date>` lines, private per-run receipts, duration, phase, exit status,
report identity and counts. Keep credentials, market values and raw child output
out of these diagnostics. Starts without receipts remain evidence of interruption.

Check report content hashes, current manifest, freshness, gaps, five observed
sessions and forecast maturity. Keep process success distinct from scientific
completion. Enforce the original observation window, an exclusive launcher lock,
bounded child duration and existing account quotas. A second trigger must skip
verified completion; an incomplete run must remain incomplete. Never create a
new experiment, decision, model call or broker order.

## Implementation and evidence

[Launcher](../../src/trade_theorist/observation_job.py),
[entry point](../../scripts/run_step_11_job.py), and
[tests](../../tests/test_observation_job.py) implement this contract outside the
frozen runtime hash. Tests cover stale/foreign/tampered reports, incomplete exit-zero
results, deadlines, timeouts, actual cross-process overlap and killed-lock-owner
recovery, notifications, and durable interruption evidence.

The actual private trial passed a read-only rehearsal with zero transport
attempts. [The handoff](../../docs/step-11-automation.md) records final checks,
storage locations, exit meanings and limits. Future completion is still pending.

Final validation: 21 focused launcher tests and the full 363-test/36-module suite
passed, as did 1,983 field classifications and the clean offline installation check.
Frozen scientific inputs are unchanged. Private logs and installation plans are
excluded from Git; public evidence contains only operational metadata.

## Handoff

Step 11B uses this launcher. Step 12 audits its receipts alongside the scientific
evidence. Step 15 generalizes it after its own prerequisites; implementation here
does not enable recurring work.
