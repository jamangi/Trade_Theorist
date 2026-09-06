"""Operational v2 contracts. These describe records, never expected accounting answers."""

from .schema import (S, ID, HASH, UTC, DEC, MONEY, SIGNED, N, POS, BOOL,
                     CONTAMINATION, RIGHT, FIELDS as V1_FIELDS, obj, array, enum, nullable)

MODE = enum("character_portfolio", "council")
BASIS = enum("simulated", "paper_broker")
CLASS = enum("private_strategy", "private_reconstructable", "private_market_provenance", "private_attribution")
CLIENT = {"type": "string", "pattern": "^[a-f0-9]{32}$"}
PRECISE = {"type": "string", "pattern": "^(0|[1-9][0-9]*)(\\.[0-9]{1,28})?$"}
SOURCE = obj(rights_id=ID, source_event_ids=array(ID), source_hash=HASH)
FLOW = obj(amount=MONEY, boundary_mark_ids=array(ID))
VALUE = obj(value=nullable(SIGNED), reason=nullable(S), unit=enum("USD", "ratio", "count"))
POINT = obj(at=UTC, equity=nullable(SIGNED), wealth=nullable(SIGNED), drawdown=nullable(SIGNED), reason=nullable(S))
EVENTS = {
    "funding": FLOW, "contribution": FLOW, "withdrawal": FLOW,
    "segment_end": obj(reason=S),
    "order": obj(order_id=ID),
    "reservation": obj(order_id=ID, cash=MONEY, quantity=DEC),
    "release": obj(order_id=ID, reservation_id=ID, cash=MONEY, quantity=DEC, reason=S),
    "fill": obj(order_id=ID, instrument_id=ID, side=enum("buy", "sell"), quantity=DEC,
                price=DEC, notional=MONEY, fees=MONEY, fee_treatment=enum("included", "separate"),
                incremental_fill_id=ID),
    "fee": obj(amount=MONEY, allocation=enum("acquisition", "disposal", "unallocated"), fill_id=nullable(ID)),
    "dividend_entitlement": obj(action_id=ID, instrument_id=ID, eligible_quantity=DEC,
                                per_share=DEC, amount=MONEY, ex_at=UTC, mark_id=ID, policy_hash=HASH),
    "dividend_payment": obj(entitlement_id=ID, amount=MONEY),
    "split": obj(action_id=ID, instrument_id=ID, numerator=POS, denominator=POS, mark_id=ID,
                 pending_orders=enum("none", "reconciled", "requires_reconciliation")),
    "cash_in_lieu": obj(action_event_id=ID, instrument_id=ID, quantity=DEC, price=DEC, amount=MONEY),
    "correction": obj(corrects_id=ID, replacement_id=nullable(ID), reason=S, projection_revision=POS),
    "mark": obj(instrument_id=ID, price=nullable(DEC), event_at=UTC, published_at=UTC, received_at=UTC,
                feed=S, adjustment=enum("raw", "split_adjusted", "total_return"), observation_id=ID,
                observation_revision=POS, eligibility_cutoff=UTC, status=enum("eligible", "stale", "missing"),
                reason=nullable(S), mark_policy_hash=HASH),
    "halt": obj(reason=S),
    "reconciliation_gap": obj(reason=S, evidence_hash=HASH),
}

FIELDS = {
    "inspection_context": dict(portfolio_id=ID, segment_id=ID, character_version=ID, as_of=UTC,
        label=S, horizon=S, advice=enum("none", "bounded"), belief=nullable(S), rationale=nullable(S), invalidation=nullable(S),
        learning_statement=S, learning_completed=N, learning_total=N,
        source_citations=array(obj(title=S, edition=S, locator=S)),
        advice_log=array(obj(author_version=ID, kind=S, status=S, summary=S)),
        forecasts=obj(matured=N, pending=N, unscorable=N, brier=VALUE), abstentions=N,
        heartbeat_status=enum("no_data", "completed", "pending", "failed"), last_successful_heartbeat=nullable(UTC)),
    "source_rights": dict(source_id=ID, origin=enum("original_synthetic", "licensed", "owner_authored"),
                          private_storage=RIGHT, private_replay=RIGHT, private_read_model=RIGHT,
                          public_output={"const": "denied"}, evidence=array(S, 1), reviewed_at=UTC),
    "character": dict(character_id=ID, version=S, constitution_hash=HASH, curriculum_hash=HASH,
                      readiness=enum("not_ready", "fixture_only", "partial", "ready")),
    "policy": V1_FIELDS["policy"],
    "experiment": dict(mode=MODE, execution_basis=BASIS, character_versions=array(ID, 1), policy_id=ID,
                       instrument_ids=array(ID, 1), start_at=UTC, end_at=UTC,
                       regime=enum("fixture", "hindsight", "historical_restricted", "forward_shadow", "forward_paper")),
    "portfolio": dict(mode=MODE, execution_basis=BASIS, owner_character_version=ID, policy_id=ID,
                      currency={"const": "USD"}, role=enum("strategy", "baseline", "counterfactual", "matched_control"),
                      accounting_method={"const": "fifo-v2"}, return_method={"const": "exact-twr-v2"},
                      initialization=enum("new", "conversion_gap"), legacy_portfolio_id=nullable(ID)),
    "funded_segment": dict(portfolio_id=ID, owner_character_version=ID, ordinal=POS,
                           previous_segment_id=nullable(ID), start_at=UTC, reason=enum("initial", "refunding", "character_change")),
    "decision": dict(portfolio_id=ID, segment_id=ID, character_version=ID, snapshot_hash=HASH,
                     instrument_id=ID, side=enum("buy", "sell"), quantity=DEC, final={"const": True}),
    "order": dict(portfolio_id=ID, segment_id=ID, final_recommendation_id=ID, instrument_id=ID,
                  execution_basis=BASIS, side=enum("buy", "sell"), quantity=DEC, policy_approval_ref=S,
                  replaces_order_id=nullable(ID)),
    "lot": dict(portfolio_id=ID, segment_id=ID, instrument_id=ID, originating_fill_id=ID,
                originating_order_id=ID, acquired_at=UTC, original_quantity=DEC, remaining_quantity=DEC,
                original_basis=PRECISE, remaining_basis=PRECISE, corporate_action_ids=array(ID),
                projection_revision=POS, previous_lot_revision_id=nullable(ID), lot_id=ID),
    "lot_relief": dict(portfolio_id=ID, segment_id=ID, sale_fill_id=ID, lot_revision_id=ID,
                       quantity=DEC, allocated_basis=PRECISE, proceeds=PRECISE, disposal_fees=PRECISE,
                       projection_revision=POS),
    "projection": dict(portfolio_id=ID, segment_id=ID, owner_character_version=ID, mode=MODE,
                       execution_basis=BASIS, currency={"const": "USD"}, policy_id=ID,
                       source_event_ids=array(ID, 1), source_chain_hash=HASH,
                       effective_cutoff=UTC, receipt_cutoff=UTC, mark_policy_hash=HASH,
                       accounting_method={"const": "fifo-v2"}, return_method={"const": "exact-twr-v2"},
                       revision=POS, previous_projection_id=nullable(ID),
                       publication_class={"const": "private-owner-v2"},
                       status=enum("pending_calculation", "complete", "gap"), null_reasons=array(S),
                       result_hash=nullable(HASH)),
    "submission_mapping": dict(portfolio_id=ID, segment_id=ID, internal_order_id=ID,
                               client_order_id=CLIENT, policy_approval_ref=S),
    "outbox": dict(portfolio_id=ID, segment_id=ID, mapping_id=ID, internal_order_id=ID,
                   state=enum("prepared", "unknown", "acknowledged", "cancelled", "rejected"),
                   revision=POS, previous_outbox_id=nullable(ID), request_hash=HASH,
                   action={"const": "submit_once"}),
    "broker_update": dict(portfolio_id=ID, segment_id=ID, mapping_id=ID, provider_event_id=ID,
                          broker_order_id=S, effective_at=UTC, observed_at=UTC,
                          cumulative_quantity=DEC, cumulative_notional=MONEY, cumulative_fees=MONEY,
                          incremental_fill_id=nullable(ID), status=enum("accepted", "partially_filled", "filled", "cancelled", "rejected", "unknown")),
    "migration_lineage": dict(conversion_version={"const": "v1-to-v2-boundary-1"}, source_chain_hash=HASH,
                              source_records_hash=HASH, source_migrations_hash=HASH, destination_identity=HASH,
                              source_event_versions=array(S), limitations=array(S, 1),
                              converted_event_ids=array(ID), gaps=array(obj(source_id=ID, code=S))),
    "accounting_plan": dict(portfolio_id=ID, approved_at=UTC, approval_ref=S,
        flows=array(obj(segment_id=ID, event_type=enum("funding", "contribution", "withdrawal"), effective_at=UTC, amount=MONEY)),
        mark_schedule=array(UTC, 1), max_mark_age_seconds=N,
        execution_model={"const": "eligible-next-event-v2"}, fee_per_share=MONEY, slippage_bps=DEC,
        spread_bps=DEC, fractional_shares=BOOL, corporate_actions={"const": "explicit-raw-v2"},
        baseline_portfolio_id=nullable(ID), baseline_construction=S),
    "execution_terms": dict(portfolio_id=ID, segment_id=ID, order_id=ID, earliest_fill_at=UTC, expires_at=UTC, price_cap=DEC),
    "execution_command": dict(portfolio_id=ID, input_hash=HASH, record_ids=array(ID), result_hash=HASH),
    "operating_expense": dict(portfolio_id=ID, effective_at=UTC, category=enum("model", "data", "hosting", "learning", "development"),
                              recurring=BOOL, amount=nullable(MONEY), reason=nullable(S)),
    "account_reconciliation": dict(portfolio_id=ID, segment_id=ID, effective_at=UTC, observed_at=UTC, evidence_hash=HASH,
        broker_cash=SIGNED, economic_cash=SIGNED, broker_positions=array(obj(instrument_id=ID, quantity=DEC)),
        account_reset=BOOL, status=enum("matched", "halted"), differences=array(S)),
    "performance_result": dict(portfolio_id=ID, segment_id=ID, accounting_plan_id=ID, projection_revision=POS,
        effective_cutoff=UTC, receipt_cutoff=UTC, source_event_ids=array(ID, 1), source_chain_hash=HASH,
        publication_class={"const": "private-owner-v2"}, execution_basis=BASIS, mode=MODE, owner_character_version=ID,
        evidence_grade=CONTAMINATION, promotion_eligible={"const": False}, review_blockers=array(S, 1),
        cash=SIGNED, reserved=DEC, available=SIGNED, initial_funding=DEC, net_external_flows=SIGNED,
        fifo_basis=DEC, realized=SIGNED, income=SIGNED, fees=DEC, receivables=DEC, unallocated_expenses=DEC,
        equity=VALUE, unrealized=VALUE, strategy_pnl=VALUE, twr=VALUE, max_drawdown=VALUE, volatility=VALUE,
        turnover=VALUE, hit_rate=VALUE, lot_relief_win_rate=VALUE, recurring_expense=VALUE, one_time_expense=VALUE,
        economics_pnl=VALUE, cash_baseline=VALUE, broad_market_baseline=VALUE, benchmark_status=S,
        holdings=array(obj(instrument_id=ID, quantity=DEC, fifo_basis=DEC, value=nullable(SIGNED))),
        history=array(POINT), flow_signature=HASH, comparison_hash=HASH, halted=BOOL, gaps=array(S),
        closed_segments=array(obj(segment_id=ID, twr=nullable(SIGNED), reason=nullable(S))),
        order_outcomes=array(obj(order_id=ID, filled_quantity=DEC, remaining_quantity=DEC, status=S)),
        baseline_result_hash=nullable(HASH), operating_expense_ids=array(ID), definitions=array(S, 1)),
}

FIELD_CLASSES = {k: "private_strategy" for k in FIELDS}
FIELD_CLASSES.update(source_rights="private_market_provenance", ledger_event="private_reconstructable",
                     lot="private_reconstructable", lot_relief="private_reconstructable", projection="private_reconstructable",
                     submission_mapping="private_attribution", outbox="private_attribution", broker_update="private_attribution")
FIELD_CLASSES.update(performance_result="private_reconstructable", operating_expense="private_strategy")
FIELD_CLASSES["account_reconciliation"] = "private_attribution"


def schema():
    def common(kind):
        return dict(id=ID, schema_version={"const": 2}, record_type={"const": kind}, experiment_id=ID,
                    created_at=UTC, contamination=CONTAMINATION, field_class={"const": FIELD_CLASSES[kind]}, provenance=SOURCE)
    definitions = {kind: obj(**common(kind), **fields) for kind, fields in FIELDS.items()}
    definitions["ledger_event"] = {"oneOf": [obj(**common("ledger_event"), portfolio_id=ID, segment_id=ID,
        idempotency_key=ID, sequence=POS, effective_at=UTC, observed_at=UTC,
        event_type={"const": kind}, payload=payload) for kind, payload in EVENTS.items()]}
    for kind in ("experiment", "portfolio", "projection"):
        definitions[kind]["allOf"] = [{"if": {"properties": {"mode": {"const": "character_portfolio"}}},
            "then": {"properties": {"execution_basis": {"const": "simulated"}}}}]
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://trade-theorist.local/schemas/contracts-v2.json",
            "oneOf": [{"$ref": f"#/$defs/{kind}"} for kind in definitions], "$defs": definitions}
