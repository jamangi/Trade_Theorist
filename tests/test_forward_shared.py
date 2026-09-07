from copy import deepcopy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from trade_theorist.adapters.alpaca_market_data import Response
from trade_theorist.contracts import ContractError, digest
from trade_theorist.forward.fixtures import setup
from trade_theorist.forward.shared import ForwardRound, RecordedDecisions
from trade_theorist.market_requests import Coordinator


class ForwardSharedTests(unittest.TestCase):
    def make(self, **kwargs):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        owner, manifest, wire, provider = setup(root, **kwargs)
        self.addCleanup(owner.close)
        return root, owner, manifest, wire, provider, ForwardRound(owner, manifest["id"])

    def test_shared_complete_snapshot_and_private_report_are_cached(self):
        _, owner, m, wire, provider, round = self.make()
        first = round.execute(provider, max_pages=1)
        self.assertEqual(first["status"], "deferred")
        self.assertEqual(provider.calls, 0)
        self.assertIsNone(round._existing(m["snapshot_ref"]))
        result = round.execute(provider)
        self.assertEqual(result["status"], "decided")
        self.assertEqual((len(wire.calls), provider.calls), (2, 3))
        self.assertEqual(len(set(provider.snapshots)), 1)
        self.assertEqual({o["snapshot_ref"] for o in result["outcomes"]}, {m["snapshot_ref"]})
        self.assertEqual({o["snapshot_hash"] for o in result["outcomes"]}, {result["snapshot_hash"]})
        self.assertEqual(round.execute(provider), result)
        report = round.report()
        self.assertEqual(report["progress"]["physical_usage"]["attempts"], 2)
        self.assertEqual(report["completed_real_sessions"], 0)
        self.assertFalse(report["promotion_eligible"])
        self.assertEqual((len(wire.calls), provider.calls), (2, 3))
        owner.store.verify_v2()

    def test_attempt_budget_seals_uniform_abstention_without_early_symbol_bias(self):
        _, owner, m, wire, provider, round = self.make(request_attempts=1)
        result = round.execute(provider)
        self.assertEqual((result["status"], result["reason"]), ("abstained", "attempt_budget"))
        self.assertEqual((len(wire.calls), provider.calls), (1, 0))
        snap = owner.store.v2_record(m["snapshot_ref"])
        self.assertEqual(snap["observations"], [])
        self.assertEqual({r["action"] for r in result["outcomes"]}, {"abstain"})
        self.assertTrue(round.report()["progress"]["incomplete_pages"])
        owner.clock.sleep(1000)
        self.assertEqual(round.execute(provider), result)
        self.assertEqual(len(wire.calls), 1)

    def test_cooldown_defers_all_consumers_then_recovers_same_snapshot(self):
        _, owner, m, wire, provider, round = self.make()
        wire.responses.insert(0, Response(429, {"Retry-After": "120"}, {}, "2099-01-03T21:00:00Z"))
        wait = round.execute(provider)
        self.assertEqual((wait["status"], wait["reason"], provider.calls), ("deferred", "cooldown", 0))
        self.assertEqual(wait["snapshot_ref"], m["snapshot_ref"])
        owner.clock.sleep(120)
        result = round.execute(provider)
        self.assertEqual(result["status"], "decided")
        usage = round.report()["progress"]["physical_usage"]
        self.assertEqual((usage["attempts"], usage["retries"], usage["throttles"]), (3, 1, 1))
        self.assertEqual(result["snapshot_ref"], wait["snapshot_ref"])

    def test_deadline_never_relaxes_cutoff_or_revises_sealed_abstention(self):
        _, owner, m, wire, provider, round = self.make()
        wire.responses.insert(0, Response(429, {"retry-after": "600"}, {}, "2099-01-03T21:00:00Z"))
        deferred = round.execute(provider)
        owner.clock.sleep(600)
        result = round.execute(provider)
        self.assertEqual((result["status"], result["reason"], provider.calls), ("abstained", "deadline", 0))
        self.assertEqual(result["snapshot_ref"], deferred["snapshot_ref"])
        self.assertEqual(len(wire.calls), 1)
        self.assertTrue(round.report()["progress"]["deadline_missed"])

    def test_missing_coverage_and_late_receipt_are_not_snapshots(self):
        for failure in ("missing", "late"):
            with self.subTest(failure=failure):
                _, owner, m, wire, provider, round = self.make()
                if failure == "missing": wire.responses[-1] = Response(200, {}, {"bars": {}, "next_page_token": None}, "2099-01-03T21:00:00Z")
                else:
                    old = wire.responses[-1]
                    wire.responses[-1] = Response(200, {}, old.body, "2099-01-03T21:06:00Z")
                result = round.execute(provider)
                self.assertEqual(result["status"], "abstained")
                self.assertEqual(owner.store.v2_record(m["snapshot_ref"])["observations"], [])
                self.assertEqual(provider.calls, 0)

    def test_snapshot_commit_crash_reuses_cache_and_model_reservation_never_repeats(self):
        _, owner, m, wire, provider, round = self.make()
        def crash(): raise RuntimeError("Injected interruption")
        with self.assertRaises(RuntimeError): round.prepare(before_commit=crash)
        self.assertIsNone(round._existing(m["snapshot_ref"]))
        with self.assertRaises(RuntimeError): round.execute(provider, after_reserve=crash)
        self.assertEqual((len(wire.calls), provider.calls), (2, 0))
        resumed = ForwardRound(owner, m["id"]).execute(provider)
        self.assertEqual((resumed["status"], resumed["reason"]), ("abstained", "execution_ambiguous"))
        self.assertEqual(provider.calls, 0)

    def test_request_and_model_budgets_are_independent(self):
        _, owner, m, wire, provider, round = self.make(model_changes={"max_calls": 2})
        result = round.execute(provider)
        self.assertEqual(result["reason"], "model_budget")
        self.assertEqual((len(wire.calls), provider.calls), (2, 0))
        self.assertEqual(owner.store.v2_record(m["snapshot_ref"])["status"], "ready")

    def test_frozen_references_and_stopping_rule_reject_mutation(self):
        _, owner, m, _, _, _ = self.make()
        from trade_theorist.contracts_v2 import validate_references
        changes = []
        for field in ("character_hash", "plan_hash", "policy_hash"):
            changed = deepcopy(m); changed["participants"][0][field] = "0" * 64; changes.append(changed)
        changed = deepcopy(m); changed["participants"][1] = deepcopy(changed["participants"][0]); changes.append(changed)
        changed = deepcopy(m); changed["stopping_rule"]["min_completed_sessions"] = 1; changes.append(changed)
        changed = deepcopy(m); changed["max_request_attempts"] = 10000; changes.append(changed)
        changed = deepcopy(m); changed["data_deadline"] = "2099-01-03T20:00:00Z"; changes.append(changed)
        for changed in changes:
            with self.assertRaises(ContractError): validate_references(changed, owner.store.v2_record)

    def test_second_preregistered_round_uses_eligible_cache_without_calls(self):
        _, owner, m, wire, provider, round = self.make()
        second = deepcopy(m)
        second["id"] = "forward:second-paired-round"
        second["snapshot_ref"] = "snapshot:forward-" + digest([second["id"], second["decision_at"], second["query_hash"]])
        owner.store.put_v2([second])
        round.execute(provider)
        result = ForwardRound(owner, second["id"]).execute(provider)
        self.assertEqual((result["status"], len(wire.calls)), ("decided", 2))
        report = ForwardRound(owner, second["id"]).report()
        self.assertGreater(report["progress"]["work_usage"]["cache_hits"], 0)
        self.assertEqual(report["progress"]["physical_work_ref"], m["work_ref"])

    def test_preexisting_larger_shared_budget_cannot_spend_round_allowance(self):
        _, owner, m, wire, provider, round = self.make(request_attempts=1)
        owner.submit(m["query"], consumer="manual", max_attempts=30, deadline=m["data_deadline"])
        result = round.execute(provider)
        self.assertEqual(result["reason"], "attempt_budget")
        self.assertEqual((len(wire.calls), provider.calls), (0, 0))

    def test_restart_keeps_page_checkpoint_and_common_plan(self):
        root, owner, m, wire, provider, round = self.make()
        round.execute(provider, max_pages=1)
        clock, policy = owner.clock, owner.policy
        owner.close()
        reopened = Coordinator(root / "data", policy, wire, synthetic=True, registry_root=root / "registry", clock=clock, jitter=lambda: .25)
        self.addCleanup(reopened.close)
        resumed = ForwardRound(reopened, m["id"])
        self.assertEqual(resumed.execute(provider)["reason"], "recovery")
        clock.sleep(60)
        result = resumed.execute(provider)
        self.assertEqual((result["status"], len(wire.calls), provider.calls), ("decided", 2, 3))
        self.assertEqual(wire.calls[-1]["page_token"], "second-symbol")

    def test_commit_deadlines_roll_back_success_for_every_peer(self):
        for phase in ("snapshot", "decision"):
            with self.subTest(phase=phase):
                _, owner, m, _, provider, round = self.make()
                if phase == "snapshot":
                    result = round.prepare(before_commit=lambda: owner.clock.advance_to(m["data_deadline"]))
                    self.assertEqual(result["observations"], [])
                    result = round.execute(provider)
                    self.assertEqual(provider.calls, 0)
                else:
                    result = round.execute(provider, before_commit=lambda: owner.clock.advance_to(m["decision_at"]))
                    self.assertEqual(provider.calls, 3)
                self.assertEqual((result["status"], result["reason"]), ("abstained", "deadline"))
                self.assertEqual({o["action"] for o in result["outcomes"]}, {"abstain"})

    def test_conflicting_same_receipt_revision_abstains_latest_receipt_is_frozen(self):
        for conflict in (False, True):
            with self.subTest(conflict=conflict):
                _, owner, m, wire, provider, round = self.make()
                first_symbol = m["query"]["symbols"][0]
                revised = dict(wire.responses[0].body["bars"][first_symbol][0], c=102)
                body = deepcopy(wire.responses[1].body)
                body["bars"][first_symbol] = [revised]
                wire.responses[1] = Response(200, {}, body, "2099-01-03T21:00:00Z" if conflict else "2099-01-03T21:00:00.100000Z")
                result = round.execute(provider)
                self.assertEqual(result["status"], "abstained" if conflict else "decided")
                if not conflict:
                    snap = owner.store.v2_record(m["snapshot_ref"])
                    self.assertEqual(len(snap["observations"]), 2)
                    self.assertEqual(next(o["bar"]["c"] for o in snap["observations"] if o["bar"]["symbol"] == first_symbol), 102)

    def test_invalid_provider_usage_and_crashed_batch_are_truthfully_unknown(self):
        _, owner, m, wire, provider, round = self.make()
        provider.outputs[m["participants"][0]["portfolio_ref"]]["tokens"] = 100000
        result = round.execute(provider)
        self.assertEqual(result["reason"], "model_budget")
        self.assertIsNone(result["model_tokens"])
        self.assertEqual((result["model_calls"], result["calls_reserved"]), (1, 3))
        _, owner, m, wire, provider, round = self.make()
        def crash(): raise RuntimeError("Interrupt after callbacks")
        with self.assertRaises(RuntimeError): round.execute(provider, before_commit=crash)
        result = round.execute(provider)
        self.assertEqual((result["reason"], provider.calls), ("execution_ambiguous", 3))
        self.assertIsNone(result["model_calls"])
        self.assertIsNone(result["model_tokens"])

    def test_cost_flow_or_real_identity_cannot_enter_frozen_pair(self):
        from trade_theorist.contracts_v2 import validate_references
        _, owner, m, _, _, _ = self.make()
        for field in ("fee_per_share", "flows"):
            altered = deepcopy(m)
            plan = owner.store.v2_record(m["participants"][0]["plan_ref"])
            if field == "flows": plan["flows"][0]["amount"] = "999.00"
            else: plan[field] = "2.00"
            altered["participants"][0]["plan_hash"] = digest(plan)
            with self.assertRaisesRegex(ContractError, "identical baseline"):
                validate_references(altered, lambda i: plan if i == plan["id"] else owner.store.v2_record(i))
        changed = deepcopy(m); changed["participants"][0]["execution_basis"] = "paper_broker"
        with self.assertRaises(ContractError): validate_references(changed, owner.store.v2_record)

    def test_heartbeat_entry_uses_shared_round_and_report_cannot_dispatch(self):
        from trade_theorist.heartbeat import run_forward_round
        _, owner, m, wire, provider, round = self.make()
        result = run_forward_round(owner, m["id"], provider)
        self.assertEqual(result["status"], "decided")
        owner.transport = lambda *_: self.fail("Report dispatched")
        report = round.report()
        self.assertEqual(report["result"], result)

    def test_fixture_command_is_offline_and_validates_additive_records(self):
        from trade_theorist.cli import main
        with tempfile.TemporaryDirectory() as temp:
            with patch("socket.socket.connect", side_effect=AssertionError("External transport forbidden")):
                output = io.StringIO()
                with redirect_stdout(output): code = main(["forward-fixture", "--output-root", temp])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output.getvalue())["scenarios"], 4)
            with redirect_stdout(io.StringIO()): code = main(["validate", str(Path(temp) / "manifest.json")])
            self.assertEqual(code, 0)

    def test_production_transport_cannot_enter_fixture_forward_path(self):
        from trade_theorist.adapters.alpaca_market_data.transport import SingleAttemptTransport
        _, owner, m, _, _, _ = self.make()
        owner.transport = SingleAttemptTransport("original-fixture-key", "original-fixture-secret")
        with self.assertRaises(ContractError): ForwardRound(owner, m["id"])


if __name__ == "__main__": unittest.main()
