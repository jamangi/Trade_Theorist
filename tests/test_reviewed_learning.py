"""Original tiny integration text; these tests do not need or simulate Bogle reading."""

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from trade_theorist.contracts import ContractError, digest, validate_bundle
from trade_theorist.fixtures import base_records, CONSTITUTION
from trade_theorist.learn import BoundedModel, Learner
from trade_theorist.learn.reviewed import ReviewedTranscriptProvider, foundation_status, material_from_pages, write_once
from trade_theorist.storage import Store


ROOT = Path(__file__).resolve().parents[1]


class ReviewedLearningTests(unittest.TestCase):
    def setUp(self):
        self.pages = ["Original test page: the basket pays a cost.", "Original test page: different proceeds may offset a cost."]
        self.review = dict(source_id="source:original-integration-text", source_pdf_sha256="0" * 64, sections=[
            dict(number=1, pdf_start=1, pdf_end=1, claims=[dict(text="An expense reduces proceeds.", page=1, anchor="pays a cost", disposition="accept")], assimilation="Accept the stated subtraction.", adversarial_review="Other proceeds may differ.", memory_delta="Compare net proceeds."),
            dict(number=2, pdf_start=2, pdf_end=2, claims=[dict(text="Different proceeds may offset expenses.", page=2, anchor="different proceeds", disposition="qualify")], assimilation="Qualify the equal-proceeds premise.", adversarial_review="This is original test text, not market evidence.", memory_delta="Retain the matching assumption.")])
        self.ranges = [(1, 1), (2, 2)]
        self.material = material_from_pages(self.pages, self.review, expected_ranges=self.ranges)
        self.curriculum = [dict(position=1, source_id=self.review["source_id"], intended_lesson="Original test only")]
        source = deepcopy(base_records()[0])
        source.update(id=self.review["source_id"], title="Original two-page integration test, not a published book", contamination="hindsight-contaminated", access="user_supplied", ingestion_status="complete")
        self.scope = "learning-session:original-integration"
        self.char = "character:original-integration"
        base = dict(schema_version=1, experiment_id=self.scope, created_at=source["created_at"], contamination="hindsight-contaminated")
        session = dict(base, id=self.scope, record_type="learning_session", mode="learning", character_versions=[self.char], source_ids=[source["id"]], authorization="Project-authored test text; no third-party source", provenance="Deterministic integration test, not evidence of real book learning")
        character = dict(base, id=self.char, record_type="character", character_id="original_test", version="test-v1", readiness="partial", constitution_hash=digest(CONSTITUTION), curriculum_hash=digest(self.curriculum), foundation_source_id=source["id"])
        self.records = [source, session, character]

    def learner(self, store, provider):
        model = BoundedModel(store, self.scope, provider, budget_id="budget:original-integration", model_id="review-import-test", prompt_version="section-only-test", max_calls=2, max_tokens=100000, max_output_tokens=2000)
        return Learner(store, model)

    def test_nontrading_scope_resumes_real_material_path_without_policy(self):
        provider = ReviewedTranscriptProvider(self.review, self.material, CONSTITUTION, self.curriculum)
        with TemporaryDirectory() as directory:
            with Store(directory) as store:
                store.put_records(self.records)
                learner = self.learner(store, provider)
                session = learner.freeze(character_version=self.char, curriculum=self.curriculum, constitution=CONSTITUTION, material=self.material, source_id=self.review["source_id"], position=1)
                first = learner.step(session)
                self.assertEqual(first["reading_status"], "partial")
            with Store(directory) as store:
                learner = self.learner(store, provider)
                final = learner.step(session)
                self.assertEqual(final["reading_status"], "complete")
                self.assertEqual(learner.step(session), final)
                self.assertEqual(provider.calls, 2)
                self.assertEqual(final["consolidated_memory"][0]["citations"][0]["passage_hash"], digest(self.pages[0]))
                self.assertFalse(any(r["record_type"] in ("policy", "portfolio", "experiment") for r in store.records()))
                store.verify()

    def test_market_records_and_forward_labels_cannot_enter_learning_scope(self):
        portfolio = deepcopy(base_records()[4])
        portfolio.update(experiment_id=self.scope, contamination="hindsight-contaminated", owner_character_version=self.char)
        with self.assertRaisesRegex(ContractError, "market or portfolio"):
            validate_bundle(self.records + [portfolio])
        invalid = deepcopy(self.records)
        invalid[1]["contamination"] = "forward-reviewed"
        with self.assertRaises(ContractError):
            validate_bundle(invalid)

    def test_coverage_and_wrong_page_anchors_fail(self):
        changes = [lambda r: r["sections"].reverse(), lambda r: r["sections"].pop(), lambda r: r["sections"][0]["claims"][0].update(page=2), lambda r: r["sections"][0]["claims"][0].update(anchor="does not appear")]
        for change in changes:
            invalid = deepcopy(self.review)
            change(invalid)
            with self.assertRaises(ContractError):
                material_from_pages(self.pages, invalid, expected_ranges=self.ranges)

    def test_public_export_is_immutable_but_repeatable(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.json"
            write_once(path, {"original": 1, "second": 2})
            original_bytes = path.read_bytes()
            write_once(path, {"second": 2, "original": 1})
            self.assertEqual(path.read_bytes(), original_bytes)
            with self.assertRaises(ContractError):
                write_once(path, {"original": 2})

    def test_published_foundation_is_complete_and_has_no_private_requests(self):
        directory = ROOT / "characters/index_steward"
        status = foundation_status(directory, "book:9781119404521")
        self.assertEqual(status["sections_completed"], 21)
        self.assertFalse(status["curriculum_complete"])
        bundle = json.loads((directory / "checkpoints/bogle-2017.bundle.json").read_text(encoding="utf-8"))
        text = json.dumps(bundle)
        self.assertNotIn("[PDF PAGE ", text)
        self.assertNotIn('"request":', text)
        self.assertNotIn('"quote":', text)
        self.assertEqual(sum(r["record_type"] == "theory" for r in bundle), 1)
        with self.assertRaises(ContractError):
            foundation_status(directory, "book:9781119404507")

    def test_tampered_completion_cannot_claim_readiness(self):
        directory = ROOT / "characters/index_steward"
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in ("checkpoints/bogle-2017-completion.json", "checkpoints/bogle-2017.bundle.json"):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text((directory / relative).read_text(encoding="utf-8"), encoding="utf-8")
            path = root / "checkpoints/bogle-2017.bundle.json"
            bundle = json.loads(path.read_text(encoding="utf-8"))
            next(r for r in bundle if r["record_type"] == "checkpoint")["memory_delta"] = ["Tampered memory"]
            path.write_text(json.dumps(bundle), encoding="utf-8")
            with self.assertRaises(ContractError):
                foundation_status(root, "book:9781119404521")


if __name__ == "__main__":
    unittest.main()
