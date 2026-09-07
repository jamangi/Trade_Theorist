"""Run a logged, finite Step 11 action. Safe default is a read-only report."""
import argparse
import json
import os
from pathlib import Path

from trade_theorist.observation_job import run_job


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['observe', 'report', 'check'], nargs='?', default='report')
    parser.add_argument('--notify', action='store_true', help='Show a bounded local warning on a changed failure')
    parser.add_argument('--local-app-data', type=Path, help='Pinned existing data/profile root from the installer')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    saved_environment = root / '.local/step-11-task-plan/environment.json'
    local = args.local_app_data
    if local is None and saved_environment.exists():
        local = Path(json.loads(saved_environment.read_text(encoding='utf-8-sig'))['local_app_data'])
    if local is None:
        # Windows packaged apps can redirect individual files into LocalCache.
        # Resolve the existing manifest, not an ancestor that may be a merged view.
        manifest = Path(os.environ['LOCALAPPDATA']) / 'TradeTheorist/alpaca-market-data/step-11-forward/manifest.json'
        local = manifest.resolve(strict=True).parents[3]
    os.environ['LOCALAPPDATA'] = str(local.resolve(strict=True))
    private = Path(os.environ['LOCALAPPDATA']) / 'TradeTheorist/alpaca-market-data'
    raise SystemExit(run_job(root, private, args.action, notify=args.notify))
