"""Build three independent, explicitly synthetic recommendation opinions."""

from copy import deepcopy
import json
from pathlib import Path

from trade_theorist.contracts import digest, validate_bundle
from trade_theorist.fixtures import complete_bundle
from trade_theorist.theorize import OpinionAdapter


ROOT = Path(__file__).resolve().parents[1]


def write(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and json.loads(path.read_text(encoding="utf-8")) != value:
        path.write_text(encoded, encoding="utf-8", newline="\n")
    elif not path.exists():
        path.write_text(encoded, encoding="utf-8", newline="\n")


def build():
    records = complete_bundle()
    experiment = next(record for record in records if record["record_type"] == "experiment")
    original_character = next(record for record in records if record["record_type"] == "character" and record["experiment_id"] == experiment["id"])
    original_checkpoint = next(record for record in records if record["record_type"] == "checkpoint" and record["experiment_id"] == experiment["id"])
    original_registration = next(record for record in records if record["record_type"] == "registration" and record["experiment_id"] == experiment["id"])
    original_theory = next(record for record in records if record["record_type"] == "theory" and record["experiment_id"] == experiment["id"])
    characters = [("index_steward", original_character, original_checkpoint, original_registration, original_theory)]
    for slug in ("value_rationalist", "systematic_trend_operator"):
        label = slug.replace("_", "-")
        character = deepcopy(original_character)
        character.update(id=f"character:{label}-fixture-v1", character_id=f"{slug}_fixture")
        checkpoint = deepcopy(original_checkpoint)
        checkpoint.update(id=f"checkpoint:{label}-fixture", character_version=character["id"])
        registration = deepcopy(original_registration)
        registration.update(id=f"registration:{label}-fixture", character_version=character["id"])
        theory = deepcopy(original_theory)
        theory.update(id=f"theory:{label}-fixture", character_version=character["id"], checkpoint_id=checkpoint["id"], test_registration_id=registration["id"])
        records.extend([character, checkpoint, registration, theory])
        characters.append((slug, character, checkpoint, registration, theory))
    experiment["character_versions"] = [item[1]["id"] for item in characters]
    portfolio = next(record for record in records if record["record_type"] == "portfolio")
    snapshot = next(record for record in records if record["record_type"] == "snapshot")
    source = next(record for record in records if record["record_type"] == "source")
    responses = {
        "index_steward": dict(action="abstain", instrument_id=None, quantity="0", horizon="one session", confidence=0.62, confidence_event="The fixture does not overcome the cost-conscious inactivity prior", invalidation_conditions=["Eligible evidence establishes a net advantage after costs"], citations=[original_theory["evidence_and_citations"][0]], abstention_reason="No fixture edge over inactivity is established", theory_ids=[original_theory["id"]], forecast=None),
        "value_rationalist": dict(action="wait", instrument_id=None, quantity="0", horizon="one session", confidence=0.55, confidence_event="The fixture contains no business value estimate", invalidation_conditions=["A point-in-time value estimate and margin for error become available"], citations=[original_theory["evidence_and_citations"][0]], abstention_reason="Price is not paired with evidence of underlying value", theory_ids=["theory:value-rationalist-fixture"], forecast=None),
        "systematic_trend_operator": dict(action="buy", instrument_id="instrument:fixture-fund", quantity="10", horizon="five synthetic sessions", confidence=0.58, confidence_event="The fictional rule signal is present but only moderately informative", invalidation_conditions=["The fictional close crosses its predeclared exit threshold"], citations=[original_theory["evidence_and_citations"][0]], abstention_reason=None, theory_ids=["theory:systematic-trend-operator-fixture"], forecast=dict(proposition="The fictional trend persists for five sessions", resolves_at="2026-09-10T12:00:00Z", success_condition="Synthetic terminal close exceeds the snapshot close", failure_condition="Synthetic terminal close does not exceed the snapshot close")),
    }
    recommendations, pins = [], []
    for slug, character, checkpoint, registration, theory in characters:
        adapter = OpinionAdapter(lambda request, maximum, value=responses[slug]: deepcopy(value), model_id="recorded-fixture-opinion-v1", prompt_version="independent-opinion-v1")
        recommendation, request, forecast = adapter.complete(
            records=records, character_version=character["id"], knowledge_version=theory["id"],
            portfolio_id=portfolio["id"], snapshot_id=snapshot["id"],
            portfolio_state={"cash": "10000.00", "positions": []},
            evidence_ids=[theory["id"]], expires_at="2026-09-06T12:00:00Z",
            created_at="2026-09-05T12:00:00Z",
        )
        recommendations.append(recommendation)
        pins.append({
            "character_version": character["id"], "recommendation_id": recommendation["id"],
            "request_hash": digest(request), "model_id": request["model_id"],
            "prompt_version": request["prompt_version"], "knowledge_version": request["knowledge_version"],
            "knowledge_hash": request["knowledge_hash"], "portfolio_state_hash": request["portfolio_state_hash"],
            "snapshot_hash": request["snapshot_hash"], "evidence_hash": request["evidence_hash"],
            "expires_at": request["expires_at"], "tools": request["tools"], "forecast": forecast,
        })
    records.extend(recommendations)
    records.sort(key=lambda value: value["id"])
    validate_bundle(records)
    write("examples/theorize/independent-opinions.bundle.json", records)
    write("examples/theorize/independent-opinions.pins.json", {
        "fixture_only": True,
        "description": "Three independently constructed opinions over the same synthetic snapshot and portfolio; no real readiness or performance claim.",
        "pins": pins,
    })


if __name__ == "__main__":
    build()
