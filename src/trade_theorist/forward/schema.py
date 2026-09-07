"""Additive v2 contracts for one preregistered, paired forward decision round."""
from ..schema import ID, HASH, UTC, N, POS, S, BOOL, DEC, CONF, obj, array, enum, nullable
from ..request_contracts import POLICY, BAR_QUERY, QUERY, TELEMETRY

ANCESTRY = obj(local_character_ref=ID, character_id=S, eligible_version_id=ID, eligible_version_hash=HASH,
    learning_version_id=ID, learning_version_hash=HASH, knowledge_id=ID, knowledge_hash=HASH,
    constitution_hash=HASH, curriculum_hash=HASH, foundation_completed_at=UTC)
PUBLIC_FACT = obj(source_id=ID, url=S, published_at=nullable(UTC), ingested_at=UTC, availability_evidence=S,
                  text=S, payload_hash=HASH)
REAL_CONTEXT = obj(readiness_register_hash=HASH, ancestry=array(ANCESTRY,3),
    bars_qualification_hash=HASH, actions_qualification_hash=HASH, action_receipts_hash=HASH,
    runtime_id={"const":"foundation-rules-v1"}, runtime_hash=HASH,
    information_tools={"const":[]}, public_facts=array(PUBLIC_FACT),
    advice_policy={"const":"independent-initials-then-three-bounded-messages-index-leads"},
    calendar=array(obj(session=S,open_at=UTC,close_at=UTC),1),
    forecast=obj(horizon_sessions=POS,resolves_at=UTC,event=S,probability=CONF),
    order_expiry=UTC, allocation_fraction=DEC,
    observation_policy=obj(review_at=UTC,max_total_attempts=POS,queries=array(QUERY,2)),
    trend_lookback=POS,
    operating_cost_policy=S, external_flow_policy={"const":"initial-funding-only"},
    trial_variant={"const":"one-fixed-policy-no-tuning"})

REASON = enum("none", "quota", "cooldown", "recovery", "page_limit", "attempt_budget", "deadline",
              "entitlement", "retry_limit", "transport", "response", "coverage", "busy",
              "model_budget", "execution_ambiguous", "execution_failed")
PARTICIPANT = obj(portfolio_ref=ID, segment_ref=ID, character_ref=ID, plan_ref=ID,
    portfolio_hash=HASH, segment_hash=HASH, character_hash=HASH, plan_hash=HASH, policy_hash=HASH,
    mode=enum("character_portfolio", "council"), execution_basis={"const": "simulated"})
BAR = obj(symbol=S, t=UTC, o={"type": "number"}, h={"type": "number"}, l={"type": "number"},
          c={"type": "number"}, v=N)
BAR["properties"].update(n=N, vw={"type": "number"})
OBSERVATION = obj(id=ID, bar=BAR, received_at=UTC, request_hash=HASH)
OUTCOME = obj(portfolio_ref=ID, character_ref=ID, snapshot_ref=ID, snapshot_hash=HASH,
    action=enum("hold", "buy", "sell", "abstain"), reason=REASON, rationale=S)
FIELDS = {
    'forward_audit': dict(manifest_ref=ID,snapshot_ref=ID,purpose=enum('request','allocations','settled','observation_attempt'),payload_json=S,payload_hash=HASH),
    "forward_manifest": dict(start_at=UTC, end_at=UTC, decision_at=UTC, data_deadline=UTC,
        snapshot_ref=ID, work_ref=ID, query=BAR_QUERY, query_hash=HASH, quota_policy=POLICY, quota_policy_hash=HASH,
        max_request_attempts=POS, estimated_pages=POS, estimated_attempts_with_retries=POS,
        estimate_is_bound={"const": False}, partial_coverage={"const": "require_complete"}, revision_rule={"const": "latest_received_before_cutoff"},
        participants=array(PARTICIPANT, 2), baseline_ref=ID, baseline_plan_ref=ID, baseline_hash=HASH,
        baseline_plan_hash=HASH, comparison_hash=HASH,
        model_budget=obj(model_ref=ID, max_calls=POS, max_tokens=POS, max_output_tokens=POS),
        stopping_rule=obj(horizon_sessions=POS, min_completed_sessions=POS, min_matured_forecasts=POS,
            stop_at=UTC, stop_on_data_failure={"const": True}),
        publication_class={"const": "private-owner-v2"}, broker_orders_allowed={"const": False},
        evidence_grade=enum("fixture","forward-insufficient"), promotion_eligible={"const": False}, real_context=REAL_CONTEXT),
    "forward_snapshot": dict(manifest_ref=ID, work_ref=ID, query_hash=HASH, decision_at=UTC,
        status=enum("ready", "abstained"), reason=REASON, observations=array(OBSERVATION),
        coverage_expected=POS, coverage_observed=N, publication_class={"const": "private-owner-v2"}),
    "forward_progress": dict(manifest_ref=ID, snapshot_ref=ID, status=enum("deferred", "ready", "abstained"),
        reason=REASON, work_usage=TELEMETRY, physical_usage=TELEMETRY,
        physical_work_ref=ID, estimated_pages=POS, estimated_attempts_with_retries=POS,
        incomplete_pages=BOOL, deadline_missed=BOOL, shared_consumers=POS,
        publication_class={"const": "private-owner-v2"}),
    "forward_reservation": dict(manifest_ref=ID, snapshot_ref=ID, calls_reserved=POS, tokens_reserved=POS),
    "forward_result": dict(manifest_ref=ID, snapshot_ref=ID, snapshot_hash=HASH,
        status=enum("decided", "abstained"), reason=REASON, outcomes=array(OUTCOME, 2),
        model_calls=nullable(N), model_tokens=nullable(N), calls_reserved=N, tokens_reserved=N,
        publication_class={"const": "private-owner-v2"}, evidence_grade=enum("fixture","forward-insufficient"),
        promotion_eligible={"const": False}, broker_orders={"const": 0}),
    "forward_opinion": dict(manifest_ref=ID,snapshot_ref=ID,snapshot_hash=HASH,portfolio_ref=ID,
        character_ref=ID,knowledge_id=ID,knowledge_hash=HASH,phase=enum('independent','council'),
        action=enum('buy','sell','hold','abstain'),rationale=S,request_hash=HASH,
        advice_refs=array(ID),allocation_fraction=DEC,forecast_probability=nullable(CONF),forecast_resolves_at=UTC,
        model_calls={"const":0},runtime_id={"const":"foundation-rules-v1"}),
}
