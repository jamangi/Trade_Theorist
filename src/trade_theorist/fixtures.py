"""Original synthetic examples; no book text, live data, or paid model calls."""

from copy import deepcopy
import json
from pathlib import Path

from .contracts import digest, validate_bundle

TIME = "2026-09-05T12:00:00Z"
EXP = "experiment:foundation-fixture"
CHAR = "character:index-steward-fixture-v1"
SOURCE = "source:original-arithmetic-fixture"
CONSTITUTION = "Fixture-only design prior: check arithmetic, record costs, and preserve objections. This is not Bogle-derived learning."
CURRICULUM = [{"position": 1, "source_id": SOURCE, "intended_lesson": "Test source citations, cost arithmetic and a qualified counterexample."}]
MATERIAL = dict(source_id=SOURCE, scope="fixture", completeness_verified=True, coverage_evidence="Complete two-section project-authored fixture; not a book.", sections=[
    {"index": 1, "locator": "fixture/section-1", "text": "In this fictional arithmetic example, a basket earns 100 units before expenses. A cost of 4 units leaves 96 units. A cost of 1 unit leaves 99 units. The two baskets have identical gross proceeds."},
    {"index": 2, "locator": "fixture/section-2", "text": "The identical-proceeds assumption can fail. In a separate fictional example, basket A earns 110 units and costs 4 units, leaving 106. Basket B earns 100 units and costs 1 unit, leaving 99. Cost alone does not determine the winner."},
])


def record(record_type, identifier, **fields):
    return dict(id=identifier, schema_version=1, record_type=record_type, experiment_id=EXP, created_at=TIME, contamination="fixture", **fields)


def base_records():
    universe = [dict(instrument_id="instrument:fixture-fund", symbol="FIXTURE", asset_class="unleveraged_us_etf", liquid=True, leveraged=False, inverse=False, sector="diversified", diversified=True)]
    clock = dict(calendar="synthetic-daily-v1", cadence="daily_session", max_stale_sessions=0, eligibility="publication_and_ingestion", missing_data="halt_all")
    costs = dict(fee_per_order="0.00", slippage_bps="5", spread_bps="2", fill_model="synthetic-next-open-v1", corporate_actions="explicit_fixture_events")
    source = record("source", SOURCE, title="Original arithmetic fixture", authors=["Trade Theorist project"], edition="fixture-v1", isbn=None, publisher="Trade Theorist project", locator="fixture://arithmetic-v1", retrieved_at=TIME, checked_at=TIME, next_check_at="2099-01-01T00:00:00Z", access="public_full_text", rights=dict(reading="permitted", machine_ingestion="permitted", private_storage="permitted", redistribution="permitted", evidence=["Original synthetic project text created for software tests; no third-party book text."]), publication_eligibility="raw_permitted", private_locator=None, ingestion_status="not_started", blocker=None)
    source["experiment_id"] = None
    policy = record("policy", "policy:synthetic-v1", version="fixture-v1", stage="fixture", synthetic=True, universe=universe, limits=dict(initial_cash="10000.00", max_deployed_capital="10000.00", company_weight=0.2, sector_weight=0.4, diversified_etf_weight=1.0, gross_exposure=1.0, daily_loss=0.02, drawdown=0.1, turnover=0.2, orders_per_session=5, max_quote_age_seconds=60, max_spread_bps="20"), clock=clock, costs=costs, long_only=True, cash_only=True, approval_ref=None, approved_at=None, operator=None, kill_switch_owner=None, reconciliation_owner=None, incident_owner=None)
    character = record("character", CHAR, character_id="index_steward_fixture", version="fixture-v1", constitution_hash=digest(CONSTITUTION), curriculum_hash=digest(CURRICULUM), readiness="fixture_only", foundation_source_id=SOURCE)
    experiment = record("experiment", EXP, mode="council", regime="fixture", character_versions=[CHAR], policy_id=policy["id"], universe=universe, baseline_cash="zero-yield fictional cash", baseline_fund="FIXTURE broad basket; not a real fund", membership_basis="synthetic fixed instrument", decision_cadence="daily_session", sizing_rules="fixture policy only", data_feeds=["synthetic-v1"], costs=costs, start_at="2099-01-03T00:00:00Z", end_at="2099-02-03T00:00:00Z", development_end_at="2099-01-01T00:00:00Z", validation_end_at="2099-01-02T00:00:00Z", metrics=["net_return", "drawdown", "calibration"], minimum_sessions=2, minimum_forecasts=2, advice="none", knowledge_cutoff=TIME, retrieval_policy="Original fixtures only; no external retrieval", model_limitations="Recorded synthetic outputs, no evidence of source learning or performance", approval_ref="synthetic-test-only")
    portfolio = record("portfolio", "portfolio:fixture-council", mode="council", owner_character_version=CHAR, initial_cash="10000.00", currency="USD")
    run = record("run_manifest", "run:foundation-fixture", mode="learning", code_commit="acdb8626539f3a70aa5f600ce86fb9b55c923d62", policy_version="fixture-v1", source_revisions=[digest(MATERIAL)], character_versions=[CHAR], model_id="recorded-fixture-v1", prompt_version="learning-v1", sampling=dict(temperature=0, seed=0), market_cutoff=TIME, knowledge_cutoff=TIME, input_hash=digest(MATERIAL), output_hash=None, phase_status=dict(prepare="pending", execute="pending", export="pending"), usage=dict(input_tokens=0, output_tokens=0, calls=0, cost_usd="0.00"), failure=None, resume_from=None, parent_run_id=None)
    return [source, policy, character, experiment, portfolio, run]


def complete_bundle():
    records = base_records()
    observation = record("observation", "observation:fixture-1", instrument_id="instrument:fixture-fund", asset_class="unleveraged_us_etf", event_at=TIME, published_at=TIME, ingested_at=TIME, availability_evidence="Synthetic event created with all three timestamps", revision=1, supersedes_id=None, superseded_at=None, feed="synthetic-v1", units="USD", payload_hash=digest({"price": "100.00"}), quality="eligible", publication_eligibility="raw_permitted")
    snapshot = record("snapshot", "snapshot:fixture-1", cutoff=TIME, clock_policy=records[1]["clock"], observation_ids=[observation["id"]], exclusions=[], content_hash=digest([observation]))
    conversation = record("conversation", "conversation:fixture-1", participant_character_versions=[CHAR], snapshot_id=snapshot["id"], portfolio_id="portfolio:fixture-council", deadline="2026-09-06T12:00:00Z")
    call = record("model_call", "call:contract-fixture", model_id="recorded-fixture-v1", prompt_version="learning-v1", input_hash=digest(MATERIAL), response_hash=digest("synthetic-contract-example"), source_ids=[SOURCE], usage=dict(input_tokens=0, output_tokens=0, calls=1, cost_usd="0.00"))
    citation = dict(source_id=SOURCE, locator=MATERIAL["sections"][0]["locator"], passage_hash=digest(MATERIAL["sections"][0]["text"]))
    claim = dict(claim_id="claim:fixture-1", text="Identical gross proceeds and lower costs leave more net units.", citations=[citation])
    checkpoint = record("checkpoint", "checkpoint:contract-fixture", character_version=CHAR, curriculum_position=1, section_index=1, source_ids=[SOURCE], source_hash=digest(MATERIAL), prior_hash=digest(CONSTITUTION), prior_checkpoint_id=None, accepted_claims=[claim], rejected_claims=[], memory_delta=[claim["text"]], consolidated_memory=[claim], adversarial_review=["Gross proceeds need not be identical."], reading_status="partial", material_scope="fixture", model_call_id="call:contract-fixture")
    registration = record("registration", "registration:contract-fixture", character_version=CHAR, prediction="The lower-cost identical-gross fixture retains three more units.", horizon="One synthetic event", benchmark="Identical-gross basket", failure_condition="Net-unit difference is not three", evaluation_start="2099-01-03T00:00:00Z", evaluation_end="2099-02-03T00:00:00Z", metrics=["net_units"])
    theory = record("theory", "theory:contract-fixture", character_version=CHAR, version="fixture-v1", checkpoint_id=checkpoint["id"], test_registration_id=registration["id"], position=claim["text"], minimal_logic_chain=["Equal gross units", "Subtract different costs", "Lower costs leave more net units"], scope="Original arithmetic fixture only", assumptions=["Gross proceeds equal"], predicted_observables=["Three-unit net difference"], portfolio_implication="wait", invalidation_conditions=["Gross proceeds differ"], strongest_counterarguments=["Other costs or outcomes may differ"], rebuttals=["Limit the claim to the stated example"], confidence=0.8, evidence_and_citations=[citation])
    recommendation = record("recommendation", "recommendation:fixture-wait", character_version=CHAR, portfolio_id="portfolio:fixture-council", snapshot_id=snapshot["id"], instrument_id=None, action="wait", quantity="0", horizon="one session", confidence=0.5, confidence_event="No sufficient evidence for activity", invalidation_conditions=["Eligible additional evidence arrives"], citations=[citation], expires_at="2026-09-06T12:00:00Z", abstention_reason="Fixture does not establish a tradable edge", theory_ids=[theory["id"]])
    message = record("message", "message:fixture-objection", conversation_id="conversation:fixture-1", sender_character_version=CHAR, recipient_character_ids=[CHAR], portfolio_context="portfolio:fixture-council", snapshot_id=snapshot["id"], available_at=TIME, expires_at="2026-09-06T12:00:00Z", reply_to=None, kind="objection", question=None, body="The equal-gross assumption needs testing.", evidence_ids=[observation["id"]], related_theory_ids=[theory["id"]])
    ledger = record("ledger_event", "ledger:fixture-funding", portfolio_id="portfolio:fixture-council", decision_id=None, order_id=None, event_kind="funding", instrument_id=None, quantity="0", price=None, fees="0.00", cash_delta="10000.00", event_at=TIME, simulation_model_version="fixture-v1", corrects_id=None)
    evaluation = record("evaluation", "evaluation:fixture-empty", window_start=TIME, window_end="2026-09-06T12:00:00Z", eligible_sample=0, benchmark="zero-yield fictional cash", cost_model="fixture-v1", metrics=[dict(name="hit_rate", value=None, null_reason="No closed positions")], evidence_status="fixture", source_run_ids=["run:foundation-fixture"])
    records.extend([observation, snapshot, conversation, call, checkpoint, registration, theory, recommendation, message, ledger, evaluation])
    validate_bundle(records)
    return records


def fixture_response(section):
    first = section["index"] == 1
    claim_id = "claim:learning-" + str(section["index"])
    text = "With identical gross proceeds, the cheaper basket retains three more units." if first else "Different gross proceeds can outweigh the cost advantage."
    quote = "A cost of 4 units leaves 96 units." if first else "Cost alone does not determine the winner."
    return dict(
        extraction=[dict(claim_id=claim_id, text=text, locator=section["locator"], quote=quote)],
        accepted_claim_ids=[claim_id], rejected_claim_ids=[],
        assimilation=["Accept this arithmetic under the stated conditions; do not generalize it into market performance."],
        adversarial_review=["The baskets may have different gross proceeds; real comparisons need matched exposures and all costs."],
        memory_delta=[text, "This is an original fixture, not evidence of reading Bogle."],
        theory=dict(position=text, minimal_logic_chain=["Observe stated gross proceeds", "Subtract the stated costs", "Compare remaining units"], scope="Two fictional baskets only", assumptions=["All costs and gross proceeds are specified"], predicted_observables=["Net units equal gross units less costs"], portfolio_implication="wait", invalidation_conditions=["Missing cost or mismatched gross proceeds"], strongest_counterarguments=["Toy arithmetic does not establish an investable edge"], rebuttals=["Restrict the theory to fixture arithmetic"], confidence=0.8),
        test=dict(prediction="Recompute and match the stated net units", horizon="One synthetic arithmetic event", benchmark="Stated fictional basket", failure_condition="Computed net units differ from stated totals", evaluation_start="2099-01-03T00:00:00Z", evaluation_end="2099-02-03T00:00:00Z", metrics=["net_units"]),
    )
