from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from trade_theorist import private_backup as backup
from trade_theorist.contracts import ContractError, digest
from trade_theorist.fixtures_accounting_v2 import golden, at
from trade_theorist.evaluate.portfolio_v2 import evaluate
from trade_theorist.market_requests import RequestStore, owner_lock


class PrivateBackupTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def bundle(self, name='backup-fixture'):
        bundle = self.root / name
        payload = bundle / 'payload'
        payload.mkdir(parents=True)
        source = self.root / (name + '-source')
        with RequestStore(source, synthetic=True) as store:
            fixture = golden(store)
            evaluate(store, fixture.portfolio, effective_cutoff=at(11), receipt_cutoff=at(11))
            # No transport; nonzero spent work is preserved through restoration.
            store.connection.execute("INSERT INTO market_work VALUES ('work:fixture','hash','{}','{}')")
            store.connection.execute("INSERT INTO market_attempts VALUES (1,'work:fixture',1,'hash','200',2)")
            backup.online_snapshot(source / 'research.sqlite3', payload / 'evidence.sqlite3')
        # Full database integrity/accounting is real; only the frozen Step 11
        # ancestry check is mocked for this deliberately small synthetic bundle.
        trial = {'id': 'synthetic:trial'}
        with closing(sqlite3.connect(payload / 'evidence.sqlite3')) as conn:
            row = conn.execute("SELECT body FROM v2_records WHERE record_type='experiment' LIMIT 1").fetchone()
            trial = json.loads(row[0])
        forward = payload / 'private/step-11-forward'
        backup.atomic(forward / 'manifest.json', trial)
        report = dict(manifest_id=trial['id'], manifest_hash=digest(trial))
        report_hash = digest(report)
        backup.atomic(forward / ('report-' + report_hash + '.json'), report)
        backup.atomic(forward / 'latest-report.json', dict(report_hash=report_hash, path='C:/original/private/report.json'))
        backup.atomic(payload / 'repository/config/step-11-jobs.json', dict(manifest_hash=digest(trial)))
        manifest = dict(schema_version=1, restore_mode='offline_evidence_only',
                        snapshot_finished_at=backup.now(), files=backup.file_inventory(payload),
                        database=backup.database_evidence(payload / 'evidence.sqlite3'))
        backup.atomic(bundle / 'backup.json', manifest)
        backup.atomic(bundle / 'verified.json', dict(manifest_hash=digest(manifest)))
        return bundle, digest(manifest)

    def test_online_snapshot_includes_wal_and_concurrent_commits(self):
        source = self.root / 'live.sqlite3'
        writer = sqlite3.connect(source, isolation_level=None)
        self.addCleanup(writer.close)
        writer.execute('PRAGMA journal_mode=WAL')
        writer.execute('CREATE TABLE events(id INTEGER PRIMARY KEY, body BLOB)')
        writer.executemany('INSERT INTO events VALUES (?,zeroblob(8192))', [(i,) for i in range(100)])
        committed = []
        def during(status, remaining, total):
            if not committed and remaining:
                writer.execute('INSERT INTO events VALUES (100,zeroblob(8192))')
                committed.append(True)
        destination = self.root / 'snapshot.sqlite3'
        backup.online_snapshot(source, destination, progress=during)
        self.assertTrue(committed)
        with backup.readonly(destination) as conn:
            self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM events').fetchone()[0], 101)

    def test_snapshot_timeout_is_not_success(self):
        source = self.root / 'live.sqlite3'
        with closing(sqlite3.connect(source)) as conn:
            conn.execute('CREATE TABLE records(id)')
        with self.assertRaises(TimeoutError):
            backup.online_snapshot(source, self.root / 'partial.sqlite3', timeout=-1)

    @patch('trade_theorist.forward.prospective.check_runtime_inputs')
    def test_restore_replays_and_preserves_spent_state_without_network(self, _):
        bundle, h = self.bundle()
        before = backup.sha(bundle / 'payload/evidence.sqlite3')
        with patch('socket.socket.connect', side_effect=AssertionError('No network')):
            result = backup.restore_backup(bundle, self.root / 'restore', expected_hash=h, synthetic=True)
        self.assertEqual(result['database']['accounted_attempts'], 1)
        self.assertEqual(result['database']['replayed_performance_results'], 1)
        self.assertEqual(result['provider_calls'], 0)
        restored = self.root / 'restore/restored/payload'
        self.assertEqual(backup.sha(restored / 'evidence.sqlite3'), before)
        self.assertFalse(list((self.root / 'restore').rglob('research.sqlite3')))
        self.assertFalse(backup.read(self.root / 'restore/OFFLINE-ONLY.json')['account_activation_allowed'])
        with backup.readonly(restored / 'evidence.sqlite3') as conn:
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute('DELETE FROM market_attempts')

    @patch('trade_theorist.forward.prospective.check_runtime_inputs')
    def test_corrupt_payload_and_manifest_rejected(self, _):
        bundle, h = self.bundle()
        with (bundle / 'payload/evidence.sqlite3').open('ab') as out:
            out.write(b'corruption')
        with self.assertRaises(ContractError):
            backup.verify_bundle(bundle, expected_hash=h)
        with self.assertRaises(ContractError):
            backup.verify_bundle(bundle, expected_hash='0' * 64)

    @patch('trade_theorist.forward.prospective.check_runtime_inputs')
    def test_rehashed_corrupt_report_rejected_by_content_hash(self, _):
        bundle, h = self.bundle()
        p = next((bundle / 'payload/private/step-11-forward').glob('report-*.json'))
        backup.atomic(p, dict(manifest_id='foreign', manifest_hash='0' * 64))
        manifest = backup.read(bundle / 'backup.json')
        manifest['files'] = backup.file_inventory(bundle / 'payload')
        backup.atomic(bundle / 'backup.json', manifest)
        with self.assertRaises(ContractError):
            backup.verify_bundle(bundle, expected_hash=digest(manifest))

    @patch('trade_theorist.forward.prospective.check_runtime_inputs')
    def test_interrupted_copy_never_publishes_restored_bundle(self, _):
        bundle, h = self.bundle()
        original = backup.copy_file
        calls = []
        def interrupted(src, dst):
            calls.append(src)
            if len(calls) > 1:
                raise OSError('sensitive raw provider value must never enter receipt')
            original(src, dst)
        with patch.object(backup, 'copy_file', interrupted), self.assertRaises(OSError):
            backup.restore_backup(bundle, self.root / 'failed', expected_hash=h, synthetic=True)
        self.assertFalse((self.root / 'failed/restored').exists())
        self.assertTrue((self.root / 'failed/restored.partial').exists())
        receipt = next((self.root / 'failed/operations').rglob('receipt.json'))
        self.assertNotIn('sensitive', receipt.read_text())
        self.assertEqual(backup.read(receipt)['exit_code'], 1)
        self.assertIn('end ', receipt.with_name('run.log').read_text())

    @patch('trade_theorist.forward.prospective.check_runtime_inputs')
    def test_retention_keeps_last_verified_and_corrupt_or_partial_evidence(self, _):
        root = self.root / 'retention'
        root.mkdir()
        for i in range(3):
            bundle, h = self.bundle('backup-' + str(i))
            shutil.move(str(bundle), root / bundle.name)
        partial = root / 'backup-interrupted.partial'
        partial.mkdir()
        corrupt = root / 'backup-corrupt'
        corrupt.mkdir()
        backup.atomic(corrupt / 'verified.json', dict(manifest_hash='0' * 64))
        result = backup.retain_backups(root, keep=1)
        self.assertEqual(result, dict(verified_retained=1, removed=2))
        self.assertTrue(partial.exists()); self.assertTrue(corrupt.exists())
        self.assertEqual(backup.retain_backups(root, keep=1)['removed'], 0)
        with self.assertRaises(ValueError):
            backup.retain_backups(root, keep=0)

    def test_path_traversal_and_credentials_rejected(self):
        for path in ('../escape', '/absolute', 'C:/drive', 'a\\b', 'a//b', 'a/./b'):
            with self.subTest(path=path), self.assertRaises(ContractError):
                backup.inside(self.root, path)
        secret = self.root / '.env'
        secret.write_text('DO_NOT_COPY=secret')
        with self.assertRaises(ContractError):
            backup.copy_file(secret, self.root / 'copy')

    def test_repository_destination_rejected(self):
        (self.root / '.git').mkdir()
        with self.assertRaises(ContractError):
            backup.private_directory(self.root / 'backup')

    def test_existing_restore_destination_rejected(self):
        with self.assertRaises(ContractError):
            backup.restore_backup(self.root, self.root, expected_hash='0' * 64, synthetic=True)

    def test_overlap_receipt_and_no_snapshot(self):
        source = self.root / 'source'
        source.mkdir()
        root = self.root / 'backup'
        root.mkdir()
        with owner_lock(root / 'backup.lock'), patch.object(backup, '_snapshot') as snapshot:
            with self.assertRaises(OSError):
                backup.create_backup(self.root, source, self.root / 'registry', root, synthetic=True)
            snapshot.assert_not_called()
        self.assertEqual(backup.read(next((root / 'operations').rglob('receipt.json')))['exit_code'], 1)

    def test_interruption_leaves_start_without_fabricated_receipt(self):
        # Abrupt termination cannot run finally. A durable start is still evidence.
        import subprocess
        import sys
        script = ('from pathlib import Path; import os; '
                  'from trade_theorist.private_backup import logged; '
                  'logged(Path(__import__("sys").argv[1]), "backup", lambda: os._exit(7))')
        result = subprocess.run([sys.executable, '-c', script, str(self.root)], capture_output=True)
        self.assertEqual(result.returncode, 7)
        start = next(self.root.rglob('start.json'))
        self.assertFalse(start.with_name('receipt.json').exists())
        self.assertTrue(start.with_name('run.log').read_text().startswith('start '))


if __name__ == '__main__':
    unittest.main()
