"""Version 1 contracts; emit standard JSON Schema with scripts/export_schemas.py."""

S = {"type": "string", "minLength": 1}
ID = {"type": "string", "pattern": "^[a-z][a-z0-9_.:-]{2,127}$"}
HASH = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
UTC = {"type": "string", "format": "date-time", "pattern": "Z$"}
DEC = {"type": "string", "pattern": "^(0|[1-9][0-9]*)(\\.[0-9]{1,8})?$"}
SIGNED = {"type": "string", "pattern": "^-?(0|[1-9][0-9]*)(\\.[0-9]{1,8})?$"}
MONEY = {"type": "string", "pattern": "^(0|[1-9][0-9]*)\\.[0-9]{2}$"}
N = {"type": "integer", "minimum": 0}
POS = {"type": "integer", "minimum": 1}
BOOL = {"type": "boolean"}
CONF = {"type": "number", "minimum": 0, "maximum": 1}


def enum(*values):
    return {"enum": list(values)}


def nullable(value):
    return {"anyOf": [value, {"type": "null"}]}


def array(value, minimum=0):
    return {"type": "array", "items": value, "minItems": minimum, "uniqueItems": True}


def obj(**props):
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


STRINGS = array(S)
IDS = array(ID)
CONTAMINATION = enum("fixture", "hindsight-contaminated", "historical-qualified", "forward-insufficient", "forward-reviewed")
CITATION = obj(source_id=ID, locator=S, passage_hash=HASH)
CLAIM = obj(claim_id=ID, text=S, citations=array(CITATION, 1))
USAGE = obj(input_tokens=N, output_tokens=N, calls=N, cost_usd=nullable(MONEY))
ASSET = enum("us_equity", "unleveraged_us_etf")
PHASE = enum("pending", "running", "complete", "failed")
RIGHT = enum("unknown", "permitted", "denied")
RIGHTS = obj(reading=RIGHT, machine_ingestion=RIGHT, private_storage=RIGHT, redistribution=RIGHT, evidence=array(S, 1))
INSTRUMENT = obj(instrument_id=ID, symbol=S, asset_class=ASSET, liquid={"const": True}, leveraged={"const": False}, inverse={"const": False}, sector=S, diversified=BOOL)
LIMITS = obj(initial_cash=MONEY, max_deployed_capital=MONEY, company_weight=CONF, sector_weight=CONF, diversified_etf_weight=CONF, gross_exposure=CONF, daily_loss=CONF, drawdown=CONF, turnover=CONF, orders_per_session=POS, max_quote_age_seconds=POS, max_spread_bps=DEC)
CLOCK = obj(calendar=S, cadence=S, max_stale_sessions=N, eligibility=enum("publication_and_ingestion", "archived_publication"), missing_data=enum("halt_all", "halt_affected"))
COSTS = obj(fee_per_order=MONEY, slippage_bps=DEC, spread_bps=DEC, fill_model=S, corporate_actions=S)

COMPLETABLE_SCOPES = ("full_book", "full_paper", "approved_excerpt")


FIELDS = {
    "learning_session": dict(mode={"const": "learning"}, character_versions=array(ID, 1), source_ids=array(ID, 1), authorization=S, provenance=S),
    "conversation": dict(participant_character_versions=array(ID, 1), snapshot_id=ID, portfolio_id=ID, deadline=UTC),
    "model_call": dict(model_id=S, prompt_version=S, input_hash=HASH, response_hash=HASH, source_ids=array(ID, 1), usage=USAGE),
    "source": dict(title=S, authors=array(S, 1), edition=S, isbn=nullable({"type": "string", "pattern": "^[0-9]{13}$"}), publisher=S, locator=S, retrieved_at=UTC, checked_at=UTC, next_check_at=UTC, access=enum("unknown", "public_full_text", "sample_only", "library_loan", "owned_copy", "user_supplied", "purchase_required", "unavailable"), rights=RIGHTS, publication_eligibility=enum("unknown", "metadata_only", "derived_permitted", "raw_permitted"), private_locator=nullable(S), ingestion_status=enum("not_started", "partial", "complete", "blocked"), blocker=nullable(S)),
    "experiment": dict(mode=enum("council", "character_portfolio"), regime=enum("fixture", "historical_restricted", "hindsight", "forward_shadow", "forward_paper"), character_versions=array(ID, 1), policy_id=ID, universe=array(INSTRUMENT, 1), baseline_cash=S, baseline_fund=S, membership_basis=S, decision_cadence=S, sizing_rules=S, data_feeds=array(S, 1), costs=COSTS, start_at=UTC, end_at=UTC, development_end_at=UTC, validation_end_at=UTC, metrics=array(S, 1), minimum_sessions=POS, minimum_forecasts=POS, advice=enum("none", "bounded"), knowledge_cutoff=UTC, retrieval_policy=S, model_limitations=S, approval_ref=S),
    "character": dict(character_id=ID, version=S, constitution_hash=HASH, curriculum_hash=HASH, readiness=enum("not_ready", "fixture_only", "partial", "ready"), foundation_source_id=ID),
    "portfolio": dict(mode=enum("council", "character_portfolio", "baseline"), owner_character_version=ID, initial_cash=MONEY, currency={"const": "USD"}),
    "checkpoint": dict(character_version=ID, curriculum_position=POS, section_index=POS, source_ids=array(ID, 1), source_hash=HASH, prior_hash=HASH, prior_checkpoint_id=nullable(ID), accepted_claims=array(CLAIM), rejected_claims=array(CLAIM), memory_delta=array(S, 1), consolidated_memory=array(CLAIM, 1), adversarial_review=array(S, 1), reading_status=enum("partial", "complete"), material_scope=enum("fixture", "sample", *COMPLETABLE_SCOPES), model_call_id=ID),
    "registration": dict(character_version=ID, prediction=S, horizon=S, benchmark=S, failure_condition=S, evaluation_start=UTC, evaluation_end=UTC, metrics=array(S, 1)),
    "theory": dict(character_version=ID, version=S, checkpoint_id=ID, test_registration_id=ID, position=S, minimal_logic_chain=array(S, 3), scope=S, assumptions=array(S, 1), predicted_observables=array(S, 1), portfolio_implication=enum("buy", "sell", "size", "wait", "abstain"), invalidation_conditions=array(S, 1), strongest_counterarguments=array(S, 1), rebuttals=STRINGS, confidence=CONF, evidence_and_citations=array(CITATION, 1)),
    "observation": dict(instrument_id=ID, asset_class=ASSET, event_at=UTC, published_at=UTC, ingested_at=UTC, availability_evidence=S, revision=POS, supersedes_id=nullable(ID), superseded_at=nullable(UTC), feed=S, units=S, payload_hash=HASH, quality=enum("eligible", "quarantined", "missing"), publication_eligibility=enum("unknown", "private_only", "derived_permitted", "raw_permitted")),
    "snapshot": dict(cutoff=UTC, clock_policy=CLOCK, observation_ids=array(ID, 1), exclusions=array(obj(observation_id=ID, reason=S)), content_hash=HASH),
    "message": dict(conversation_id=ID, sender_character_version=ID, recipient_character_ids=array(ID, 1), portfolio_context=ID, snapshot_id=ID, available_at=UTC, expires_at=UTC, reply_to=nullable(ID), kind=enum("question", "evidence", "objection", "reply", "decision", "retrospective"), question=nullable(S), body={"type": "string", "minLength": 1, "maxLength": 12000}, evidence_ids=IDS, related_theory_ids=IDS),
    "recommendation": dict(character_version=ID, portfolio_id=ID, snapshot_id=ID, instrument_id=nullable(ID), action=enum("buy", "sell", "hold", "wait", "abstain"), quantity=DEC, horizon=S, confidence=CONF, confidence_event=S, invalidation_conditions=array(S, 1), citations=array(CITATION), expires_at=UTC, abstention_reason=nullable(S), theory_ids=IDS),
    "policy": dict(version=S, stage=enum("fixture", "paper"), synthetic=BOOL, universe=array(INSTRUMENT, 1), limits=LIMITS, clock=CLOCK, costs=COSTS, long_only={"const": True}, cash_only={"const": True}, approval_ref=nullable(S), approved_at=nullable(UTC), operator=nullable(S), kill_switch_owner=nullable(S), reconciliation_owner=nullable(S), incident_owner=nullable(S)),
    "ledger_event": dict(portfolio_id=ID, decision_id=nullable(ID), order_id=nullable(ID), event_kind=enum("funding", "order", "reservation", "fill", "cancellation", "fee", "distribution", "split", "correction", "mark"), instrument_id=nullable(ID), quantity=SIGNED, price=nullable(MONEY), fees=MONEY, cash_delta=SIGNED, event_at=UTC, simulation_model_version=S, corrects_id=nullable(ID)),
    "evaluation": dict(window_start=UTC, window_end=UTC, eligible_sample=N, benchmark=S, cost_model=S, metrics=array(obj(name=S, value=nullable(SIGNED), null_reason=nullable(S)), 1), evidence_status=CONTAMINATION, source_run_ids=array(ID, 1)),
    "run_manifest": dict(mode=enum("council", "character_portfolio", "learning"), code_commit={"type": "string", "pattern": "^[a-f0-9]{40}$"}, policy_version=S, source_revisions=array(S, 1), character_versions=array(ID, 1), model_id=S, prompt_version=S, sampling=obj(temperature=CONF, seed=nullable(N)), market_cutoff=UTC, knowledge_cutoff=UTC, input_hash=HASH, output_hash=nullable(HASH), phase_status=obj(prepare=PHASE, execute=PHASE, export=PHASE), usage=USAGE, failure=nullable(S), resume_from=nullable(S), parent_run_id=nullable(ID)),
}


def schema():
    definitions = {}
    for kind, fields in FIELDS.items():
        definitions[kind] = obj(id=ID, schema_version={"const": 1}, record_type={"const": kind}, experiment_id=nullable(ID) if kind == "source" else ID, created_at=UTC, contamination=CONTAMINATION, **fields)
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://trade-theorist.local/schemas/contracts-v1.json", "oneOf": [{"$ref": f"#/$defs/{kind}"} for kind in FIELDS], "$defs": definitions}
