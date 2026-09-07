"""Encrypt locally, transfer over pinned SSH, and prove an offline restore.

Only public recipients belong in configuration. Restore identity files are
provided explicitly; hardware-backed age identities can require PIN and touch.
"""
import base64
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tarfile
import uuid

from .contracts import ContractError, digest
from .market_requests import owner_lock
from .private_backup import (atomic, inside, logged, now, private_directory, read,
                             restore_backup, sha, verify_bundle)

MAX_CIPHERTEXT = 64 * 1024 * 1024
MAX_PLAINTEXT = 128 * 1024 * 1024
SSH_OPTIONS = ['-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
               '-o', 'ForwardAgent=no', '-o', 'ConnectTimeout=15',
               '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3', '-T']


def load_config(path):
    c = read(Path(path))
    if (c['schema_version'] != 1 or c['profile'] != 'crcs-lab'
            or not re.fullmatch('[0-9a-f]{64}', c['receiver_sha256'])
            or c['receiver_path'] != '/home/ubuntu/.local/lib/trade-theorist-backups/' + c['receiver_sha256'] + '/backup_receiver.py'
            or sha(Path(c['age_executable'])) != c['age_sha256']
            or sha(Path(c['recipients_file'])) != c['recipients_sha256']
            or not c['storage_terms_recorded']):
        raise ContractError('Remote destination, tool or recipient configuration differs')
    return c


class SSHReceiver:
    def __init__(self, config):
        self.config = config

    def call(self, request, *, source=None, destination=None):
        encoded = base64.urlsafe_b64encode(json.dumps(request, allow_nan=False).encode()).decode()
        # OpenSSH sends one remote command string; quote every argument there too.
        remote = ' '.join(shlex.quote(s) for s in ['python3', self.config['receiver_path'], encoded])
        args = ['ssh', *SSH_OPTIONS, self.config['profile'], remote]
        incoming = source.open('rb') if source else subprocess.DEVNULL
        outgoing = destination.open('xb') if destination else subprocess.PIPE
        try:
            result = subprocess.run(args, stdin=incoming, stdout=outgoing,
                                    stderr=subprocess.DEVNULL, timeout=135)
            if result.returncode:
                raise ContractError('Remote backup operation failed; inspect private receipts')
            if destination:
                outgoing.flush(); os.fsync(outgoing.fileno())
                return None
            if len(result.stdout) > 1024 * 1024:
                raise ContractError('Remote response exceeds metadata limit')
            return json.loads(result.stdout)
        finally:
            if source:
                incoming.close()
            if destination:
                outgoing.close()


def run_age(config, arguments, *, interactive=False):
    if sha(Path(config['age_executable'])) != config['age_sha256']:
        raise ContractError('Encryption executable changed')
    env = dict(os.environ)
    if config.get('plugin_directory'):
        # Pin plugin bytes just as the encryption executable; never trust PATH
        # to select a different hardware implementation during recovery.
        for name, expected in config['plugin_hashes'].items():
            if Path(name).name != name or sha(Path(config['plugin_directory']) / name) != expected:
                raise ContractError('Hardware plugin changed')
        env['PATH'] = config['plugin_directory'] + os.pathsep + env.get('PATH', '')
    arguments = list(arguments)
    secret_input = None
    hardware = config.get('identity_mode') == 'fido2_envelope' and '--decrypt' in arguments
    if hardware:
        from .hardware_recovery import unlock
        if not interactive:
            raise ContractError('FIDO recovery requires an interactive PIN-and-touch session')
        capsule = Path(arguments[arguments.index('--identity') + 1])
        if sha(capsule) != config['capsule_sha256']:
            raise ContractError('Recovery capsule differs from independent pin')
        secret_input = unlock(read(capsule), config['hardware_key_label'])
        arguments[arguments.index('--identity') + 1] = '-'
    input_options = dict(input=secret_input) if hardware else dict(stdin=None if interactive else subprocess.DEVNULL)
    result = subprocess.run([config['age_executable'], *arguments],
        **input_options, stdout=subprocess.DEVNULL,
        stderr=None if interactive else subprocess.DEVNULL, env=env, timeout=180)
    if result.returncode:
        raise ContractError('Encryption or authenticated decryption failed')


def pack_bundle(bundle, archive, expected_hash):
    verify_bundle(bundle, expected_hash=expected_hash)
    manifest = read(bundle / 'backup.json')
    names = ['backup.json', *('payload/' + n for n in manifest['files'])]
    if sum((inside(bundle, n).stat().st_size for n in names)) > MAX_PLAINTEXT:
        raise ContractError('Bundle exceeds finite archive limit')
    with tarfile.open(archive, 'x:gz') as out:
        for name in sorted(names):
            p = inside(bundle, name)
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = p.stat().st_size, 0o600, 0
            with p.open('rb') as src:
                out.addfile(info, src)


def unpack_bundle(archive, destination, expected_hash):
    destination.mkdir()
    seen, total = set(), 0
    with tarfile.open(archive, 'r:gz') as source:
        for member in source:
            if not member.isfile() or member.name in seen or len(seen) >= 20000:
                raise ContractError('Archive contains links, duplicates or unsupported members')
            total += member.size
            if member.size < 0 or total > MAX_PLAINTEXT:
                raise ContractError('Archive exceeds finite extraction limit')
            target = inside(destination, member.name)
            seen.add(member.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.extractfile(member) as src, target.open('xb') as out:
                while data := src.read(65536):
                    out.write(data)
                out.flush(); os.fsync(out.fileno())
    manifest = read(destination / 'backup.json')
    expected = {'backup.json', *('payload/' + n for n in manifest['files'])}
    if seen != expected or digest(manifest) != expected_hash:
        raise ContractError('Archive members or manifest identity differ')
    return verify_bundle(destination, expected_hash=expected_hash)


def download_restore(config, receiver, metadata, directory, identity, *, interactive=False, synthetic=False):
    """No upload cache or source bundle is used on this recovery path."""
    directory = private_directory(directory, synthetic=synthetic)
    ciphertext = directory / 'download.age'
    receiver.call(dict(action='get', id=metadata['id'], ciphertext_hash=metadata['ciphertext_hash']), destination=ciphertext)
    if (ciphertext.stat().st_size != metadata['bytes'] or ciphertext.stat().st_size > MAX_CIPHERTEXT
            or sha(ciphertext) != metadata['ciphertext_hash']):
        raise ContractError('Downloaded ciphertext differs')
    plaintext = directory / 'decrypted.tar.gz.partial'
    try:
        run_age(config, ['--decrypt', '--identity', str(identity), '--output', str(plaintext), str(ciphertext)], interactive=interactive)
        unpack_bundle(plaintext, directory / 'bundle', metadata['manifest_hash'])
        result = restore_backup(directory / 'bundle', directory / 'offline-restore',
                                expected_hash=metadata['manifest_hash'], synthetic=synthetic)
    finally:
        # age can emit a plaintext prefix before rejecting a later bad chunk.
        # Never keep that intermediate or treat it as a restored bundle.
        plaintext.unlink(missing_ok=True)
    return result


def publish_roundtrip(config, bundle, root, identity, *, expected_hash, interactive=False, synthetic=False, receiver=None):
    root = private_directory(root, synthetic=synthetic)
    receiver = receiver or SSHReceiver(config)
    def operation():
        with owner_lock(root / 'remote.lock'):
            identifier = 'backup-' + uuid.uuid4().hex
            work = root / identifier
            work.mkdir()
            archive, ciphertext = work / 'bundle.tar.gz', work / 'upload.age'
            try:
                pack_bundle(Path(bundle), archive, expected_hash)
                if sha(Path(config['recipients_file'])) != config['recipients_sha256']:
                    raise ContractError('Recipients changed')
                run_age(config, ['--recipients-file', config['recipients_file'], '--output', str(ciphertext), str(archive)])
            finally:
                archive.unlink(missing_ok=True)
            if ciphertext.stat().st_size > MAX_CIPHERTEXT:
                raise ContractError('Ciphertext exceeds finite transfer limit')
            metadata = dict(id=identifier, bytes=ciphertext.stat().st_size,
                            ciphertext_hash=sha(ciphertext), manifest_hash=expected_hash)
            atomic(work / 'pinned-object.json', metadata)
            uploaded = receiver.call(dict(action='put', **metadata), source=ciphertext)
            if any(uploaded.get(k) != v for k, v in metadata.items()):
                raise ContractError('Upload receipt differs')
            result = download_restore(config, receiver, metadata, work / 'roundtrip', Path(identity),
                                      interactive=interactive, synthetic=synthetic)
            marked = receiver.call(dict(action='mark_verified', id=identifier,
                ciphertext_hash=metadata['ciphertext_hash'], manifest_hash=expected_hash))
            if marked.get('status') != 'roundtrip_verified' or any(marked.get(k) != v for k, v in metadata.items()):
                raise ContractError('Remote verification receipt differs')
            atomic(root / 'verified-remote' / (identifier + '.json'), marked)
            return dict(result, remote_id=identifier, ciphertext_hash=metadata['ciphertext_hash'],
                        ciphertext_bytes=metadata['bytes'], remote_recovery_verified=True,
                        hardware_custody_verified=config.get('identity_mode') == 'fido2_envelope',
                        restored_account_activation_allowed=False)
    return logged(root, 'remote_roundtrip', operation)


def prune_remote(config, root, identity, *, keep=3, interactive=False, synthetic=False, receiver=None):
    if type(keep) is not int or keep < 1:
        raise ValueError('Keep at least one round-trip-verified backup')
    root = private_directory(root, synthetic=synthetic)
    receiver = receiver or SSHReceiver(config)
    with owner_lock(root / 'remote.lock'):
        listing = receiver.call(dict(action='list'))['objects']
        candidates = []
        for obj in listing:
            if obj.get('status') != 'roundtrip_verified':
                continue
            if not re.fullmatch('backup-[0-9a-f]{32}', obj['id']):
                raise ContractError('Invalid remote object identity')
            pin = root / 'verified-remote' / (obj['id'] + '.json')
            if not pin.is_file():
                continue  # Never delete objects outside this installation's receipt set.
            saved = read(pin)
            if any(obj[k] != saved[k] for k in ('id', 'ciphertext_hash', 'manifest_hash', 'bytes')):
                raise ContractError('Remote receipt differs from independent local pin')
            candidates.append(obj)
        candidates.sort(key=lambda obj: obj['uploaded_at'], reverse=True)
        if len(candidates) <= keep:
            return dict(removed=0, verified_retained=len(candidates))
        survivor = candidates[0]
        def operation():
            download_restore(config, receiver, survivor, root / ('retention-proof-' + uuid.uuid4().hex),
                             Path(identity), interactive=interactive, synthetic=synthetic)
            removed = 0
            for old in candidates[keep:]:
                response = receiver.call(dict(action='delete', id=old['id'], survivor=survivor['id'],
                                              survivor_hash=survivor['ciphertext_hash']))
                if response.get('deleted') != old['id'] or response.get('survivor') != survivor['id']:
                    raise ContractError('Unexpected retention receipt')
                removed += 1
            return dict(manifest_hash=survivor['manifest_hash'], removed=removed, verified_retained=keep)
        return logged(root, 'remote_retention', operation)
