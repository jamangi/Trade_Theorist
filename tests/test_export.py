from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from trade_theorist.contracts import ContractError, digest
from trade_theorist.export import build_dashboard, export_dashboard, validate_export
from trade_theorist.operations import run_demo, FINAL_CUTOFF
from trade_theorist.storage import Store


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        run_demo(cls.root / "store")
        cls.store = Store(cls.root / "store", synthetic=True)
        cls.public = build_dashboard(cls.store, as_of=FINAL_CUTOFF)

    @classmethod
    def tearDownClass(cls):
        cls.store.close()
        cls.temp.cleanup()

    def test_schema_hash_versions_and_six_connected_answers(self):
        validate_export(self.public)
        self.assertEqual(len(self.public["versions"]), 2)
        ids = {e["id"] for e in self.public["evidence"]}
        for version in self.public["versions"]:
            for card in version["cards"]:
                self.assertEqual(len(card["answers"]), 6)
                self.assertTrue(all(set(a["evidence_ids"]) <= ids for a in card["answers"]))
        council = next(c for c in self.public["versions"][-1]["cards"] if c["trial_id"] == "trial:demo-council")
        self.assertIn("Governor rejected: turnover", [d["outcome"] for d in council["decisions"]])
        self.assertIn("Unresolved objection", [a["status"] for a in council["advice_log"]])

    def test_private_reflections_raw_payloads_and_unknown_fields_never_export(self):
        encoded = json.dumps(self.public)
        for private in ("The valuation objection is useful but does not independently", "personal_thoughts", "raw_response", "payload_hash", "research.sqlite3"):
            self.assertNotIn(private, encoded)
        self.assertTrue(all("reflection" not in e["id"] for e in self.public["evidence"]))
        broken = deepcopy(self.public)
        broken["api_key"] = "do-not-export"
        broken["content_hash"] = digest({k: v for k, v in broken.items() if k != "content_hash"})
        with self.assertRaises(ContractError):
            validate_export(broken)
        broken = deepcopy(self.public)
        broken["notice"] = "tampered"
        with self.assertRaises(ContractError):
            validate_export(broken)

    def test_stale_empty_pending_and_readiness_states_are_distinct(self):
        cards = self.public["versions"][-1]["cards"]
        trend = next(c for c in cards if c["trial_id"] == "trial:demo-trend")
        council = next(c for c in cards if c["trial_id"] == "trial:demo-council")
        self.assertIsNone(trend["equity"])
        self.assertEqual(council["holdings"], [])
        self.assertEqual(council["forecasts"]["pending"], 1)
        self.assertTrue(all(r["status"] == "not_ready" for r in self.public["roster"]))

    def test_atomic_failure_keeps_previous_entry_and_readable_assets(self):
        root = self.root / "atomic-public"
        path = export_dashboard(self.store, root, as_of="2099-01-04T21:02:00Z")
        before = path.read_bytes()
        def fail():
            raise RuntimeError("interruption before handoff")
        with self.assertRaises(RuntimeError):
            export_dashboard(self.store, root, as_of=FINAL_CUTOFF, before_publish=fail)
        self.assertEqual(before, path.read_bytes())
        export_dashboard(self.store, root, as_of=FINAL_CUTOFF)
        self.assertNotEqual(before, path.read_bytes())
        self.assertIn("<base href=", path.read_text())

    def test_no_reports_is_a_concrete_blocker(self):
        with TemporaryDirectory() as directory, Store(directory, synthetic=True) as store:
            with self.assertRaisesRegex(ContractError, "run evaluate first"):
                build_dashboard(store, as_of=FINAL_CUTOFF)

    def test_nonfixture_results_and_private_evidence_are_rejected(self):
        for field, value in (("regime", "forward_paper"), ("evidence_grade", "forward-insufficient")):
            broken = deepcopy(self.public)
            broken["versions"][0]["cards"][0][field] = value
            broken["content_hash"] = digest({k: v for k, v in broken.items() if k != "content_hash"})
            with self.assertRaisesRegex(ContractError, "synthetic fixtures only"):
                validate_export(broken)
        broken = deepcopy(self.public)
        broken["evidence"][0]["visibility"] = "private"
        broken["content_hash"] = digest({k: v for k, v in broken.items() if k != "content_hash"})
        with self.assertRaisesRegex(ContractError, "private evidence"):
            validate_export(broken)

    def test_private_store_cannot_write_a_public_bundle(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with Store(root / "private") as store:
                with self.assertRaisesRegex(ContractError, "synthetic fixtures only"):
                    export_dashboard(store, root / "output", as_of=FINAL_CUTOFF)
            self.assertFalse((root / "output").exists())

    def test_fixture_flag_cannot_reclassify_persisted_private_records(self):
        from trade_theorist.fixtures import base_records
        with TemporaryDirectory() as directory:
            root = Path(directory)
            private_source = deepcopy(next(r for r in base_records() if r["record_type"] == "source"))
            private_source["contamination"] = "forward-insufficient"
            with Store(root) as store:
                store.put_records([private_source])
            with Store(root, synthetic=True) as store:
                with self.assertRaisesRegex(ContractError, "non-fixture records"):
                    build_dashboard(store, as_of=FINAL_CUTOFF)


if __name__ == "__main__":
    unittest.main()
