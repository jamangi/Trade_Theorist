# Step 11B: Schedule the existing observation window on Windows

- Status: implemented and installed 2026-09-07; actual scheduler rehearsal passed.
- Recommended model / effort: Sol / medium.
- Queue: [ordered roadmap](../README.md); early bounded part of [TASK-020](../TASK-020-medium-Sol.md).
- Starting evidence: [11A](STEP-11A-run-observability.md), the existing frozen trial, and the owner's explicit September 7 request to implement 11A/11B.

## Purpose and finished state

Remove the need to remember a narrow manual observation window. Register two
finite Windows tasks under the owner's normal account and prove a read-only
launch through Task Scheduler itself. Preserve the Step 11 dates and budgets.

## Scope and acceptance

Use the [checked configuration](../../config/step-11-jobs.json): primary observation
September 14 at 7:30 p.m. Chicago; fallback September 15 at 8 a.m.; independent
local deadline check September 15 at noon. Stop at September 15 at 5 p.m. Chicago.
Fallback continues only unfinished work within the existing request budget.
No recurring trigger, new forecast, new decision or new trial window is allowed.

Use absolute executable/working/data paths, the same account quota owner, an
interactive limited principal, wake and missed-start settings, overlap prevention,
and a task execution limit. Verify exported trigger instants against configuration.
Keep a private installation plan and scheduled-run evidence; refuse unrelated
task-name collisions. Reinstallation must update owned tasks without duplication.

The actual scheduled account must load the real frozen inputs and create a fresh
report without requests. Local warnings and nonzero task results expose failures;
unchanged failures suppress repeated warnings. Retain a manual launcher and an
explicit disable/recovery runbook.

## Implementation and limits

[Installer](../../scripts/install_step_11_tasks.ps1) defaults to preview; `-Install`
registers the finite jobs, and `-Verify` runs and removes a temporary report task.
The two production tasks are installed. [Recorded status](../../examples/step-11/automation-status.json)
and the [runbook](../../docs/step-11-automation.md) contain acceptance evidence.

Actual acceptance: September 7 at 13:13 UTC, Windows Task Scheduler returned 0
for a fresh `report_only` run with zero transport attempts under the installed
account. Exported production triggers match 00:30/13:00/17:00 UTC and expire at
22:00 UTC. Reinstallation updated owned jobs without duplicates; the temporary
verification task was removed. The 363-test suite and clean offline installation
check passed. No future observation or physical sleep/wake test is claimed.

The owner must remain signed into Windows; locking the screen is fine. Wake is
requested but depends on machine power settings/hardware. No powered-off or
logged-out execution, reboot-without-sign-in recovery, external monitoring or
off-machine notification is claimed. These remain Step 15 design work. The Codex
app and a dashboard need not be open. The scheduled Python process makes no AI calls.

## Handoff

Allow Step 11's real window to elapse. Step 12 reviews outcomes and disables or
removes these expired tasks. Step 11C and eligible Step 14 work can proceed during
the wait; they do not bypass Step 12. General recurrence stays in Step 15.
