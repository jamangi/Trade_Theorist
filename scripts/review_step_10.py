"""Build or check the bounded participant-readiness review without source/model calls."""

import argparse
from pathlib import Path

from trade_theorist.learn.readiness import (
    REGISTER_PATH, VERSION_PATH, audit_readiness, check_saved_readiness,
)
from trade_theorist.learn.reviewed import write_once


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify committed evidence without writing")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.check:
        register = check_saved_readiness(root)
    else:
        register, bundle = audit_readiness(root)
        write_once(root / VERSION_PATH, bundle)
        write_once(root / REGISTER_PATH, register)
    for participant in register["participants"]:
        print(f"{participant['character_id']}: {participant['decision']}; {participant['sections_reviewed']} reviewed sections")
    print(f"Readiness evidence verified; participant gate: {register['participant_gate']}; Step 11: blocked")
    return 0  # A successfully reproduced blocked gate is a successful audit.


if __name__ == "__main__":
    raise SystemExit(main())
