"""Private, finite snapshots and offline recovery. No account or network client.

The database is restored as evidence.sqlite3, never as a runnable quota owner.
The original registry bindings remain evidence; activation is a separate review.
"""
from contextlib import ExitStack, closing, contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import subprocess
import time
import uuid

from .contracts import ContractError, digest
from .market_requests import owner_lock
from .observation_job import atomic, read
from .storage_v2 import V2Store


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def inside(root, name):
    """Accept only canonical relative paths, including on Windows."""
    p = PurePosixPath(name)
    if (not name or '\\' in name or ':' in name or p.is_absolute()
            or any(x in ('', '.', '..') for x in name.split('/'))):
        raise ContractError('Unsafe backup path')
    target = root.joinpath(*p.parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ContractError('Backup path escapes root')
    if any(x.is_symlink() or getattr(x, 'is_junction', lambda: False)()
           for x in (target, *target.parents) if x.is_relative_to(root)):
        raise ContractError('Backup links are forbidden')
    return target


def private_directory(path, *, synthetic=False):
    path = Path(path).resolve()
    if not synthetic and any((p / '.git').exists() for p in (path, *path.parents)):
        raise ContractError('Real backup and restore storage must be outside Git')
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not synthetic and os.name == 'nt':
        # Protect only the explicitly selected backup/recovery root, never source data.
        identity = subprocess.check_output(['whoami', '/user', '/fo', 'csv', '/nh'], text=True)
        import csv
        sid = next(csv.reader([identity.strip()]))[1]
        subprocess.run(['icacls', str(path), '/inheritance:r', '/grant:r',
                        '*' + sid + ':(OI)(CI)F', '*S-1-5-18:(OI)(CI)F'],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif not synthetic:
        path.chmod(0o700)
    return path


@contextmanager
def readonly(path):
    connection = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA query_only=ON')
    try:
        yield connection
    finally:
        connection.close()


def online_snapshot(source, destination, *, timeout=60, progress=None):
    """SQLite's online API includes committed WAL data, with a bounded deadline."""
    started = time.monotonic()
    def tick(status, remaining, total):
        if time.monotonic() - started > timeout:
            raise TimeoutError('Snapshot deadline exceeded')
        if progress:
            progress(status, remaining, total)
    with readonly(source) as src, closing(sqlite3.connect(destination)) as dst:
        src.backup(dst, pages=64, progress=tick, sleep=0.01)
        # The isolated snapshot is one durable file; opening it for verification
        # must not create WAL/SHM sidecars that change the payload inventory.
        dst.execute('PRAGMA journal_mode=DELETE')
    with destination.open('r+b') as handle:
        os.fsync(handle.fileno())


def database_evidence(path):
    """Verify original hash chains/references and replay accounting without writes."""
    from .adapters.trader_user_sim.v2 import SimulatorV2
    from .evaluate.portfolio_v2 import number
    with readonly(path) as connection:
        store = V2Store.__new__(V2Store)
        store.connection = connection
        result = store.verify()
        if list(connection.execute('PRAGMA foreign_key_check')):
            raise ContractError('Broken database references')
        tables = [r[0] for r in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'market_%' ORDER BY name")]
        # Preserve every quota, attempt, subscriber, page and checkpoint value.
        result['request_state'] = {name: digest([list(r) for r in connection.execute(
            'SELECT * FROM "' + name.replace('"', '""') + '" ORDER BY rowid')]) for name in tables}
        result['accounted_attempts'] = connection.execute('SELECT COUNT(*) FROM market_attempts').fetchone()[0]
        count = 0
        for report in store.iter_v2(kind='performance_result'):
            state, _ = SimulatorV2(store, report['portfolio_id']).state(
                effective_cutoff=report['effective_cutoff'], receipt_cutoff=report['receipt_cutoff'])
            for field, value in dict(cash=state.cash, reserved=state.reserved,
                                     fifo_basis=state.basis, realized=state.realized,
                                     income=state.income, fees=state.fees).items():
                if report[field] != number(value):
                    raise ContractError('Restored accounting does not reconcile')
            count += 1
        result['replayed_performance_results'] = count
        return result


def file_inventory(root):
    result = {}
    for p in sorted(root.rglob('*')):
        name = p.relative_to(root).as_posix()
        inside(root, name)
        if p.is_file():
            result[name] = dict(sha256=sha(p), bytes=p.stat().st_size)
    return result


def copy_file(source, destination):
    if source.is_symlink() or getattr(source, 'is_junction', lambda: False)():
        raise ContractError('Source links are forbidden')
    if source.name.startswith('.env') or source.suffix.lower() in ('.key', '.pem', '.pfx', '.p12'):
        raise ContractError('Credential files are excluded')
    before = sha(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open('rb') as src, destination.open('xb') as dst:
        shutil.copyfileobj(src, dst)
        dst.flush(); os.fsync(dst.fileno())
    if before != sha(destination) or before != sha(source):
        raise ContractError('Source changed while copying')


def verify_bundle(bundle, *, expected_hash=None):
    bundle = Path(bundle).resolve()
    manifest = read(bundle / 'backup.json')
    if expected_hash is not None and digest(manifest) != expected_hash:
        raise ContractError('Backup manifest hash differs')
    if manifest['schema_version'] != 1 or manifest['restore_mode'] != 'offline_evidence_only':
        raise ContractError('Unsupported backup format')
    payload = bundle / 'payload'
    actual = file_inventory(payload)
    if actual != manifest['files']:
        raise ContractError('Backup content is missing, extra or corrupt')
    for name in manifest['files']:
        inside(payload, name)
    evidence = database_evidence(payload / 'evidence.sqlite3')
    if evidence != manifest['database']:
        raise ContractError('Database evidence differs')
    forward = payload / 'private/step-11-forward'
    trial = read(forward / 'manifest.json')
    with readonly(payload / 'evidence.sqlite3') as conn:
        row = conn.execute('SELECT body FROM v2_records WHERE id=?', (trial['id'],)).fetchone()
        if not row or digest(json.loads(row[0])) != digest(trial):
            raise ContractError('Trial file and stored manifest differ')
    from .forward.prospective import check_runtime_inputs
    check_runtime_inputs(payload / 'repository', trial)
    config = read(payload / 'repository/config/step-11-jobs.json')
    if digest(trial) != config['manifest_hash']:
        raise ContractError('Trial and scheduled configuration differ')
    reports = list(forward.glob('report-*.json'))
    if not reports:
        raise ContractError('Missing immutable reports')
    for p in reports:
        report = read(p)
        if (p.name != 'report-' + digest(report) + '.json'
                or report['manifest_hash'] != digest(trial) or report['manifest_id'] != trial['id']):
            raise ContractError('Report content or ancestry differs')
        with readonly(payload / 'evidence.sqlite3') as conn:
            for performance in report.get('performance', []):
                row = conn.execute('SELECT body FROM v2_records WHERE id=?', (performance['id'],)).fetchone()
                if not row or digest(json.loads(row[0])) != digest(performance):
                    raise ContractError('Report accounting differs from stored evidence')
    pointer = read(forward / 'latest-report.json')
    # Original absolute path is preserved as evidence, never followed on recovery.
    if not (forward / ('report-' + pointer['report_hash'] + '.json')).is_file():
        raise ContractError('Latest report is missing')
    return dict(manifest_hash=digest(manifest), files=len(actual),
                database=evidence, reports=len(reports), provider_calls=0, model_calls=0)


def _snapshot(repo, source, registry, destination, *, keep, synthetic):
    policy = read(source / 'policy.json')
    key = digest(policy['quota_id'])
    with ExitStack() as locks:
        # Serialize publication with observation; freeze the owner for a coherent
        # database + immutable files + pointer snapshot. No credentials are loaded.
        locks.enter_context(owner_lock(source / 'step-11-operations/launcher.lock', create=False))
        locks.enter_context(owner_lock(registry / (key + '.lock'), create=False))
        binding = read(registry / (key + '.json'))
        if Path(binding['root']).resolve() != source:
            raise ContractError('Source is not the registered quota owner')
        payload = destination / 'payload'
        payload.mkdir()
        began = now()
        online_snapshot(source / 'research.sqlite3', payload / 'evidence.sqlite3')
        for folder in ('step-09', 'step-11-actions', 'step-11-forward', 'step-11-operations'):
            if not (source / folder).is_dir():
                raise ContractError('Required private evidence directory is missing')
            for p in sorted((source / folder).rglob('*')):
                inside(source, p.relative_to(source).as_posix())
                if p.is_file() and p.suffix != '.lock':
                    copy_file(p, payload / 'private' / p.relative_to(source))
        copy_file(source / 'policy.json', payload / 'private/policy.json')
        copy_file(registry / (key + '.json'), payload / 'owner-bindings' / (key + '.json'))
        command = ['git', '-c', 'safe.directory=' + repo.as_posix(), '-C', str(repo)]
        names = subprocess.check_output(command + ['ls-files', '-z']).decode().split('\0')
        names = sorted(set(names) | {'src/trade_theorist/private_backup.py', 'scripts/run_step_11_backup.py'})
        allowed = {'src', 'scripts', 'schemas', 'characters', 'config', 'examples', 'library', 'docs', 'decisions', 'tasks'}
        for name in filter(None, names):
            p = PurePosixPath(name)
            if p.parts[0] in allowed or name in ('README.md', 'pyproject.toml', 'requirements.lock', 'requirements-hardware-recovery.txt'):
                copy_file(inside(repo, name), payload / 'repository' / name)
        revision = subprocess.check_output(command + ['rev-parse', 'HEAD'], text=True).strip()
        manifest = dict(schema_version=1, backup_id=destination.name.removesuffix('.partial'),
            started_at=began, snapshot_finished_at=now(), software_revision=revision,
            working_tree_captured=True, restore_mode='offline_evidence_only',
            retention=dict(keep_verified=keep, last_verified_must_survive=True),
            database=database_evidence(payload / 'evidence.sqlite3'), files=file_inventory(payload),
            recovery_dependencies=dict(runtime='Included repository files and exact hashes; install requirements.lock offline',
                source_books='Original PDFs are not needed for stored ledger replay. Recover separately from the owner Investing-Books/books library; source identity and hashes are in the included catalog/checkpoints.',
                credentials='Excluded. Reprovision separately only after single-owner reconciliation.',
                activation='No runnable research.sqlite3 or quota registry is installed. Disable all original jobs, reconcile spent attempts/checkpoints with the newest surviving store and binding, and review ownership before manual activation.',
                remote='This local manifest does not certify replication. Independently pinned remote receipts and the separate encrypted recovery capsule are required; see docs/step-11-remote-recovery.md.'))
        atomic(destination / 'backup.json', manifest)
    return verify_bundle(destination, expected_hash=digest(manifest))


def logged(root, action, operation):
    run_id = uuid.uuid4().hex
    directory = root / 'operations/runs' / run_id
    start = dict(schema_version=1, run_id=run_id, action=action, started_at=now())
    atomic(directory / 'start.json', start)
    began = time.monotonic()
    def log(label):
        with (directory / 'run.log').open('a', encoding='utf-8') as out:
            out.write(label + ' ' + now() + '\n'); out.flush(); os.fsync(out.fileno())
    log('start')
    receipt = dict(start, exit_code=1, status='failed', phase=action)
    try:
        result = operation()
        receipt.update(exit_code=0, status='verified', manifest_hash=result['manifest_hash'])
        return result
    except Exception as exc:
        receipt['error_type'] = type(exc).__name__
        raise
    finally:
        receipt.update(ended_at=now(), duration_seconds=round(time.monotonic() - began, 3))
        atomic(directory / 'receipt.json', receipt)
        log('end')


def create_backup(repo, source, registry, root, *, keep=3, synthetic=False):
    if not isinstance(keep, int) or keep < 1:
        raise ValueError('Keep at least one verified backup')
    repo, source, registry = (Path(p).resolve() for p in (repo, source, registry))
    root = Path(root).resolve()
    if root.is_relative_to(source) or source.is_relative_to(root):
        raise ContractError('Backup storage must be separate from source data')
    root = private_directory(root, synthetic=synthetic)
    def operation():
        with owner_lock(root / 'backup.lock'):
            identifier = 'backup-' + uuid.uuid4().hex
            staging = root / (identifier + '.partial')
            staging.mkdir()
            result = _snapshot(repo, source, registry, staging, keep=keep, synthetic=synthetic)
            atomic(staging / 'verified.json', dict(manifest_hash=result['manifest_hash'], verified_at=now()))
            staging.rename(root / identifier)
            return dict(result, backup_path=str(root / identifier))
    return logged(root, 'backup', operation)


def restore_backup(bundle, destination, *, expected_hash, synthetic=False):
    bundle, destination = Path(bundle).resolve(), Path(destination).resolve()
    if destination.exists() or destination.is_relative_to(bundle) or bundle.is_relative_to(destination):
        raise ContractError('Restore requires a new isolated directory')
    private_directory(destination, synthetic=synthetic)
    def operation():
        result = verify_bundle(bundle, expected_hash=expected_hash)
        staging = destination / 'restored.partial'
        staging.mkdir()
        for name in ('backup.json', *('payload/' + n for n in read(bundle / 'backup.json')['files'])):
            copy_file(inside(bundle, name), inside(staging, name))
        verify_bundle(staging, expected_hash=expected_hash)
        staging.rename(destination / 'restored')
        atomic(destination / 'OFFLINE-ONLY.json', dict(manifest_hash=expected_hash,
            account_activation_allowed=False, single_owner_reconciliation_required=True,
            provider_calls=0, model_calls=0))
        return result
    return logged(destination, 'restore', operation)


def retain_backups(root, *, keep=3):
    """Only explicit pruning deletes; incomplete/corrupt evidence stays for inspection."""
    root = Path(root).resolve()
    if not isinstance(keep, int) or keep < 1:
        raise ValueError('Keep at least one verified backup')
    with owner_lock(root / 'backup.lock'):
        verified = []
        for p in root.glob('backup-*'):
            if p.name.endswith('.partial') or p.is_symlink() or getattr(p, 'is_junction', lambda: False)():
                continue
            try:
                marker = read(p / 'verified.json')
                verify_bundle(p, expected_hash=marker['manifest_hash'])
                verified.append((read(p / 'backup.json')['snapshot_finished_at'], p))
            except (OSError, ValueError, KeyError, ContractError, sqlite3.Error):
                continue
        verified.sort(key=lambda pair: pair[0], reverse=True)
        removed = 0
        for _, p in verified[keep:]:
            # Validate the resolved target immediately before recursive deletion.
            if p.resolve().parent != root or not p.name.startswith('backup-'):
                raise ContractError('Retention target escaped backup root')
            shutil.rmtree(p)
            removed += 1
        return dict(verified_retained=min(keep, len(verified)), removed=removed)
