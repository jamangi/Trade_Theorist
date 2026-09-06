from copy import deepcopy
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator

from trade_theorist.contracts import ContractError, digest, validate, validate_bundle
from trade_theorist.fixtures_v2 import bundle, record, event, PORT, SEG, EXP, AT, CHAR, POLICY, INSTRUMENT
from trade_theorist.schema_v2 import schema, EVENTS


class V2ContractsTests(unittest.TestCase):
    def test_schema_dispatch_and_generated_fixture(self):
        Draft202012Validator.check_schema(schema())
        validate_bundle(bundle())
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(json.loads((root / "schemas/contracts-v2.json").read_text()), schema())
        self.assertEqual(json.loads((root / "examples/contracts-v2/bundle.json").read_text()), bundle())
        for version in (0, 3, "2", None):
            r = bundle()[0]
            r["schema_version"] = version
            with self.assertRaises(ContractError): validate(r)

    def test_modes_basis_field_classes_and_unknown_fields(self):
        for mode, basis in (("character_portfolio", "paper_broker"), ("character_portfolios", "simulated"), ("baseline", "simulated")):
            with self.assertRaises(ContractError): validate_bundle(bundle(mode=mode, basis=basis))
        validate_bundle(bundle(mode="council", basis="paper_broker"))
        for field, value in (("field_class", "public"), ("field_class", "private_strategy"), ("surprise", "private")):
            r = bundle()[-1]
            r[field] = value
            with self.assertRaises(ContractError): validate(r)

    def test_cross_portfolio_and_character_references(self):
        for target in ("event:v2-fill", "lot:v2-buy-r1", "order:v2-buy"):
            records = bundle()
            other = deepcopy(next(r for r in records if r["record_type"] == "portfolio"))
            other["id"] = "portfolio:other"
            records.append(other)
            next(r for r in records if r["id"] == target)["portfolio_id"] = other["id"]
            with self.assertRaises(ContractError): validate_bundle(records)
        records = bundle()
        next(r for r in records if r["record_type"] == "experiment")["character_versions"] = ["character:unknown"]
        with self.assertRaises(ContractError): validate_bundle(records)

    def test_flows_require_times_and_known_typed_payload(self):
        for kind in ("funding", "contribution", "withdrawal"):
            for key in ("effective_at", "observed_at", "idempotency_key", "sequence"):
                r = event("event:flow", 9, kind, amount="10.00", boundary_mark_ids=[])
                del r[key]
                with self.assertRaises(ContractError): validate(r)
        r = event("event:flow", 9, "funding", amount="10.00", boundary_mark_ids=[])
        r["event_type"] = "magic_credit"
        with self.assertRaises(ContractError): validate(r)
        r["event_type"] = "funding"
        r["observed_at"] = "2098-01-01T00:00:00Z"
        with self.assertRaises(ContractError): validate(r)

    def test_individual_has_no_client_id_and_fee_cannot_double_count(self):
        r = next(r for r in bundle() if r["record_type"] == "order")
        r["client_order_id"] = "0" * 32
        with self.assertRaises(ContractError): validate(r)
        fee = event("event:fee", 6, "fee", amount="2.00", allocation="acquisition", fill_id="event:v2-fill")
        with self.assertRaises(ContractError): validate_bundle(bundle() + [fee])

    def test_marks_and_projection_preserve_as_known_boundary(self):
        records = bundle()
        mark = next(r for r in records if r.get("event_type") == "mark")
        mark["payload"]["status"] = "stale"
        with self.assertRaises(ContractError): validate_bundle(records)
        mark["payload"].update(price=None, reason="Missing current session")
        validate_bundle(records)
        events = [r for r in records if r["record_type"] == "ledger_event"]
        p = record("projection", "projection:v2-r1", portfolio_id=PORT, segment_id=SEG, owner_character_version=CHAR,
            mode="character_portfolio", execution_basis="simulated", currency="USD", policy_id=POLICY,
            source_event_ids=[r["id"] for r in events], source_chain_hash=digest(events), effective_cutoff=AT, receipt_cutoff=AT,
            mark_policy_hash=digest("raw close"), accounting_method="fifo-v2", return_method="exact-twr-v2", revision=1,
            previous_projection_id=None, publication_class="private-owner-v2", status="gap", null_reasons=["Stale mark"], result_hash=None)
        validate_bundle(records + [p])
        p["receipt_cutoff"] = "2098-01-01T00:00:00Z"
        with self.assertRaises(ContractError): validate_bundle(records + [p])
        p["receipt_cutoff"] = AT
        p["publication_class"] = "public"
        with self.assertRaises(ContractError): validate(p)

    def test_cash_actions_and_corrections_are_typed(self):
        specimens = [
            event("event:release", 6, "release", order_id="order:v2-buy", reservation_id="event:v2-reservation", cash="202.00", quantity="0", reason="filled"),
            event("event:div", 7, "dividend_entitlement", action_id="action:div", instrument_id=INSTRUMENT, eligible_quantity="2", per_share="1", amount="2.00", ex_at=AT, mark_id="event:v2-mark", policy_hash=digest("policy")),
            event("event:payment", 8, "dividend_payment", entitlement_id="event:div", amount="2.00"),
            event("event:split", 9, "split", action_id="action:split", instrument_id=INSTRUMENT, numerator=2, denominator=1, mark_id="event:v2-mark", pending_orders="none"),
            event("event:correction", 10, "correction", corrects_id="event:v2-mark", replacement_id=None, reason="Source withdrew mark", projection_revision=2),
        ]
        validate_bundle(bundle() + specimens)
        specimens[-1]["payload"]["corrects_id"] = "event:correction"
        with self.assertRaises(ContractError): validate_bundle(bundle() + specimens)

    def test_rights_not_inferred_from_private_or_fixture_label(self):
        records = bundle()
        records[0]["private_storage"] = "unknown"
        with self.assertRaises(ContractError): validate_bundle(records)

    def test_duplicate_or_leaking_mapping_contracts(self):
        records = bundle(mode="council", basis="paper_broker")
        order = next(r for r in records if r["record_type"] == "order")
        mapping = record("submission_mapping", "mapping:fixture", portfolio_id=PORT, segment_id=SEG,
            internal_order_id=order["id"], client_order_id="0123456789abcdef0123456789abcdef", policy_approval_ref=order["policy_approval_ref"])
        outbox = record("outbox", "outbox:fixture", portfolio_id=PORT, segment_id=SEG, mapping_id=mapping["id"],
            internal_order_id=order["id"], state="prepared", revision=1, previous_outbox_id=None, request_hash=digest(order), action="submit_once")
        validate_bundle(records + [mapping, outbox])
        duplicate = dict(mapping, id="mapping:duplicate")
        with self.assertRaises(ContractError): validate_bundle(records + [mapping, outbox, duplicate, dict(outbox, id="outbox:duplicate", mapping_id=duplicate["id"])])
        mapping["client_order_id"] = "character-fixture-experiment-name"
        with self.assertRaises(ContractError): validate(mapping)

    def test_json_schema_rejects_individual_paper_basis(self):
        portfolio = next(r for r in bundle() if r["record_type"] == "portfolio")
        portfolio["execution_basis"] = "paper_broker"
        self.assertFalse(Draft202012Validator(schema()).is_valid(portfolio))


if __name__ == "__main__": unittest.main()
