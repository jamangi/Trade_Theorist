"""Run tests in separate, quiet processes; keep complete output in ignored logs."""

import argparse
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modules", nargs="*", help="Test module stems, e.g. test_simulation test_risk")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    modules = args.modules or [p.stem for p in sorted((root / "tests").glob("test_*.py"))]
    if any(not (root / "tests" / (m + ".py")).is_file() or not m.startswith("test_") or Path(m).name != m for m in modules):
        parser.error("Use existing test module stems")
    log_dir = root / ".local" / "test-logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    failed, started = [], time.monotonic()
    for module in modules:
        log = log_dir / (module + ".log")
        with log.open("w", encoding="utf-8") as output:
            result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", module + ".py", "-q"],
                                    cwd=root, stdout=output, stderr=subprocess.STDOUT)
        # Full tracebacks and unexpected test output stay on disk, never buffered here.
        if result.returncode:
            failed.append(module)
            print(f"FAIL {module}: {log.relative_to(root)}", flush=True)
        else:
            print(f"PASS {module}", flush=True)
    print(f"{len(modules) - len(failed)}/{len(modules)} modules passed in {time.monotonic() - started:.1f}s. Logs: .local/test-logs", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
