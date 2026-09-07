"""Finite Step 11 process supervision, outside the frozen research runtime.

Receipts describe execution separately from scientific completion. No credentials,
market values, child stdout or exception messages enter these operational logs.
"""
from contextlib import ExitStack
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from .contracts import ContractError, digest, utc
from .forward.prospective import check_runtime_inputs
from .market_requests import owner_lock


def clock():
    return datetime.now(timezone.utc)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with temporary.open('w', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, path)


def load_config(repo):
    config = read(repo / 'config/step-11-jobs.json')
    if (config['schema_version'] != 1
            or config['manifest_id'] != 'forward:step11-20260907'
            or config['manifest_hash'] != '7329f2a3c468ff419014250997a90fa20fe0c0938b2a40727d268520d9dc2b8a'
            or config['review_at'] != '2026-09-15T00:20:01Z'
            or config['stop_at'] != '2026-09-15T22:00:00Z'
            or not 1 <= config['child_timeout_seconds'] <= 600):
        raise ContractError('Unrecognized finite trial configuration')
    return config


def verified_report(directory, config, *, earliest=None):
    """A pointer/file is evidence only after scope, content and time validation."""
    pointer = read(directory / 'latest-report.json')
    path = Path(pointer['path']).resolve()
    if path.parent != directory.resolve() or path.name != 'report-' + pointer['report_hash'] + '.json':
        raise ContractError('Report pointer escapes its immutable report directory')
    report = read(path)
    if (digest(report) != pointer['report_hash']
            or report['manifest_id'] != config['manifest_id']
            or report['manifest_hash'] != config['manifest_hash']
            or report['review_at'] != config['review_at']
            or report['stop_at'] != config['stop_at']
            or report['broker_orders'] != 0 or report['external_model_calls'] != 0
            or utc(report['as_of']) > clock()
            or earliest is not None and utc(report['as_of']) < earliest):
        raise ContractError('Report is corrupt, out of scope or stale for this invocation')
    complete = (report['status'] == 'window_observed'
                and report['completed_real_sessions'] >= 5
                and report['elapsed_sessions'] >= 5
                and report['matured_forecasts'] >= 1
                and report['immature_forecasts'] == 0
                and report['unscorable_forecasts'] == 0 and not report['gaps'])
    if complete and not utc(config['review_at']) <= utc(report['as_of']):
        raise ContractError('Completion predates the observation window')
    summary = {key: report[key] for key in ('status', 'as_of', 'completed_real_sessions',
               'matured_forecasts', 'immature_forecasts', 'unscorable_forecasts')}
    summary.update(report_hash=pointer['report_hash'], source_gaps=len(report['gaps']), complete=complete)
    return summary


def child(repo, action, timeout):
    # The existing coordinator owns all account budgets, caching and crash recovery.
    # No outer retry loop; stdout/stderr can contain private diagnostics, so discard.
    process = subprocess.Popen([sys.executable, str(repo / 'scripts/run_step_11.py'), action],
        cwd=repo, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    try:
        return process.wait(timeout=timeout)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def notify_owner():
    """One bounded local warning; no email, AI, secrets, or remote destination."""
    if os.name != 'nt':
        return False
    command = "$w=New-Object -ComObject WScript.Shell; $null=$w.Popup('Trade Theorist Step 11 needs attention. Check the private step-11-operations folder and docs/step-11-automation.md.',20,'Trade Theorist',48)"
    try:
        result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-WindowStyle',
            'Hidden', '-Command', command], timeout=30, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def run_job(repo, private, action, *, notify=False):
    if action not in ('observe', 'report', 'check'):
        raise ValueError('Only observe, report and check are supported')
    repo, private = Path(repo).resolve(), Path(private).resolve()
    operations = private / 'step-11-operations'
    directory = private / 'step-11-forward'
    run_id = uuid.uuid4().hex
    run_dir = operations / 'runs' / run_id
    started = clock()
    began = time.monotonic()
    receipt = dict(schema_version=1, run_id=run_id, action=action,
                   started_at=started.isoformat(), pid=os.getpid(),
                   # Identity stays private. It helps diagnose the wrong scheduled account.
                   windows_user=os.environ.get('USERNAME'), private_root=str(private))
    atomic(run_dir / 'start.json', receipt)
    log_path = run_dir / 'run.log'

    def log(label):
        line = label + ' ' + clock().isoformat()
        with log_path.open('a', encoding='utf-8') as handle:
            handle.write(line + '\n'); handle.flush(); os.fsync(handle.fileno())
        if sys.stdout is not None:
            print(line, flush=True)

    log('start')
    code, status, acquired = 1, 'error', False
    with ExitStack() as stack:
        try:
            try:
                stack.enter_context(owner_lock(operations / 'launcher.lock'))
                acquired = True
            except OSError:
                code, status = 4, 'overlap'
            if acquired:
                # An abrupt shutdown can leave a start with no end. Preserve that
                # fact and mark recovery separately instead of fabricating an end.
                interrupted = [p.parent.name for p in (operations / 'runs').glob('*/start.json')
                               if p.parent != run_dir and not (p.parent / 'receipt.json').exists()]
                receipt['previous_unfinished_runs'] = sorted(interrupted)
                receipt['stage'] = 'configuration'
                config = load_config(repo)
                receipt['config_hash'] = digest(config)
                manifest = read(directory / 'manifest.json')
                if manifest['id'] != config['manifest_id'] or digest(manifest) != config['manifest_hash']:
                    raise ContractError('Frozen manifest differs')
                receipt['stage'] = 'frozen_inputs'
                check_runtime_inputs(repo, manifest)
                receipt['stage'] = 'existing_report'
                summary = verified_report(directory, config)
                receipt['report'] = summary
                now = clock()
                if summary['complete']:
                    code, status = 0, 'already_complete'
                elif action == 'check':
                    code, status = 2, 'attention_required'
                elif action == 'observe' and now < utc(config['review_at']):
                    code, status = 0, 'not_due'
                elif action == 'observe' and now >= utc(config['stop_at']):
                    code, status = 3, 'expired'
                else:
                    child_started = clock()
                    receipt['stage'] = 'child'
                    timeout = config['child_timeout_seconds']
                    if action == 'observe':
                        timeout = min(timeout, (utc(config['stop_at']) - child_started).total_seconds())
                        if timeout <= 0:
                            raise ContractError('Observation deadline reached')
                    receipt['child_exit_code'] = child(repo, action, timeout)
                    if receipt['child_exit_code'] != 0:
                        code, status = 1, 'child_failed'
                    else:
                        receipt['stage'] = 'fresh_report'
                        summary = verified_report(directory, config, earliest=child_started)
                        receipt['report'] = summary
                        attempts = read(directory / 'transport-attempts-latest.json')
                        receipt['transport_attempts'] = len(attempts)
                        if action == 'report' and attempts:
                            raise ContractError('Read-only rehearsal made account requests')
                        if summary['complete']:
                            code, status = 0, 'observed'
                        elif action == 'report':
                            code, status = 0, 'report_only'
                        else:
                            code, status = 2, 'incomplete'
        except subprocess.TimeoutExpired:
            code, status = 1, 'timeout'
        except Exception as exc:
            receipt['error_type'] = type(exc).__name__
            code, status = 1, 'error'
        finally:
            receipt.update(status=status, exit_code=code, ended_at=clock().isoformat(),
                           duration_seconds=round(time.monotonic() - began, 3))
            if acquired:
                if code:
                    try:
                        previous = read(operations / 'attention.json')
                    except (OSError, ValueError):
                        previous = {}
                    # A successful read-only probe never clears an unresolved alert.
                    alert_key = [status, receipt.get('report', {}).get('report_hash')]
                    warned = notify and (previous.get('alert_key') != alert_key or not previous.get('notified'))
                    receipt['notification_display_requested'] = bool(warned)
                    if warned:
                        receipt['notification_command_succeeded'] = notify_owner()
                    atomic(operations / 'attention.json', dict(run_id=run_id, status=status,
                           alert_key=alert_key, at=receipt['ended_at'], resolved=False,
                           notified=receipt.get('notification_command_succeeded', False)
                           or (previous.get('alert_key') == alert_key and previous.get('notified', False))))
                elif status in ('observed', 'already_complete'):
                    atomic(operations / 'attention.json', dict(run_id=run_id, resolved=True,
                           at=receipt['ended_at']))
                atomic(operations / 'latest.json', receipt)
            atomic(run_dir / 'receipt.json', receipt)
            log('end')
    return code
