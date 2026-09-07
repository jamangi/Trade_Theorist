from contextlib import contextmanager
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from trade_theorist import remote_backup as remote
from trade_theorist.private_backup import atomic, read, sha
from trade_theorist.contracts import ContractError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('backup_receiver', ROOT / 'scripts/backup_receiver.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class LocalReceiver:
    def __init__(self, root):
        self.server = server.Receiver(root)

    def call(self, request, *, source=None, destination=None):
        incoming = source.open('rb') if source else io.BytesIO()
        outgoing = destination.open('xb') if destination else io.BytesIO()
        try:
            return self.server.run(request, incoming, outgoing)
        finally:
            incoming.close(); outgoing.close()


class ReceiverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.receiver = server.Receiver(self.root / 'remote')
        self.name = 'backup-' + 'a' * 32
        self.data = server.MAGIC + b'original synthetic encrypted-looking fixture'
        self.meta = dict(id=self.name, bytes=len(self.data), ciphertext_hash=hashlib.sha256(self.data).hexdigest(), manifest_hash='b' * 64)

    def put(self, **kwargs):
        return self.receiver.run(dict(action='put', **(self.meta | kwargs)), io.BytesIO(self.data), io.BytesIO())

    def test_capsule_roundtrip_bounded_immutable_and_rejects_extra_secrets(self):
        import base64
        capsule = dict(schema_version=1, kind='fido2-wrapped-age-identity', recipient='public', keys=[])
        for label in ('primary', 'spare'):
            capsule['keys'].append(dict(header=dict(schema_version=1, label=label,
                rp_id='trade-theorist-backup.localhost', recipient='public',
                credential_id='public metadata', public_key='public metadata', salt='public metadata'),
                nonce=base64.urlsafe_b64encode(b'n' * 12).decode(),
                ciphertext=base64.urlsafe_b64encode(b'synthetic encrypted bytes' * 4).decode()))
        data = json.dumps(capsule).encode()
        h = hashlib.sha256(data).hexdigest()
        put = dict(action='put_capsule', capsule_hash=h)
        for _ in range(2):
            self.assertEqual(self.receiver.handle(put, io.BytesIO(data), io.BytesIO())['capsule_hash'], h)
        out = io.BytesIO()
        self.receiver.handle(dict(action='get_capsule', capsule_hash=h), io.BytesIO(), out)
        self.assertEqual(out.getvalue(), data)
        with self.assertRaises(ValueError):
            self.receiver.handle(put, io.BytesIO(data[:-1]), io.BytesIO())
        capsule['private_identity'] = 'must not store an extra plaintext secret'
        invalid = json.dumps(capsule).encode()
        with self.assertRaises(ValueError):
            self.receiver.handle(dict(action='put_capsule', capsule_hash=hashlib.sha256(invalid).hexdigest()),
                                 io.BytesIO(invalid), io.BytesIO())
        with self.assertRaises(ValueError):
            self.receiver.handle(dict(action='get_capsule', capsule_hash='../escape'), io.BytesIO(), io.BytesIO())

    def test_publish_download_and_explicit_roundtrip_mark(self):
        self.assertEqual(self.put()['status'], 'uploaded_unverified')
        out = io.BytesIO()
        self.receiver.handle(dict(action='get', id=self.name, ciphertext_hash=self.meta['ciphertext_hash']), io.BytesIO(), out)
        self.assertEqual(out.getvalue(), self.data)
        marked = self.receiver.handle(dict(action='mark_verified', id=self.name,
            ciphertext_hash=self.meta['ciphertext_hash'], manifest_hash=self.meta['manifest_hash']), io.BytesIO(), io.BytesIO())
        self.assertEqual(marked['status'], 'roundtrip_verified')
        with self.assertRaises(ValueError):
            self.put()

    def test_interrupted_and_wrong_hash_uploads_never_publish(self):
        for body, changed in [(self.data[:-3], {}), (self.data, {'ciphertext_hash': '0' * 64}),
                              (b'plaintext content instead of age', {}), (self.data + b'extra', {})]:
            with self.subTest(body=body[:10]), self.assertRaises(ValueError):
                self.receiver.run(dict(action='put', **(self.meta | changed)), io.BytesIO(body), io.BytesIO())
        self.assertFalse(list((self.root / 'remote/objects').iterdir()))
        self.assertFalse(list((self.root / 'remote/receipts').iterdir()))
        self.assertEqual(len(list((self.root / 'remote/incoming').iterdir())), 4)

    def test_corruption_blocks_download_and_retention(self):
        self.put()
        (self.root / 'remote/objects' / (self.name + '.age')).write_bytes(self.data[:-1])
        with self.assertRaises(ValueError):
            self.receiver.handle(dict(action='get', id=self.name, ciphertext_hash=self.meta['ciphertext_hash']), io.BytesIO(), io.BytesIO())
        listing = self.receiver.handle(dict(action='list'), io.BytesIO(), io.BytesIO())
        self.assertEqual(listing['objects'][0]['status'], 'corrupt_or_missing')

    def test_last_verified_survivor_cannot_be_deleted(self):
        self.put()
        mark = dict(action='mark_verified', id=self.name, ciphertext_hash=self.meta['ciphertext_hash'], manifest_hash=self.meta['manifest_hash'])
        self.receiver.handle(mark, io.BytesIO(), io.BytesIO())
        with self.assertRaises(ValueError):
            self.receiver.handle(dict(action='delete', id=self.name, survivor=self.name,
                survivor_hash=self.meta['ciphertext_hash']), io.BytesIO(), io.BytesIO())
        other = 'backup-' + 'c' * 32
        self.put(id=other)
        with self.assertRaises(ValueError):
            self.receiver.handle(dict(action='delete', id=self.name, survivor=other,
                survivor_hash=self.meta['ciphertext_hash']), io.BytesIO(), io.BytesIO())

    def test_paths_limits_and_owner_collisions_rejected(self):
        for name in ('../escape', 'backup-' + 'a' * 32 + '/other', 'C:/file'):
            with self.assertRaises(ValueError):
                self.put(id=name)
        with self.assertRaises(ValueError):
            self.put(bytes=server.MAX_BYTES + 1)
        atomic(self.root / 'remote/owner.json', dict(project='other'))
        with self.assertRaises(ValueError):
            server.Receiver(self.root / 'remote')

    def test_overlap_and_failure_receipts(self):
        with server.exclusive(self.root / 'remote/receiver.lock'), self.assertRaises(OSError):
            self.put()
        receipt = read(next((self.root / 'remote/operations').glob('*/receipt.json')))
        self.assertEqual(receipt['exit_code'], 1)
        self.assertNotIn('original synthetic', json.dumps(receipt))


class RemoteClientTests(unittest.TestCase):
    def test_capsule_bootstrap_has_no_local_key_or_recipient_dependency(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / 'bootstrap.json'
            c = dict(schema_version=1, profile='crcs-lab', receiver_sha256='a' * 64,
                     receiver_path='/home/ubuntu/.local/lib/trade-theorist-backups/' + 'a' * 64 + '/backup_receiver.py',
                     capsule_sha256='b' * 64, storage_terms_recorded=True)
            atomic(config, c)
            self.assertEqual(remote.load_config(config, capsule_only=True), c)
            c['profile'] = 'other-host'; atomic(config, c)
            with self.assertRaises(ContractError):
                remote.load_config(config, capsule_only=True)
            c['profile'] = 'crcs-lab'; c['capsule_sha256'] = '../escape'; atomic(config, c)
            with self.assertRaises(ContractError):
                remote.load_config(config, capsule_only=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_tar_rejects_links_duplicates_escape_and_expansion(self):
        for i, (name, kind, size) in enumerate([('../escape', tarfile.REGTYPE, 1),
                ('link', tarfile.SYMTYPE, 0), ('oversize', tarfile.REGTYPE, remote.MAX_PLAINTEXT + 1)]):
            p = self.root / (str(i) + '.tar.gz')
            import gzip
            info = tarfile.TarInfo(name); info.type = kind; info.size = size
            # Construct hostile headers directly, without allocating an oversized body.
            with gzip.open(p, 'wb') as out:
                out.write(info.tobuf()); out.write(b'x' * 512 if size == 1 else b'')
                out.write(b'\0' * 1024)
            with self.assertRaises((ContractError, tarfile.ReadError)):
                remote.unpack_bundle(p, self.root / str(i), '0' * 64)

    def test_ssh_uses_strict_host_check_no_forwarding_and_safe_command(self):
        config = dict(profile='crcs-lab', receiver_path='/home/ubuntu/.local/lib/revision/backup_receiver.py')
        with patch.object(remote.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, b'{}')) as run:
            remote.SSHReceiver(config).call(dict(action='list'))
        args = run.call_args.args[0]
        self.assertIn('StrictHostKeyChecking=yes', args)
        self.assertIn('ForwardAgent=no', args)
        self.assertIn('BatchMode=yes', args)
        self.assertNotIn('shell', run.call_args.kwargs)

    def test_failed_authentication_removes_plaintext_prefix(self):
        receiver = unittest.mock.Mock()
        ciphertext = b'ciphertext'
        def download(request, destination):
            destination.write_bytes(ciphertext)
        receiver.call.side_effect = download
        def invalid(c, arguments, **kwargs):
            Path(arguments[arguments.index('--output') + 1]).write_bytes(b'unauthenticated prefix')
            raise ContractError('rejected')
        metadata = dict(id='backup-' + 'a' * 32, bytes=len(ciphertext), ciphertext_hash=hashlib.sha256(ciphertext).hexdigest(), manifest_hash='b' * 64)
        with patch.object(remote, 'run_age', invalid), self.assertRaises(ContractError):
            remote.download_restore({}, receiver, metadata, self.root / 'restore', self.root / 'identity', synthetic=True)
        self.assertFalse((self.root / 'restore/decrypted.tar.gz.partial').exists())
        self.assertFalse((self.root / 'restore/offline-restore').exists())

    def test_prune_requires_new_recovery_of_independently_pinned_survivor(self):
        receiver = unittest.mock.Mock()
        objects = [dict(id='backup-' + ch * 32, bytes=10, ciphertext_hash=ch * 64, manifest_hash='d' * 64,
                        status='roundtrip_verified', uploaded_at=f'2026-09-07T00:00:0{i}Z') for i, ch in enumerate('abc')]
        for obj in objects:
            atomic(self.root / 'verified-remote' / (obj['id'] + '.json'), obj)
        receiver.call.return_value = dict(objects=objects)
        with patch.object(remote, 'download_restore', side_effect=ContractError('Survivor failed')), self.assertRaises(ContractError):
            remote.prune_remote({}, self.root, self.root / 'identity', keep=1, synthetic=True, receiver=receiver)
        self.assertEqual(receiver.call.call_count, 1)  # listing only; no deletion
        with self.assertRaises(ValueError):
            remote.prune_remote({}, self.root, self.root / 'identity', keep=0, synthetic=True, receiver=receiver)


class AgeIntegrationTests(unittest.TestCase):
    def test_full_local_protocol_roundtrip_and_retention_with_real_age(self):
        import os
        import test_private_backup as fixtures
        binary = os.environ.get('TRADE_THEORIST_TEST_AGE')
        if not binary:
            self.skipTest('Set TRADE_THEORIST_TEST_AGE for actual encrypted round-trip testing')
        case = fixtures.PrivateBackupTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        bundle, manifest_hash = case.bundle()
        keygen = Path(binary).with_name('age-keygen.exe' if os.name == 'nt' else 'age-keygen')
        key, recipients = case.root / 'test-identity', case.root / 'test-recipients'
        subprocess.run([str(keygen), '-o', str(key)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with recipients.open('wb') as out:
            subprocess.run([str(keygen), '-y', str(key)], check=True, stdout=out, stderr=subprocess.DEVNULL)
        config = dict(age_executable=binary, age_sha256=sha(Path(binary)),
                      recipients_file=str(recipients), recipients_sha256=sha(recipients))
        receiver = LocalReceiver(case.root / 'server')
        local = case.root / 'client'
        # The small accounting fixture has no real Step 11 knowledge ancestry.
        # Every other byte/hash, cipher, ledger replay and transfer check is real.
        with patch('trade_theorist.forward.prospective.check_runtime_inputs'), patch('socket.socket.connect', side_effect=AssertionError('No provider')):
            for _ in range(2):
                result = remote.publish_roundtrip(config, bundle, local, key,
                    expected_hash=manifest_hash, synthetic=True, receiver=receiver)
                self.assertEqual(result['database']['accounted_attempts'], 1)
                self.assertEqual(result['database']['replayed_performance_results'], 1)
            retained = remote.prune_remote(config, local, key, keep=1, synthetic=True, receiver=receiver)
        self.assertEqual(retained['removed'], 1)
        self.assertEqual(len(receiver.call(dict(action='list'))['objects']), 1)
        self.assertFalse(list(local.rglob('research.sqlite3')))
        self.assertFalse(list(local.rglob('*.tar.gz')))

    def test_real_encryption_wrong_identity_tamper_and_roundtrip(self):
        # A real age binary is needed for this explicit integration check. CI's
        # ordinary suite does not pretend a mocked cipher proves authentication.
        import os
        binary = os.environ.get('TRADE_THEORIST_TEST_AGE')
        if not binary:
            self.skipTest('Set TRADE_THEORIST_TEST_AGE for the pinned real-age integration rehearsal')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executable = Path(binary)
            keygen = executable.with_name('age-keygen.exe' if os.name == 'nt' else 'age-keygen')
            config = dict(age_executable=str(executable), age_sha256=sha(executable))
            keys = []
            for name in ('primary', 'spare'):
                key = root / name
                subprocess.run([str(keygen), '-o', str(key)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                keys.append(key)
            recipients = root / 'recipients.txt'
            with recipients.open('wb') as out:
                subprocess.run([str(keygen), '-y', str(keys[0])], check=True, stdout=out, stderr=subprocess.DEVNULL)
            plaintext, encrypted = root / 'source', root / 'cipher.age'
            plaintext.write_bytes(b'original fixture for actual authenticated encryption')
            remote.run_age(config, ['-R', str(recipients), '-o', str(encrypted), str(plaintext)])
            remote.run_age(config, ['-d', '-i', str(keys[0]), '-o', str(root / 'good'), str(encrypted)])
            self.assertEqual((root / 'good').read_bytes(), plaintext.read_bytes())
            with self.assertRaises(ContractError):
                remote.run_age(config, ['-d', '-i', str(keys[1]), '-o', str(root / 'wrong'), str(encrypted)])
            data = bytearray(encrypted.read_bytes()); data[-1] ^= 1; encrypted.write_bytes(data)
            with self.assertRaises(ContractError):
                remote.run_age(config, ['-d', '-i', str(keys[0]), '-o', str(root / 'tampered'), str(encrypted)])


if __name__ == '__main__':
    unittest.main()
