"""Rebuild original contract fixtures and a checked, temporary side-by-side migration."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from trade_theorist.contracts import validate_bundle
from trade_theorist.fixtures import base_records, EXP
from trade_theorist.fixtures_v2 import bundle
from trade_theorist.migrate_v2 import migrate
from trade_theorist.storage import Store
from trade_theorist.storage_v2 import V2Store
from trade_theorist.adapters.trader_user_sim import VERSION, State

ROOT = Path(__file__).resolve().parents[1]
AT = "2099-01-03T21:00:00Z"


def build():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        with Store(root / "source", synthetic=True) as source:
            source.put_records(base_records())
            source.append("event:step-01-funding", EXP, "simulation", dict(version=VERSION,
                portfolio_id="portfolio:fixture-council", type="funding", at=AT, amount="10000.00"), created_at=AT)
            preview = migrate(source.path, synthetic=True)
            applied = migrate(source.path, synthetic=True, destination=root / "destination", apply=True)
            repeated = migrate(source.path, synthetic=True, destination=root / "destination", apply=True)
            with V2Store(root / "destination", synthetic=True) as destination:
                checked = destination.verify()
                assert checked["v1"] == source.verify()
                states = []
                for store in (source, destination):
                    state = State()
                    for event in store.iter_events(EXP, "simulation"): state.apply(event["payload"])
                    states.append(vars(state))
                assert states[0] == states[1]
                copied_records = list(destination.iter_v2())
            source.append("event:step-01-gap", EXP, "simulation", dict(version=VERSION,
                portfolio_id="portfolio:fixture-council", type="halt", at=AT), created_at=AT)
            gap = migrate(source.path, synthetic=True)
    return dict(preview=preview, applied=applied, repeated=repeated, gap_preview=gap,
                verification=checked, v1_replay_equal=True), copied_records


if __name__ == "__main__":
    output = ROOT / "examples/contracts-v2"
    output.mkdir(parents=True, exist_ok=True)
    report, migrated = build()
    artifacts = {"bundle.json": bundle(), "migration-report.json": report, "migrated.bundle.json": migrated}
    for name, value in artifacts.items():
        if name.endswith("bundle.json"): validate_bundle(value)
        (output / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Built 3 original v2 artifacts; v1 hashes/replay preserved, duplicate apply reused, gaps explicit")
