"""Rebuild the packaged offline heartbeat fixture."""
from pathlib import Path
from trade_theorist.heartbeat.fixture import *
from trade_theorist.heartbeat.fixture import _write

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    built = build()
    output = ROOT / "examples" / "heartbeat"
    _write(output / "bundle.json", built["bundle"])
    _write(output / "report.json", built["report"])
    _write(output / "events.json", built["events"])
    for relative, content in built["council_mail"].items():
        _write(output / "council-mail" / relative, content)
    for relative, content in built["individual_mail"].items():
        _write(output / "individual-mail" / relative, content)
    print("Built bounded council mail and isolated council/individual heartbeat fixtures.")
