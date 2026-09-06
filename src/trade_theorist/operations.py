"""Offline operating recipes; real prerequisites remain explicit, resumable blockers."""

from copy import deepcopy
from importlib.resources import files
import json
import sqlite3
from pathlib import Path
import os
import sys

from .adapters.trader_user_sim import Simulator
from .contracts import ContractError, digest
from .evaluate import Evaluator
from .heartbeat import HeartbeatInterrupted
from .heartbeat.fixture import build_records, FixtureScenario, SESSIONS, HEARTBEAT_AT, FINAL_AT
from .ingest.market import CSVMarketAdapter, Normalized, RevisionBook, SessionCalendar
from .storage import Store

DEMO_VERSION = "offline-observatory-v1"
REGISTERED_AT = "2098-12-01T00:00:00Z"
FINAL_CUTOFF = "2099-01-05T21:02:00Z"


def demo_setups():
    setups = []
    for name, council, reject in (("demo-council", True, True), ("demo-index", False, False),
                                   ("demo-value", False, False), ("demo-trend", False, False),
                                   ("demo-no-mail", True, True), ("demo-baseline", False, False),
                                   ("demo-counterfactual", True, True)):
        s = build_records(name, council=council, risk_reject=reject, include_source=not setups)
        if name == "demo-no-mail":
            s["experiment"]["advice"] = "none"
        if name == "demo-baseline":
            policy = next(r for r in s["records"] if r["record_type"] == "policy")
            policy["limits"]["turnover"] = 1.0
            s["final"]["quantity"] = "99.99"
        s["name"] = name
        s["trial_id"] = "trial:" + name
        s["role"] = "index_baseline" if name == "demo-baseline" else "counterfactual" if name == "demo-counterfactual" else "strategy"
        setups.append(s)
    return setups


def seed_demo(store):
    if not store.synthetic:
        raise ContractError("Demo requires an explicitly synthetic store")
    setups = demo_setups()
    store.put_records([r for s in setups for r in s["records"]])
    evaluator = Evaluator(store)
    for s in setups:
        evaluator.register_trial(s["trial_id"], s["experiment"]["id"], s["portfolio"]["id"], sessions=SESSIONS,
            family_id="family:offline-observatory", at=REGISTERED_AT, role=s["role"],
            baseline_trial_id=None if s["role"] == "index_baseline" else "trial:demo-baseline",
            rejected_decision_id=setups[0]["final"]["id"] if s["role"] == "counterfactual" else None)
        save_market(store, Normalized(s["observation"], s["payload"]))
        for suffix, outcome in (("mature", "2099-01-04T21:00:00Z"), ("pending", "2099-01-06T21:00:00Z")):
            evaluator.register_forecast("forecast:" + s["name"] + "-" + suffix, s["final"]["id"],
                outcome_at=outcome, threshold="100", probability="0.55", at=FINAL_AT)
    return setups


def save_market(store, item):
    o, bar = item.observation, item.payload
    if digest(bar) != o["payload_hash"]:
        raise ContractError("Market payload hash mismatch")
    with store.transaction():
        store.put_records([o])
        store.append("market:" + digest(o["id"]), o["experiment_id"], "market.payload",
                     dict(observation_id=o["id"], instrument_id=o["instrument_id"], event_at=o["event_at"], bar=bar), created_at=o["ingested_at"])


def fixture_heartbeat(store, setup, *, crash_after=None):
    scenario = FixtureScenario(store, setup, store.root / "mail" / setup["name"])
    return scenario.heartbeat().run(at=HEARTBEAT_AT, crash_after=crash_after)


def advance_fixture(store, setup):
    sim = Simulator(store, setup["experiment"]["id"], setup["portfolio"]["id"], SESSIONS)
    if setup["role"] != "strategy":
        sim.mark(setup["snapshot"]["id"], [Normalized(setup["observation"], setup["payload"])], at=setup["snapshot"]["cutoff"])
        sim.submit(setup["final"]["id"], at=FINAL_AT, price_cap="100")
    for day, opened, closed in ((4, "100", "102"), (5, "101", "99")):
        if day == 5 and setup["name"] == "demo-trend":
            continue  # Deliberately missing session: the dashboard must show stale data.
        effective = f"2099-01-{day:02d}T21:00:00Z"
        cutoff = f"2099-01-{day:02d}T21:02:00Z"
        bar = dict(setup["payload"], session=effective[:10], event_at=effective, published_at=effective,
                   ingested_at=effective, open=opened, close=closed, high=str(max(int(opened), int(closed))), low=str(min(int(opened), int(closed))))
        obs = dict(setup["observation"], id=f"observation:{setup['name']}-{day}", created_at=cutoff,
                   event_at=effective, published_at=effective, ingested_at=effective, payload_hash=digest(bar))
        save_market(store, Normalized(obs, bar))
        snap = dict(setup["snapshot"], id=f"snapshot:{setup['name']}-{day}", created_at=cutoff, cutoff=cutoff,
                    observation_ids=[obs["id"]], content_hash=digest([obs]))
        store.put_records([snap])
        if day == 5:
            sim.corporate_action("dividend:" + setup["name"], kind="dividend_ex", instrument_id=bar["instrument_id"],
                                 at="2099-01-05T13:00:00Z", value="1", evidence="Original demo ex-distribution fixture")
            sim.corporate_action("dividend:" + setup["name"], kind="dividend_pay", instrument_id=bar["instrument_id"],
                                 at="2099-01-05T13:01:00Z", evidence="Original demo payment fixture")
        sim.process_bar(Normalized(obs, bar), at=cutoff)
        sim.mark(snap["id"], [Normalized(obs, bar)], at=cutoff)
    return sim.reconcile(at=FINAL_CUTOFF)


def run_demo(data_root, *, crash_after=None):
    from .export import export_dashboard
    with Store(data_root, synthetic=True) as store:
        setups = seed_demo(store)
        code_root = Path(__file__).parent
        code_hash = digest({p.relative_to(code_root).as_posix(): digest(p.read_text(encoding="utf-8"))
                            for p in sorted(code_root.rglob("*.py"))})
        for setup in setups:
            store.append("demo-runtime:" + digest([setup["experiment"]["id"], code_hash]), setup["experiment"]["id"],
                         "run.provenance", {"recipe": DEMO_VERSION, "executing_source_hash": code_hash,
                                            "manifest_note": "Fixture manifests retain their historical specimen commit; this event pins executing source"})
        for s in setups:
            if s["role"] == "strategy":
                fixture_heartbeat(store, s, crash_after=crash_after)
            advance_fixture(store, s)
        evaluator = Evaluator(store)
        for s in setups:
            evaluator.trial_status(s["trial_id"], "partial", at=FINAL_CUTOFF)
        for cutoff in ("2099-01-04T21:02:00Z", FINAL_CUTOFF):
            for s in setups:
                evaluator.evaluate(s["trial_id"], as_of=cutoff)
        store.verify()
        result = export_dashboard(store, store.root / "public", as_of=FINAL_CUTOFF)
        return dict(status="fixture_only", version=DEMO_VERSION, portfolios=7, model_calls=0, network_calls=0,
                    report=str(result), resume="Repeat the same demo command; completed phases and fills are reused")


def ingest_csv(store, experiment_id, path, capability, sessions):
    exp = store.record(experiment_id, "experiment")
    policy = store.record(exp["policy_id"], "policy")
    if capability["feed"] not in exp["data_feeds"] or not capability["storage_retention"] or not capability["internal_replay"]:
        raise ContractError("CSV source needs pinned feed, storage and internal replay permissions")
    old = [Normalized(store.record(e["payload"]["observation_id"], "observation"), e["payload"]["bar"])
           for e in store.iter_events(experiment_id, "market.payload")]
    adapter = CSVMarketAdapter(experiment_id=experiment_id, contamination=exp["contamination"], universe=exp["universe"],
              calendar=SessionCalendar(policy["clock"]["calendar"], tuple(s["session"] for s in sessions)),
              capability=capability, revision_book=RevisionBook(old))
    accepted, quarantined = adapter.ingest(Path(path).read_text(encoding="utf-8"))
    for item in accepted:
        save_market(store, item)
    return dict(status="imported" if not quarantined else "partial", new_observations=len(accepted), quarantined=len(quarantined),
                reasons=sorted({q.reason for q in quarantined}), resume="Correct quarantined input rows, then repeat ingest with the same source")


def doctor(data_root=None, *, synthetic=False, policy_path=None):
    checks = [dict(name="Runtime", status="ready", action=f"Python {sys.version_info.major}.{sys.version_info.minor}; contract schema version 1"),
              dict(name="Optional model credentials", status="configured" if os.environ.get("OPENAI_API_KEY") else "not_configured",
                   action="The offline demo needs no credentials; no live model provider is enabled")]
    if data_root:
        try:
            with Store(data_root, synthetic=synthetic) as store:
                store.connection.execute("PRAGMA quick_check").fetchone()
            checks.append(dict(name="Private storage", status="ready", action="Storage is writable"))
        except (ValueError, OSError, sqlite3.Error):
            checks.append(dict(name="Private storage", status="blocked", action="Choose an absolute writable data root outside Git for real work"))
    else:
        checks.append(dict(name="Private storage", status="blocked", action="Set TRADE_THEORIST_DATA_ROOT or pass --data-root"))
    if policy_path:
        from .contracts import validate
        try:
            policy = json.loads(Path(policy_path).read_text(encoding="utf-8"))
            validate(policy)
            ready = policy["stage"] == "paper"
        except (ContractError, ValueError, OSError, KeyError):
            ready = False
        checks.append(dict(name="Paper policy", status="ready" if ready else "blocked", action="Record complete numeric limits and owner approval" if not ready else "Recorded paper policy structure is complete; readiness review is still required"))
    else:
        checks.append(dict(name="Paper policy", status="blocked", action="Supply an owner-approved numeric paper policy; the template is incomplete"))
    checks.extend([
        dict(name="Character learning", status="blocked", action="Verify the recorded Index foundation and finish Value/Trend reviewed learning. Use learn --character to inspect source-grounded status"),
        dict(name="Market source", status="blocked", action="Qualify a permitted vendor and session calendar; local permitted CSV ingestion is available"),
        dict(name="Offline demo", status="ready", action="Run trade-theorist demo; no accounts or external model needed"),
        dict(name="Real execution", status="blocked", action="Complete later forward-shadow and paper-readiness reviews; no live endpoint exists"),
    ])
    return dict(status="real_work_blocked", schema_version=1, checks=checks, secrets="Credential values are never inspected or printed")


def learn_plan(path, data_root, *, synthetic=False, expected_character=None):
    from .learn import BoundedModel, Learner, RecordedProvider
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {"records", "character_version", "constitution", "curriculum", "material", "source_id", "position", "outputs", "model_id", "prompt_version", "budget_id"}
    if set(plan) != required:
        raise ContractError("Reviewed learning plan has missing or unknown fields")
    provider = RecordedProvider(plan["outputs"])
    with Store(data_root, synthetic=synthetic) as store:
        store.put_records(plan["records"])
        character = store.record(plan["character_version"], "character")
        if expected_character and character["character_id"].removesuffix("_fixture") != expected_character:
            raise ContractError("Learning plan belongs to another Character")
        model = BoundedModel(store, character["experiment_id"], provider, budget_id=plan["budget_id"], model_id=plan["model_id"],
                             prompt_version=plan["prompt_version"], max_calls=len(plan["material"]["sections"]), max_tokens=100000, max_output_tokens=4000)
        learner = Learner(store, model)
        frozen = learner.freeze(**{k: plan[k] for k in ("character_version", "constitution", "curriculum", "material", "source_id", "position")})
        results = [learner.step(frozen, section_index=s["index"]) for s in plan["material"]["sections"]]
        return dict(status="reviewed_steps_saved", sections=len(results), checkpoint_ids=[r["id"] for r in results],
                    new_recorded_responses=provider.calls, external_model_calls=0, resume="Repeat this plan; committed checkpoints are reused")
