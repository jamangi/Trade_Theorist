"""Explicit remote operations; hardware recovery prompts require --interactive."""
import argparse
import json
from pathlib import Path

from trade_theorist.remote_backup import load_config, publish_roundtrip, prune_remote, download_restore, SSHReceiver
from trade_theorist.private_backup import read, sha, private_directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['roundtrip', 'prune', 'restore', 'fetch-capsule'])
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--local-root', type=Path, required=True)
    parser.add_argument('--identity', type=Path)
    parser.add_argument('--key', choices=['primary', 'spare'])
    parser.add_argument('--metadata', type=Path)
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--manifest-hash')
    parser.add_argument('--keep', type=int, default=3)
    parser.add_argument('--interactive', action='store_true')
    args = parser.parse_args()
    try:
        c = load_config(args.config, capsule_only=args.action == 'fetch-capsule')
        if args.key:
            c['hardware_key_label'] = args.key
        if args.action != 'fetch-capsule' and args.identity is None:
            parser.error('This operation requires --identity')
        if args.action == 'roundtrip':
            if args.bundle is None or args.manifest_hash is None:
                parser.error('roundtrip requires --bundle and --manifest-hash')
            result = publish_roundtrip(c, args.bundle, args.local_root, args.identity,
                expected_hash=args.manifest_hash, interactive=args.interactive)
        elif args.action == 'prune':
            result = prune_remote(c, args.local_root, args.identity, keep=args.keep, interactive=args.interactive)
        elif args.action == 'restore':
            if args.metadata is None:
                parser.error('restore requires --metadata')
            result = download_restore(c, SSHReceiver(c), read(args.metadata), args.local_root,
                                      args.identity, interactive=args.interactive)
        else:
            target = private_directory(args.local_root) / 'recovery-capsule.json'
            SSHReceiver(c).call(dict(action='get_capsule', capsule_hash=c['capsule_sha256']), destination=target)
            if sha(target) != c['capsule_sha256']:
                raise ValueError('Downloaded capsule differs')
            result = dict(capsule_sha256=c['capsule_sha256'], status='encrypted_capsule_retrieved')
        print(json.dumps({k: v for k, v in result.items() if k != 'database'}))
        return 0
    except Exception as exc:
        print(json.dumps(dict(status='failed', error_type=type(exc).__name__)))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
