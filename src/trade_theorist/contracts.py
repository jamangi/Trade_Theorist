"""Deterministic structural and experiment-aware reference validation."""

from datetime import datetime
from decimal import Decimal
import hashlib
import json

from jsonschema import Draft202012Validator, FormatChecker

from .schema import COMPLETABLE_SCOPES, schema


class ContractError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def utc(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate(record):
    try:
        canonical(record)
    except (ValueError, TypeError) as exc:
        raise ContractError("Record must contain finite JSON values") from exc
    definitions = schema()["$defs"]
    kind = record.get("record_type")
    if kind not in definitions:
        raise ContractError("Unknown record type")
    errors = sorted(Draft202012Validator(definitions[kind], format_checker=FormatChecker()).iter_errors(record), key=lambda e: str(list(e.path)))
    if errors:
        # Do not echo private payload values in validation errors.
        raise ContractError("Invalid contract at " + "/".join(map(str, errors[0].path)) + ": " + errors[0].validator)
    if kind != "source" and record["experiment_id"] is None:
        raise ContractError("Experiment scope required")
    if kind == "learning_session":
        if record["id"] != record["experiment_id"] or record["contamination"] not in ("fixture", "hindsight-contaminated"):
            raise ContractError("Learning session requires its own non-prospective scope")
    if kind == "experiment":
        if record["id"] != record["experiment_id"]:
            raise ContractError("Experiment identity differs from scope")
        if not utc(record["development_end_at"]) < utc(record["validation_end_at"]) < utc(record["start_at"]) < utc(record["end_at"]):
            raise ContractError("Development, validation and holdout must be ordered")
        if utc(record["created_at"]) >= utc(record["start_at"]):
            raise ContractError("Preregister before evaluation starts")
        expected = {"fixture": "fixture", "hindsight": "hindsight-contaminated", "historical_restricted": "historical-qualified"}
        if record["regime"] in expected and record["contamination"] != expected[record["regime"]]:
            raise ContractError("Regime/contamination mismatch")
        if record["regime"].startswith("forward") and not record["contamination"].startswith("forward"):
            raise ContractError("Forward record has incompatible evidence status")
    if kind == "policy":
        if record["stage"] == "fixture":
            if not record["synthetic"] or record["contamination"] != "fixture":
                raise ContractError("Fixture policy must be synthetic")
        elif record["synthetic"] or record["contamination"] == "fixture" or any(record[k] is None for k in ("approval_ref", "approved_at", "operator", "kill_switch_owner", "reconciliation_owner", "incident_owner")):
            raise ContractError("Paper policy requires explicit approval and operational ownership")
        if Decimal(record["limits"]["initial_cash"]) <= 0 or Decimal(record["limits"]["max_deployed_capital"]) > Decimal(record["limits"]["initial_cash"]):
            raise ContractError("Invalid capital limits")
        if len({i["instrument_id"] for i in record["universe"]}) != len(record["universe"]):
            raise ContractError("Duplicate instrument identity")
    for start, end in (("window_start", "window_end"), ("evaluation_start", "evaluation_end"), ("available_at", "expires_at"), ("created_at", "expires_at"), ("checked_at", "next_check_at")):
        if start in record and end in record and utc(record[start]) >= utc(record[end]):
            raise ContractError(f"{end} must follow {start}")
    if kind == "registration" and utc(record["created_at"]) >= utc(record["evaluation_start"]):
        raise ContractError("Test must be registered before outcomes")
    if kind == "character" and record["contamination"] == "fixture" and record["readiness"] not in ("not_ready", "fixture_only"):
        raise ContractError("Fixture Character cannot claim real readiness")
    if kind == "checkpoint":
        if record["reading_status"] == "complete" and record["material_scope"] not in COMPLETABLE_SCOPES:
            raise ContractError("Sample and fixture checkpoints must remain partial")
        if (record["material_scope"] == "fixture") != (record["contamination"] == "fixture"):
            raise ContractError("Checkpoint scope and evidence label mismatch")
        accepted = {c["claim_id"] for c in record["accepted_claims"]}
        rejected = {c["claim_id"] for c in record["rejected_claims"]}
        if accepted & rejected or len(accepted) != len(record["accepted_claims"]) or len(rejected) != len(record["rejected_claims"]):
            raise ContractError("Claim dispositions must have distinct identities")
    if kind == "source" and record["ingestion_status"] in ("partial", "complete"):
        if record["access"] not in ("public_full_text", "sample_only", "owned_copy", "user_supplied", "library_loan") or any(record["rights"][k] != "permitted" for k in ("reading", "machine_ingestion", "private_storage")):
            raise ContractError("Ingested source requires access and permissions")
        if record["access"] == "sample_only" and record["ingestion_status"] == "complete":
            raise ContractError("Sample access cannot imply complete ingestion")
    if kind == "observation":
        if utc(record["event_at"]) > utc(record["published_at"]):
            raise ContractError("Publication cannot precede the observed event")
        if utc(record["published_at"]) > utc(record["ingested_at"]):
            raise ContractError("Ingestion cannot precede publication")
        if record["availability_evidence"].strip().lower() in ("unknown", "undocumented", "none", "n/a"):
            raise ContractError("Observation needs documented publication availability")
        if record["revision"] == 1 and record["supersedes_id"] is not None:
            raise ContractError("First revision cannot supersede another observation")
        if record["revision"] > 1 and record["supersedes_id"] is None:
            raise ContractError("Later revision must retain its predecessor")
    if kind == "recommendation":
        active = record["action"] in ("buy", "sell")
        if active and (record["instrument_id"] is None or Decimal(record["quantity"]) <= 0 or not record["citations"]):
            raise ContractError("Action requires instrument, positive quantity and evidence")
        if not active and Decimal(record["quantity"]) != 0:
            raise ContractError("Inactive recommendation must have zero quantity")
        if record["action"] in ("wait", "abstain") and not record["abstention_reason"]:
            raise ContractError("Abstention requires a reason")
        if record["confidence"] == 1:
            raise ContractError("Absolute certainty is unsupported")
    if kind == "ledger_event":
        if record["event_kind"] == "fill" and any(record[k] is None for k in ("decision_id", "order_id", "instrument_id", "price")):
            raise ContractError("Fill requires order, decision, instrument and price")
        if record["event_kind"] == "correction" and record["corrects_id"] is None:
            raise ContractError("Correction requires original event")
    if kind == "evaluation":
        if record["evidence_status"] != record["contamination"]:
            raise ContractError("Evidence status mismatch")
        for metric in record["metrics"]:
            if (metric["value"] is None) == (metric["null_reason"] is None):
                raise ContractError("Metrics need a value or an unavailable reason")
    return record


# Field names encode a typed relationship; never silently ignore a dangling ID.
REFS = {
    "conversation_id": "conversation", "participant_character_versions": "character", "model_call_id": "model_call", "order_id": "ledger_event",
    "policy_id": "policy", "foundation_source_id": "source", "owner_character_version": "character",
    "character_version": "character", "character_versions": "character", "sender_character_version": "character",
    "recipient_character_ids": "character", "prior_checkpoint_id": "checkpoint", "checkpoint_id": "checkpoint",
    "source_id": "source", "source_ids": "source", "test_registration_id": "registration",
    "supersedes_id": "observation", "observation_id": "observation", "observation_ids": "observation",
    "snapshot_id": "snapshot", "portfolio_context": "portfolio", "portfolio_id": "portfolio", "reply_to": "message",
    "related_theory_ids": "theory", "theory_ids": "theory", "evidence_ids": None,
    "decision_id": "recommendation", "corrects_id": "ledger_event", "source_run_ids": "run_manifest", "parent_run_id": "run_manifest",
}


def validate_bundle(records):
    records = list(records)
    index = {}
    for record in records:
        validate(record)
        if record["id"] in index:
            raise ContractError("Duplicate record identity")
        index[record["id"]] = record

    def reference(owner, identifier, expected):
        target = index.get(identifier)
        if target is None or (expected and target["record_type"] != expected):
            raise ContractError("Missing or incorrectly typed reference")
        if target["experiment_id"] != owner["experiment_id"] and not (target["record_type"] == "source" and target["experiment_id"] is None):
            raise ContractError("Cross-experiment reference")
        return target

    def walk(owner, value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in REFS and item is not None:
                    for identifier in item if isinstance(item, list) else [item]:
                        reference(owner, identifier, REFS[key])
                walk(owner, item)
        elif isinstance(value, list):
            for item in value:
                walk(owner, item)

    for record in records:
        if record["record_type"] != "source":
            experiment = reference(record, record["experiment_id"], None)
            if experiment["record_type"] not in ("experiment", "learning_session"):
                raise ContractError("Scope must be an experiment or learning session")
            if experiment["record_type"] == "learning_session":
                if record["record_type"] not in ("learning_session", "character", "checkpoint", "registration", "theory", "model_call", "run_manifest"):
                    raise ContractError("Learning scope cannot contain market or portfolio activity")
                if record["record_type"] == "run_manifest" and record["mode"] != "learning":
                    raise ContractError("Learning scope requires a learning run")
            if record["contamination"] != experiment["contamination"]:
                raise ContractError("Evidence labels must match experiment")
            instruments = {i["instrument_id"] for i in experiment.get("universe", [])}
            if record.get("instrument_id") and record["instrument_id"] not in instruments:
                raise ContractError("Instrument outside preregistered universe")
            if record.get("character_version") and record["character_version"] not in experiment["character_versions"]:
                raise ContractError("Character is not registered in this experiment")
        walk(record, record)
        if record["record_type"] == "experiment":
            policy = index[record["policy_id"]]
            if record["universe"] != policy["universe"] or record["costs"] != policy["costs"]:
                raise ContractError("Experiment differs from pinned policy")
            if record["regime"] == "forward_paper" and policy["stage"] != "paper":
                raise ContractError("Paper experiment requires paper policy")
            if record["regime"].startswith("forward") and policy["clock"]["eligibility"] != "publication_and_ingestion":
                raise ContractError("Forward decisions require publication and ingestion eligibility")
        if record["record_type"] == "snapshot":
            experiment = index[record["experiment_id"]]
            if record["clock_policy"] != index[experiment["policy_id"]]["clock"]:
                raise ContractError("Snapshot clock differs from pinned policy")
            observations = [index[i] for i in record["observation_ids"]]
            if digest(observations) != record["content_hash"]:
                raise ContractError("Snapshot hash mismatch")
            for observation in observations:
                if observation["quality"] != "eligible" or utc(observation["event_at"]) > utc(record["cutoff"]) or utc(observation["published_at"]) > utc(record["cutoff"]):
                    raise ContractError("Ineligible snapshot observation")
                if record["clock_policy"]["eligibility"] == "publication_and_ingestion" and utc(observation["ingested_at"]) > utc(record["cutoff"]):
                    raise ContractError("Observation ingested after cutoff")
                later = [candidate for candidate in index.values() if candidate.get("record_type") == "observation" and candidate.get("supersedes_id") == observation["id"]]
                for candidate in later:
                    known = utc(candidate["published_at"]) <= utc(record["cutoff"])
                    if record["clock_policy"]["eligibility"] == "publication_and_ingestion":
                        known = known and utc(candidate["ingested_at"]) <= utc(record["cutoff"])
                    if known:
                        raise ContractError("Snapshot retained a superseded observation")
        if record["record_type"] == "ledger_event" and record["order_id"] is not None:
            order = index[record["order_id"]]
            if order["event_kind"] != "order" or order["portfolio_id"] != record["portfolio_id"]:
                raise ContractError("Ledger event needs an order in its own portfolio")
        if record["record_type"] == "message":
            conversation = index[record["conversation_id"]]
            participants = conversation["participant_character_versions"]
            if record["sender_character_version"] not in participants or any(i not in participants for i in record["recipient_character_ids"]):
                raise ContractError("Message participant is not in the conversation")
            if record["snapshot_id"] != conversation["snapshot_id"] or record["portfolio_context"] != conversation["portfolio_id"]:
                raise ContractError("Message context differs from conversation")
        if record["record_type"] == "theory":
            registration = index[record["test_registration_id"]]
            checkpoint = index[record["checkpoint_id"]]
            if registration["character_version"] != record["character_version"] or checkpoint["character_version"] != record["character_version"]:
                raise ContractError("Theory belongs to another Character")
            if utc(registration["created_at"]) > utc(record["created_at"]):
                raise ContractError("Theory predates registration")
            if utc(record["created_at"]) >= utc(registration["evaluation_start"]):
                raise ContractError("Theory must be committed before its evaluation starts")
        if record["record_type"] == "checkpoint" and record["prior_checkpoint_id"] is not None:
            prior = index[record["prior_checkpoint_id"]]
            if prior["character_version"] != record["character_version"] or record["prior_hash"] != digest(prior):
                raise ContractError("Checkpoint prior is not the same Character's frozen state")
            expected_next = (prior["curriculum_position"], prior["section_index"] + 1)
            next_book = (prior["curriculum_position"] + 1, 1)
            actual = (record["curriculum_position"], record["section_index"])
            if actual != expected_next and not (actual == next_book and prior["reading_status"] == "complete"):
                raise ContractError("Checkpoint sequence skipped a section or unfinished book")
    return index


def migrate_v0_theory(record):
    """Explicit, non-mutating migration of only the documented v0 renamed field."""
    if record.get("schema_version") != 0 or record.get("record_type") != "theory" or "logic_chain" not in record:
        raise ContractError("No supported migration")
    migrated = json.loads(canonical(record))
    migrated["schema_version"] = 1
    migrated["minimal_logic_chain"] = migrated.pop("logic_chain")
    validate(migrated)
    return migrated
