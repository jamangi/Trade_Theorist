from contextlib import closing, redirect_stdout, redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from trade_theorist.cli import main
from trade_theorist.contracts import ContractError
from trade_theorist.operations_v2 import DEMO_CUTOFF, ReadOnlyV2, run_demo, doctor
from trade_theorist.storage import Store
from trade_theorist.storage_v2 import V2Store
from trade_theorist.fixtures_accounting_v2 import FixtureV2, at
from trade_theorist.export_v2 import export_private


class PrivateOperatingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = TemporaryDirectory()
        cls.seed = Path(cls.base.name) / "seed"
        with patch("socket.socket.connect", side_effect=AssertionError("No network")):
            cls.demo = run_demo(cls.seed, Path(cls.base.name) / "bundle")

    @classmethod
    def tearDownClass(cls):
        cls.base.cleanup()

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "data"
        self.output = Path(self.tmp.name) / "bundle"
        self.root.mkdir()
        shutil.copy2(self.seed / "research.sqlite3", self.root / "research.sqlite3")
        self.addCleanup(patch.stopall)
        patch("socket.socket.connect", side_effect=AssertionError("No network")).start()
        patch("socket.create_connection", side_effect=AssertionError("No network")).start()

    def invoke(self, command, *extra, version="2"):
        out = io.StringIO()
        args = [command, "--projection-version", version, "--fixture", "--data-root", str(self.root)]
        with redirect_stdout(out), redirect_stderr(out):
            code = main(args + list(extra))
        return code, out.getvalue()

    def fingerprint(self):
        with ReadOnlyV2(self.root, synthetic=True) as store:
            return store.verify()

    def test_commands_reuse_evaluation_export_and_validate_offline(self):
        before = self.fingerprint()
        code, text = self.invoke("demo", "--output-root", str(self.output))
        self.assertEqual(code, 0, text)
        code, text = self.invoke("evaluate", "--portfolio", self.demo["portfolio"], "--as-of", at(11), "--receipt-cutoff", at(13))
        self.assertEqual(code, 0, text)
        self.assertEqual(json.loads(text)["status"], "evaluated")
        self.assertEqual(before, self.fingerprint())
        code, text = self.invoke("export", "--as-of", DEMO_CUTOFF, "--output-root", str(self.output))
        self.assertEqual(code, 0, text)
        self.assertEqual(before, self.fingerprint())
        report = next((self.output / "versions").glob("*/report.json"))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["validate", str(report)]), 0)

    def test_doctor_and_export_use_read_only_connection_and_no_store_initialization(self):
        before = (self.root / "research.sqlite3").read_bytes()
        with patch.object(V2Store, "__init__", side_effect=AssertionError("Cannot initialize/migrate")):
            result = doctor(self.root, self.output, fixture=True)
            self.assertEqual(result["status"], "ready_with_gaps")
            code, text = self.invoke("export", "--as-of", DEMO_CUTOFF, "--output-root", str(self.output))
            self.assertEqual(code, 0, text)
        self.assertEqual(before, (self.root / "research.sqlite3").read_bytes())
        with ReadOnlyV2(self.root, synthetic=True) as store:
            with self.assertRaises(sqlite3.OperationalError):
                store.connection.execute("DELETE FROM v2_records")

    def test_missing_database_and_paths_never_create_them(self):
        absent = Path(self.tmp.name) / "absent"
        result = doctor(absent, self.output, fixture=True)
        self.assertEqual(result["code"], "missing_database")
        self.assertFalse(absent.exists())
        self.assertFalse(self.output.exists())
        self.assertEqual(doctor("relative", self.output, fixture=True)["code"], "missing_data_root")
        self.assertEqual(doctor(self.root, self.root, fixture=True)["code"], "bundle_contains_database")
        self.assertEqual(doctor(self.root, self.root.parent, fixture=True)["code"], "bundle_contains_database")

    def test_v1_migrations_are_reported_without_upgrading_or_reinterpreting(self):
        legacy = Path(self.tmp.name) / "legacy"
        with Store(legacy, synthetic=True):
            pass
        before = (legacy / "research.sqlite3").read_bytes()
        self.assertEqual(doctor(legacy, self.output, fixture=True)["code"], "missing_migrations")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["demo", "--projection-version", "2", "--data-root", str(legacy)]), 2)
        self.assertEqual(before, (legacy / "research.sqlite3").read_bytes())

    def test_changed_or_unknown_migration_is_actionable(self):
        for sql in ("UPDATE schema_migrations SET content_hash='changed' WHERE version=4", "INSERT INTO schema_migrations VALUES (99,'unknown')"):
            with closing(sqlite3.connect(self.root / "research.sqlite3")) as connection, connection:
                connection.execute(sql)
            result = doctor(self.root, self.output, fixture=True)
            self.assertEqual(result["code"], "migration_integrity")
            self.assertIn("checksums", result["resume"])

    def test_rights_are_reported_without_raw_sources_or_secrets(self):
        with V2Store(self.root, synthetic=True) as store:
            rights = deepcopy(next(store.iter_v2(kind="source_rights")))
            rights.update(id="rights:secret-source", private_read_model="denied")
            rights["provenance"]["rights_id"] = rights["id"]
            store.put_v2([rights])
        with patch.dict("os.environ", {"OPENAI_API_KEY": "SECRET-KEY"}):
            code, text = self.invoke("doctor", "--output-root", str(self.output))
        self.assertEqual(code, 2, text)
        self.assertIn("missing_rights", text)
        self.assertNotIn("SECRET", text)
        self.assertNotIn("secret-source", text)

    def test_paper_without_reconciliation_still_allows_inspection(self):
        with V2Store(self.root, synthetic=True) as store:
            FixtureV2(store, "no-account-check", mode="council", basis="paper_broker")
        result = doctor(self.root, self.output, fixture=True)
        self.assertEqual(result["status"], "ready_with_gaps")
        self.assertEqual(result["reconciliation_incomplete"], 1)
        self.assertIn("reconciliation_incomplete", {i["code"] for i in result["issues"]})
        code, text = self.invoke("export", "--as-of", DEMO_CUTOFF, "--output-root", str(self.output))
        self.assertEqual(code, 0, text)

    def test_source_provenance_overrides_fixture_export_location(self):
        with V2Store(self.root, synthetic=True) as store:
            context = deepcopy(next(store.iter_v2(kind="inspection_context")))
            rights = deepcopy(store.v2_record(context["provenance"]["rights_id"]))
            rights.update(id="rights:owner-context", origin="owner_authored")
            rights["provenance"]["rights_id"] = rights["id"]
            context.update(id="context:owner", created_at=at(11, 1))
            context["provenance"]["rights_id"] = rights["id"]
            store.put_v2([rights, context])
        # Simulate a Git checkout, including the linked-worktree .git-file form.
        (Path(self.tmp.name) / ".git").write_text("gitdir: elsewhere")
        code, text = self.invoke("export", "--as-of", DEMO_CUTOFF, "--output-root", str(self.output))
        self.assertEqual(code, 1, text)
        self.assertFalse(self.output.exists())
        self.assertIn("private_path_inside_git", {i["code"] for i in doctor(self.root, self.output, fixture=True)["issues"]})

    def test_doctor_sees_new_account_mismatch_after_last_evaluation(self):
        from trade_theorist.adapters.trader_user_sim.broker_v2 import BrokerReconcilerV2
        from trade_theorist.contracts import digest
        with V2Store(self.root, synthetic=True) as store:
            paper = next(p for p in store.iter_v2(kind="portfolio") if p["execution_basis"] == "paper_broker")
            BrokerReconcilerV2(store, paper["id"]).account("account:new-mismatch", effective_at=at(13), observed_at=at(13),
                cash="0.00", positions=[], evidence_hash=digest("original mismatch"))
        result = doctor(self.root, self.output, fixture=True)
        self.assertEqual(result["reconciliation_incomplete"], 1)
        self.assertEqual(result["status"], "ready_with_gaps")

    def test_new_seed_failure_rolls_back_and_retry_completes(self):
        from trade_theorist.fixtures_dashboard_v2 import seed_dashboard
        fresh = Path(self.tmp.name) / "fresh"
        def interrupted(store):
            seed_dashboard(store)
            raise OSError("SECRET-DETAIL")
        with patch("trade_theorist.fixtures_dashboard_v2.seed_dashboard", interrupted):
            with self.assertRaises(OSError):
                run_demo(fresh, self.output)
        with ReadOnlyV2(fresh, synthetic=True) as store:
            self.assertEqual(store.verify_v2()["records"], 0)
        result = run_demo(fresh, self.output)
        self.assertEqual(result["status"], "fixture_only")
        self.assertTrue(Path(result["report"]).exists())

    def test_failed_export_retains_previous_bundle_and_seed_then_resumes(self):
        run_demo(self.root, self.output)
        before, index = self.fingerprint(), (self.output / "index.html").read_bytes()
        def interrupted(store, destination, *, as_of):
            def fail():
                raise OSError("SECRET-FAILURE")
            return export_private(store, destination, as_of=as_of, before_publish=fail)
        with patch("trade_theorist.operations_v2.export_private", interrupted):
            code, text = self.invoke("demo", "--output-root", str(self.output))
        self.assertEqual(code, 1, text)
        self.assertNotIn("SECRET", text)
        self.assertIn("Repeat demo", text)
        self.assertEqual(before, self.fingerprint())
        self.assertEqual(index, (self.output / "index.html").read_bytes())
        self.assertEqual(self.invoke("demo", "--output-root", str(self.output))[0], 0)

    def test_demo_refuses_existing_research_and_in_git_serving_without_writes(self):
        foreign = Path(self.tmp.name) / "foreign"
        with V2Store(foreign, synthetic=True) as store:
            FixtureV2(store, "foreign")
            before = store.verify()
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["demo", "--projection-version", "2", "--data-root", str(foreign)]), 2)
        with ReadOnlyV2(foreign, synthetic=True) as store:
            self.assertEqual(before, store.verify())
        before = self.fingerprint()
        (Path(self.tmp.name) / ".git").mkdir()
        self.assertEqual(self.invoke("demo", "--serve", "--output-root", str(self.output))[0], 1)
        self.assertEqual(before, self.fingerprint())

    def test_explicit_selection_and_cutoffs_fail_before_mutations(self):
        before = self.fingerprint()
        cases = [("evaluate", ()), ("evaluate", ("--as-of", at(11))),
                 ("export", ("--as-of", at(13), "--experiment", "unimplemented-filter")),
                 ("evaluate", ("--as-of", at(11), "--portfolio", self.demo["portfolio"], "--experiment", "wrong")),
                 ("heartbeat", ("--experiment", "sample")), ("ingest", ("--experiment", "sample", "--source", "sample"))]
        for command, args in cases:
            with self.subTest(command=command, args=args):
                self.assertEqual(self.invoke(command, *args)[0], 2)
        self.assertEqual(self.invoke("evaluate", "--portfolio", self.demo["portfolio"], version="1")[0], 2)
        self.assertEqual(before, self.fingerprint())

    def test_config_version_and_cli_override_are_unambiguous(self):
        config = Path(self.tmp.name) / "operator.json"
        config.write_text(json.dumps(dict(schema_version=1, projection_version=2, fixture=True,
                                         data_root=str(self.root), private_bundle_root=str(self.output))))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["demo", "--config", str(config)]), 0)
        legacy = Path(self.tmp.name) / "legacy"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["demo", "--config", str(config), "--projection-version", "1", "--data-root", str(legacy)]), 0)
        self.assertTrue((legacy / "public" / "index.html").exists())
        for invalid in ([], dict(projection_version=True), dict(data_root=12), dict(private_bundle_root=[])):
            config.write_text(json.dumps(invalid))
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(main(["doctor", "--config", str(config)]), 1)


if __name__ == "__main__":
    unittest.main()
