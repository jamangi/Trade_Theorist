"""Verify existing private Step 11 evidence; publish only counts and hashes."""
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from trade_theorist.observation_job import atomic, read
from trade_theorist.readiness_audit import verify_saved_trial


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-app-data', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    # No account clients and no network escape through Python sockets.
    try:
        local = args.local_app_data
        if local is None:
            local = Path(read(repo / '.local/step-11-task-plan/environment.json')['local_app_data'])
        with patch('socket.socket.connect', side_effect=RuntimeError('Audit network forbidden')), \
             patch('socket.socket.connect_ex', side_effect=RuntimeError('Audit network forbidden')), \
             patch('socket.create_connection', side_effect=RuntimeError('Audit network forbidden')):
            result = verify_saved_trial(repo, local / 'TradeTheorist/alpaca-market-data')
    except Exception as exc:
        # Do not leak private paths/values via exception messages or keep a stale PASS.
        atomic(args.output, dict(schema_version=1, status='verification_failed', error_type=type(exc).__name__,
            checked_at=datetime.now(timezone.utc).isoformat(), promotion_eligible=False))
        print('FAIL: saved evidence verification ('+type(exc).__name__+')')
        return 1
    result.update(status='verified', checked_at=datetime.now(timezone.utc).isoformat())
    paths = sorted((repo / 'src/trade_theorist').rglob('*.py'))
    paths += sorted((repo / 'src/trade_theorist/migrations').glob('*.sql'))
    paths += sorted((repo / 'tests').glob('*.py')) + [Path(__file__).resolve()]
    result['source_sha256'] = {p.relative_to(repo).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    atomic(args.output, result)
    print('VERIFIED: saved evidence; '+result['stage_decision']+'; zero account calls')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
