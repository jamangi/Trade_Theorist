"""Install one immutable, owner-only SSH receiver; no daemon or new SSH identity."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

from trade_theorist.remote_backup import SSH_OPTIONS

INSTALL = '''import base64, hashlib, json, os
from pathlib import Path
os.umask(0o077)
p=json.load(__import__('sys').stdin)
data=base64.b64decode(p['source'])
h=hashlib.sha256(data).hexdigest()
assert h==p['sha256']
root=Path.home()/'.local/lib/trade-theorist-backups'
assert not root.is_symlink()
root.mkdir(parents=True,exist_ok=True,mode=0o700)
assert root.stat().st_uid==os.getuid() and root.stat().st_mode & 0o077 == 0
release=root/h
assert not release.is_symlink()
release.mkdir(exist_ok=True,mode=0o700)
target=release/'backup_receiver.py'
assert not target.is_symlink()
if target.exists():
    assert hashlib.sha256(target.read_bytes()).hexdigest()==h
else:
    with target.open('xb') as out:
        out.write(data);out.flush();os.fsync(out.fileno())
target.chmod(0o600)
print(json.dumps(dict(receiver_path=str(target),receiver_sha256=h)))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    path = Path(__file__).with_name('backup_receiver.py')
    data = path.read_bytes()
    h = hashlib.sha256(data).hexdigest()
    # Deploy only the committed receiver bytes, preserving a reproducible release.
    root = path.resolve().parents[1]
    committed = subprocess.check_output(['git', '-c', 'safe.directory=' + root.as_posix(), '-C', str(root), 'show', 'HEAD:scripts/backup_receiver.py'])
    if committed.replace(b'\r\n', b'\n') != data.replace(b'\r\n', b'\n'):
        raise SystemExit('Commit receiver changes before deployment')
    if not args.install:
        print(json.dumps(dict(profile='crcs-lab', receiver_sha256=h, action='preview')))
        return
    request = json.dumps(dict(source=base64.b64encode(data).decode(), sha256=h)).encode()
    command = 'python3 -c ' + shlex.quote(INSTALL)
    result = subprocess.run(['ssh', *SSH_OPTIONS, 'crcs-lab', command], input=request,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=45)
    if result.returncode:
        raise SystemExit('Receiver installation failed')
    response = json.loads(result.stdout)
    if response['receiver_sha256'] != h:
        raise SystemExit('Installed receiver differs')
    print(json.dumps(response))


if __name__ == '__main__':
    main()
