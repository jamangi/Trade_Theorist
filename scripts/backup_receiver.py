"""Bounded SSH command storing ciphertext only; standalone Python 3.12+.

Install under a revisioned owner-only directory. No listener, credentials,
decryption key, account client, shell command execution or scheduler.
"""
import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import sys
import time
import uuid

MAX_BYTES = 64 * 1024 * 1024
MAGIC = b'age-encryption.org/v1\n'


def stamp():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def atomic(path, value):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.partial')
    with temporary.open('x', encoding='utf-8') as out:
        json.dump(value, out, allow_nan=False); out.flush(); os.fsync(out.fileno())
    os.replace(temporary, path)
    if os.name != 'nt':
        fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def checksum(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def hexhash(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('Invalid digest')
    return value


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch('backup-[0-9a-f]{32}', value):
        raise ValueError('Invalid object identity')
    return value


@contextmanager
def exclusive(path):
    with path.open('a+b') as handle:
        if handle.tell() == 0:
            handle.write(b'0'); handle.flush()
        handle.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


class Receiver:
    def __init__(self, root):
        self.root = Path(root)
        if self.root.is_symlink():
            raise ValueError('Symlink root forbidden')
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name != 'nt' and (self.root.stat().st_uid != os.getuid() or self.root.stat().st_mode & 0o077):
            raise ValueError('Storage must be owner-only')
        for name in ('objects', 'incoming', 'receipts', 'operations'):
            path = self.root / name
            if path.is_symlink():
                raise ValueError('Symlink directory forbidden')
            path.mkdir(exist_ok=True, mode=0o700)
        marker = self.root / 'owner.json'
        expected = dict(schema_version=1, project='Trade_Theorist', ciphertext_only=True)
        if marker.exists() and read(marker) != expected:
            raise ValueError('Storage belongs to another project')
        if not marker.exists():
            atomic(marker, expected)

    def path(self, folder, name, suffix):
        p = self.root / folder / (identifier(name) + suffix)
        if p.is_symlink() or p.resolve().parent != (self.root / folder).resolve():
            raise ValueError('Unsafe object path')
        return p

    def verified_object(self, name):
        meta = read(self.path('receipts', name, '.json'))
        p = self.path('objects', name, '.age')
        if (meta['id'] != name or p.stat().st_size != meta['bytes']
                or checksum(p) != meta['ciphertext_hash']):
            raise ValueError('Ciphertext integrity failure')
        return meta, p

    def handle(self, request, source, output):
        action = request['action']
        with exclusive(self.root / 'receiver.lock'):
            if action == 'list':
                objects = []
                for p in sorted((self.root / 'receipts').glob('backup-*.json')):
                    try:
                        meta, _ = self.verified_object(p.stem)
                        objects.append(meta)
                    except (OSError, ValueError, KeyError):
                        objects.append(dict(id=p.stem, status='corrupt_or_missing'))
                return dict(objects=objects, partial_uploads=len(list((self.root / 'incoming').glob('*.partial'))))
            name = identifier(request['id'])
            if action == 'put':
                size, h = request['bytes'], hexhash(request['ciphertext_hash'])
                mh = hexhash(request['manifest_hash'])
                if type(size) is not int or not len(MAGIC) < size <= MAX_BYTES:
                    raise ValueError('Ciphertext size outside bound')
                final = self.path('objects', name, '.age')
                receipt = self.path('receipts', name, '.json')
                if final.exists() or receipt.exists():
                    # No overwrite, including after ambiguous process interruption.
                    raise ValueError('Object already exists; inspect before retry')
                temporary = self.root / 'incoming' / (name + '.' + uuid.uuid4().hex + '.partial')
                got, hasher = 0, hashlib.sha256()
                with temporary.open('xb') as out:
                    prefix = source.read(len(MAGIC))
                    if prefix != MAGIC:
                        raise ValueError('Only age ciphertext is accepted')
                    out.write(prefix); hasher.update(prefix); got += len(prefix)
                    while got < size:
                        data = source.read(min(65536, size - got))
                        if not data:
                            raise ValueError('Interrupted upload')
                        out.write(data); hasher.update(data); got += len(data)
                    if source.read(1) or hasher.hexdigest() != h:
                        raise ValueError('Ciphertext length or checksum differs')
                    out.flush(); os.fsync(out.fileno())
                os.replace(temporary, final)
                meta = dict(schema_version=1, id=name, bytes=size, ciphertext_hash=h,
                            manifest_hash=mh, uploaded_at=stamp(), status='uploaded_unverified')
                atomic(receipt, meta)
                return meta
            if action == 'get':
                meta, path = self.verified_object(name)
                if meta['ciphertext_hash'] != hexhash(request['ciphertext_hash']):
                    raise ValueError('Pinned ciphertext differs')
                with path.open('rb') as handle:
                    while data := handle.read(65536):
                        output.write(data)
                output.flush()
                return None
            if action == 'mark_verified':
                meta, _ = self.verified_object(name)
                if (meta['ciphertext_hash'] != hexhash(request['ciphertext_hash'])
                        or meta['manifest_hash'] != hexhash(request['manifest_hash'])):
                    raise ValueError('Round-trip receipt differs')
                meta.update(status='roundtrip_verified', verified_at=stamp())
                atomic(self.path('receipts', name, '.json'), meta)
                return meta
            if action == 'delete':
                # Caller has just downloaded/decrypted/restored the survivor.
                survivor = identifier(request['survivor'])
                if survivor == name:
                    raise ValueError('Cannot delete the verified survivor')
                keep, _ = self.verified_object(survivor)
                victim, path = self.verified_object(name)
                if (keep['status'] != 'roundtrip_verified' or victim['status'] != 'roundtrip_verified'
                        or keep['ciphertext_hash'] != hexhash(request['survivor_hash'])):
                    raise ValueError('Retention requires intact verified objects')
                # Paths are fixed files below the project root, never recursive.
                path.unlink()
                self.path('receipts', name, '.json').unlink()
                return dict(deleted=name, survivor=survivor)
            raise ValueError('Unsupported remote operation')

    def run(self, request, source, output):
        run = self.root / 'operations' / uuid.uuid4().hex
        run.mkdir(mode=0o700)
        began = time.monotonic()
        start = dict(schema_version=1, action=request.get('action'), started_at=stamp())
        atomic(run / 'start.json', start)
        def log(label):
            with (run / 'run.log').open('a') as out:
                out.write(label + ' ' + stamp() + '\n'); out.flush(); os.fsync(out.fileno())
        log('start')
        receipt = dict(start, exit_code=1, status='failed')
        try:
            result = self.handle(request, source, output)
            receipt.update(exit_code=0, status='process_succeeded')
            return result
        except Exception as exc:
            receipt['error_type'] = type(exc).__name__
            raise
        finally:
            receipt.update(ended_at=stamp(), duration_seconds=round(time.monotonic() - began, 3))
            atomic(run / 'receipt.json', receipt)
            log('end')


def main():
    os.umask(0o077)
    if hasattr(signal, 'alarm'):
        signal.alarm(120)
    try:
        if len(sys.argv) != 2 or len(sys.argv[1]) > 4096:
            raise ValueError('One bounded request is required')
        request = json.loads(base64.urlsafe_b64decode(sys.argv[1]))
        receiver = Receiver(Path.home() / '.local/share/trade-theorist-backups')
        result = receiver.run(request, sys.stdin.buffer, sys.stdout.buffer)
        if result is not None:
            print(json.dumps(result, allow_nan=False))
        return 0
    except Exception as exc:
        print(json.dumps(dict(status='failed', error_type=type(exc).__name__)), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
