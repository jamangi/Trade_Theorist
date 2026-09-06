"""Verify original golden accounting, then save only original synthetic evidence."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from trade_theorist.adapters.trader_user_sim import State, VERSION
from trade_theorist.contracts import validate_bundle
from trade_theorist.fixtures import base_records, EXP
from trade_theorist.fixtures_accounting_v2 import golden, broad_market, at
from trade_theorist.evaluate.portfolio_v2 import evaluate
from trade_theorist.migrate_v2 import migrate
from trade_theorist.storage import Store
from trade_theorist.storage_v2 import V2Store

ROOT = Path(__file__).resolve().parents[1]


def legacy(source):
    records = base_records()
    policy, exp, portfolio = (next(r for r in records if r["record_type"] == kind) for kind in ("policy", "experiment", "portfolio"))
    policy["limits"].update(initial_cash="1000.00", max_deployed_capital="1000.00")
    portfolio["initial_cash"] = "1000.00"
    exp.update(start_at=at(1), development_end_at="2098-12-29T00:00:00Z", validation_end_at="2098-12-30T00:00:00Z")
    source.put_records(records)
    serial = 0
    def emit(kind, day, **payload):
        nonlocal serial
        serial += 1
        source.append(f"event:original-v1-{serial}", EXP, "simulation", dict(version=VERSION, portfolio_id=portfolio["id"],
            type=kind, at=at(day), session=at(day)[:10], **payload), created_at=at(day))
    emit("funding", 1, amount="1000.00")
    for day, side, quantity, notional, fee, price in ((2,"buy","2","200.00","2.00","100"),
            (3,"buy","2","240.00","2.00","120"), (4,"sell","1","130.00","1.00","130")):
        oid="order:original-v1-"+str(day)
        emit("order", day, order_id=oid, order=dict(instrument_id="instrument:fixture-fund", side=side, quantity=quantity, reserved="0"))
        emit("fill", day, order_id=oid, notional=notional, fee=fee)
        emit("mark", day, marks={"instrument:fixture-fund": dict(price=price, session=at(day)[:10], at=at(day), phase="close")})
    emit("dividend_ex", 5, action_id="action:original-dividend", instrument_id="instrument:fixture-fund", amount="3.00", per_share="1")
    emit("dividend_pay", 6, action_id="action:original-dividend")
    emit("split", 7, instrument_id="instrument:fixture-fund", ratio="2")
    emit("mark", 8, marks={"instrument:fixture-fund": dict(price="65", session=at(8)[:10], at=at(8), phase="close")})


def old_values(store):
    state = State()
    for event in store.iter_events(EXP, "simulation"): state.apply(event["payload"])
    return dict(cash=str(state.cash), equity=str(state.equity()), realized=str(state.realized),
                basis=str(sum(state.basis.values())), income=str(state.income), accounting_method="historical-average-cost-v1")


def build():
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        with V2Store(root / "v2", synthetic=True) as store:
            baseline = broad_market(store)
            fixture = golden(store, baseline=baseline.portfolio)
            before_flow = evaluate(store, fixture.portfolio, effective_cutoff=at(8), receipt_cutoff=at(8))
            before_stale = evaluate(store, fixture.portfolio, effective_cutoff=at(11), receipt_cutoff=at(11))
            after_stale = evaluate(store, fixture.portfolio, effective_cutoff=at(12), receipt_cutoff=at(12))
            for key, expected in (("cash","1188.00000000"),("fifo_basis","343.00000000"),("realized","28.00000000")):
                assert before_stale[key] == expected
            assert before_stale["twr"]["value"] == "0.05750570"
            assert before_stale["max_drawdown"]["value"] == "0.01901141"
            assert after_stale["equity"]["value"] is None
            assert evaluate(store, fixture.portfolio, effective_cutoff=at(11), receipt_cutoff=at(11)) == before_stale
            checked = store.verify_v2()
            # A private-read-model consumer can resolve every identity from this original fixture bundle.
            persisted = list(store.iter_v2())
        with Store(root / "old", synthetic=True) as source:
            legacy(source)
            original, hashes = old_values(source), source.verify()
            conversion = migrate(source.path, synthetic=True, destination=root / "copy", apply=True)
            with V2Store(root / "copy", synthetic=True) as copied:
                assert old_values(copied) == original
                assert copied.verify()["v1"] == hashes
                assert not list(copied.iter_v2(kind="lot"))
            assert source.verify() == hashes
        assert original["equity"] == "1078.00"
        report = dict(provenance="original-synthetic", v1_before_external_flow=original,
            v2_before_external_flow={k: before_flow[k] for k in ("cash", "equity", "realized", "fifo_basis", "income", "twr")},
            v1_hashes_preserved=hashes, conversion_report=conversion, v2_verification=checked,
            interpretation="FIFO changes the realized/unrealized split, never total equity for identical fills. External-flow TWR remains a separate v2 calculation.")
        return {"before-stale.json": before_stale, "after-stale.json": after_stale, "side-by-side.json": report, "bundle.json": persisted}


if __name__ == "__main__":
    artifacts = build()
    destination = ROOT / "examples/accounting-v2"
    destination.mkdir(parents=True, exist_ok=True)
    validate_bundle(artifacts["bundle.json"])
    for name, content in artifacts.items():
        (destination / name).write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Verified golden v2 values, null stale state, matched baseline, preserved v1 replay and explicit conversion gaps")
