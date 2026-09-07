"""Interactive dedicated FIDO backup enrollment. Never resets existing credentials."""
import argparse
from pathlib import Path
from trade_theorist.hardware_recovery import enroll_pair
from trade_theorist.private_backup import atomic, private_directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--age', type=Path, required=True)
    args = parser.parse_args()
    result = 0
    try:
        enroll_pair(args.directory, args.age)
        print('\nBoth keys are verified. Store the spare securely away from the computer.')
    except Exception as exc:
        # PINs, identity bytes, credential IDs and provider diagnostics stay out of logs.
        print('\nSetup stopped: ' + type(exc).__name__ + '. No existing login credential was reset.')
        atomic(private_directory(args.directory) / 'setup-failure.json', dict(error_type=type(exc).__name__))
        result = 1
    input('Press Enter to close this window. ')
    return result


if __name__ == '__main__':
    raise SystemExit(main())
