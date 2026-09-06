"""Turn one independent structured opinion into a validated recommendation.

The adapter deliberately has no market, web, repository, or brokerage tools.  Its
entire evidence view is an immutable set of already-persisted records supplied by
the caller.  Provider integration and persistence can therefore be added without
changing the recommendation contract or widening the model's authority.
"""

from copy import deepcopy
from datetime import timedelta

from jsonschema import Draft202012Validator

from ..contracts import ContractError, canonical, digest, utc, validate, validate_bundle
from ..schema import CITATION, CONF, DEC, ID, S, STRINGS, array, enum, nullable, obj


OPINION_OUTPUT = obj(
    action=enum("buy", "sell", "hold", "wait", "abstain"),
    instrument_id=nullable(ID),
    quantity=DEC,
    horizon=S,
    confidence=CONF,
    confidence_event=S,
    invalidation_conditions=array(S, 1),
    citations=array(CITATION),
    abstention_reason=nullable(S),
    theory_ids=array(ID),
    forecast=nullable(obj(
        proposition=S,
        resolves_at=S,
        success_condition=S,
        failure_condition=S,
    )),
)


def recommendation_request(*, records, character_version, knowledge_version,
                           portfolio_id, snapshot_id, portfolio_state,
                           evidence_ids, model_id, prompt_version, expires_at):
    """Build a frozen, hash-addressed view for one Character's independent call."""
    records = list(records)
    validate_bundle(records)
    index = {record["id"]: record for record in records}
    try:
        character = index[character_version]
        knowledge = index[knowledge_version]
        portfolio = index[portfolio_id]
        snapshot = index[snapshot_id]
        evidence = [index[identifier] for identifier in evidence_ids]
    except KeyError as exc:
        raise ContractError("Recommendation input references an unknown record") from exc
    if character["record_type"] != "character":
        raise ContractError("Character version is not a Character record")
    if knowledge["record_type"] not in ("checkpoint", "theory") or knowledge.get("character_version") != character_version:
        raise ContractError("Knowledge version does not belong to the Character")
    if portfolio["record_type"] != "portfolio" or snapshot["record_type"] != "snapshot":
        raise ContractError("Recommendation needs a portfolio and snapshot")
    experiment_id = portfolio["experiment_id"]
    if any(record["experiment_id"] != experiment_id for record in (character, portfolio, snapshot, *evidence)):
        raise ContractError("Recommendation inputs cross experiment boundaries")
    if utc(expires_at) <= utc(snapshot["cutoff"]):
        raise ContractError("Recommendation must expire after the snapshot cutoff")
    if not isinstance(portfolio_state, dict) or not portfolio_state:
        raise ContractError("Portfolio state must be a nonempty structured value")
    # Canonicalization rejects NaN and non-JSON state before it can reach a model.
    canonical(portfolio_state)
    return {
        "instruction": (
            "Return one independent opinion using only the frozen inputs. "
            "Use explicit abstention when evidence is insufficient. Never claim "
            "certainty, modify policy, request tools, or emit an order."
        ),
        "output_schema": OPINION_OUTPUT,
        "model_id": model_id,
        "prompt_version": prompt_version,
        "tools": [],
        "character_version": character_version,
        "knowledge_version": knowledge_version,
        "knowledge": deepcopy(knowledge),
        "knowledge_hash": digest(knowledge),
        "portfolio_id": portfolio_id,
        "portfolio_state": deepcopy(portfolio_state),
        "portfolio_state_hash": digest(portfolio_state),
        "snapshot_id": snapshot_id,
        "snapshot": deepcopy(snapshot),
        "snapshot_hash": digest(snapshot),
        "evidence_ids": list(evidence_ids),
        "evidence": deepcopy(evidence),
        "evidence_hash": digest(evidence),
        "expires_at": expires_at,
    }


class OpinionAdapter:
    """Validate bounded provider output and construct, but never execute, advice."""

    def __init__(self, provider, *, model_id, prompt_version,
                 max_output_bytes=32_000, max_horizon_days=366):
        if not model_id or not prompt_version or max_output_bytes < 256 or max_horizon_days < 1:
            raise ValueError("Invalid recommendation adapter limits")
        self.provider = provider
        self.model_id = model_id
        self.prompt_version = prompt_version
        self.max_output_bytes = max_output_bytes
        self.max_horizon_days = max_horizon_days
        self.calls = 0

    def complete(self, *, records, character_version, knowledge_version,
                 portfolio_id, snapshot_id, portfolio_state, evidence_ids,
                 expires_at, created_at):
        records = list(records)
        request = recommendation_request(
            records=records, character_version=character_version,
            knowledge_version=knowledge_version, portfolio_id=portfolio_id,
            snapshot_id=snapshot_id, portfolio_state=portfolio_state,
            evidence_ids=evidence_ids, model_id=self.model_id,
            prompt_version=self.prompt_version, expires_at=expires_at,
        )
        if utc(expires_at) - utc(created_at) > timedelta(days=self.max_horizon_days):
            raise ContractError("Recommendation expiry exceeds the bounded horizon")
        response = self.provider(deepcopy(request), self.max_output_bytes)
        self.calls += 1
        try:
            size = len(canonical(response).encode("utf-8"))
        except (TypeError, ValueError) as exc:
            raise ContractError("Opinion output must be finite JSON") from exc
        if size > self.max_output_bytes:
            raise ContractError("Opinion output exceeds its byte limit")
        errors = sorted(Draft202012Validator(OPINION_OUTPUT).iter_errors(response), key=lambda error: str(list(error.path)))
        if errors:
            raise ContractError("Malformed opinion output")
        if response["confidence"] == 1:
            raise ContractError("Absolute certainty is unsupported")
        if response["action"] in ("buy", "sell") and not response["citations"]:
            raise ContractError("Active recommendation needs citations")
        allowed_evidence = {request["knowledge_version"], *request["evidence_ids"]}
        def cited_sources(value):
            found = set()
            if isinstance(value, dict):
                if set(("source_id", "locator", "passage_hash")) <= set(value):
                    found.add(value["source_id"])
                for item in value.values():
                    found.update(cited_sources(item))
            elif isinstance(value, list):
                for item in value:
                    found.update(cited_sources(item))
            return found
        frozen_records = [record for record in records if record["id"] in allowed_evidence]
        allowed_sources = set().union(*(cited_sources(record) for record in frozen_records))
        if any(citation["source_id"] not in allowed_sources for citation in response["citations"]):
            raise ContractError("Opinion cites a source outside the frozen bundle")
        if any(identifier not in allowed_evidence for identifier in response["theory_ids"]):
            raise ContractError("Opinion references evidence outside the frozen view")
        if response["forecast"] is not None and utc(response["forecast"]["resolves_at"]) <= utc(created_at):
            raise ContractError("Forecast must resolve in the future")
        record = {
            "id": "recommendation:" + digest([request, response]),
            "schema_version": 1,
            "record_type": "recommendation",
            "experiment_id": next(item for item in records if item["id"] == portfolio_id)["experiment_id"],
            "created_at": created_at,
            "contamination": next(item for item in records if item["id"] == character_version)["contamination"],
            "character_version": character_version,
            "portfolio_id": portfolio_id,
            "snapshot_id": snapshot_id,
            "instrument_id": response["instrument_id"],
            "action": response["action"],
            "quantity": response["quantity"],
            "horizon": response["horizon"],
            "confidence": response["confidence"],
            "confidence_event": response["confidence_event"],
            "invalidation_conditions": response["invalidation_conditions"],
            "citations": response["citations"],
            "expires_at": expires_at,
            "abstention_reason": response["abstention_reason"],
            "theory_ids": response["theory_ids"],
        }
        validate(record)
        return record, request, response["forecast"]
