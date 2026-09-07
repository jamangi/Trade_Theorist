<#
Preview by default; -Install registers only the finite observation/check jobs.
-Verify runs a temporary read-only job through Windows Task Scheduler and removes
that verification task afterward. Run as the owner, never as SYSTEM or a sandbox
identity. No password is requested or stored. See docs/step-11-automation.md.
#>
[CmdletBinding()]
param([switch]$Install, [switch]$Verify)
$ErrorActionPreference = 'Stop'
Import-Module ScheduledTasks
$repoRoot = Split-Path -Parent $PSScriptRoot
$config = Get-Content -LiteralPath (Join-Path $repoRoot 'config/step-11-jobs.json') -Raw | ConvertFrom-Json
function As-Instant($value) {
    # PowerShell 7.5+ decodes ISO JSON timestamps to DateTime automatically.
    # Parsing that object's culture-formatted string would silently lose UTC.
    if ($value -is [DateTime]) { return [DateTimeOffset]$value }
    return [DateTimeOffset]::Parse([string]$value, [Globalization.CultureInfo]::InvariantCulture)
}
$python = Join-Path $repoRoot '.venv/Scripts/pythonw.exe'
$pythonConsole = Join-Path $repoRoot '.venv/Scripts/python.exe'
$launcher = Join-Path $PSScriptRoot 'run_step_11_job.py'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($identity.IsSystem -or $identity.Name -match 'codexsandbox') { throw 'Run this installer as the Windows owner.' }
if (-not (Test-Path -LiteralPath $python)) { throw 'The repository virtual environment is missing.' }
& $pythonConsole -c 'from pathlib import Path; from trade_theorist.observation_job import load_config; import sys; load_config(Path(sys.argv[1]))' $repoRoot
if ($LASTEXITCODE -ne 0) { throw 'Invalid finite trial configuration.' }
if ($config.logon_type -ne 'InteractiveToken' -or $config.task_path -ne '\TradeTheorist\' -or $config.task_prefix -ne 'Step11-20260907') {
    throw 'Unexpected task namespace or principal type.'
}
$end = As-Instant $config.stop_at
if ($Install -and [DateTimeOffset]::UtcNow -ge $end) { throw 'This trial has expired; do not install a replacement window.' }
$principal = New-ScheduledTaskPrincipal -UserId $identity.Name -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 12)
$marker = 'TradeTheorist finite step11-20260907; managed by scripts/install_step_11_tasks.ps1'
$planRoot = Join-Path $repoRoot '.local/step-11-task-plan'
New-Item -ItemType Directory -Path $planRoot -Force | Out-Null
$environmentPath = Join-Path $planRoot 'environment.json'
if (Test-Path -LiteralPath $environmentPath) {
    $localData = (Get-Content -LiteralPath $environmentPath -Raw | ConvertFrom-Json).local_app_data
} else {
    $localData = & $pythonConsole -c 'import os; from pathlib import Path; p=Path(os.environ["LOCALAPPDATA"])/"TradeTheorist/alpaca-market-data/step-11-forward/manifest.json"; print(p.resolve(strict=True).parents[3])'
    if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve the existing trial manifest.' }
    @{local_app_data=$localData} | ConvertTo-Json | Set-Content -LiteralPath $environmentPath -Encoding utf8
}

function New-Definition([string]$actionName, [object[]]$times, [bool]$notify) {
    $arguments = '"' + $launcher + '" ' + $actionName + ' --local-app-data "' + $localData + '"'
    if ($notify) { $arguments += ' --notify' }
    $action = New-ScheduledTaskAction -Execute $python -Argument $arguments -WorkingDirectory $repoRoot
    $triggers = @($times | ForEach-Object {
        $when = As-Instant $_
        if ($when -lt (As-Instant $config.review_at) -or $when -ge $end) { throw 'Trigger outside the existing window.' }
        $trigger = New-ScheduledTaskTrigger -Once -At $when.LocalDateTime
        # Explicit offsets preserve these exact instants across host time zones/DST.
        $trigger.StartBoundary = $when.ToLocalTime().ToString('yyyy-MM-ddTHH:mm:sszzz')
        $trigger.EndBoundary = $end.ToLocalTime().ToString('yyyy-MM-ddTHH:mm:sszzz')
        $trigger
    })
    if ($triggers.Count) {
        New-ScheduledTask -Action $action -Trigger $triggers -Principal $principal -Settings $settings -Description $marker
    } else {
        New-ScheduledTask -Action $action -Principal $principal -Settings $settings -Description $marker
    }
}

function Register-Owned([string]$name, $definition) {
    $existing = Get-ScheduledTask -TaskPath $config.task_path -TaskName $name -ErrorAction SilentlyContinue
    if ($existing) {
        $existingUser = $existing.Principal.UserId
        if ($existingUser -notmatch '^S-1-') { $existingUser = ([Security.Principal.NTAccount]$existingUser).Translate([Security.Principal.SecurityIdentifier]).Value }
        if ($existing.Description -ne $marker -or $existingUser -ne $identity.User.Value) {
            throw "Refusing to replace an unrelated task: $name"
        }
    }
    Register-ScheduledTask -TaskPath $config.task_path -TaskName $name -InputObject $definition -Force | Out-Null
}

$definitions = [ordered]@{}
$definitions[$config.task_prefix + '-Observe'] = New-Definition 'observe' $config.observe_at $true
$definitions[$config.task_prefix + '-DeadlineCheck'] = New-Definition 'check' @($config.check_at) $true
foreach ($entry in $definitions.GetEnumerator()) {
    [ordered]@{ name=$entry.Key; principal=$identity.Name; logon_type='InteractiveToken';
        executable=$python; arguments=$entry.Value.Actions.Arguments; working_directory=$repoRoot;
        start_boundaries=@($entry.Value.Triggers.StartBoundary); end_boundary=$config.stop_at;
        wake_to_run=$true; start_when_available=$true; overlap='IgnoreNew'; timeout_minutes=12
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $planRoot ($entry.Key + '.json')) -Encoding utf8
}
Write-Output ('Prepared finite task definitions for ' + $identity.Name + '; interactive sign-in required.')
if (-not $Install -and -not $Verify) { return }
$service = New-Object -ComObject Schedule.Service
$service.Connect()
try { $null = $service.GetFolder($config.task_path.TrimEnd('\')) }
catch { $null = $service.GetFolder('\').CreateFolder('TradeTheorist') }
if ($Install) {
    foreach ($entry in $definitions.GetEnumerator()) {
        Register-Owned $entry.Key $entry.Value
        $exported = Export-ScheduledTask -TaskPath $config.task_path -TaskName $entry.Key
        $exported | Set-Content -LiteralPath (Join-Path $planRoot ($entry.Key + '.xml')) -Encoding utf8
        [xml]$actual = $exported
        $configuredTimes = if ($entry.Key.EndsWith('-Observe')) { $config.observe_at } else { @($config.check_at) }
        $expectedTimes = @($configuredTimes | ForEach-Object { (As-Instant $_).ToUniversalTime().ToString('o') })
        $actualTimes = @($actual.Task.Triggers.TimeTrigger | ForEach-Object { [DateTimeOffset]::Parse($_.StartBoundary).ToUniversalTime().ToString('o') })
        if (Compare-Object $expectedTimes $actualTimes) {
            Disable-ScheduledTask -TaskPath $config.task_path -TaskName $entry.Key | Out-Null
            throw 'Windows changed the trigger instants; task disabled.'
        }
        foreach ($trigger in $actual.Task.Triggers.TimeTrigger) {
            if ([DateTimeOffset]::Parse($trigger.EndBoundary) -ne $end) {
                Disable-ScheduledTask -TaskPath $config.task_path -TaskName $entry.Key | Out-Null
                throw 'Windows changed the task deadline; task disabled.'
            }
        }
    }
    Write-Output 'Installed two finite tasks: two observation triggers and one deadline check. No recurring trigger.'
}
if ($Verify) {
    $testName = $config.task_prefix + '-Verify'
    $testDefinition = New-Definition 'report' @() $false
    Register-Owned $testName $testDefinition
    $before = [DateTime]::Now
    try {
        Start-ScheduledTask -TaskPath $config.task_path -TaskName $testName
        $deadline = [DateTime]::Now.AddSeconds(90)
        do {
            Start-Sleep -Seconds 2
            $task = Get-ScheduledTask -TaskPath $config.task_path -TaskName $testName
            $info = Get-ScheduledTaskInfo -TaskPath $config.task_path -TaskName $testName
        } until (($info.LastRunTime -ge $before.AddSeconds(-1) -and $task.State -notin @('Running','Queued') -and $info.LastTaskResult -ne 267009) -or [DateTime]::Now -ge $deadline)
        if ($info.LastRunTime -lt $before.AddSeconds(-1) -or $task.State -in @('Running','Queued') -or $info.LastTaskResult -ne 0) {
            throw "Scheduled rehearsal failed: result=$($info.LastTaskResult), state=$($task.State), last_run=$($info.LastRunTime). Inspect private logs."
        }
        $operations = Join-Path $localData 'TradeTheorist/alpaca-market-data/step-11-operations'
        $receipt = Get-Content -LiteralPath (Join-Path $operations 'latest.json') -Raw | ConvertFrom-Json
        if ($receipt.action -ne 'report' -or $receipt.status -notin @('report_only', 'already_complete') -or
            (As-Instant $receipt.started_at).LocalDateTime -lt $before.AddSeconds(-1) -or
            $receipt.windows_user -ne $env:USERNAME -or $receipt.transport_attempts -gt 0) {
            throw 'The scheduled receipt does not match this zero-request rehearsal.'
        }
        $evidence = [ordered]@{ verified_at = [DateTimeOffset]::UtcNow.ToString('o'); run_id = $receipt.run_id;
            last_task_result = $info.LastTaskResult; logon_type = 'InteractiveToken'; status = $receipt.status;
            config_hash = $receipt.config_hash; transport_attempts = $receipt.transport_attempts }
        $evidence | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $operations 'scheduler-verification.json') -Encoding utf8
        Write-Output ($evidence | ConvertTo-Json -Compress)
    } finally {
        Stop-ScheduledTask -TaskPath $config.task_path -TaskName $testName -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskPath $config.task_path -TaskName $testName -Confirm:$false
    }
}
