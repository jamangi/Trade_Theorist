import unittest

from trade_theorist.contracts import ContractError, digest
from trade_theorist.forward import (
    ForwardEvidenceGate, FutureInformationError, commit_shadow_decision,
    freeze_manifest, shadow_report,
)
from trade_theorist.ingest import allowed_tools, enforce_tool_access


def ready_manifest(**changes):
    args = dict(
        manifest_id="forward:fixture-ready", frozen_at="2026-09-06T12:00:00Z",
        start_at="2026-09-07T13:30:00Z", end_at="2026-10-07T20:00:00Z",
        horizon_sessions=5,
        characters=[{"character_id": "index_steward", "readiness": "ready",
                     "version_hash": "character-version:" + "a" * 64}],
        opportunity_set=[{"instrument_id": "instrument:aapl", "session": "2026-09-07"}],
        data_feed="alpaca:sip", retrieval_policy="Qualified timestamped adapters only",
    )
    args.update(changes)
    return freeze_manifest(**args)


def evidence(**changes):
    item = dict(
        source_kind="qualified_public_research", source_id="source:official-filing",
        event_at="2026-09-07T14:00:00Z", published_at="2026-09-07T14:01:00Z",
        ingested_at="2026-09-07T14:02:00Z", availability_evidence="Official receipt record",
        payload_hash=digest("fixture evidence"),
    )
    item.update(changes)
    return item


class ForwardShadowTests(unittest.TestCase):
    def test_repo_mail_retrieval_and_late_evidence_cannot_cross_gate(self):
        manifest = ready_manifest()
        gate = ForwardEvidenceGate(manifest=manifest, decision_cutoff="2026-09-07T15:00:00Z",
                                   provided_tools=["market_data_qualified"])
        for source_kind in ("repository", "mail", "retrieval"):
            with self.subTest(source_kind=source_kind), self.assertRaises(FutureInformationError):
                gate.admit(evidence(source_kind=source_kind))
        with self.assertRaisesRegex(FutureInformationError, "after the decision cutoff"):
            gate.admit(evidence(ingested_at="2026-09-07T15:00:01Z"))
        identifier = gate.admit(evidence())
        saved = gate.snapshot()["evidence"][0]
        self.assertEqual(saved["id"], identifier)
        self.assertEqual(saved["published_at"], "2026-09-07T14:01:00Z")
        self.assertEqual(saved["ingested_at"], "2026-09-07T14:02:00Z")

    def test_generic_tools_are_absent_and_broker_fails_construction(self):
        requested = ["repository", "mail", "retrieval", "web", "http", "broker",
                     "market_data_qualified", "public_research_qualified", "calculator"]
        self.assertEqual(
            allowed_tools("forward_shadow", requested),
            {"market_data_qualified", "public_research_qualified", "calculator"},
        )
        with self.assertRaises(ContractError):
            enforce_tool_access("forward_shadow", ["broker"])

    def test_identical_opportunities_commit_before_cutoff_and_remain_immature(self):
        manifest = ready_manifest()
        gate = ForwardEvidenceGate(manifest=manifest, decision_cutoff="2026-09-07T15:00:00Z")
        gate.admit(evidence())
        snapshot = gate.snapshot()
        decision = commit_shadow_decision(
            manifest=manifest, evidence_snapshot=snapshot,
            character_version="character-version:" + "a" * 64,
            created_at="2026-09-07T14:59:59Z", action="wait",
        )
        self.assertEqual(decision.opportunity_set_hash, manifest["opportunity_set_hash"])
        with self.assertRaisesRegex(ContractError, "cutoff"):
            commit_shadow_decision(
                manifest=manifest, evidence_snapshot=snapshot,
                character_version=decision.character_version,
                created_at="2026-09-07T15:00:01Z", action="wait",
            )
        report = shadow_report(manifest=manifest, decisions=[decision],
                               completed_session_closes=["2026-09-08T20:00:00Z"],
                               matured_forecasts=0, as_of="2026-09-08T20:00:00Z")
        self.assertEqual(report["status"], "immature")
        self.assertEqual(report["broker_orders"], 0)
        self.assertIn("Only 1 real sessions", report["blockers"][0])
        with self.assertRaisesRegex(ContractError, "elapsed closes"):
            shadow_report(manifest=manifest, decisions=[decision],
                          completed_session_closes=["2026-09-09T20:00:00Z"],
                          matured_forecasts=1, as_of="2026-09-08T20:00:00Z")

    def test_real_candidate_manifest_exposes_readiness_and_source_blockers(self):
        manifest = ready_manifest(
            manifest_id="forward:pilot-candidate-2026-09-06",
            characters=[
                {"character_id": "index_steward", "readiness": "partial", "version_hash": None},
                {"character_id": "value_rationalist", "readiness": "partial", "version_hash": None},
                {"character_id": "systematic_trend_operator", "readiness": "partial", "version_hash": None},
            ],
            source_blockers=["Alpaca account-authorized coverage and private storage rights are unresolved."],
        )
        self.assertEqual(manifest["status"], "blocked")
        self.assertEqual(len(manifest["eligible_character_versions"]), 0)
        with self.assertRaisesRegex(ContractError, "blocked"):
            ForwardEvidenceGate(manifest=manifest, decision_cutoff="2026-09-07T15:00:00Z")
        report = shadow_report(manifest=manifest, as_of="2026-09-06T12:00:00Z")
        self.assertEqual(report["evidence_grade"], "forward-blocked")
        self.assertGreaterEqual(len(report["blockers"]), 5)


if __name__ == "__main__":
    unittest.main()
