"""Build deterministic council-mail and two-mode heartbeat examples."""

from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from trade_theorist.adapters.trader_user_sim import Simulator
from trade_theorist.contracts import digest, validate_bundle
from trade_theorist.council import Council
from trade_theorist.fixtures import base_records, CONSTITUTION, CURRICULUM, SOURCE
from trade_theorist.heartbeat import Heartbeat, ModelCallCache, PHASES
from trade_theorist.ingest.market import Normalized
from trade_theorist.storage import Store



FIXTURE_BASE_COMMIT = "2524a733a4cc69ce4ae385f2ae05fa980469cc98"
SESSION = "2099-01-03"
CUTOFF = "2099-01-03T21:02:00Z"
OPINION_AT = "2099-01-03T21:05:00Z"
DISCUSSION_AT = "2099-01-03T21:06:00Z"
FINAL_AT = "2099-01-03T21:09:00Z"
HEARTBEAT_AT = "2099-01-03T21:10:00Z"
DEADLINE = "2099-01-03T21:20:00Z"
EXPIRES = "2099-01-05T00:00:00Z"
SESSIONS = [
    {"session": "2099-01-03", "open_at": "2099-01-03T14:00:00Z", "close_at": "2099-01-03T21:00:00Z"},
    {"session": "2099-01-04", "open_at": "2099-01-04T14:00:00Z", "close_at": "2099-01-04T21:00:00Z"},
    {"session": "2099-01-05", "open_at": "2099-01-05T14:00:00Z", "close_at": "2099-01-05T21:00:00Z"},
]


def _record(experiment_id, kind, identifier, **fields):
    return {"id": identifier, "schema_version": 1, "record_type": kind,
            "experiment_id": experiment_id, "created_at": "2026-09-05T12:00:00Z",
            "contamination": "fixture", **fields}


def _remap(value, mapping):
    if isinstance(value, dict):
        return {key: _remap(item, mapping) for key, item in value.items()}
    if isinstance(value, list):
        return [_remap(item, mapping) for item in value]
    return mapping.get(value, value) if isinstance(value, str) else value


def build_records(name, *, council=True, risk_reject=False, include_source=True):
    source, policy, character, experiment, portfolio, _ = deepcopy(base_records())
    suffix = "-heartbeat-" + name
    mapping = {policy["id"]: policy["id"] + suffix, character["id"]: character["id"] + suffix,
               experiment["id"]: experiment["id"] + suffix, portfolio["id"]: portfolio["id"] + suffix}
    policy, character, experiment, portfolio = _remap([policy, character, experiment, portfolio], mapping)
    experiment_id = experiment["id"]
    policy.update(approval_ref="fixture-engineering-only-task-010", approved_at=policy["created_at"],
                  operator="fixture-owner", kill_switch_owner="fixture-owner",
                  reconciliation_owner="fixture-owner", incident_owner="fixture-owner")
    policy["costs"].update(fee_per_order="1.00", slippage_bps="0", spread_bps="0")
    policy["limits"]["turnover"] = 0.2
    experiment.update(advice="bounded", costs=deepcopy(policy["costs"]))
    character.update(character_id=("council_lead" if council else "individual_owner") + "_fixture")
    if not council:
        experiment["mode"] = portfolio["mode"] = "character_portfolio"
    characters = [character]
    if council:
        for slug in ("value_adviser", "trend_adviser"):
            adviser = deepcopy(character)
            adviser.update(id=f"character:{slug.replace('_', '-')}-fixture-{name}", character_id=slug + "_fixture")
            characters.append(adviser)
        experiment["character_versions"] = [item["id"] for item in characters]
    payload = {"kind": "bar", "instrument_id": "instrument:fixture-fund",
               "asset_class": "unleveraged_us_etf", "session": SESSION,
               "event_at": "2099-01-03T21:00:00Z", "published_at": "2099-01-03T21:00:00Z",
               "ingested_at": "2099-01-03T21:00:00Z", "feed": "synthetic-v1",
               "adjustment": "raw", "open": "100", "high": "100", "low": "100",
               "close": "100", "volume": "1000"}
    observation = _record(experiment_id, "observation", f"observation:heartbeat-{name}",
                          instrument_id=payload["instrument_id"], asset_class=payload["asset_class"],
                          event_at=payload["event_at"], published_at=payload["published_at"],
                          ingested_at=payload["ingested_at"], availability_evidence="Original synthetic heartbeat bar",
                          revision=1, supersedes_id=None, superseded_at=None, feed=payload["feed"], units="USD",
                          payload_hash=digest(payload), quality="eligible", publication_eligibility="raw_permitted")
    observation["created_at"] = CUTOFF
    snapshot = _record(experiment_id, "snapshot", f"snapshot:heartbeat-{name}", cutoff=CUTOFF,
                       clock_policy=policy["clock"], observation_ids=[observation["id"]], exclusions=[],
                       content_hash=digest([observation]))
    snapshot["created_at"] = CUTOFF
    conversation = _record(experiment_id, "conversation", f"conversation:heartbeat-{name}",
                           participant_character_versions=[item["id"] for item in characters],
                           snapshot_id=snapshot["id"], portfolio_id=portfolio["id"], deadline=DEADLINE)
    conversation["created_at"] = CUTOFF
    citation = {"source_id": SOURCE, "locator": "fixture/section-1", "passage_hash": digest("synthetic arithmetic")}
    actions = (["abstain", "wait", "buy"] if council else ["buy"])
    recommendations = []
    for index, (owner, action) in enumerate(zip(characters, actions)):
        active = action == "buy"
        item = _record(experiment_id, "recommendation", f"recommendation:heartbeat-{name}-initial-{index}",
                       character_version=owner["id"], portfolio_id=portfolio["id"], snapshot_id=snapshot["id"],
                       instrument_id="instrument:fixture-fund" if active else None, action=action,
                       quantity="10" if active else "0", horizon="one fixture session", confidence=0.55,
                       confidence_event="Original fixture opinion; no real-performance claim",
                       invalidation_conditions=["The frozen fixture context changes"], citations=[citation],
                       expires_at=EXPIRES, abstention_reason=None if active else "Fixture evidence does not require activity",
                       theory_ids=[])
        item["created_at"] = "2099-01-03T21:03:00Z"
        recommendations.append(item)
    final = deepcopy(recommendations[0])
    final.update(id=f"recommendation:heartbeat-{name}-final", created_at="2099-01-03T21:08:00Z",
                 action="buy", instrument_id="instrument:fixture-fund",
                 quantity="25" if risk_reject else "10", abstention_reason=None,
                 confidence_event="Fixture final after bounded disagreement")
    records = ([source] if include_source else []) + [policy, *characters, experiment, portfolio,
                                                       observation, snapshot, conversation, *recommendations, final]
    phase_inputs = {
        "freeze_snapshot": {"snapshot_id": snapshot["id"], "snapshot_hash": digest(snapshot)},
        "mark_portfolio": {"portfolio_id": portfolio["id"], "snapshot_id": snapshot["id"], "bar_hash": digest(payload)},
        "deliver_mail": {"conversation_id": conversation["id"], "eligible_at": DISCUSSION_AT},
        "independent_opinions": {"characters": [item["id"] for item in characters],
                                 "expected_recommendations": [item["id"] for item in recommendations],
                                 "model_id": "recorded-heartbeat-fixture-v1", "prompt_version": "independent-opinion-v1"},
        "deliberation": {"conversation_id": conversation["id"], "rounds": 1,
                         "questions_per_character": 1, "recipients_per_question": 2},
        "final_decisions": {"recommendation_ids": [final["id"]]},
        "risk_gate": {"policy_id": policy["id"], "candidate_ids": [final["id"]]},
        "queue_execution": {"endpoint": "simulation", "price_cap": "100"},
        "evaluation_handoff": {"window": "pending-next-eligible-event"},
        "export_handoff": {"format": "generated-mail-v1", "visibility": "fixture"},
    }
    run = _record(experiment_id, "run_manifest", f"run:heartbeat-{name}", mode=experiment["mode"],
                  code_commit=FIXTURE_BASE_COMMIT, policy_version=policy["version"], source_revisions=[digest(payload)],
                  character_versions=[item["id"] for item in characters], model_id="recorded-heartbeat-fixture-v1",
                  prompt_version="independent-opinion-v1", sampling={"temperature": 0, "seed": 0},
                  market_cutoff=CUTOFF, knowledge_cutoff=experiment["knowledge_cutoff"],
                  input_hash=digest({"phases": PHASES, "phase_inputs": phase_inputs}), output_hash=None,
                  phase_status={"prepare": "pending", "execute": "pending", "export": "pending"},
                  usage={"input_tokens": 0, "output_tokens": 0, "calls": 0, "cost_usd": "0.00"},
                  failure=None, resume_from=None, parent_run_id=None)
    records.append(run)
    if include_source:
        validate_bundle(records)
    return {"records": records, "phase_inputs": phase_inputs, "payload": payload,
            "observation": observation, "snapshot": snapshot, "conversation": conversation,
            "characters": characters, "recommendations": recommendations, "final": final,
            "run": run, "portfolio": portfolio, "experiment": experiment}


class RecordedOpinionProvider:
    def __init__(self):
        self.calls = 0

    def __call__(self, request, _maximum):
        self.calls += 1
        return {"response": {"recommendation_id": request["expected_recommendation_id"]},
                "usage": {"input_tokens": 40, "output_tokens": 8, "calls": 1, "cost_usd": "0.00"}}


class FixtureScenario:
    def __init__(self, store, setup, export_root, provider=None):
        self.store, self.setup = store, setup
        self.export_root = Path(export_root).resolve()
        self.provider = provider or RecordedOpinionProvider()
        self.council = Council(store, setup["conversation"]["id"]) if setup["experiment"]["advice"] == "bounded" else None
        self.simulator = Simulator(store, setup["experiment"]["id"], setup["portfolio"]["id"], SESSIONS)
        self.model = ModelCallCache(store, setup["experiment"]["id"], self.provider,
                                    budget_id="budget:heartbeat-" + setup["run"]["id"].split(":")[-1],
                                    model_id="recorded-heartbeat-fixture-v1", prompt_version="independent-opinion-v1",
                                    max_calls=len(setup["characters"]), max_tokens=100000, max_output_tokens=1024)

    def external_opinions(self, context):
        results = []
        portfolio_state = context["prior_outputs"]["mark_portfolio"]["portfolio_state"]
        for character, recommendation in zip(self.setup["characters"], self.setup["recommendations"]):
            request = {"experiment_id": self.setup["experiment"]["id"],
                       "model_id": "recorded-heartbeat-fixture-v1", "prompt_version": "independent-opinion-v1",
                       "character_version": character["id"], "snapshot_id": self.setup["snapshot"]["id"],
                       "snapshot_hash": digest(self.setup["snapshot"]), "portfolio_id": self.setup["portfolio"]["id"],
                       "portfolio_state": portfolio_state, "portfolio_state_hash": digest(portfolio_state),
                       "knowledge_hash": digest([character["constitution_hash"], character["curriculum_hash"]]),
                       "expected_recommendation_id": recommendation["id"], "source_revision": digest(self.setup["payload"]),
                       "source_ids": [SOURCE], "output_schema_version": "recommendation-v1",
                       "sampling": {"temperature": 0, "seed": 0}, "tools": []}
            response, call_id, _cached = self.model.complete(request, source_ids=[SOURCE], completed_at=OPINION_AT)
            results.append({"character_version": character["id"], "recommendation_id": response["recommendation_id"],
                            "model_call_id": call_id, "request_hash": digest(request)})
        return {"opinions": results, "usage": self.model.usage()}

    def operations(self):
        setup, council, simulator = self.setup, self.council, self.simulator

        def freeze(_store, _context, _external):
            return {"snapshot_id": setup["snapshot"]["id"], "snapshot_hash": digest(setup["snapshot"]),
                    "cutoff": setup["snapshot"]["cutoff"]}

        def mark(_store, _context, _external):
            item = Normalized(setup["observation"], setup["payload"])
            state = simulator.mark(setup["snapshot"]["id"], [item], at=CUTOFF)
            return {"portfolio_id": setup["portfolio"]["id"], "portfolio_state": state,
                    "portfolio_state_hash": digest(state)}

        def deliver(_store, _context, _external):
            if council is None:
                return {"delivered": []}
            delivered = []
            for message in council._messages():
                for recipient in message["recipient_character_ids"]:
                    if council.status(message["id"], recipient) == "pending" and message["available_at"] <= DISCUSSION_AT:
                        delivered.append(council.deliver(message["id"], recipient, at=DISCUSSION_AT))
            return {"delivered": delivered}

        def opinions(_store, _context, external):
            commits = [council.commit_initial(item["recommendation_id"], at=OPINION_AT) if council else
                       _store.append("no-mail-initial:" + digest(item["recommendation_id"]), setup["experiment"]["id"],
                                     "opinions.initial", {"recommendation_id": item["recommendation_id"]}, created_at=OPINION_AT)
                       for item in external["opinions"]]
            return {"recommendation_ids": [item["recommendation_id"] for item in external["opinions"]],
                    "model_call_ids": [item["model_call_id"] for item in external["opinions"]],
                    "commits": commits, "usage": external["usage"]}

        def deliberate(_store, _context, _external):
            if len(setup["characters"]) == 1 or setup["experiment"]["advice"] == "none":
                return {"question_ids": [], "reply_ids": [], "objection_ids": [], "rounds": 0}
            lead, first, second = [item["id"] for item in setup["characters"]]
            question = council.send(f"message:heartbeat-{setup['run']['id'].split(':')[-1]}-question", sender=lead,
                                    recipients=[first, second], kind="question", title="Should the council act on this signal?",
                                    question="Do costs or missing evidence defeat the proposed activity?",
                                    body="Identify the strongest evidence-based objection to acting in this frozen fixture.",
                                    available_at=DISCUSSION_AT, expires_at=EXPIRES,
                                    evidence_ids=[setup["observation"]["id"]])
            replies = []
            for index, recipient in enumerate((first, second)):
                council.deliver(question["id"], recipient, at=DISCUSSION_AT)
                council.read(question["id"], recipient, at=DISCUSSION_AT)
                reply = council.send(f"message:heartbeat-{setup['run']['id'].split(':')[-1]}-reply-{index}",
                                     sender=recipient, recipients=[lead], kind="reply",
                                     title="Bounded adviser response", body=("The snapshot does not establish business value."
                                            if index == 0 else "The signal exists, but sizing must remain inside turnover limits."),
                                     available_at=DISCUSSION_AT, expires_at=EXPIRES, reply_to=question["id"])
                council.deliver(reply["id"], lead, at=DISCUSSION_AT)
                council.read(reply["id"], lead, at=DISCUSSION_AT)
                replies.append(reply)
            objection = council.send(f"message:heartbeat-{setup['run']['id'].split(':')[-1]}-objection",
                                     sender=first, recipients=[lead], kind="objection",
                                     title="Outstanding valuation objection",
                                     body="No business-value evidence is present; this objection remains even if a rule signal exists.",
                                     available_at=DISCUSSION_AT, expires_at=EXPIRES,
                                     evidence_ids=[setup["observation"]["id"]])
            council.deliver(objection["id"], lead, at=DISCUSSION_AT)
            council.reflect(f"reflection:{setup['run']['id'].split(':')[-1]}", author=lead, subject_character=first,
                            body="The valuation objection is useful but does not independently set the deterministic risk limit.",
                            source_message_ids=[objection["id"]], at=DISCUSSION_AT)
            return {"question_ids": [question["id"]], "reply_ids": [item["id"] for item in replies],
                    "objection_ids": [objection["id"]], "rounds": 1}

        def decide(_store, context, _external):
            considered = context["prior_outputs"]["deliberation"]["reply_ids"]
            commit = council.commit_final(setup["final"]["id"], at=FINAL_AT, considered_message_ids=considered) if council else \
                _store.append("no-mail-final:" + digest(setup["final"]["id"]), setup["experiment"]["id"], "opinions.final",
                              {"recommendation_id": setup["final"]["id"]}, created_at=FINAL_AT)
            return {"recommendation_ids": [setup["final"]["id"]], "commits": [commit],
                    "initial_abstentions": [r["id"] for r in setup["recommendations"]
                                             if r["action"] in {"abstain", "wait"}]}

        def risk(_store, _context, _external):
            state = simulator.state()
            recommendation = setup["final"]
            if recommendation["action"] not in {"buy", "sell"}:
                return {"checks": [{"recommendation_id": recommendation["id"], "status": "abstained",
                                    "reasons": ["No active order"], "policy_id": simulator.policy["id"]}]}
            price, fee = Decimal("100"), Decimal(simulator.policy["costs"]["fee_per_order"])
            order = {"decision_id": recommendation["id"], "instrument_id": recommendation["instrument_id"],
                     "side": recommendation["action"], "quantity": recommendation["quantity"],
                     "expires_at": recommendation["expires_at"], "decision_at": FINAL_AT,
                     "decision_session": SESSION, "price_cap": "100", "reserved": "0"}
            reasons = simulator.governor.check(state, order, price=price, fee=fee, session=SESSION,
                                               at=FINAL_AT, sessions=simulator.session_ids,
                                               expected_session=SESSION)
            return {"checks": [{"recommendation_id": recommendation["id"],
                                "status": "rejected" if reasons else "approved", "reasons": reasons,
                                "policy_id": simulator.policy["id"]}]}

        def queue(_store, context, _external):
            check = context["prior_outputs"]["risk_gate"]["checks"][0]
            if check["status"] != "approved":
                return {"orders": [], "not_queued": [{"recommendation_id": setup["final"]["id"],
                                                        "reasons": check["reasons"]}]}
            result = simulator.submit(setup["final"]["id"], at=FINAL_AT, price_cap="100")
            return {"orders": [result] if result["status"] == "pending" else [],
                    "not_queued": [] if result["status"] == "pending" else [result]}

        def evaluate(store, context, _external):
            payload = {"run_id": setup["run"]["id"], "portfolio_id": setup["portfolio"]["id"],
                       "snapshot_id": setup["snapshot"]["id"], "status": "pending_next_eligible_event",
                       "order_ids": [item["order_id"] for item in context["prior_outputs"]["queue_execution"]["orders"]]}
            event_id = "evaluation-handoff:" + digest(setup["run"]["id"])
            store.append(event_id, setup["experiment"]["id"], "evaluation.handoff", payload,
                         created_at=HEARTBEAT_AT)
            return {"handoff_event_id": event_id, "status": payload["status"]}

        def export(_store, _context, _external):
            if council is None:
                return {"manifest_hash": digest({"advice": "none"}), "files": [],
                        "destination_name": self.export_root.name, "source_event_ids": []}
            result = council.export(self.export_root, generated_at=HEARTBEAT_AT)
            return {"manifest_hash": result["manifest_hash"], "files": result["files"],
                    "destination_name": self.export_root.name, "source_event_ids": result["source_event_ids"]}

        return dict(zip(PHASES, (freeze, mark, deliver, opinions, deliberate, decide,
                                 risk, queue, evaluate, export)))

    def heartbeat(self):
        return Heartbeat(self.store, self.setup["run"]["id"], phase_inputs=self.setup["phase_inputs"],
                         operations=self.operations(), external_operations={"independent_opinions": self.external_opinions})


def build():
    council_setup = build_records("council", council=True, risk_reject=True)
    individual_setup = build_records("individual", council=False, risk_reject=False, include_source=False)
    combined = council_setup["records"] + individual_setup["records"]
    validate_bundle(combined)
    with TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        with Store(root / "store", synthetic=True) as store:
            store.put_records(combined)
            council = FixtureScenario(store, council_setup, root / "council-mail")
            council_result = council.heartbeat().run(at=HEARTBEAT_AT)
            individual = FixtureScenario(store, individual_setup, root / "individual-mail")
            individual_result = individual.heartbeat().run(at=HEARTBEAT_AT)
            integrity = store.verify()
            events = [{"id": event["id"], "experiment_id": event["experiment_id"],
                       "kind": event["kind"], "payload": event["payload"]}
                      for event in store.events()]
            council_mail = {path.relative_to(root / "council-mail").as_posix(): path.read_text(encoding="utf-8")
                            for path in (root / "council-mail").rglob("*") if path.is_file()}
            individual_mail = {path.relative_to(root / "individual-mail").as_posix(): path.read_text(encoding="utf-8")
                               for path in (root / "individual-mail").rglob("*") if path.is_file()}
            report = {"fixture_only": True,
                      "description": "Scripted engineering evidence; no real Character readiness, market edge or live order authority.",
                      "council": council_result, "individual": individual_result,
                      "provider_calls": {"council": council.provider.calls, "individual": individual.provider.calls},
                      "integrity": {"records": integrity["records"], "events": integrity["events"],
                                    "hash_chain_verified": True},
                      "isolation": {"experiment_ids": [council_setup["experiment"]["id"], individual_setup["experiment"]["id"]],
                                    "portfolio_ids": [council_setup["portfolio"]["id"], individual_setup["portfolio"]["id"]],
                                    "private_reflection_experiment": council_setup["experiment"]["id"]}}
    return {"bundle": combined, "report": report, "events": events,
            "council_mail": council_mail, "individual_mail": individual_mail}


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, indent=2, ensure_ascii=False) + "\n" if not isinstance(value, str) else value
    if not path.exists() or path.read_text(encoding="utf-8") != encoded:
        path.write_text(encoded, encoding="utf-8", newline="\n")
