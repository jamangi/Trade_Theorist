# Step 12 handoff after scheduled collection

> **Superseded by the [completed Step 12 audit](step-12-readiness-audit.md),
> September 15, 2026.** Paper promotion is held; the finite tasks were disabled
> after review at 10:18 UTC, before their redundant remaining triggers. The
> original handoff below preserves the evidence locations and earlier status.

Verified September 15, 2026, at approximately 04:55 Chicago time. **Step 11's
data collection is complete. Step 12, the readiness audit, is the next task.**
Read [the active Step 12 brief](../tasks/active/STEP-12-readiness-audit.md) for its
full acceptance criteria. No conversational history is needed to locate the
scheduled jobs or the evidence described here.

## What actually ran

Windows task `\TradeTheorist\Step11-20260907-Observe` ran September 14 at
19:30 Chicago / September 15 at 00:30 UTC and returned result 0. The private
launcher receipt records `observed`, two transport attempts, no previous
unfinished launcher runs, and completion at 00:31:03.882539 UTC after 62.312 seconds.
The immutable scientific report is dated 00:31:03.279016 UTC.

The [public completion evidence](../examples/step-11/observation-completion.json)
contains scheduler results, original run identity, manifest/report hashes and
verification counts. The [scheduler-produced forward status](../examples/step-11/forward-status.json)
matches the verified private report:

- Five completed real sessions: September 8, 9, 10, 11 and 14.
- One matured forecast; zero immature or unscorable forecasts; zero source gaps.
- No broker orders or external model calls.
- `promotion_eligible: false`, `evidence_grade: forward-insufficient`.

The frozen report still contains its original `automatic_continuation: false`
and "No unattended continuation" wording. Those fields are hardcoded in the
original runtime and predate the 11B Windows wrapper; they are not scheduler
status. Use the actual task results and launcher receipts to establish that this
finite automated observation ran. Preserve the original report rather than
editing its scientific evidence to update those operational labels.

The September 15 check verified the report hash, frozen manifest/runtime/learning
inputs, original successful launcher receipt, database hash chains/references and
report-to-store accounting. It replayed all 35 stored performance results against
their ledgers. The store contained 248 v2 records and 11 accounted requests across
its existing workloads; those totals are not the trial's request budget. This
verification used read-only database access with Python network connections
blocked and made no new provider/model calls. It is evidence verification, not
the full adversarial Step 12 audit.

## Start here in a new task

1. Read the active Step 12 brief, this handoff, the completion evidence and the
   [11A/11B operating guide](step-11-automation.md). The latter describes task
   installation, private-path binding, failure receipts, sign-in requirements and
   cleanup. Steps 11A/11B/11C are implemented; Step 11 has now observed its window.
2. Inspect current scheduler state. The captured September 15 status is historical
   evidence; it is not a live monitor. The commands below only inspect Windows.
3. Verify the saved report through the existing launcher `check` command. For the
   already verified completed trial, it should return 0 and record
   `already_complete`, without starting a child collector or making requests.
   This command writes an operational receipt; preserve the original observation
   receipt separately. If it fails, investigate saved evidence and frozen inputs.
   Do not run `start`, replace the manifest, reset quotas or launch a new trial.
4. Read the immutable private scientific report and trace its records to the
   existing SQLite store. Use the private paths below; never copy raw bars,
   positions, returns or credentials into Git. Reproduce the audit requirements
   in the active brief and publish only reviewed summaries/counts/hashes.
5. Record the Step 12 decision and blockers. Review numeric paper limits and
   record the owner's policy/stage decision where required. The five-session,
   one-forecast trial remains below the 60-session/30-forecast evidence floors.
   A finding of insufficient evidence is valid. Do not start Step 13 automatically
   or treat engineering success as evidence of an edge or live-capital authority.

From the existing Trade Theorist checkout under the owner's Windows account:

```powershell
Get-ScheduledTask -TaskPath '\TradeTheorist\'
Get-ScheduledTaskInfo -TaskPath '\TradeTheorist\' -TaskName 'Step11-20260907-Observe'
Get-ScheduledTaskInfo -TaskPath '\TradeTheorist\' -TaskName 'Step11-20260907-DeadlineCheck'
.venv/Scripts/python.exe scripts/run_step_11_job.py check
```

Scheduler inspection may require elevated read access. If the task is running,
allow its bounded operation to finish before inspecting the final receipt; do not
remove locks or start a second account owner. No provider credentials are needed
to inspect the saved evidence.

## Locate the private evidence reliably

The launcher reads the gitignored `.local/step-11-task-plan/environment.json`
field `local_app_data`. This is the installed task's resolved existing data root.
Windows packaged-app redirection means a fresh process's default
`%LOCALAPPDATA%` may select the wrong folder. Do not relocate or copy the live
database to work around that difference.

If the local plan is absent in a new checkout, inspect the installed Observe
task's action and use its `--local-app-data` value with the launcher. If both
the plan and task are absent, locate and verify the original installation or
follow the recovery runbook; do not initialize a replacement account owner.

```powershell
(Get-ScheduledTask -TaskPath '\TradeTheorist\' -TaskName 'Step11-20260907-Observe').Actions
# Only when the local plan is absent; use the actual installed action's value:
.venv/Scripts/python.exe scripts/run_step_11_job.py check --local-app-data <resolved-existing-root>
```

Under that resolved root, use `TradeTheorist/alpaca-market-data/`:

| Relative location | Evidence |
| --- | --- |
| `research.sqlite3` | Existing private records, request state and accounting ledger |
| `step-11-forward/manifest.json` | Original frozen trial; hash pinned in completion evidence and job configuration |
| `step-11-forward/latest-report.json` | Current pointer; verify content hash and scope before trusting it |
| `step-11-forward/report-<report-hash>.json` | Immutable scientific report identified by completion evidence |
| `step-11-operations/runs/274a4dbb95cc4ee49da4fbe1ee914b71/` | Original scheduled observation's `start.json`, `run.log`, and `receipt.json` |
| `step-11-operations/latest.json` | Latest launcher result; later checks/fallback may replace this pointer |
| `step-11-operations/attention.json` | Current local warning/resolution state |

Read `verified_report` in `src/trade_theorist/observation_job.py` for report
verification and `database_evidence` in `src/trade_theorist/private_backup.py`
for read-only chain/reference verification and stored accounting replay. The
full Step 12 review still needs golden accounting, adversarial checks, rights,
privacy, migrations, baseline fairness, ownership and policy decisions.

## Remaining scheduled work and recovery limits

At inspection, the Observe fallback at **September 15, 08:00 Chicago** and
DeadlineCheck at **12:00 Chicago** were still enabled and had not occurred.
With valid completed evidence, both should verify completion and skip collection.
That behavior is defined by the launcher; these future runs have not been claimed
as successful. The hard stop remains **17:00 Chicago / 22:00 UTC** that day.
This handoff did not change or disable either task. After the Step 12 review,
disable/remove the expired tasks using the operating guide; check for running
work separately before removal. No general recurring job has been installed.

[Local recovery](step-11-private-backups.md) and
[encrypted remote recovery](step-11-remote-recovery.md) were verified September 7.
Those dated snapshots predate this observation; they do not prove that September
14's new evidence is remotely backed up. Review backup freshness as an operational
gap during Step 12. A new verified remote backup requires the separate attended
FIDO PIN-and-touch procedure. No new backup or restored-account activation was
performed by this status check.
