"""Original operational contract fixtures, with no accounting projections calculated."""
from copy import deepcopy
from .contracts import digest
from .fixtures import base_records
from .migrate_v2 import envelope

EXP, PORT, CHAR, RIGHTS, POLICY, SEG = ("experiment:v2-fixture", "portfolio:v2-fixture", "character:v2-fixture",
                                      "rights:v2-fixture", "policy:v2-fixture", "segment:v2-fixture")
AT = "2099-01-01T21:00:00Z"
INSTRUMENT = "instrument:fixture-fund"


def record(kind, identifier, **fields):
    return envelope(kind, identifier, EXP, AT, RIGHTS, source_hash=digest("original operational fixture"), **fields)


def event(identifier, sequence, kind, **payload):
    return record("ledger_event", identifier, portfolio_id=PORT, segment_id=SEG, sequence=sequence,
                  idempotency_key=identifier, effective_at=AT, observed_at=AT, event_type=kind, payload=payload)


def bundle(*, mode="character_portfolio", basis="simulated"):
    policy = deepcopy(base_records()[1])
    policy = record("policy", POLICY, **{k: v for k, v in policy.items() if k not in {"id", "schema_version", "record_type", "experiment_id", "created_at", "contamination"}})
    records = [record("source_rights", RIGHTS, source_id="source:original-v2-fixture", origin="original_synthetic",
        private_storage="permitted", private_replay="permitted", private_read_model="permitted", public_output="denied",
        evidence=["Original project arithmetic; no provider observations"], reviewed_at=AT), policy,
        record("character", CHAR, character_id="character:fixture", version="fixture-v2", constitution_hash=digest("fixture constitution"),
               curriculum_hash=digest("fixture curriculum"), readiness="fixture_only"),
        record("experiment", EXP, mode=mode, execution_basis=basis, character_versions=[CHAR], policy_id=POLICY,
               instrument_ids=[INSTRUMENT], start_at=AT, end_at="2099-02-01T21:00:00Z", regime="fixture"),
        record("portfolio", PORT, mode=mode, execution_basis=basis, owner_character_version=CHAR, policy_id=POLICY,
               currency="USD", role="strategy", accounting_method="fifo-v2", return_method="exact-twr-v2",
               initialization="new", legacy_portfolio_id=None),
        record("funded_segment", SEG, portfolio_id=PORT, owner_character_version=CHAR, ordinal=1, previous_segment_id=None, start_at=AT, reason="initial"),
        event("event:v2-funding", 1, "funding", amount="1000.00", boundary_mark_ids=[]),
        record("decision", "decision:v2-buy", portfolio_id=PORT, segment_id=SEG, character_version=CHAR,
               snapshot_hash=digest("shared fictional snapshot"), instrument_id=INSTRUMENT, side="buy", quantity="2", final=True),
        record("order", "order:v2-buy", portfolio_id=PORT, segment_id=SEG, final_recommendation_id="decision:v2-buy",
               instrument_id=INSTRUMENT, execution_basis=basis, side="buy", quantity="2", policy_approval_ref="original-fixture-only", replaces_order_id=None),
        event("event:v2-order", 2, "order", order_id="order:v2-buy"),
        event("event:v2-reservation", 3, "reservation", order_id="order:v2-buy", cash="202.00", quantity="0"),
        event("event:v2-mark", 4, "mark", instrument_id=INSTRUMENT, price="100", event_at=AT, published_at=AT,
              received_at=AT, feed="original-synthetic-v2", adjustment="raw", observation_id="observation:original-v2",
              observation_revision=1, eligibility_cutoff=AT, status="eligible", reason=None, mark_policy_hash=digest("raw close")),
        event("event:v2-fill", 5, "fill", order_id="order:v2-buy", instrument_id=INSTRUMENT, side="buy", quantity="2",
              price="100", notional="200.00", fees="2.00", fee_treatment="included", incremental_fill_id="fill:v2-buy"),
        record("lot", "lot:v2-buy-r1", portfolio_id=PORT, segment_id=SEG, instrument_id=INSTRUMENT, originating_fill_id="event:v2-fill",
               originating_order_id="order:v2-buy", acquired_at=AT, original_quantity="2", remaining_quantity="2",
               original_basis="202", remaining_basis="202", corporate_action_ids=[], projection_revision=1,
               previous_lot_revision_id=None, lot_id="lot:v2-buy"),
    ]
    return records
