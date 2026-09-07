"""Independent offline preflight; portable evidence, quiet console, local tracebacks."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "tests"))
    from test_request_preflight import RequestPreflight
    records = []

    class Result(unittest.TextTestResult):
        def startTest(self, test):
            super().startTest(test)
            self.outcome = "pass"
            self.detail = None

        def addFailure(self, test, err):
            self.outcome = "fail"
            self.detail = str(err[1])[:500]
            super().addFailure(test, err)

        def addError(self, test, err):
            self.outcome = "error"
            self.detail = type(err[1]).__name__ + ": " + str(err[1])[:500]
            super().addError(test, err)

        def stopTest(self, test):
            records.append(dict(test=test.id().split(".")[-1], status=self.outcome, failure=self.detail, evidence=test.evidence))
            print(f"{self.outcome.upper()} {records[-1]['test']}", flush=True)
            super().stopTest(test)

    paths = sorted((root / "src" / "trade_theorist").rglob("*.py")) + sorted((root / "src" / "trade_theorist" / "migrations").glob("*.sql"))
    paths += [root / "tests" / name for name in ("preflight_support.py", "preflight_worker.py", "test_request_preflight.py")]
    paths += [Path(__file__).resolve()]
    hashes = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    source = subprocess.run(["git", "-c", f"safe.directory={root.as_posix()}", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    log = root / ".local" / "preflight-logs" / (args.output.stem + ".log")
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8") as out:
        result = unittest.TextTestRunner(stream=out, verbosity=2, resultclass=Result).run(unittest.defaultTestLoader.loadTestsFromTestCase(RequestPreflight))
    artifact = dict(version="step-08-independent-preflight-v1", recorded_at=datetime.now(timezone.utc).isoformat(),
        source_base_commit=source, source_sha256=hashes, status="pass" if result.wasSuccessful() else "fail", tests=records,
        scope="Original synthetic inputs and transport-side timestamps; socket networking forbidden. Production HTTP boundary mocked with real waiting.",
        guarantee="Cooperating callers only; unknown outside account traffic is not measured.",
        remaining_gates=["Step 09 real-source qualification and rights", "Step 12 final audit", "Step 13 separate live paper Trading adapter/quota policy"],
        retained_blockers=[dict(id="live-trading-quota-unimplemented", status="not_implemented",
            blocks="Live paper Trading quota verification and operation; Market Data rejects Trading policies and URLs.",
            next_owner="Step 13, after its stage decision; does not block Step 09 Market Data qualification.")],
        account_calls=0, orders=0, promotion_eligible=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"{artifact['status'].upper()}: {len(records)} cases; evidence: {args.output}; tracebacks: {log.relative_to(root)}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
