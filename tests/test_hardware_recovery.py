"""Software failure checks; actual two-device ceremony is separate evidence."""
import copy
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from trade_theorist import hardware_recovery as hw, remote_backup as remote
from trade_theorist.contracts import ContractError
from trade_theorist.private_backup import atomic, sha


@unittest.skipUnless(importlib.util.find_spec('cryptography'), 'Optional hardware environment required')
class HardwareRecoveryTests(unittest.TestCase):
    def test_authenticated_wrapping_rejects_changes_and_wrong_device_secret(self):
        from cryptography.exceptions import InvalidTag
        header = dict(schema_version=1, label='primary', rp_id=hw.RP_ID, recipient='public')
        secret, identity = os.urandom(32), b'SYNTHETIC PRIVATE IDENTITY'
        entry = hw.seal(identity, secret, header)
        self.assertEqual(hw.unseal(entry, secret), identity)
        for field in ('header', 'nonce', 'ciphertext'):
            changed = copy.deepcopy(entry)
            if field == 'header':
                changed[field]['label'] = 'spare'
            else:
                raw = bytearray(hw.unb64(changed[field])); raw[-1] ^= 1
                changed[field] = hw.b64(raw)
            with self.assertRaises(InvalidTag):
                hw.unseal(changed, secret)
        with self.assertRaises(InvalidTag):
            hw.unseal(entry, os.urandom(32))
        with self.assertRaises(ContractError):
            hw.seal(identity, b'short', header)

    def test_unlock_requires_exact_label_and_recipient(self):
        header = dict(schema_version=1, label='primary', rp_id=hw.RP_ID, recipient='public')
        capsule = dict(schema_version=1, kind='fido2-wrapped-age-identity', recipient='public',
                       keys=[hw.seal(b'synthetic', b'x' * 32, header)])
        with patch.object(hw, 'hardware_secret') as device:
            with self.assertRaises(ContractError):
                hw.unlock(capsule, 'spare')
            capsule['recipient'] = 'different'
            with self.assertRaises(ContractError):
                hw.unlock(capsule, 'primary')
            device.assert_not_called()

    def test_age_hardware_input_is_piped_and_requires_interaction_and_pin(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            age, capsule = root / 'age', root / 'capsule'
            age.write_bytes(b'fake executable')
            atomic(capsule, {'synthetic': True})
            c = dict(age_executable=str(age), age_sha256=sha(age), identity_mode='fido2_envelope',
                     capsule_sha256=sha(capsule), hardware_key_label='primary')
            args = ['--decrypt', '--identity', str(capsule), '--output', str(root / 'out'), 'ciphertext']
            with patch.object(hw, 'unlock') as unlock, patch.object(remote.subprocess, 'run') as run:
                with self.assertRaises(ContractError):
                    remote.run_age(c, args)
                unlock.assert_not_called(); run.assert_not_called()
                unlock.side_effect = ContractError('No registered device')
                with self.assertRaises(ContractError):
                    remote.run_age(c, args, interactive=True)
                run.assert_not_called()
                unlock.side_effect = None; unlock.return_value = b'synthetic identity'
                run.return_value.returncode = 0
                remote.run_age(c, args, interactive=True)
                self.assertEqual(run.call_args.kwargs['input'], b'synthetic identity')
                command = run.call_args.args[0]
                self.assertEqual(command[command.index('--identity') + 1], '-')
                self.assertNotIn(b'synthetic identity', [p.read_bytes() for p in root.iterdir()])
                capsule.write_bytes(b'tampered')
                unlock.reset_mock(); run.reset_mock()
                with self.assertRaises(ContractError):
                    remote.run_age(c, args, interactive=True)
                unlock.assert_not_called(); run.assert_not_called()

    def test_real_age_identity_proof_never_writes_private_identity(self):
        import subprocess
        binary = os.environ.get('TRADE_THEORIST_TEST_AGE')
        if not binary:
            self.skipTest('Pinned real age executable required')
        with tempfile.TemporaryDirectory() as temp:
            age = Path(binary)
            keygen = age.with_name('age-keygen.exe' if os.name == 'nt' else 'age-keygen')
            identity = subprocess.check_output([str(keygen)], stderr=subprocess.DEVNULL)
            recipient = subprocess.check_output([str(keygen), '-y'], input=identity).decode().strip()
            hw.prove_identity(age, sha(age), identity, recipient, Path(temp))
            self.assertEqual(list(Path(temp).iterdir()), [])

    @unittest.skipUnless(importlib.util.find_spec('fido2'), 'Optional FIDO library required')
    def test_interrupted_enrollment_resumes_same_identity_without_replacing_primary(self):
        from fido2.client import ClientError
        from fido2.ctap import CtapError
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            age = root / 'age'; age.write_bytes(b'executable fixture')
            header = dict(schema_version=1, label='primary', rp_id=hw.RP_ID, recipient='public')
            primary = hw.seal(b'synthetic identity', b'p' * 32, header)
            partial = dict(schema_version=1, kind='fido2-wrapped-age-identity', recipient='public', keys=[primary])
            atomic(root / 'recovery-capsule.partial.json', partial)
            absent = ClientError.ERR.DEVICE_INELIGIBLE(CtapError(CtapError.ERR.NO_CREDENTIALS))
            with patch.object(hw, 'private_directory', return_value=root), patch('builtins.input', return_value=''), \
                    patch('builtins.print'), patch.object(hw, 'unlock', return_value=b'synthetic identity'), \
                    patch.object(hw, 'prove_identity'), patch.object(hw.subprocess, 'check_output') as keygen, \
                    patch.object(hw, 'enroll_credential', return_value=dict(header, label='spare')) as enroll, \
                    patch.object(hw, 'hardware_secret', side_effect=[absent, b's' * 32]):
                final = hw.enroll_pair(root, age)
            keygen.assert_not_called()
            enroll.assert_called_once_with('spare', 'public')
            self.assertEqual(hw.read(final)['keys'][0], primary)
            self.assertFalse((root / 'recovery-capsule.partial.json').exists())


if __name__ == '__main__':
    unittest.main()
