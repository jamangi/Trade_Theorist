# Step 11 automation and fresh-session handoff

Updated September 7, 2026. The owner requested repository briefs, roadmap updates,
implementation of 11A/11B and publication to main. 11A and 11B are implemented;
the two finite Windows tasks are installed and a real scheduled report rehearsal
passed. Step 11 remains in progress with zero completed future sessions. See
[trial status](../examples/step-11/forward-status.json),
[automation status](../examples/step-11/automation-status.json), and
[the roadmap](../tasks/README.md). Saved status files are dated evidence, not a live
monitor. This document is the operational authority for the new launcher.

## What runs, and when

The app does not need to run all day. Native Windows Task Scheduler starts an
ordinary local Python process for each of these finite triggers. Neither Codex
nor the private dashboard needs to be open. No Codex agent polls through the day.

| Task under `\TradeTheorist\` | Chicago time | UTC | Action |
| --- | --- | --- | --- |
| `Step11-20260907-Observe` | September 14, 2026, 7:30 p.m. | September 15, 00:30 | Observe the existing trial |
| Same task, fallback trigger | September 15, 8 a.m. | September 15, 13:00 | Skip verified completion; otherwise resume only permitted unfinished work |
| `Step11-20260907-DeadlineCheck` | September 15, noon | September 15, 17:00 | Verify saved completion; warn locally if unfinished, with five hours left |

The frozen observation window is September 15, **00:20:01–22:00 UTC**. Triggers
expire at its end. Late observation launches return `expired` without downloading
or extending the trial. Catch-up requests use the same boundaries and existing
durable quota owner. There is no weekly schedule, scheduler restart loop, new
recommendation or reset of the original twelve-attempt trial budget. The fallback
may have no attempts remaining; it cannot manufacture another allowance.

The current scientific runtime applies deterministic foundation-informed rules.
These jobs make **zero external model calls** and submit **zero broker orders**.
AI development/reading usage is separate and was not measured as runtime spend.
A future AI runtime requires its own recorded model/version, knowledge/tool
boundary, prompt, call/token/cost ceilings and prospective validation before it
is enabled. Step 15 must not silently turn this trial into recurring AI deliberation.

## Human contact and practical limits

- Keep the PC available and your Windows account signed in through the window.
  A locked screen is supported. Wake timers are requested; sleep/wake behavior
  depends on Windows power settings and hardware and has not been physically tested.
- After a reboot, sign in. A powered-off machine cannot run these local jobs.
  `StartWhenAvailable` requests catch-up after missed starts, still subject to
  the original deadline. Full service operation without sign-in stays in Step 15.
- Changed failures request a 20-second local warning and leave a durable private
  `attention.json` plus a nonzero Task Scheduler result. A warning may be missed
  while the screen is locked. No email, off-machine monitor or alert during a
  total host failure is installed; check the saved result after the window.
- Fix exceptional failures such as unavailable credentials, a missing environment,
  lost connectivity or changed frozen inputs. The ordinary successful run needs
  no human click. Review the scientific evidence and Step 12's decision afterward.
  Governance, scope/budget changes and live-capital authority remain human decisions.

## Private paths, evidence and process semantics

The installer pins the **actual existing** private root in the gitignored
`.local/step-11-task-plan/environment.json` and in each task action. Windows can
redirect files created inside a packaged app into its `LocalCache`; using an
unresolved `%LOCALAPPDATA%` outside Codex initially reached a different directory.
The installer resolves the existing manifest file, and the launcher explicitly
sets the same data/profile root for its child and the quota-owner registry.
No database was copied or new quota owner created to solve this difference.
Do not relocate this installation while the trial is active.

Under that pinned root's `TradeTheorist/alpaca-market-data/`:

| Location | Meaning |
| --- | --- |
| `step-11-forward/manifest.json` | Original frozen trial |
| `step-11-forward/report-<hash>.json` | Immutable private scientific report |
| `step-11-forward/latest-report.json` | Pointer to the latest report, verified against its content |
| `step-11-operations/runs/<run-id>/run.log` | Flushed `start <UTC date>` and `end <UTC date>` lines |
| Same run directory, `start.json` / `receipt.json` | Start, final status, elapsed seconds, phase, exit code, report hash and counts |
| `step-11-operations/latest.json` | Most recent lock-owning launcher result |
| `step-11-operations/attention.json` | Unresolved operational warning or verified resolution |
| `step-11-operations/scheduler-verification.json` | Actual zero-request scheduled rehearsal evidence |

All these files are private and outside Git. `.local/` is also gitignored; it holds
installation plans and exported task XML. Operational receipts exclude market
values, credentials and raw child output. Detailed scientific reports remain private.

An exit-zero process with an in-progress report does **not** mean the experiment
finished. Completion requires a content-hash-verified report for the pinned manifest,
five completed real sessions, matured forecast evidence and no source gaps or
unscorable/immature forecasts. A newly invoked child must produce a fresh report.
A previously verified complete report permits a zero-request skip.

| Exit code | Interpretation |
| --- | --- |
| 0 | `observed`, `already_complete`, `report_only`, or `not_due`; inspect the status to distinguish these |
| 1 | Configuration/input/report error, child failure or timeout |
| 2 | Incomplete observation or deadline check requiring attention |
| 3 | Observation window expired |
| 4 | Another launcher owns the lock; no child launched |

A start without a final receipt means abrupt interruption, not success. The next
lock owner lists unfinished run IDs without fabricating their end times. OS locks
release after process death; the existing account coordinator independently rejects
overlapping owners and preserves spent attempts/checkpoints. A killed launcher
can briefly leave its child running; the coordinator continues to protect account
ownership. Do not delete locks or quota files to force a retry. The wrapper kills
and reaps its direct child on a normal timeout; the Windows task also has a
twelve-minute execution limit. No general process/service recovery is claimed.

## Commands and recovery

From the repository, using the owner's Windows account:

```powershell
# Inspect without account requests; produces a logged fresh report.
.venv/Scripts/python.exe scripts/run_step_11_job.py report
# Manually continue only within the original window; no new trial is possible.
.venv/Scripts/python.exe scripts/run_step_11_job.py observe
# Check saved evidence and optionally show a local warning.
.venv/Scripts/python.exe scripts/run_step_11_job.py check --notify
# Preview task definitions, then install/update owned tasks or verify a report.
./scripts/install_step_11_tasks.ps1
./scripts/install_step_11_tasks.ps1 -Install -Verify
Get-ScheduledTask -TaskPath '\TradeTheorist\'
Get-ScheduledTaskInfo -TaskPath '\TradeTheorist\' -TaskName 'Step11-20260907-Observe'
# Stop future automatic starts; inspect any currently running work separately.
Disable-ScheduledTask -TaskPath '\TradeTheorist\' -TaskName 'Step11-20260907-Observe'
Disable-ScheduledTask -TaskPath '\TradeTheorist\' -TaskName 'Step11-20260907-DeadlineCheck'
```

Disabling a task does not terminate an active process. If immediate cancellation
is necessary, use `Stop-ScheduledTask` for that exact task; inspect receipts and
existing coordinator recovery before resuming. Reinstalling re-enables these
owned finite tasks. It refuses installation after the original stop time. The
temporary verification task is removed after each rehearsal. Expired production
tasks remain inspectable until Step 12 disables/removes them; there is no later trigger.

Preserve the frozen runtime and knowledge/qualification inputs. Their current
hashes are checked before launching. Continue independent development in files
outside that set or in another checkout. If a frozen input changed accidentally,
restore the original from its recorded version; do not update the manifest hash
to make an altered experiment pass. Never run `start` to recover this observation.

## Acceptance evidence and next work

The actual scheduled `report` finished September 7 at 13:13 UTC with Task Scheduler
result 0, `report_only`, zero transport attempts and a fresh private report. This
proved account identity, interpreter, working directory, private file access,
frozen-input verification and report production outside Codex. It did not test
future market availability, power-off recovery, sleep/wake hardware or maturity.

The rehearsal found and fixed packaged-app data redirection, PowerShell's automatic
JSON timestamp conversion losing UTC on string coercion, and a scheduler-status
race during completion checks. Exported trigger instants are now checked against
the configured instants, including the original stop time.

Final validation passed: **363 tests across 36 modules**, including 21 launcher
tests; 1,983 classified schema fields; 245 changed-document local file links;
and the clean offline installed-package check. The frozen trial runtime, knowledge
and qualification inputs are unchanged. The dated automation-status artifact
records the same evidence. [11C](step-11-private-backups.md) now provides a verified
local snapshot and isolated offline restore with preserved quotas and reconciled
accounting. [Remote recovery](step-11-remote-recovery.md) is also verified using
the existing Lightsail server and both PIN-and-touch FIDO keys. No recurring
backup is configured.
Step 14 may work with stored evidence during the wait. Step 12 still requires real
outcomes and retains its paper gates. Steps 13/15 reuse these receipts and request
controls; Step 15 owns general repetition, holiday/session handling, service
recovery, remote monitoring, recurring backup and future model budgets.
