"""Adversarial checks for the actual saved participant evidence, without PDFs."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from trade_theorist.contracts import ContractError, digest, validate_bundle
from trade_theorist.forward import ForwardEvidenceGate, freeze_manifest
from trade_theorist.learn.readiness import (
    POLICY_PATH, REGISTER_PATH, VERSION_PATH, audit_readiness, check_saved_readiness,
)
from trade_theorist.learn.reviewed import write_once


ROOT = Path(__file__).resolve().parents[1]


class PilotReadinessTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        register = json.loads((ROOT / REGISTER_PATH).read_text(encoding="utf-8"))
        for relative in (*register["evidence_hashes"], REGISTER_PATH, VERSION_PATH):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    def read(self, path):
        return json.loads((self.root / path).read_text(encoding="utf-8"))

    def write(self, path, value):
        (self.root / path).write_text(json.dumps(value), encoding="utf-8")

    def test_reproduces_exact_versions_partial_sources_and_blocked_roster(self):
        register = check_saved_readiness(self.root)
        self.assertEqual([p["eligible"] for p in register["participants"]], [True, False, False])
        self.assertEqual([p["sections_reviewed"] for p in register["participants"]], [21, 1, 1])
        self.assertEqual([p["books_completed"] for p in register["participants"]], [1, 0, 0])
        self.assertEqual(register["participant_gate"], "blocked")
        self.assertTrue(all(p["evaluation_status"] == "not_run" for p in register["participants"]))
        versions = validate_bundle(self.read(VERSION_PATH))
        index = register["participants"][0]
        self.assertEqual(versions[index["character_version"]]["constitution_hash"], index["reviewed_constitution_hash"])
        self.assertNotEqual(index["character_version"], index["learning_character_version"])
        original = self.read("characters/index_steward/checkpoints/bogle-2017.bundle.json")
        self.assertEqual(next(r for r in original if r["record_type"] == "character")["readiness"], "partial")

    def test_preserves_blockers_when_presented_to_existing_manifest_gate(self):
        register = check_saved_readiness(self.root)
        manifest = freeze_manifest(
            manifest_id="test:readiness-only", frozen_at="2026-09-07T04:00:00Z",
            start_at="2026-09-08T22:00:00Z", end_at="2026-10-01T22:00:00Z", horizon_sessions=5,
            characters=[dict(character_id=p["character_id"], readiness=p["decision"], version_hash=p["version_hash"])
                        for p in register["participants"]],
            opportunity_set=[{"symbol": "VTI"}], data_feed="test:unexecuted", retrieval_policy="test only",
            source_blockers=register["step_11_prerequisites"][1:],
        )
        self.assertEqual(manifest["status"], "blocked")
        self.assertEqual(len(manifest["eligible_character_versions"]), 1)
        with self.assertRaisesRegex(ContractError, "blocked"):
            ForwardEvidenceGate(manifest=manifest, decision_cutoff="2026-09-09T22:00:00Z")

    def test_cannot_drop_a_participant_to_pass(self):
        policy = self.read(POLICY_PATH)
        policy["participants"] = policy["participants"][:1]
        self.write(POLICY_PATH, policy)
        with self.assertRaisesRegex(ContractError, "all three"):
            audit_readiness(self.root)

    def test_forged_ready_decision_even_with_recomputed_hash_fails(self):
        register = self.read(REGISTER_PATH)
        register["participants"][1]["eligible"] = True
        register["participant_gate"] = "passed"
        register["content_hash"] = digest({k: v for k, v in register.items() if k != "content_hash"})
        self.write(REGISTER_PATH, register)
        with self.assertRaisesRegex(ContractError, "reproducible"):
            check_saved_readiness(self.root)

    def test_constitution_edit_invalidates_saved_version(self):
        path = self.root / "characters/index_steward/constitution.v1.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nInvented belief.\n", encoding="utf-8")
        with self.assertRaisesRegex(ContractError, "reproducible"):
            check_saved_readiness(self.root)

    def test_standalone_memory_edit_is_detected(self):
        path = "characters/value_rationalist/memory/foundation-consolidated.json"
        memory = self.read(path)
        memory["claims"][0]["text"] = "An invented valuation method."
        self.write(path, memory)
        with self.assertRaisesRegex(ContractError, "Published memory"):
            audit_readiness(self.root)

    def test_rehashed_checkpoint_cannot_change_review_disposition_or_prior(self):
        prefix = "characters/value_rationalist/checkpoints/"
        original = self.read(prefix + "foundation.bundle.json")
        for alteration in ("disposition", "prior", "fixture", "page"):
            with self.subTest(alteration=alteration):
                bundle = deepcopy(original)
                checkpoint = next(r for r in bundle if r["record_type"] == "checkpoint")
                if alteration == "disposition":
                    checkpoint["rejected_claims"].append(checkpoint["accepted_claims"].pop())
                elif alteration == "prior":
                    checkpoint["prior_hash"] = "f" * 64
                elif alteration == "fixture":
                    checkpoint["contamination"] = "fixture"
                else:
                    checkpoint["accepted_claims"][0]["citations"][0]["locator"] += "0"
                status = self.read(prefix + "foundation-status.json")
                status["bundle_hash"] = digest(bundle)
                self.write(prefix + "foundation.bundle.json", bundle)
                self.write(prefix + "foundation-status.json", status)
                with self.assertRaises(ContractError):
                    audit_readiness(self.root)

    def test_sample_cannot_be_promoted_to_full_foundation(self):
        path = "characters/systematic_trend_operator/checkpoints/foundation-status.json"
        status = self.read(path)
        status.update(real_readiness=True, books_read=1)
        self.write(path, status)
        with self.assertRaisesRegex(ContractError, "overstates"):
            audit_readiness(self.root)

    def test_theory_export_and_edition_tampering_are_detected(self):
        path = "characters/index_steward/theories/bogle-2017.json"
        original = self.read(path)
        theory = deepcopy(original)
        theory[0]["horizon"] = "One day"
        self.write(path, theory)
        with self.assertRaisesRegex(ContractError, "theory/test"):
            audit_readiness(self.root)
        self.write(path, original)
        path = "library/catalog/bogle-2017-acquisition.json"
        acquisition = self.read(path)
        acquisition["source_pdf_sha256"] = "f" * 64
        self.write(path, acquisition)
        with self.assertRaisesRegex(ContractError, "fingerprints"):
            audit_readiness(self.root)

    def test_rerun_preserves_bytes_and_refuses_changed_version(self):
        before = (self.root / VERSION_PATH).read_bytes()
        register, bundle = audit_readiness(self.root)
        write_once(self.root / VERSION_PATH, bundle)
        write_once(self.root / REGISTER_PATH, register)
        self.assertEqual((self.root / VERSION_PATH).read_bytes(), before)
        bundle[-1]["readiness"] = "partial"
        with self.assertRaisesRegex(ContractError, "append a new version"):
            write_once(self.root / VERSION_PATH, bundle)


if __name__ == "__main__":
    unittest.main()
