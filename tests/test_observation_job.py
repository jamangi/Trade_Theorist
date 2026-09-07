from datetime import timedelta
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

from trade_theorist.contracts import ContractError, digest, utc
from trade_theorist import observation_job as job

ROOT = Path(__file__).resolve().parents[1]


class ObservationJobTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.private = Path(temporary.name)
        self.directory = self.private / 'step-11-forward'
        self.ops = self.private / 'step-11-operations'
        self.config = job.load_config(ROOT)
        self.manifest = {'id': self.config['manifest_id'], 'fixture': True}
        self.config['manifest_hash'] = digest(self.manifest)
        job.atomic(self.directory / 'manifest.json', self.manifest)
        self.now = utc('2026-09-15T01:00:00Z')
        self.report = dict(manifest_id=self.config['manifest_id'], manifest_hash=self.config['manifest_hash'],
            review_at=self.config['review_at'], stop_at=self.config['stop_at'], broker_orders=0,
            external_model_calls=0, as_of=(self.now - timedelta(seconds=5)).isoformat(), status='in_progress',
            elapsed_sessions=5, completed_real_sessions=0, matured_forecasts=0, immature_forecasts=1,
            unscorable_forecasts=0, gaps=[])
        self.save_report()
        for name, value in [('clock', lambda: self.now), ('load_config', lambda _: self.config),
                            ('check_runtime_inputs', lambda *_: None)]:
            context = patch.object(job, name, value)
            context.start(); self.addCleanup(context.stop)
        self.child = Mock(side_effect=self.fresh_report)
        context = patch.object(job, 'child', self.child)
        context.start(); self.addCleanup(context.stop)

    def save_report(self):
        key = digest(self.report)
        path = self.directory / ('report-' + key + '.json')
        job.atomic(path, self.report)
        job.atomic(self.directory / 'latest-report.json', dict(path=str(path), report_hash=key))

    def fresh_report(self, *_):
        self.report['as_of'] = self.now.isoformat()
        self.save_report()
        job.atomic(self.directory / 'transport-attempts-latest.json', [])
        return 0

    def complete(self):
        self.report.update(status='window_observed', completed_real_sessions=5,
                           matured_forecasts=1, immature_forecasts=0)
        self.save_report()

    def run_action(self, action='observe', **kwargs):
        with patch.object(job.sys, 'stdout', None):
            code = job.run_job(ROOT, self.private, action, **kwargs)
        receipts = [job.read(p) for p in (self.ops / 'runs').glob('*/receipt.json')]
        receipt = max(receipts, key=lambda r: (self.ops / 'runs' / r['run_id'] / 'receipt.json').stat().st_mtime_ns)
        text = (self.ops / 'runs' / receipt['run_id'] / 'run.log').read_text()
        self.assertIn('start ', text); self.assertIn('end ', text)
        self.assertEqual(code, receipt['exit_code'])
        return receipt

    def test_pending_exit_zero_is_not_scientific_success(self):
        receipt = self.run_action()
        self.assertEqual(receipt['status'], 'incomplete')
        self.assertEqual(receipt['exit_code'], 2)
        self.assertFalse(receipt['report']['complete'])

    def test_fresh_completion_and_duplicate_skip(self):
        def observe(*args):
            self.complete()
            return self.fresh_report(*args)
        self.child.side_effect = observe
        self.assertEqual(self.run_action()['status'], 'observed')
        self.assertEqual(self.run_action()['status'], 'already_complete')
        self.assertEqual(self.child.call_count, 1)
        self.assertTrue(job.read(self.ops / 'attention.json')['resolved'])

    def test_read_only_rehearsal_does_not_claim_completion(self):
        receipt = self.run_action('report')
        self.assertEqual(receipt['status'], 'report_only')
        self.assertEqual(receipt['transport_attempts'], 0)
        self.assertEqual(self.child.call_args.args[1], 'report')

    def test_read_only_rehearsal_rejects_requests(self):
        def bad(*args):
            self.fresh_report(*args)
            job.atomic(self.directory / 'transport-attempts-latest.json', [{'fixture': True}])
            return 0
        self.child.side_effect = bad
        self.assertEqual(self.run_action('report')['status'], 'error')

    def test_stale_report_rejected_even_when_child_succeeded(self):
        self.child.side_effect = lambda *_: 0
        self.assertEqual(self.run_action()['status'], 'error')

    def test_future_report_rejected(self):
        self.report['as_of'] = (self.now + timedelta(seconds=1)).isoformat()
        self.save_report()
        self.assertEqual(self.run_action()['status'], 'error')
        self.child.assert_not_called()

    def test_not_due_no_child(self):
        self.now = utc(self.config['review_at']) - timedelta(seconds=1)
        self.report['as_of'] = (self.now - timedelta(seconds=1)).isoformat(); self.save_report()
        self.assertEqual(self.run_action()['status'], 'not_due')
        self.child.assert_not_called()

    def test_expiry_no_new_window(self):
        self.now = utc(self.config['stop_at'])
        self.assertEqual(self.run_action()['status'], 'expired')
        self.child.assert_not_called()

    def test_deadline_check_requires_attention_without_requests(self):
        self.assertEqual(self.run_action('check')['status'], 'attention_required')
        self.child.assert_not_called()

    def test_timeout_is_bounded_by_remaining_window(self):
        self.now = utc(self.config['stop_at']) - timedelta(seconds=3)
        self.child.side_effect = subprocess.TimeoutExpired('fixture', 3)
        self.assertEqual(self.run_action()['status'], 'timeout')
        self.assertEqual(self.child.call_args.args[2], 3)

    def test_child_failure_receipt_has_no_sensitive_exception_text(self):
        self.child.side_effect = RuntimeError('secret-token-or-market-data')
        receipt = self.run_action()
        self.assertEqual(receipt['error_type'], 'RuntimeError')
        self.assertNotIn('secret-token', json.dumps(receipt))

    def test_manifest_change_prevents_launch(self):
        job.atomic(self.directory / 'manifest.json', dict(self.manifest, changed=True))
        self.assertEqual(self.run_action()['status'], 'error')
        self.child.assert_not_called()

    def test_runtime_change_prevents_launch(self):
        with patch.object(job, 'check_runtime_inputs', side_effect=ContractError('changed')):
            self.assertEqual(self.run_action()['status'], 'error')
        self.child.assert_not_called()

    def test_tampered_or_foreign_report_prevents_launch(self):
        pointer = job.read(self.directory / 'latest-report.json')
        job.atomic(Path(pointer['path']), dict(self.report, gaps=['altered']))
        self.assertEqual(self.run_action()['status'], 'error')
        self.report['manifest_id'] = 'foreign'; self.save_report()
        self.assertEqual(self.run_action()['status'], 'error')
        self.child.assert_not_called()

    def test_pointer_cannot_escape_private_report_directory(self):
        pointer = job.read(self.directory / 'latest-report.json')
        pointer['path'] = str(self.private / Path(pointer['path']).name)
        job.atomic(Path(pointer['path']), self.report)
        job.atomic(self.directory / 'latest-report.json', pointer)
        self.assertEqual(self.run_action()['status'], 'error')

    def test_status_alone_is_not_completion(self):
        self.complete()
        for changes in ({'gaps': ['missing']}, {'unscorable_forecasts': 1}, {'completed_real_sessions': 4}):
            with self.subTest(changes=changes):
                old = dict(self.report); self.report.update(changes); self.save_report()
                self.assertFalse(job.verified_report(self.directory, self.config)['complete'])
                self.report = old

    def test_interrupted_start_preserved_and_recorded_on_recovery(self):
        job.atomic(self.ops / 'runs/dead-process/start.json', {'pid': -1})
        receipt = self.run_action('report')
        self.assertEqual(receipt['previous_unfinished_runs'], ['dead-process'])
        self.assertFalse((self.ops / 'runs/dead-process/receipt.json').exists())

    def test_real_process_overlap_then_killed_owner_recovery(self):
        self.ops.mkdir()
        code = 'from pathlib import Path; import sys,time; from trade_theorist.market_requests import owner_lock\nwith owner_lock(Path(sys.argv[1])):\n print("ready",flush=True)\n time.sleep(30)'
        process = subprocess.Popen([sys.executable, '-c', code, str(self.ops / 'launcher.lock')], stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(process.stdout.readline().strip(), 'ready')
            self.assertEqual(self.run_action()['status'], 'overlap')
            self.child.assert_not_called()
        finally:
            process.kill(); process.wait(); process.stdout.close()
        self.assertEqual(self.run_action('report')['status'], 'report_only')

    def test_notifications_only_on_changed_unresolved_failure(self):
        with patch.object(job, 'notify_owner', return_value=True) as notifier:
            self.run_action('check')
            self.run_action('check', notify=True)
            self.run_action('check', notify=True)
            self.assertEqual(notifier.call_count, 1)
            self.run_action('report')
            self.assertFalse(job.read(self.ops / 'attention.json')['resolved'])

    def test_corrupt_attention_file_does_not_lose_end_receipt(self):
        self.ops.mkdir()
        (self.ops / 'attention.json').write_text('broken')
        self.assertEqual(self.run_action('check')['status'], 'attention_required')


class ChildSupervisionTests(unittest.TestCase):
    def test_timeout_kills_and_reaps_child(self):
        process = Mock()
        process.wait.side_effect = [subprocess.TimeoutExpired('fixture', 1), 1]
        process.poll.return_value = None
        with patch.object(job.subprocess, 'Popen', return_value=process):
            with self.assertRaises(subprocess.TimeoutExpired):
                job.child(ROOT, 'observe', 1)
        process.kill.assert_called_once()
        self.assertEqual(process.wait.call_count, 2)


if __name__ == '__main__':
    unittest.main()
