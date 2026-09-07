"""Rebuild and verify original shared-forward evidence without reading large JSON."""
from pathlib import Path
from trade_theorist.forward.fixtures import build_evidence

if __name__ == "__main__":
    result = build_evidence(Path(__file__).resolve().parents[1] / "examples/step-07")
    print(f"PASS {result['scenarios']} original forward scenarios; zero account/model/broker calls")
