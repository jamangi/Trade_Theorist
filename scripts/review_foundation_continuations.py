"""Reproduce the append-only participant gate after both completed foundations."""

import argparse
import json
from pathlib import Path

from trade_theorist.learn.continuation import REGISTER, audit_readiness_v2, check_saved_readiness_v2
from trade_theorist.learn.reviewed import write_once

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        register, versions = audit_readiness_v2(ROOT)
        for path, bundle in versions.items():
            write_once(ROOT / path, bundle)
        write_once(ROOT / REGISTER, register)
    result = check_saved_readiness_v2(ROOT)
    print(json.dumps(dict(participant_gate=result['participant_gate'], participants=[
        dict(character=p['character_id'], sections=p['sections_reviewed'], books=p['books_completed'],
             eligible=p['eligible']) for p in result['participants']]), indent=2))
