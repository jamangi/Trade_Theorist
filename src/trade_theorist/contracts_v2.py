"""Strict v2 structure and typed, portfolio-scoped reference validation."""

from decimal import Decimal as D
from jsonschema import Draft202012Validator, FormatChecker

from .contracts import ContractError, canonical, digest, utc
from .schema_v2 import schema, FIELD_CLASSES

DEFINITIONS = schema()["$defs"]
CLASSES = FIELD_CLASSES
REFS = dict(rights_id="source_rights", policy_id="policy", character_versions="character",
            owner_character_version="character", character_version="character", portfolio_id="portfolio",
            segment_id="funded_segment", previous_segment_id="funded_segment", final_recommendation_id="decision",
            order_id="order", internal_order_id="order", originating_order_id="order", replaces_order_id="order",
            originating_fill_id="ledger_event", sale_fill_id="ledger_event", fill_id="ledger_event",
            reservation_id="ledger_event", entitlement_id="ledger_event", action_event_id="ledger_event",
            mark_id="ledger_event", boundary_mark_ids="ledger_event", corrects_id="ledger_event",
            replacement_id="ledger_event", corporate_action_ids="ledger_event", mapping_id="submission_mapping",
            previous_outbox_id="outbox", previous_projection_id="projection", previous_lot_revision_id="lot",
            lot_revision_id="lot")
REFS["accounting_plan_id"] = "accounting_plan"
REFS["operating_expense_ids"] = "operating_expense"


def validate(record):
    try:
        canonical(record)
        definition = DEFINITIONS[record["record_type"]]
    except (ValueError, TypeError, KeyError) as exc:
        raise ContractError("Unknown or invalid v2 record") from exc
    errors = list(Draft202012Validator(definition, format_checker=FormatChecker()).iter_errors(record))
    if errors:
        raise ContractError("Invalid v2 contract structure")
    kind = record["record_type"]
    if kind == "inspection_context":
        if utc(record["as_of"]) > utc(record["created_at"]) or record["learning_completed"] > record["learning_total"]:
            raise ContractError("Invalid saved inspection context timing or progress")
        if record["last_successful_heartbeat"] is not None and utc(record["last_successful_heartbeat"]) > utc(record["as_of"]):
            raise ContractError("Saved context cannot claim a future heartbeat")
        metric = record["forecasts"]["brier"]
        if (metric["value"] is None) != (metric["reason"] is not None):
            raise ContractError("Forecast metric needs a value or explicit unknown reason")
    if record["field_class"] != CLASSES[kind]:
        raise ContractError("Incorrect field classification")
    if record.get("mode") == "character_portfolio" and record.get("execution_basis") == "paper_broker":
        raise ContractError("Individual portfolios are simulated only")
    if kind == "experiment":
        if record["id"] != record["experiment_id"] or utc(record["start_at"]) >= utc(record["end_at"]):
            raise ContractError("Invalid experiment identity or window")
        expected = {"fixture": "fixture", "hindsight": "hindsight-contaminated", "historical_restricted": "historical-qualified"}
        if record["regime"] in expected and record["contamination"] != expected[record["regime"]]:
            raise ContractError("Evidence regime mismatch")
        if record["regime"].startswith("forward") and not record["contamination"].startswith("forward"):
            raise ContractError("Forward evidence label required")
    if kind == "character" and record["contamination"] == "fixture" and record["readiness"] not in {"fixture_only", "not_ready"}:
        raise ContractError("Fixture Character is not real-ready")
    if kind == "policy":
        from .contracts import validate as validate_v1
        legacy = {k: v for k, v in record.items() if k not in {"field_class", "provenance"}}
        legacy["schema_version"] = 1
        validate_v1(legacy)
    if kind in {"ledger_event", "broker_update"}:
        if utc(record["effective_at"]) > utc(record["observed_at"]) or utc(record["observed_at"]) > utc(record["created_at"]):
            raise ContractError("Effective/observed/recorded times are inconsistent")
    if kind in {"decision", "order", "lot_relief"} and D(record["quantity"]) <= 0:
        raise ContractError("Positive quantity required")
    if kind == "lot":
        if D(record["original_quantity"]) <= 0 or (not record["corporate_action_ids"] and D(record["remaining_quantity"]) > D(record["original_quantity"])) or D(record["remaining_basis"]) > D(record["original_basis"]):
            raise ContractError("Invalid lot remainder")
    if kind == "projection":
        if (record["status"] == "complete") != (record["result_hash"] is not None and not record["null_reasons"]):
            raise ContractError("Projection status requires a result or explicit gap")
        if record["status"] == "gap" and not record["null_reasons"]:
            raise ContractError("Gap requires reasons")
    if kind == "operating_expense":
        if (record["amount"] is None) != (record["reason"] is not None):
            raise ContractError("Operating expense needs a value or explicit unknown reason")
        if record["category"] in {"learning", "development"} and record["recurring"]:
            raise ContractError("Learning/development cost must remain separately classified")
    if kind == "account_reconciliation":
        if len({p["instrument_id"] for p in record["broker_positions"]}) != len(record["broker_positions"]):
            raise ContractError("Duplicate aggregate instrument")
        if utc(record["effective_at"]) > utc(record["observed_at"]) or utc(record["observed_at"]) > utc(record["created_at"]):
            raise ContractError("Invalid reconciliation timing")
    if kind == "performance_result":
        for metric in record.values():
            if isinstance(metric, dict) and set(metric) == {"value", "reason", "unit"} and (metric["value"] is None) != (metric["reason"] is not None):
                raise ContractError("Performance metric requires a value or explicit null reason")
    if kind == "ledger_event":
        p, event = record["payload"], record["event_type"]
        if event in {"funding", "contribution", "withdrawal", "fee", "dividend_entitlement", "dividend_payment", "cash_in_lieu"} and D(p["amount"]) <= 0:
            raise ContractError("Positive cash-event amount required")
        if event == "fill" and (D(p["quantity"]) <= 0 or D(p["price"]) <= 0 or (p["fee_treatment"] == "separate" and D(p["fees"]) != 0)):
            raise ContractError("Invalid fill or double-counted fees")
        if event == "mark":
            if not utc(p["event_at"]) <= utc(p["published_at"]) <= utc(p["received_at"]) <= utc(record["observed_at"]):
                raise ContractError("Invalid mark timing")
            if p["status"] == "eligible" and (p["price"] is None or p["reason"] is not None or utc(p["received_at"]) > utc(p["eligibility_cutoff"])):
                raise ContractError("Mark unavailable at eligibility cutoff")
            if p["status"] != "eligible" and (not p["reason"] or p["price"] is not None):
                raise ContractError("Unavailable marks require null price and reason")
    return record


def validate_references(record, lookup):
    """lookup reads one v2 record; provenance source IDs/hashes are external evidence."""
    validate(record)
    kind = record["record_type"]

    def ref(identifier, expected):
        target = lookup(identifier)
        if target["record_type"] != expected or target["experiment_id"] != record["experiment_id"]:
            raise ContractError("Missing, mistyped or cross-experiment v2 reference")
        if "portfolio_id" in record:
            target_portfolio = target["id"] if expected == "portfolio" else target.get("portfolio_id")
            if target_portfolio and target_portfolio != record["portfolio_id"]:
                raise ContractError("Cross-portfolio v2 reference")
        if record.get("segment_id") and target.get("segment_id") and target["segment_id"] != record["segment_id"] and not (kind in {"projection", "performance_result"} and expected == "ledger_event"):
            raise ContractError("Cross-segment v2 reference")
        return target

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in REFS and item is not None:
                    for identifier in item if isinstance(item, list) else [item]:
                        ref(identifier, REFS[key])
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(record)
    exp = ref(record["experiment_id"], "experiment")
    if exp["contamination"] != record["contamination"]:
        raise ContractError("Evidence must match experiment")
    rights = ref(record["provenance"]["rights_id"], "source_rights")
    if rights["private_storage"] != "permitted":
        raise ContractError("Private storage rights are not established")
    if rights["origin"] == "original_synthetic" and record["contamination"] != "fixture":
        raise ContractError("Synthetic rights cannot establish real evidence")
    if kind.startswith("forward_"):
        from .forward.validation import validate_forward
        validate_forward(record, lookup)
    if kind == "experiment":
        policy = ref(record["policy_id"], "policy")
        if set(record["instrument_ids"]) != {i["instrument_id"] for i in policy["universe"]}:
            raise ContractError("Universe differs from pinned policy")
        if record["execution_basis"] == "paper_broker" and record["contamination"] != "fixture" and (record["regime"] != "forward_paper" or policy["stage"] != "paper"):
            raise ContractError("Real paper identity requires a paper-stage policy and experiment")
    if record.get("instrument_id") and record["instrument_id"] not in exp["instrument_ids"]:
        raise ContractError("Instrument outside frozen universe")
    for key in ("owner_character_version", "character_version"):
        if key in record and record[key] not in exp["character_versions"]:
            raise ContractError("Character version is outside frozen experiment")
    if kind in {"portfolio", "projection"}:
        if any(record[k] != exp[k] for k in ("mode", "execution_basis", "policy_id")):
            raise ContractError("Portfolio/projection differs from experiment")
    portfolio = ref(record["portfolio_id"], "portfolio") if "portfolio_id" in record else None
    if kind == "inspection_context":
        if record["character_version"] != portfolio["owner_character_version"]:
            raise ContractError("Inspection context differs from frozen owner")
        for advice in record["advice_log"]:
            if advice["author_version"] not in exp["character_versions"]:
                raise ContractError("Advice author outside frozen experiment")
    if kind == "accounting_plan":
        if utc(record["approved_at"]) > utc(exp["start_at"]) or utc(record["created_at"]) > utc(exp["start_at"]):
            raise ContractError("Accounting/funding plan must be frozen before its window")
        if sorted(record["mark_schedule"], key=utc) != record["mark_schedule"]:
            raise ContractError("Mark schedule must be ordered")
        if D(record["slippage_bps"]) + D(record["spread_bps"]) / 2 >= 10000:
            raise ContractError("Invalid execution costs")
        if record["contamination"] != "fixture" and record["approval_ref"] != ref(portfolio["policy_id"], "policy")["approval_ref"]:
            raise ContractError("Funding plan needs recorded policy approval")
    if kind == "execution_terms":
        order = ref(record["order_id"], "order")
        if not utc(order["created_at"]) < utc(record["earliest_fill_at"]) < utc(record["expires_at"]) or D(record["price_cap"]) <= 0:
            raise ContractError("Execution terms require a later eligible event and expiry")
    if kind == "performance_result":
        if any(record[k] != portfolio[k] for k in ("mode", "execution_basis", "owner_character_version")):
            raise ContractError("Result differs from its frozen portfolio")
        if rights["private_replay"] != "permitted" or rights["private_read_model"] != "permitted":
            raise ContractError("Private accounting rights unavailable")
        for identifier in record["source_event_ids"]:
            ref(identifier, "ledger_event")
    if kind == "account_reconciliation" and (portfolio["mode"] != "council" or portfolio["execution_basis"] != "paper_broker"):
        raise ContractError("Aggregate account evidence requires a Monarchy paper ledger")
    if kind in {"decision", "projection"}:
        owner_key = "character_version" if kind == "decision" else "owner_character_version"
        if record[owner_key] != ref(record["segment_id"], "funded_segment")["owner_character_version"]:
            raise ContractError("Final decision/projection owner differs from funded segment")
    if kind == "funded_segment":
        if not utc(exp["start_at"]) <= utc(record["start_at"]) < utc(exp["end_at"]):
            raise ContractError("Funded segment must begin within its experiment window")
        if record["owner_character_version"] != portfolio["owner_character_version"]:
            raise ContractError("A changed Character needs an explicitly new frozen portfolio window")
        if record["previous_segment_id"]:
            previous = ref(record["previous_segment_id"], "funded_segment")
            if record["ordinal"] != previous["ordinal"] + 1 or utc(record["start_at"]) <= utc(previous["start_at"]):
                raise ContractError("Invalid funded segment order")
        elif record["ordinal"] != 1 or record["reason"] != "initial":
            raise ContractError("Initial segment required")
    if kind == "order":
        decision = ref(record["final_recommendation_id"], "decision")
        if record["execution_basis"] != portfolio["execution_basis"] or any(record[k] != decision[k] for k in ("instrument_id", "side", "quantity")):
            raise ContractError("Order differs from approved decision or execution basis")
        if record["contamination"] != "fixture" and record["policy_approval_ref"] != ref(portfolio["policy_id"], "policy")["approval_ref"]:
            raise ContractError("Order requires the recorded policy approval")
        if utc(record["created_at"]) < utc(decision["created_at"]):
            raise ContractError("Order precedes its final decision")
    if kind in {"submission_mapping", "outbox", "broker_update"}:
        if portfolio["mode"] != "council" or portfolio["execution_basis"] != "paper_broker":
            raise ContractError("Only Monarchy paper orders have broker attribution")
        if kind == "submission_mapping":
            order = ref(record["internal_order_id"], "order")
            if order["policy_approval_ref"] != record["policy_approval_ref"]:
                raise ContractError("Mapping approval differs from internal order")
            if utc(record["created_at"]) < utc(order["created_at"]):
                raise ContractError("Mapping precedes internal approval")
        else:
            mapping = ref(record["mapping_id"], "submission_mapping")
            if kind == "outbox" and record["internal_order_id"] != mapping["internal_order_id"]:
                raise ContractError("Outbox order differs from mapping")
            if kind == "outbox" and record["request_hash"] != digest(ref(record["internal_order_id"], "order")):
                raise ContractError("Outbox request differs from immutable order")
            if kind == "broker_update":
                order = ref(mapping["internal_order_id"], "order")
                if D(record["cumulative_quantity"]) > D(order["quantity"]):
                    raise ContractError("Broker quantity exceeds internal order")
    if kind in {"outbox", "projection", "lot"}:
        prev_key = {"outbox": "previous_outbox_id", "projection": "previous_projection_id", "lot": "previous_lot_revision_id"}[kind]
        rev_key = "projection_revision" if kind == "lot" else "revision"
        if record[prev_key]:
            prior = ref(record[prev_key], kind)
            stable = {"outbox": ("mapping_id", "request_hash"), "projection": ("accounting_method",), "lot": ("lot_id", "originating_fill_id")}[kind]
            if record[rev_key] != prior[rev_key] + 1 or any(record[k] != prior[k] for k in stable):
                raise ContractError("Conflicting projection/outbox revision")
            if kind == "outbox" and record["state"] == "prepared":
                raise ContractError("Unknown or completed submission must reconcile, never reprepare")
        elif record[rev_key] != 1 or (kind == "outbox" and record["state"] != "prepared"):
            raise ContractError("First revision required")
    if kind == "projection":
        if portfolio["initialization"] == "conversion_gap" and record["status"] == "complete":
            raise ContractError("Legacy conversion gaps cannot become completed FIFO results")
        if rights["private_replay"] != "permitted" or rights["private_read_model"] != "permitted":
            raise ContractError("Private projection rights are not established")
        events = [ref(i, "ledger_event") for i in record["source_event_ids"]]
        if digest(events) != record["source_chain_hash"] or any(utc(e["effective_at"]) > utc(record["effective_cutoff"]) or utc(e["observed_at"]) > utc(record["receipt_cutoff"]) for e in events):
            raise ContractError("Projection source hash or as-known cutoff differs")
    if kind == "ledger_event":
        p, event = record["payload"], record["event_type"]
        if utc(record["effective_at"]) < utc(ref(record["segment_id"], "funded_segment")["start_at"]):
            raise ContractError("Event precedes funded segment")
        if p.get("instrument_id") and p["instrument_id"] not in exp["instrument_ids"]:
            raise ContractError("Event instrument outside frozen universe")
        expected = {"reservation_id": "reservation", "entitlement_id": "dividend_entitlement", "mark_id": "mark", "fill_id": "fill"}
        for key, event_kind in expected.items():
            if p.get(key) and ref(p[key], "ledger_event")["event_type"] != event_kind:
                raise ContractError("Incorrect event reference type")
        for identifier in p.get("boundary_mark_ids", []):
            mark = ref(identifier, "ledger_event")
            if mark["event_type"] != "mark" or utc(mark["observed_at"]) > utc(record["observed_at"]) or utc(mark["effective_at"]) > utc(record["effective_at"]):
                raise ContractError("Flow boundary mark unavailable at flow")
        if event == "fill":
            order = ref(p["order_id"], "order")
            if any(p[k] != order[k] for k in ("instrument_id", "side")) or D(p["quantity"]) > D(order["quantity"]):
                raise ContractError("Fill differs from order")
        if event == "fee" and p["fill_id"] and ref(p["fill_id"], "ledger_event")["payload"]["fee_treatment"] != "separate":
            raise ContractError("Fill fees already included")
        if event == "fee" and (p["allocation"] != "unallocated") != (p["fill_id"] is not None):
            raise ContractError("Allocated fees require one fill reference")
        if event == "correction":
            corrected = ref(p["corrects_id"], "ledger_event")
            if corrected["sequence"] >= record["sequence"] or utc(corrected["observed_at"]) > utc(record["observed_at"]):
                raise ContractError("Correction must reference prior observed history")
            if p["replacement_id"] and ref(p["replacement_id"], "ledger_event")["event_type"] != corrected["event_type"]:
                raise ContractError("Correction replacement type differs")
    if kind in {"lot", "lot_relief"}:
        fill = ref(record["originating_fill_id"] if kind == "lot" else record["sale_fill_id"], "ledger_event")
        if fill["event_type"] != "fill" or fill["payload"]["side"] != ("buy" if kind == "lot" else "sell"):
            raise ContractError("Lot references incorrect fill")
        if kind == "lot" and (record["instrument_id"] != fill["payload"]["instrument_id"] or record["originating_order_id"] != fill["payload"]["order_id"]):
            raise ContractError("Lot origin differs from fill")
        if kind == "lot":
            for identifier in record["corporate_action_ids"]:
                action = ref(identifier, "ledger_event")
                if action["event_type"] not in {"split", "cash_in_lieu", "correction"}:
                    raise ContractError("Invalid lot corporate-action lineage")
        elif ref(record["lot_revision_id"], "lot")["instrument_id"] != fill["payload"]["instrument_id"]:
            raise ContractError("Sale and relieved lot instruments differ")


def validate_bundle(records):
    records = list(records)
    index = {r["id"]: r for r in records}
    if len(index) != len(records):
        raise ContractError("Duplicate v2 record identity")
    def lookup(identifier):
        if identifier not in index:
            raise ContractError("Missing v2 reference")
        return index[identifier]
    for record in records:
        validate_references(record, lookup)
    unique = {}
    for r in records:
        kind = r["record_type"]
        keys = []
        if kind == "submission_mapping":
            keys = [("client", r["client_order_id"]), ("internal_order", r["internal_order_id"])]
            initial = [o for o in records if o["record_type"] == "outbox" and o["mapping_id"] == r["id"] and o["revision"] == 1]
            if len(initial) != 1:
                raise ContractError("Mapping requires one initial outbox")
        elif kind == "outbox": keys = [("outbox_revision", r["mapping_id"], r["revision"])]
        elif kind == "broker_update": keys = [("provider_event", r["provider_event_id"])]
        elif kind == "ledger_event": keys = [("event_key", r["idempotency_key"]), ("event_sequence", r["portfolio_id"], r["sequence"])]
        for key in keys:
            if key in unique:
                raise ContractError("Duplicate v2 attribution or event identity")
            unique[key] = r["id"]
    return records
