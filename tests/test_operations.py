from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from trade_theorist.cli import main
from trade_theorist.heartbeat import HeartbeatInterrupted
from trade_theorist.operations import run_demo, seed_demo, fixture_heartbeat, demo_setups, ingest_csv
from trade_theorist.storage import Store


class OperatingTests(unittest.TestCase):
    def test_fresh_demo_is_offline_and_repeat_is_idempotent(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "demo"
            with patch("socket.create_connection", side_effect=AssertionError("Network is forbidden")):
                first = run_demo(root)
                with Store(root, synthetic=True) as store:
                    before = store.verify()
                second = run_demo(root)
            self.assertEqual(first, second)
            with Store(root, synthetic=True) as store:
                self.assertEqual(before, store.verify())
            self.assertTrue(Path(first["report"]).is_file())
            self.assertEqual(first["model_calls"], 0)

    def test_interrupted_heartbeat_resumes_through_demo(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "demo"
            with Store(root, synthetic=True) as store:
                setups = seed_demo(store)
                with self.assertRaises(HeartbeatInterrupted):
                    fixture_heartbeat(store, setups[0], crash_after="deliberation")
            result = run_demo(root)
            self.assertEqual(result["status"], "fixture_only")
            with Store(root, synthetic=True) as store:
                phases = list(store.iter_events(setups[0]["experiment"]["id"], "phase.complete"))
                self.assertEqual(len(phases), 10)

    def test_doctor_and_configuration_never_print_secret_values(self):
        with TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            config.write_text(json.dumps(dict(schema_version=1, data_root=str(Path(directory) / "data"), fixture=True)))
            output = io.StringIO()
            with patch.dict("os.environ", {"OPENAI_API_KEY": "NEVER-PRINT-THIS"}), redirect_stdout(output):
                code = main(["doctor", "--config", str(config), "--policy", "examples/paper-policy.template.json"])
            self.assertEqual(code, 2)
            self.assertNotIn("NEVER-PRINT-THIS", output.getvalue())
            self.assertIn("Paper policy", output.getvalue())
            self.assertIn("Character learning", output.getvalue())

    def test_cli_evaluate_export_and_real_heartbeat_blocker(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "demo"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["demo", "--data-root", str(root)]), 0)
                self.assertEqual(main(["evaluate", "--data-root", str(root), "--fixture"]), 0)
                self.assertEqual(main(["export", "--data-root", str(root), "--fixture"]), 0)
                self.assertEqual(main(["heartbeat", "--data-root", str(root), "--fixture", "--experiment", "council"]), 0)
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["heartbeat", "--data-root", str(Path(directory) / "real"), "--experiment", "experiment:real"])
            self.assertEqual(code, 2)
            self.assertIn("qualified source", output.getvalue())

    def test_bad_input_has_redacted_error_and_resume_action(self):
        with TemporaryDirectory() as directory:
            secret = Path(directory) / "SECRET-CREDENTIAL.json"
            secret.write_text('{"password":"do-not-print", broken')
            output = io.StringIO()
            with redirect_stderr(output):
                code = main(["doctor", "--config", str(secret)])
            self.assertEqual(code, 1)
            self.assertNotIn("SECRET-CREDENTIAL", output.getvalue())
            self.assertNotIn("do-not-print", output.getvalue())
            self.assertIn("repeat the same command", output.getvalue())

    def test_permitted_csv_ingestion_deduplicates_and_reports_quarantine(self):
        import csv
        from trade_theorist.fixtures import base_records, EXP
        from trade_theorist.heartbeat.fixture import SESSIONS
        with TemporaryDirectory() as directory, Store(Path(directory) / "data", synthetic=True) as store:
            store.put_records(base_records())
            capability = json.loads(Path("examples/ingest/source-capability.synthetic.json").read_text())
            capability["feed"] = "synthetic-v1"
            row = dict(demo_setups()[0]["payload"], availability_evidence="Original permitted CSV fixture", publication_eligibility="raw_permitted")
            path = Path(directory) / "input.csv"
            with path.open("w", newline="", encoding="utf-8") as output:
                writer = csv.DictWriter(output, fieldnames=list(row))
                writer.writeheader()
                writer.writerow(row)
                writer.writerow(dict(row, open="-1"))
            first = ingest_csv(store, EXP, path, capability, SESSIONS)
            second = ingest_csv(store, EXP, path, capability, SESSIONS)
            self.assertEqual(first["new_observations"], 1)
            self.assertEqual(first["quarantined"], 1)
            self.assertEqual(second["new_observations"], 0)

    def test_reviewed_learning_plan_resumes_without_new_model_calls(self):
        from trade_theorist.fixtures import base_records, CHAR, CONSTITUTION, CURRICULUM, MATERIAL, SOURCE
        from trade_theorist.operations import learn_plan
        with TemporaryDirectory() as directory:
            plan = dict(records=base_records(), character_version=CHAR, constitution=CONSTITUTION, curriculum=CURRICULUM,
                        material=MATERIAL, source_id=SOURCE, position=1, model_id="recorded-fixture-v1", prompt_version="learning-v1",
                        budget_id="budget:fixture-learning", outputs=json.loads(Path("examples/learning/recorded-outputs.fixture.json").read_text()))
            path = Path(directory) / "learning.json"
            path.write_text(json.dumps(plan))
            root = Path(directory) / "learning"
            first = learn_plan(path, root, synthetic=True, expected_character="index_steward")
            second = learn_plan(path, root, synthetic=True, expected_character="index_steward")
            self.assertEqual(first["sections"], 2)
            self.assertEqual(first["checkpoint_ids"], second["checkpoint_ids"])
            self.assertEqual(second["new_recorded_responses"], 0)


if __name__ == "__main__":
    unittest.main()
