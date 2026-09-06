"""Rebuild equal-capital council/Character fixtures and an event-derived report."""

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from trade_theorist.adapters.trader_user_sim import Simulator
from trade_theorist.contracts import digest, validate_bundle
from trade_theorist.fixtures import base_records, CHAR, EXP, SOURCE
from trade_theorist.ingest.market import Normalized
from trade_theorist.storage import Store


def build():
    sessions = [dict(session=f"2099-01-{day:02d}", open_at=f"2099-01-{day:02d}T14:00:00Z",
                     close_at=f"2099-01-{day:02d}T21:00:00Z") for day in (3, 4, 5)]
    bundle, portfolios = [base_records()[0]], []
    for name in ("council", "index", "value", "trend"):
        original = base_records()[1:5]
        mapping = {r["id"]: r["id"] + "-" + name for r in original}
        def remap(value):
            if isinstance(value, dict):
                return {k: remap(v) for k, v in value.items()}
            if isinstance(value, list):
                return [remap(v) for v in value]
            return mapping.get(value, value) if isinstance(value, str) else value
        policy, character, experiment, portfolio = remap(deepcopy(original))
        character["character_id"] = name + "_simulation_fixture"
        policy.update(approval_ref="fixture-engineering-only-task-008", approved_at=policy["created_at"],
                      operator="fixture-owner", kill_switch_owner="fixture-owner", reconciliation_owner="fixture-owner",
                      incident_owner="fixture-owner")
        policy["costs"].update(fee_per_order="1.00", slippage_bps="10", spread_bps="2")
        experiment["costs"] = deepcopy(policy["costs"])
        if name != "council":
            experiment["mode"] = portfolio["mode"] = "character_portfolio"
        bundle.extend([policy, character, experiment, portfolio])
        bars, snapshots = [], []
        for day, price in ((3, "100"), (4, "102")):
            event_at, cutoff = f"2099-01-{day:02d}T21:00:00Z", f"2099-01-{day:02d}T21:02:00Z"
            payload = dict(kind="bar", instrument_id="instrument:fixture-fund", asset_class="unleveraged_us_etf", session=f"2099-01-{day:02d}",
                           event_at=event_at, published_at=event_at, ingested_at=event_at, feed="synthetic-v1", adjustment="raw",
                           open="100", high=price, low="100", close=price, volume="1000")
            common = dict(schema_version=1, experiment_id=mapping[EXP], contamination="fixture", created_at=cutoff)
            observation = dict(common, id=f"observation:sim-{name}-{day}", record_type="observation", instrument_id=payload["instrument_id"],
                               asset_class=payload["asset_class"], event_at=event_at, published_at=event_at, ingested_at=event_at,
                               availability_evidence="Original synthetic simulation bar", revision=1, supersedes_id=None, superseded_at=None,
                               feed="synthetic-v1", units="USD", payload_hash=digest(payload), quality="eligible", publication_eligibility="raw_permitted")
            snapshot = dict(common, id=f"snapshot:sim-{name}-{day}", record_type="snapshot", cutoff=cutoff, clock_policy=policy["clock"],
                            observation_ids=[observation["id"]], exclusions=[], content_hash=digest([observation]))
            bundle.extend([observation, snapshot])
            bars.append(Normalized(observation, payload))
            snapshots.append(snapshot)
        recommendation = dict(schema_version=1, record_type="recommendation", experiment_id=mapping[EXP], contamination="fixture",
                              created_at=snapshots[0]["cutoff"], id=f"recommendation:sim-{name}", character_version=mapping[CHAR],
                              portfolio_id=portfolio["id"], snapshot_id=snapshots[0]["id"], instrument_id="instrument:fixture-fund", action="buy",
                              quantity="10", horizon="one fixture session", confidence=0.5, confidence_event="fixture close above fill",
                              invalidation_conditions=["Missing eligible raw bar or policy rejection"], expires_at="2099-01-05T00:00:00Z",
                              citations=[dict(source_id=SOURCE, locator="fixture/section-1", passage_hash=digest("synthetic arithmetic"))],
                              abstention_reason=None, theory_ids=[])
        bundle.append(recommendation)
        portfolios.append((experiment, portfolio, bars, snapshots, recommendation))
    validate_bundle(bundle)
    reports = []
    with TemporaryDirectory() as directory, Store(directory, synthetic=True) as store:
        store.put_records(bundle)
        for experiment, portfolio, bars, snapshots, recommendation in portfolios:
            sim = Simulator(store, experiment["id"], portfolio["id"], sessions)
            sim.mark(snapshots[0]["id"], [bars[0]], at=snapshots[0]["cutoff"])
            result = sim.submit(recommendation["id"], at=recommendation["created_at"], price_cap="101")
            if result["status"] != "pending":
                raise RuntimeError("Fixture order unexpectedly rejected")
            sim.process_bar(bars[1], at=snapshots[1]["cutoff"])
            sim.mark(snapshots[1]["id"], [bars[1]], at=snapshots[1]["cutoff"])
            reports.append(dict(portfolio_id=portfolio["id"], experiment_id=experiment["id"], mode=portfolio["mode"],
                                evidence="fixture", **sim.reconcile(at=snapshots[1]["cutoff"])))
        store.verify()
    return dict(records=bundle, sessions=sessions, bars=[i.payload for entry in portfolios for i in entry[2]],
                report=dict(evidence="fixture", description="Scripted engineering examples; no real Character learning, recommendations or performance", portfolios=reports))


if __name__ == "__main__":
    result = build()
    root = Path(__file__).resolve().parents[1] / "examples" / "simulation"
    root.mkdir(parents=True, exist_ok=True)
    for name, value in (("bundle.json", result["records"]), ("sessions.json", result["sessions"]),
                        ("bars.json", result["bars"]), ("report.json", result["report"]),
                        ("policy.approved-fixture.json", result["records"][1])):
        (root / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print("Built and reconciled four isolated fixture portfolios: examples/simulation/report.json")
