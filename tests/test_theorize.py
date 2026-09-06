from copy import deepcopy
import unittest

from trade_theorist.contracts import ContractError
from trade_theorist.fixtures import complete_bundle
from trade_theorist.theorize import OpinionAdapter


class OpinionAdapterTests(unittest.TestCase):
    def setUp(self):
        self.records = complete_bundle()
        self.character = next(r for r in self.records if r["record_type"] == "character" and r["experiment_id"].startswith("experiment:"))["id"]
        self.knowledge = next(r for r in self.records if r["record_type"] == "theory")["id"]
        self.portfolio = next(r for r in self.records if r["record_type"] == "portfolio")["id"]
        self.snapshot = next(r for r in self.records if r["record_type"] == "snapshot")["id"]
        self.source = next(r for r in self.records if r["record_type"] == "source")["id"]
        self.citation = next(r for r in self.records if r["record_type"] == "theory")["evidence_and_citations"][0]
        self.response = dict(
            action="abstain", instrument_id=None, quantity="0", horizon="one session",
            confidence=0.4, confidence_event="Evidence does not establish an edge",
            invalidation_conditions=["A new eligible observation changes the comparison"],
            citations=[self.citation], abstention_reason="Fixture evidence is insufficient",
            theory_ids=[self.knowledge], forecast=None,
        )

    def run_adapter(self, response=None):
        captured = []
        def provider(request, maximum):
            captured.append((request, maximum))
            return deepcopy(response or self.response)
        adapter = OpinionAdapter(provider, model_id="recorded-opinion-v1", prompt_version="opinion-v1")
        result = adapter.complete(
            records=self.records, character_version=self.character,
            knowledge_version=self.knowledge, portfolio_id=self.portfolio,
            snapshot_id=self.snapshot, portfolio_state={"cash": "10000.00", "positions": []},
            evidence_ids=[self.knowledge], expires_at="2026-09-06T12:00:00Z",
            created_at="2026-09-05T12:00:00Z",
        )
        return result, captured

    def test_request_pins_versions_hashes_state_and_has_no_tools(self):
        (record, request, forecast), captured = self.run_adapter()
        self.assertEqual(record["action"], "abstain")
        self.assertIsNone(forecast)
        self.assertEqual(request["tools"], [])
        self.assertEqual(request["model_id"], "recorded-opinion-v1")
        self.assertEqual(request["knowledge_version"], self.knowledge)
        self.assertEqual(request["knowledge"]["id"], self.knowledge)
        self.assertEqual(request["evidence"][0]["id"], self.knowledge)
        self.assertEqual(request["snapshot"]["id"], self.snapshot)
        self.assertEqual(request["portfolio_state"], {"cash": "10000.00", "positions": []})
        self.assertEqual(len(request["knowledge_hash"]), 64)
        self.assertEqual(len(captured), 1)

    def test_missing_citations_invalid_quantity_and_certainty_fail(self):
        cases = []
        active = dict(self.response, action="buy", instrument_id="instrument:fixture-fund", quantity="1", citations=[], abstention_reason=None)
        cases.append(active)
        cases.append(dict(active, citations=[self.citation], quantity="-1"))
        cases.append(dict(active, citations=[self.citation], quantity="1", confidence=1))
        for response in cases:
            with self.subTest(response=response), self.assertRaises(ContractError):
                self.run_adapter(response)

    def test_abstention_needs_reason_and_evidence_is_frozen(self):
        with self.assertRaises(ContractError):
            self.run_adapter(dict(self.response, abstention_reason=None))
        foreign = dict(self.citation, source_id="source:not-frozen")
        with self.assertRaises(ContractError):
            self.run_adapter(dict(self.response, citations=[foreign]))
        with self.assertRaises(ContractError):
            self.run_adapter(dict(self.response, theory_ids=["theory:not-frozen"]))

    def test_forecast_resolves_after_creation(self):
        forecast = dict(proposition="Fixture price rises", resolves_at="2026-09-04T12:00:00Z", success_condition="Close rises", failure_condition="Close does not rise")
        with self.assertRaises(ContractError):
            self.run_adapter(dict(self.response, forecast=forecast))


if __name__ == "__main__":
    unittest.main()
