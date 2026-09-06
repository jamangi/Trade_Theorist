from copy import deepcopy
from decimal import Decimal as D
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from trade_theorist.contracts import ContractError, digest
from trade_theorist.export import validate_export
from trade_theorist.export_v2 import build_private, export_private, validate_private, PRIVATE_SCHEMA
from trade_theorist.fixtures_dashboard_v2 import seed_dashboard
from trade_theorist.fixtures_accounting_v2 import FixtureV2, at
from trade_theorist.storage_v2 import V2Store


class PrivateExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=TemporaryDirectory();cls.root=Path(cls.temp.name)
        cls.store=V2Store(cls.root/"store",synthetic=True)
        cls.ids=seed_dashboard(cls.store)
        cls.report=build_private(cls.store,as_of=at(13))

    @classmethod
    def tearDownClass(cls):
        cls.store.close();cls.temp.cleanup()

    def card(self,key,day=11,receipt=11):
        v=next(v for v in self.report["versions"] if v["as_of"]==at(day) and v["receipt_cutoff"]==at(receipt))
        return next(c for c in v["cards"] if c["performance"]["portfolio_id"]==self.ids[key])

    def test_golden_private_cash_lots_flows_and_stale_values(self):
        card=self.card("individual");p=card["performance"]
        self.assertEqual(D(p["cash"]),1188);self.assertEqual(D(p["available"]),1088)
        self.assertEqual(D(p["reserved"]),100);self.assertEqual(D(p["twr"]["value"]),D(".05750570"))
        self.assertEqual(sum(D(l["basis"]) for l in card["lots"]),343)
        self.assertEqual([f["kind"] for f in card["flows"]],["funding","contribution"])
        self.assertEqual(card["marks"][0]["status"],"eligible")
        stale=self.card("individual",12,12)
        self.assertIsNone(stale["performance"]["equity"]["value"])
        self.assertEqual(stale["marks"][0]["status"],"stale")

    def test_six_answers_learning_advice_pending_and_frozen_readiness(self):
        for v in self.report["versions"]:
            for c in v["cards"]:
                self.assertEqual(len(c["answers"]),6)
                self.assertTrue(all(a["evidence_ids"] for a in c["answers"]))
                self.assertFalse(c["performance"]["promotion_eligible"])
        c=self.card("monarchy")
        self.assertEqual(c["context"]["advice_log"][0]["status"],"Unresolved")
        self.assertEqual(c["context"]["forecasts"]["pending"],1)
        self.assertEqual(c["readiness"],"fixture_only")
        self.assertTrue(any(r["readiness"]=="not_ready" for r in self.report["roster"]))

    def test_as_known_restated_and_separate_control_are_preserved(self):
        original=self.card("individual");restated=self.card("individual",11,13)
        self.assertEqual(D(original["performance"]["equity"]["value"]),1548)
        self.assertEqual(D(restated["performance"]["equity"]["value"]),1554)
        self.assertNotEqual(original["report_id"],restated["report_id"])
        paper=self.card("paper")
        self.assertEqual(paper["performance"]["execution_basis"],"paper_broker")
        self.assertTrue(paper["matched_control_ids"])
        self.assertEqual(paper["reconciliation"]["status"],"matched")
        self.assertIsNone(paper["performance"]["recurring_expense"]["value"])
        self.assertIsNone(paper["performance"]["economics_pnl"]["value"])
        self.assertIn("remaining 2",paper["decisions"][0]["outcome"])
        self.assertEqual(self.card("cash")["decisions"],[])
        self.assertEqual(self.card("cash")["performance"]["twr"]["value"],"0.00000000")

    def test_no_broker_identity_raw_record_or_private_path_reaches_browser(self):
        text=json.dumps(self.report)
        for forbidden in ("SENSITIVE-BROKER-ID-NOT-FOR-BROWSER","client_order_id","broker_order_id","private_locator","raw_response","source_citations_private","research.sqlite3"):
            self.assertNotIn(forbidden,text)
        validate_private(self.report)
        with self.assertRaises(ContractError):validate_export(self.report)

    def test_hash_unknown_fields_and_missing_evidence_fail_closed(self):
        for change in (lambda r:r.update(api_key="unexpected"),lambda r:r["evidence"].clear(),lambda r:r["versions"][0]["cards"][0]["answers"].pop()):
            report=deepcopy(self.report);change(report)
            report["content_hash"]=digest({k:v for k,v in report.items() if k!="content_hash"})
            with self.assertRaises(ContractError):validate_private(report)
        report=deepcopy(self.report);report["notice"]="tampered"
        with self.assertRaises(ContractError):validate_private(report)

    def test_atomic_failure_preserves_previous_entry_and_offline_read_is_pure(self):
        destination=self.root/"preview"
        first=export_private(self.store,destination,as_of=at(11));before=first.read_bytes()
        chain=self.store.verify_v2()
        def fail():raise RuntimeError("Interrupted handoff")
        with self.assertRaises(RuntimeError):export_private(self.store,destination,as_of=at(13),before_publish=fail)
        self.assertEqual(first.read_bytes(),before)
        with patch("socket.create_connection",side_effect=AssertionError("No network")):
            self.assertEqual(build_private(self.store,as_of=at(13)),self.report)
        self.assertEqual(self.store.verify_v2(),chain)

    def test_no_evaluations_and_missing_research_are_honest_empty_states(self):
        with TemporaryDirectory() as directory,V2Store(directory,synthetic=True) as store:
            f=FixtureV2(store,"empty",readiness="not_ready")
            empty=build_private(store,as_of=at(13))
            self.assertEqual(empty["versions"],[])
            self.assertEqual(empty["roster"][0]["readiness"],"not_ready")
            f.event("funding",1,amount="1000.00",boundary_mark_ids=[])
            from trade_theorist.evaluate.portfolio_v2 import evaluate
            evaluate(store,f.portfolio,effective_cutoff=at(1),receipt_cutoff=at(1))
            card=build_private(store,as_of=at(1))["versions"][0]["cards"][0]
            self.assertIn("Not yet known",card["answers"][0]["answer"])
            self.assertEqual(card["context"]["heartbeat_status"],"no_data")

    def test_denied_context_rights_block_before_output_creation(self):
        with TemporaryDirectory() as directory,V2Store(Path(directory)/"store",synthetic=True) as store:
            store.put_v2(list(self.store.iter_v2()))
            context=next(store.iter_v2(kind="inspection_context"))
            rights=store.v2_record(context["provenance"]["rights_id"])
            rights=deepcopy(rights);rights["id"]="rights:denied-private-context";rights["private_read_model"]="denied"
            rights["provenance"]["rights_id"]=rights["id"]
            context=deepcopy(context);context.update(id="context:denied",created_at=at(11,1))
            context["provenance"]["rights_id"]=rights["id"]
            store.put_v2([rights,context])
            target=Path(directory)/"must-not-exist"
            with self.assertRaisesRegex(ContractError,"rights"):export_private(store,target,as_of=at(13))
            self.assertFalse(target.exists())

    def test_generated_private_schema_matches_declaration(self):
        path=Path(__file__).resolve().parents[1]/"schemas/private-owner-v2.json"
        self.assertEqual(json.loads(path.read_text()),PRIVATE_SCHEMA)

    def test_saved_context_cannot_claim_future_heartbeat(self):
        from trade_theorist.contracts_v2 import validate
        context=deepcopy(next(self.store.iter_v2(kind="inspection_context")))
        context["last_successful_heartbeat"]=at(12)
        with self.assertRaisesRegex(ContractError,"future heartbeat"):validate(context)

    def test_fixture_flag_does_not_allow_real_source_bundle_in_git(self):
        with TemporaryDirectory() as directory,V2Store(Path(directory)/"store",synthetic=True) as store:
            records=deepcopy(list(self.store.iter_v2()))
            for record in records:
                if record["record_type"]=="source_rights":record["origin"]="owner_authored"
            store.put_v2(records)
            checkout=Path(directory)/"checkout";checkout.mkdir();(checkout/".git").mkdir()
            with self.assertRaisesRegex(ContractError,"outside Git"):
                export_private(store,checkout/"private",as_of=at(13))
            self.assertFalse((checkout/"private").exists())

    def test_withdrawn_mark_is_missing_in_restated_private_view(self):
        from trade_theorist.adapters.trader_user_sim.v2 import SimulatorV2
        from trade_theorist.evaluate.portfolio_v2 import evaluate
        with TemporaryDirectory() as directory,V2Store(directory,synthetic=True) as store:
            store.put_v2(list(self.store.iter_v2()))
            pid=self.ids["individual"]
            mark=next(e for e in store.iter_v2(portfolio_id=pid,kind="ledger_event") if e["event_type"]=="mark" and e["effective_at"]==at(11))
            SimulatorV2(store,pid).correct("command:withdraw-private-mark",mark["id"],None,observed_at=at(14))
            evaluate(store,pid,effective_cutoff=at(11),receipt_cutoff=at(14))
            report=build_private(store,as_of=at(14))
            card=next(v for v in report["versions"] if v["receipt_cutoff"]==at(14))["cards"][0]
            self.assertIsNone(card["performance"]["equity"]["value"])
            self.assertEqual(card["marks"][0]["status"],"missing")


if __name__=="__main__":unittest.main()
