from copy import deepcopy
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from trade_theorist.contracts import ContractError, digest
from trade_theorist.heartbeat import Heartbeat, HeartbeatInterrupted, PHASES
from trade_theorist.storage import Store


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("heartbeat_fixture_builder", ROOT / "scripts/build_task_009_010_fixtures.py")
FIXTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURE)


class HeartbeatTests(unittest.TestCase):
    def one_setup(self, name="resume", *, risk_reject=False):
        setup = FIXTURE.build_records(name, council=True, risk_reject=risk_reject)
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        store = Store(Path(temp.name) / "store", synthetic=True)
        self.addCleanup(store.close)
        store.put_records(setup["records"])
        provider = FIXTURE.RecordedOpinionProvider()
        export_root = Path(temp.name).resolve() / "mail"
        return setup, store, provider, export_root

    def test_complete_heartbeat_orders_phases_and_reuses_exact_model_outputs(self):
        setup, store, provider, export_root = self.one_setup()
        scenario = FIXTURE.FixtureScenario(store, setup, export_root, provider)
        first = scenario.heartbeat().run(at=FIXTURE.HEARTBEAT_AT)
        second = FIXTURE.FixtureScenario(store, setup, export_root, provider).heartbeat().run(at=FIXTURE.HEARTBEAT_AT)
        self.assertEqual(first, second)
        self.assertEqual(provider.calls, 3)
        self.assertEqual(list(first["phases"]), list(PHASES))
        self.assertEqual(len(first["phases"]["queue_execution"]["orders"]), 1)
        events = store.events(setup["experiment"]["id"])
        self.assertEqual(sum(e["kind"] == "phase.complete" for e in events), len(PHASES))
        self.assertEqual(sum(e["kind"] == "model.complete" for e in events), 3)
        self.assertEqual(sum(e["kind"] == "heartbeat.released" for e in events), 1)
        orders = [e for e in events if e["kind"] == "simulation" and e["payload"].get("type") == "order"]
        self.assertEqual(len(orders), 1)

    def test_resume_after_every_durable_phase_has_no_duplicate_order_call_or_mail(self):
        for phase in PHASES:
            with self.subTest(phase=phase):
                setup = FIXTURE.build_records("crash-" + phase.replace("_", "-"), council=True)
                with TemporaryDirectory() as directory, Store(Path(directory) / "store", synthetic=True) as store:
                    store.put_records(setup["records"])
                    provider = FIXTURE.RecordedOpinionProvider()
                    export_root = Path(directory).resolve() / "mail"
                    scenario = FIXTURE.FixtureScenario(store, setup, export_root, provider)
                    with self.assertRaises(HeartbeatInterrupted):
                        scenario.heartbeat().run(at=FIXTURE.HEARTBEAT_AT, crash_after=phase)
                    resumed = FIXTURE.FixtureScenario(store, setup, export_root, provider).heartbeat().run(at=FIXTURE.HEARTBEAT_AT)
                    events = store.events(setup["experiment"]["id"])
                    self.assertEqual(len(resumed["phases"]), len(PHASES))
                    self.assertEqual(provider.calls, 3)
                    self.assertEqual(sum(e["kind"] == "model.complete" for e in events), 3)
                    self.assertEqual(sum(e["kind"] == "mail.delivered" for e in events), 5)
                    self.assertEqual(sum(e["kind"] == "simulation" and e["payload"].get("type") == "order" for e in events), 1)
                    self.assertEqual(sum(e["kind"] == "phase.complete" for e in events), len(PHASES))
                    self.assertEqual(sum(e["kind"] == "heartbeat.released" for e in events), 1)
                    store.verify()

    def test_active_lock_blocks_another_run_and_changed_plan_is_rejected(self):
        setup, store, provider, export_root = self.one_setup("lock")
        scenario = FIXTURE.FixtureScenario(store, setup, export_root, provider)
        with self.assertRaises(HeartbeatInterrupted):
            scenario.heartbeat().run(at=FIXTURE.HEARTBEAT_AT, crash_after="freeze_snapshot")
        other = deepcopy(setup["run"])
        other["id"] = "run:heartbeat-lock-competitor"
        store.put_records([other])
        competitor = Heartbeat(store, other["id"], phase_inputs=setup["phase_inputs"],
                               operations=scenario.operations())
        with self.assertRaisesRegex(ContractError, "holds"):
            competitor.run(at=FIXTURE.HEARTBEAT_AT)
        changed = deepcopy(setup["phase_inputs"])
        changed["export_handoff"]["format"] = "changed"
        with self.assertRaisesRegex(ContractError, "differs"):
            Heartbeat(store, setup["run"]["id"], phase_inputs=changed, operations=scenario.operations())

    def test_usage_is_admitted_before_calls_and_changed_input_is_not_reused(self):
        setup, store, provider, export_root = self.one_setup("usage")
        scenario = FIXTURE.FixtureScenario(store, setup, export_root, provider)
        scenario.heartbeat().run(at=FIXTURE.HEARTBEAT_AT)
        usage = scenario.model.usage()
        self.assertEqual(usage["admitted_calls"], usage["completed_calls"])
        self.assertEqual(usage["completed_calls"], 3)
        request = {"experiment_id": setup["experiment"]["id"], "model_id": "recorded-heartbeat-fixture-v1",
                   "prompt_version": "independent-opinion-v1", "source_ids": [FIXTURE.SOURCE],
                   "changed_input": True, "tools": []}
        with self.assertRaisesRegex(ContractError, "ceiling"):
            scenario.model.complete(request, source_ids=[FIXTURE.SOURCE], completed_at=FIXTURE.OPINION_AT)
        self.assertEqual(provider.calls, 3)

    def test_two_modes_keep_holdings_and_private_evidence_isolated(self):
        council = FIXTURE.build_records("isolation-council", council=True, risk_reject=True)
        individual = FIXTURE.build_records("isolation-individual", council=False, include_source=False)
        records = council["records"] + individual["records"]
        with TemporaryDirectory() as directory, Store(Path(directory) / "store", synthetic=True) as store:
            store.put_records(records)
            c = FIXTURE.FixtureScenario(store, council, Path(directory).resolve() / "council")
            i = FIXTURE.FixtureScenario(store, individual, Path(directory).resolve() / "individual")
            council_result = c.heartbeat().run(at=FIXTURE.HEARTBEAT_AT)
            individual_result = i.heartbeat().run(at=FIXTURE.HEARTBEAT_AT)
            self.assertEqual(council_result["phases"]["risk_gate"]["checks"][0]["status"], "rejected")
            self.assertIn("turnover", council_result["phases"]["risk_gate"]["checks"][0]["reasons"])
            self.assertEqual(c.simulator.state().positions, {})
            self.assertEqual(i.simulator.state().positions, {})
            self.assertEqual(len(individual_result["phases"]["queue_execution"]["orders"]), 1)
            self.assertTrue(any(e["kind"] == "mail.reflection" for e in store.events(council["experiment"]["id"])))
            self.assertFalse(any(e["kind"] == "mail.reflection" for e in store.events(individual["experiment"]["id"])))
            individual_text = "\n".join(p.read_text(encoding="utf-8") for p in (Path(directory) / "individual").rglob("*.md"))
            self.assertNotIn("valuation objection is useful", individual_text)
            foreign = deepcopy(individual["conversation"])
            foreign.update(id="conversation:cross-mode", participant_character_versions=[council["characters"][0]["id"]])
            with self.assertRaises(ContractError):
                store.put_records([foreign])

    def test_checked_in_fixture_rebuild_is_reproducible_and_complete(self):
        built = FIXTURE.build()
        checked = __import__("json").loads((ROOT / "examples/heartbeat/report.json").read_text(encoding="utf-8"))
        self.assertEqual(built["report"], checked)
        self.assertEqual(built["report"]["provider_calls"], {"council": 3, "individual": 1})
        self.assertEqual(built["report"]["council"]["phases"]["final_decisions"]["initial_abstentions"],
                         ["recommendation:heartbeat-council-initial-0", "recommendation:heartbeat-council-initial-1"])
        self.assertEqual(built["report"]["council"]["phases"]["risk_gate"]["checks"][0]["status"], "rejected")
        self.assertEqual(len(built["report"]["individual"]["phases"]["queue_execution"]["orders"]), 1)


if __name__ == "__main__":
    unittest.main()
