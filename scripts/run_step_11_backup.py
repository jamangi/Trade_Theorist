"""Finite private backup/recovery commands. No recurrence, credentials or network."""
import argparse
import json
from pathlib import Path

from trade_theorist.private_backup import create_backup, restore_backup, retain_backups


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    backup = commands.add_parser('backup')
    backup.add_argument('--destination', type=Path, required=True)
    backup.add_argument('--keep', type=int, default=3)
    restore = commands.add_parser('restore')
    restore.add_argument('--bundle', type=Path, required=True)
    restore.add_argument('--destination', type=Path, required=True)
    restore.add_argument('--manifest-hash', required=True)
    prune = commands.add_parser('prune')
    prune.add_argument('--destination', type=Path, required=True)
    prune.add_argument('--keep', type=int, default=3)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    try:
        if args.action == 'backup':
            local = Path(json.loads((repo / '.local/step-11-task-plan/environment.json').read_text(encoding='utf-8-sig'))['local_app_data'])
            result = create_backup(repo, local / 'TradeTheorist/alpaca-market-data',
                local / 'TradeTheorist/quota-owners', args.destination, keep=args.keep)
        elif args.action == 'restore':
            result = restore_backup(args.bundle, args.destination, expected_hash=args.manifest_hash)
        else:
            result = retain_backups(args.destination, keep=args.keep)
        # Counts/hashes only; detailed receipts and payloads stay private.
        print(json.dumps({k: v for k, v in result.items() if k not in ('database', 'backup_path')}))
        return 0
    except Exception as exc:
        print(json.dumps(dict(status='failed', error_type=type(exc).__name__)))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
