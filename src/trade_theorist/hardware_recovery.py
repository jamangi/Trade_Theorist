"""FIDO2 hmac-secret wraps a native age identity; PIN/touch never enter logs.

Optional dependencies are isolated from the scientific runtime. This is software
key wrapping, not a claim that an age private key remains inside a PIV token.
"""
import base64
from contextlib import contextmanager
import getpass
import hashlib
import json
import os
from pathlib import Path
import subprocess

from .contracts import ContractError
from .private_backup import atomic, private_directory, read, sha

RP_ID = 'trade-theorist-backup.localhost'
ORIGIN = 'https://' + RP_ID
DOMAIN = b'TradeTheorist/FIDO2-age-recovery/v1'


def b64(value):
    return base64.urlsafe_b64encode(value).decode('ascii')


def unb64(value):
    return base64.b64decode(value, altchars=b'-_', validate=True)


def associated(header):
    return json.dumps(header, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def wrapping_key(secret, header):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    if len(secret) != 32:
        raise ContractError('Expected a 32-byte authenticator secret')
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None,
                info=DOMAIN + hashlib.sha256(associated(header)).digest()).derive(secret)


def seal(identity, secret, header):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce = os.urandom(12)
    ciphertext = AESGCM(wrapping_key(secret, header)).encrypt(nonce, identity, associated(header))
    return dict(header=header, nonce=b64(nonce), ciphertext=b64(ciphertext))


def unseal(entry, secret):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    return AESGCM(wrapping_key(secret, entry['header'])).decrypt(
        unb64(entry['nonce']), unb64(entry['ciphertext']), associated(entry['header']))


@contextmanager
def connected_client():
    from fido2.client import Fido2Client, DefaultClientDataCollector, UserInteraction
    from fido2.ctap2.extensions import HmacSecretExtension, CredProtectExtension
    from fido2.hid import CtapHidDevice
    devices = list(CtapHidDevice.list_devices())
    try:
        if len(devices) != 1 or devices[0].descriptor.vid != 0x1050:
            raise ContractError('Connect exactly one of the owner Yubico keys')
        class Interaction(UserInteraction):
            attempts = 0
            def prompt_up(self):
                print('Touch the connected security key when it flashes.', flush=True)
            def request_pin(self, permissions, rp_id):
                self.attempts += 1
                if self.attempts > 1:
                    raise ContractError('PIN rejected; stop rather than retrying toward lockout')
                return getpass.getpass('Security-key PIN (hidden; never saved): ')
        client = Fido2Client(devices[0], DefaultClientDataCollector(ORIGIN),
            user_interaction=Interaction(), extensions=[HmacSecretExtension(allow_hmac_secret=True), CredProtectExtension()])
        if 'hmac-secret' not in client.info.extensions or not client.info.options.get('clientPin'):
            raise ContractError('A PIN-configured hmac-secret key is required')
        yield client
    finally:
        for device in devices:
            device.close()


def enroll_credential(label, recipient):
    from fido2 import cbor
    with connected_client() as client:
        registration = client.make_credential(dict(
            rp=dict(id=RP_ID, name='Trade Theorist private backup recovery'),
            user=dict(id=os.urandom(32), name='backup-' + label, displayName='Backup ' + label),
            challenge=os.urandom(32), pubKeyCredParams=[dict(type='public-key', alg=-7)],
            timeout=90000, authenticatorSelection=dict(residentKey='discouraged', userVerification='required'),
            attestation='none', extensions=dict(hmacCreateSecret=True,
                credentialProtectionPolicy='userVerificationRequired', enforceCredentialProtectionPolicy=True)))
        data = registration.response.attestation_object.auth_data
        if (not registration.client_extension_results.hmac_create_secret
                or not data.is_user_present() or not data.is_user_verified()
                or data.rp_id_hash != hashlib.sha256(RP_ID.encode()).digest()
                or (data.extensions or {}).get('credProtect') != 3):
            raise ContractError('Hardware enrollment lacked secret support, PIN or touch')
        credential = data.credential_data
        return dict(schema_version=1, label=label, rp_id=RP_ID, recipient=recipient,
                    credential_id=b64(credential.credential_id),
                    public_key=b64(cbor.encode(dict(credential.public_key))), salt=b64(os.urandom(32)))


def hardware_secret(header):
    from fido2 import cbor
    from fido2.cose import CoseKey
    if header['schema_version'] != 1 or header['rp_id'] != RP_ID:
        raise ContractError('Unrecognized recovery credential scope')
    with connected_client() as client:
        selected = client.get_assertion(dict(rpId=RP_ID, challenge=os.urandom(32), timeout=90000,
            allowCredentials=[dict(type='public-key', id=unb64(header['credential_id']))],
            userVerification='required', extensions=dict(hmacGetSecret=dict(salt1=unb64(header['salt'])))))
        response = selected.get_response(0)
        auth = response.response.authenticator_data
        if (response.raw_id != unb64(header['credential_id']) or not auth.is_user_present()
                or not auth.is_user_verified() or auth.rp_id_hash != hashlib.sha256(RP_ID.encode()).digest()):
            raise ContractError('Assertion lacked the registered key, PIN or touch')
        CoseKey.parse(cbor.decode(unb64(header['public_key']))).verify(
            auth + response.response.client_data.hash, response.response.signature)
        secret = response.client_extension_results.hmac_get_secret
        if secret is None or len(secret.output1) != 32:
            raise ContractError('Authenticator did not return the recovery secret')
        return secret.output1


def unlock(capsule, label):
    if capsule['schema_version'] != 1 or capsule['kind'] != 'fido2-wrapped-age-identity':
        raise ContractError('Unrecognized hardware recovery capsule')
    entries = [e for e in capsule['keys'] if e['header']['label'] == label]
    if len(entries) != 1 or entries[0]['header']['recipient'] != capsule['recipient']:
        raise ContractError('Recovery key label or recipient differs')
    return unseal(entries[0], hardware_secret(entries[0]['header']))


def prove_identity(age, age_hash, identity, recipient, folder):
    """Real encryption/decryption; the private identity travels only over stdin."""
    if sha(age) != age_hash:
        raise ContractError('Encryption executable changed')
    plain, encrypted, restored = folder / 'proof.txt', folder / 'proof.age', folder / 'proof-restored.txt'
    plain.write_bytes(os.urandom(64))
    try:
        subprocess.run([str(age), '-r', recipient, '-o', str(encrypted), str(plain)],
            check=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([str(age), '-d', '-i', '-', '-o', str(restored), str(encrypted)],
            check=True, input=identity, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if restored.read_bytes() != plain.read_bytes():
            raise ContractError('Recovered private key failed encryption proof')
    finally:
        for p in (plain, encrypted, restored):
            p.unlink(missing_ok=True)


def enroll_pair(root, age):
    root, age = private_directory(root), Path(age).resolve()
    final = root / 'recovery-capsule.json'
    partial = root / 'recovery-capsule.partial.json'
    if final.exists():
        raise ContractError('Completed enrollment already exists; never overwrite it')
    keygen = age.with_name('age-keygen.exe' if os.name == 'nt' else 'age-keygen')
    age_hash = sha(age)
    if partial.exists():
        capsule = read(partial)
        if [e['header']['label'] for e in capsule['keys']] not in (['primary'], ['primary', 'spare']):
            raise ContractError('Unexpected partial enrollment')
        print('Resume: connect ONLY the primary key to recover the existing identity.', flush=True)
        input('Press Enter when ready. ')
        identity = unlock(capsule, 'primary')
        recipient = capsule['recipient']
        prove_identity(age, age_hash, identity, recipient, root)
    else:
        identity = subprocess.check_output([str(keygen)], stderr=subprocess.DEVNULL)
        recipient = subprocess.check_output([str(keygen), '-y'], input=identity, stderr=subprocess.DEVNULL).decode().strip()
        capsule = dict(schema_version=1, kind='fido2-wrapped-age-identity', recipient=recipient, keys=[])
    for label in ('primary', 'spare'):
        print('\nUse the ' + label + ' key ONLY. Unplug other security keys.', flush=True)
        input('Connect it, then press Enter. ')
        if label == 'spare':
            from fido2.client import ClientError
            from fido2.ctap import CtapError
            try:
                hardware_secret(capsule['keys'][0]['header'])
            except ClientError as exc:
                # Only a genuine absent-credential response proves distinctness.
                if not isinstance(exc.cause, CtapError) or exc.cause.code != CtapError.ERR.NO_CREDENTIALS:
                    raise
            else:
                raise ContractError('Primary key still connected; spare must be a different device')
        if not any(e['header']['label'] == label for e in capsule['keys']):
            header = enroll_credential(label, recipient)
            entry = seal(identity, hardware_secret(header), header)
            capsule['keys'].append(entry)
            atomic(partial, capsule)
        print('Verify the ' + label + ' key with a fresh PIN-and-touch recovery.', flush=True)
        recovered = unlock(capsule, label)
        prove_identity(age, age_hash, recovered, recipient, root)
        del recovered
        print(label.capitalize() + ' recovery verified.', flush=True)
    atomic(final, capsule)
    (root / 'recipients.txt').write_text(recipient + '\n', encoding='utf-8')
    atomic(root / 'enrollment-status.json', dict(schema_version=1, status='both_hardware_keys_verified',
        recipient=recipient, capsule_sha256=sha(final), distinct_devices=True,
        pin_and_touch_required=True, plaintext_identity_written=False))
    partial.unlink()
    del identity
    return final
