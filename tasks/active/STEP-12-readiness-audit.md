# Step 12: Decide whether evidence supports a paper stage

- Status: complete 2026-09-15; reproduced audit holds paper promotion at forward shadow. Five sessions and one matured forecast remain below the 60/30 review floors. Step 13 is blocked, not started.
- Recommended model / effort: Astra / high
- Historical coverage: [TASK-016](../TASK-016-high-Astra.md)
- Queue: [ordered remaining work](../README.md)
- Design inputs: [Evaluation](../../docs/evaluation.md), [root approvals](../../decisions/APPROVALS.md)

## Why this position

The real forward trial supplies evidence the offline preflight could not; audit the whole chain before paper operation.

## Completed audit and handoff

Read the [final audit](../../docs/step-12-readiness-audit.md),
[read-only evidence verification](../../examples/step-12/evidence-verification.json),
[validation](../../examples/step-12/validation.json),
[numeric policy/stage decision](../../examples/step-12/paper-policy-decision.json)
and [scheduler disposition](../../examples/step-12/scheduler-disposition.json).
All 35 stored performance results were replayed with expanded metric/history
checks; 7 immutable reports and 4 matched baseline comparisons verified. The trial
used 3 of 12 account attempts; audit provider/model/order counts are zero.

Validation: 401 tests discovered in 40 modules; 394 passed and 7 optional recovery
tests skipped in the base environment. Supplemental recovery runs passed all
19 tests in those two modules, including the 7 skipped cases, using the pinned
age binary and optional environment. All 401 distinct tests are therefore covered.
All 14 independent rate-preflight cases, 1,983 field classifications and the clean
offline installed-package check passed. No UI or file in the explicit frozen trial
runtime hash set was changed.

One full-suite run exposed intermittent Windows WAL opening failure after worker
termination. Its log is preserved by hash in validation. A separately reproduced
storage constructor leak is fixed: failed setup now closes the connection before
raising; all three injected setup failures failed before the fix and pass afterward.
The transient I/O cause remains uncertain. `storage.py` is outside the original
frozen runtime hash set; the broader audit source inventory pins this change.

Added `readiness_audit.py`, `run_step_12_audit.py`, `test_readiness_audit.py`, the
audit guide and public counts/hashes/policy/validation artifacts. Root README,
queue, approvals, Step 13 status and operational handoffs now link the decision.
The new audit detects false rehashed metrics and source/history/halt changes,
rejects an injected broker tool, and verifies split-crossing forecast abstention.

The existing standing owner authority delegates numeric free-paper settings;
selection is recorded without another permission request. Paper execution remains
blocked by evidence and future-run engineering prerequisites. September 7 backups
predate the observation; refresh/recovery remains a documented operational gap.
Both finite Windows tasks were idle and disabled September 15 at 10:18 UTC,
before the redundant fallback/noon triggers. Definitions and receipts remain.
Stop here; do not extend the original trial or start Step 13 automatically.

## Starting evidence

Start with the [self-contained audit handoff](../../docs/step-12-audit-handoff.md)
and [verified scheduled-completion evidence](../../examples/step-11/observation-completion.json).
The September 14, 19:30 Chicago observation succeeded: five completed real
sessions, one matured forecast and zero source gaps. The September 15 check
verified its immutable report, original launcher receipt, frozen inputs and
35 stored accounting results without provider/model calls. The data prerequisite
is satisfied; paper promotion remains false. The handoff gives exact private-file
locations, safe verification commands, remaining scheduler triggers, backup
freshness limits and the steps for a new task to begin this audit.

Before the final readiness decision, require Step 11's preregistered window to
have matured and its outcomes to have been retrieved and verified. Rights,
engineering evidence and numeric paper policy are inputs to the audit;
the dated completion evidence above establishes the observation prerequisite.

## Data collection prerequisite and exact schedule

The frozen trial `forward:step11-20260907` covers five trading sessions:
**September 8, 9, 10, 11 and 14, 2026**. September 13 is not its final session
or a scheduled collection date. The plan retrieves completed VTI daily SIP bars
and corporate-action outcomes after the five-session window, rather than running
a daily collection job throughout that week. See the
[frozen trial and observation plan](../../docs/step-11-forward-observation.md#frozen-trial).

The installed tasks under `\TradeTheorist\` use this finite schedule. Chicago
times below are CDT (UTC−05:00); the
[checked configuration](../../config/step-11-jobs.json) records UTC instants.

| Event | Chicago date and time | UTC date and time | Purpose |
| --- | --- | --- | --- |
| Earliest permitted observation | September 14, 7:20:01 p.m. | September 15, 00:20:01 | Original window opens; not a task trigger |
| `Step11-20260907-Observe` | September 14, 7:30 p.m. | September 15, 00:30 | Retrieve and evaluate outcomes for the existing trial |
| Same task, fallback | September 15, 8 a.m. | September 15, 13:00 | Skip verified completion or resume permitted unfinished work |
| `Step11-20260907-DeadlineCheck` | September 15, noon | September 15, 17:00 | Check saved completion and warn locally if unfinished |
| Original hard stop | September 15, 5 p.m. | September 15, 22:00 | Stop incomplete if necessary; do not extend dates or budgets |

The earlier read-only Windows Task Scheduler inspection on September 13 found both tasks
enabled and Ready, with the next runs and fallback matching the table. Neither
production task had run yet. This confirms the installed schedule, not successful
future collection; the September 15 evidence above records the subsequent successful
Observe run. The owner must keep the PC available and remain signed into
Windows; a locked screen is supported. Codex and the dashboard need not be open.
Wake/catch-up is requested but does not guarantee execution while powered off or
logged out. The [11A/11B handoff](../../docs/step-11-automation.md) records the
operational limits, private paths and recovery commands.

After collection, inspect the fresh immutable scientific report and operational
receipts. Require five completed real sessions, matured forecast evidence and
no unresolved source gaps or unscorable/immature forecasts before treating the
observation as complete. A successful scheduler exit alone is insufficient.
If retrieval fails, record the failure and preserved attempts; use only the
existing bounded fallback/manual window. Do not start a replacement trial.
This five-session process trial remains below the 60-session/30-forecast
paper-review evidence floors; its completion does not itself permit promotion.

## Audit inputs after observation

Inspect [11A/11B operational receipts](../../docs/step-11-automation.md) alongside
immutable scientific reports. Audit missed/overlapping/interrupted runs, actual
observation time, preserved account attempts and the original stop window. A
successful task or saved report alone does not establish maturity. Include 11C
restore evidence if available; otherwise record that operational gap. Neither
automation nor a five-session trial waives the paper evidence floors. After review,
disable/remove the expired 11B tasks.

## Finished state

A reproduced final audit records defects, uncertainty, operational responsibilities and the exact paper-policy/stage decision or blockers. It distinguishes engineering readiness from evidence of an edge.

## Implementation and acceptance

META-001 extends the final audit to Steps 01 and 02 migration integrity, FIFO/flow-neutral metrics, dividend receivables, execution-basis separation, opaque Monarchy-only mapping, private field classifications and local server boundaries. Require production replay of the golden vector, not just META-001's reference tests. Preserve the earlier offline rate preflight as a narrow partial gate that can use fixture code before real forward evidence. A private deployment is not a license grant, and reference-account arithmetic is not evidence of profit.

Review the completed implementation against clock barriers, simulated accounting, source rights, public exports, model usage, crash recovery, hard limits, and baseline fairness. Review and record the numeric paper policy under the standing owner delegation; do not request the same permission again. Distinguish engineering readiness from statistical evidence.

Use adversarial cases spanning publication lag, revised filings, splits, stale quotes, repeated runs, unavailable sources, and injected instructions. Record all unresolved limitations. No paper promotion solely because the dashboard looks complete.

Use Step 08 preflight as prior engineering evidence, then assess Step 09/11 rights, measured headroom, quota delays, usage, coverage and prospective outcomes. Reproduce production golden accounting, preserved migrations, mark/null behavior, private export/server boundaries, all-trial retention and matched execution comparisons.

Review numeric paper limits, operational ownership, loss/stop behavior and reconciliation. Record a dated reproduced audit, resolved defects, remaining blockers and the exact owner policy/stage decision where required. Separate engineering suitability for a paper experiment from evidence of profitable reasoning. Insufficient evidence is a valid outcome, and paper readiness never authorizes live capital.

## Validation and handoff

Use the [focused validation workflow](../../docs/development.md). Record changed files, actual checks, evidence artifacts and remaining blockers here. For code changes, run relevant tests and the full suite once after focused checks pass; for UI changes, verify keyboard and narrow/wide layouts too. Original synthetic acceptance never substitutes for required real-source or elapsed-time evidence.

Stop at this step's finished state. The default next item is [Step 13](STEP-13-paper-portfolios.md); do not start it automatically. Follow the queue's blocker rule for independent work. Preserve historical completion claims. No account call, order, paid subscription, public market-data deployment or recurring work is authorized merely by this task brief.
