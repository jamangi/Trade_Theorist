"""Explicit remote operations; hardware recovery prompts require --interactive."""
import argparse
import json
from pathlib import Path

from trade_theorist.remote_backup import load_config, publish_roundtrip, prune_remote


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['roundtrip', 'prune'])
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--local-root', type=Path, required=True)
    parser.add_argument('--identity', type=Path, required=True)
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--manifest-hash')
    parser.add_argument('--keep', type=int, default=3)
    parser.add_argument('--interactive', action='store_true')
    args = parser.parse_args()
    try:
        c = load_config(args.config)
        if args.action == 'roundtrip':
            if args.bundle is None or args.manifest_hash is None:
                parser.error('roundtrip requires --bundle and --manifest-hash')
            result = publish_roundtrip(c, args.bundle, args.local_root, args.identity,
                expected_hash=args.manifest_hash, interactive=args.interactive)
        else:
            result = prune_remote(c, args.local_root, args.identity, keep=args.keep, interactive=args.interactive)
        print(json.dumps({k: v for k, v in result.items() if k != 'database'}))
        return 0
    except Exception as exc:
        print(json.dumps(dict(status='failed', error_type=type(exc).__name__)))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
