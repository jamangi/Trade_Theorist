from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from trade_theorist.contracts import ContractError, digest
from trade_theorist.fixtures import base_records, CHAR, CONSTITUTION, CURRICULUM, EXP, MATERIAL, SOURCE, fixture_response
from trade_theorist.learn import BoundedModel, Learner, RecordedProvider
from trade_theorist.learn.model import AmbiguousCall, UsageExhausted
from trade_theorist.learn.engine import citation_passage, request_for
from trade_theorist.storage import Store


ROOT = Path(__file__).resolve().parents[1]


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name, synthetic=True)
        self.addCleanup(self.store.close)
        self.store.put_records(base_records())
        self.outputs = json.loads((ROOT / "examples/learning/recorded-outputs.fixture.json").read_text())
        self.provider = RecordedProvider(self.outputs)
        self.model = self.make_model(self.provider)
        self.learner = Learner(self.store, self.model)

    def make_model(self, provider, **overrides):
        options = dict(budget_id="budget:fixture-learning", model_id="recorded-fixture-v1", prompt_version="learning-v1", max_calls=2, max_tokens=100000, max_output_tokens=4000)
        options.update(overrides)
        return BoundedModel(self.store, EXP, provider, **options)

    def freeze(self, **overrides):
        options = dict(character_version=CHAR, curriculum=CURRICULUM, constitution=CONSTITUTION, material=MATERIAL, source_id=SOURCE, position=1)
        options.update(overrides)
        return self.learner.freeze(**options)

    def test_two_sections_resume_and_cited_memory(self):
        session = self.freeze()
        first = self.learner.step(session)
        self.assertEqual(first["reading_status"], "partial")
        self.assertEqual(first["material_scope"], "fixture")
        with Store(self.temp.name, synthetic=True) as reopened:
            model = BoundedModel(reopened, EXP, self.provider, budget_id="budget:fixture-learning", model_id="recorded-fixture-v1", prompt_version="learning-v1", max_calls=2, max_tokens=100000, max_output_tokens=4000)
            learner = Learner(reopened, model)
            second = learner.step(session)
            self.assertEqual(second["section_index"], 2)
            self.assertEqual(second["prior_hash"], digest(first))
            self.assertEqual(learner.step(session), second)
            self.assertEqual(learner.step(session, section_index=1), first)
        self.assertEqual(self.provider.calls, 2)
        for claim, section in zip(second["consolidated_memory"], MATERIAL["sections"]):
            self.assertEqual(claim["citations"][0]["locator"], section["locator"])
            self.assertEqual(claim["citations"][0]["passage_hash"], digest(section["text"]))
        self.assertEqual(second["reading_status"], "partial")
        self.store.verify()

    def test_request_excludes_future_chapters_and_preserves_prior_predictions(self):
        self.freeze(initial_prior=dict(constitution=CONSTITUTION, memory=[], predictions=["A prediction frozen before reading"]))
        event = self.store.events(EXP, "learning.prior_frozen")[0]["payload"]
        request = request_for(event["frozen"], MATERIAL["sections"][0], event["prior"], self.model.model_id, self.model.prompt_version)
        self.assertNotIn(MATERIAL["sections"][1]["text"], json.dumps(request))
        self.assertNotIn("sections", request["frozen"]["material"])
        self.assertEqual(request["prior"]["predictions"], ["A prediction frozen before reading"])

    def test_page_citation_cannot_borrow_text_from_another_page(self):
        section = dict(locator="pdf/test/section-1", text="[PDF PAGE 7]\nFirst page only.\n[PDF PAGE 8]\nSecond page only.")
        self.assertEqual(citation_passage(section, "pdf/test/section-1#page=7"), "First page only.")
        self.assertNotIn("Second", citation_passage(section, "pdf/test/section-1#page=7"))
        for locator in ("pdf/test/section-1#page=9", "pdf/test/section-2#page=7", "pdf/test/section-1#page=07"):
            with self.subTest(locator=locator), self.assertRaises(ContractError):
                citation_passage(section, locator)

    def test_review_can_consolidate_without_promoting_a_new_theory(self):
        for result in self.outputs.values():
            result["response"].update(theory=None, test=None)
        session = self.freeze()
        self.learner.step(session)
        second = self.learner.step(session)
        self.assertEqual(len(second["consolidated_memory"]), 2)
        self.assertFalse(any(r["record_type"] in ("theory", "registration") for r in self.store.records()))

    def test_theory_without_a_test_fails(self):
        for result in self.outputs.values():
            result["response"]["test"] = None
        with self.assertRaises(ContractError):
            self.learner.step(self.freeze())

    def test_freeze_is_idempotent_and_preserves_actual_prior(self):
        session = self.freeze()
        self.assertEqual(self.freeze(), session)
        self.learner.step(session)
        self.assertEqual(self.freeze(), session)
        frozen = self.store.events(EXP, "learning.prior_frozen")[0]["payload"]
        self.assertEqual(frozen["prior_hash"], digest(frozen["prior"]))
        self.assertEqual(len(self.store.events(EXP, "learning.prior_frozen")), 1)

    def test_no_skipped_sections_or_changed_material(self):
        session = self.freeze()
        with self.assertRaises(ContractError):
            self.learner.step(session, section_index=2)
        material = deepcopy(MATERIAL)
        material["sections"][0]["text"] = "Changed text"
        with self.assertRaises(ContractError):
            self.freeze(material=material)
        material = deepcopy(MATERIAL)
        material["sections"].reverse()
        with self.assertRaises(ContractError):
            self.freeze(material=material)

    def test_no_foundation_substitution_or_constitution_changes(self):
        with self.assertRaises(ContractError):
            self.freeze(position=2)
        with self.assertRaises(ContractError):
            self.freeze(constitution="A different foundation")

    def test_missing_permission_and_unacquired_text_rejected(self):
        records = base_records()
        records[0]["rights"]["machine_ingestion"] = "unknown"
        with patch.object(self.store, "records", return_value=records), self.assertRaises(ContractError):
            self.freeze()
        records = base_records()
        records[0]["access"] = "purchase_required"
        with patch.object(self.store, "records", return_value=records), self.assertRaises(ContractError):
            self.freeze()

    def test_stale_access_and_sample_full_book_promotion_rejected(self):
        records = base_records()
        records[0]["next_check_at"] = "2026-09-05T12:01:00Z"
        with patch.object(self.store, "records", return_value=records), self.assertRaises(ContractError):
            self.freeze()
        records = base_records()
        records[0]["access"] = "sample_only"
        material = deepcopy(MATERIAL)
        material["scope"] = "full_book"
        with patch.object(self.store, "records", return_value=records), self.assertRaises(ContractError):
            self.freeze(material=material)

    def test_fabricated_quote_fails_without_second_model_call(self):
        for result in self.outputs.values():
            result["response"]["extraction"][0]["quote"] = "This passage does not exist in the source."
        session = self.freeze()
        for _ in range(2):
            with self.assertRaises(ContractError):
                self.learner.step(session)
        self.assertEqual(self.provider.calls, 1)
        self.assertFalse(any(r["record_type"] == "checkpoint" for r in self.store.records()))

    def test_crash_after_saved_response_reuses_it(self):
        session = self.freeze()
        put = self.store.put_records
        def interrupt_checkpoint(records):
            if any(r["record_type"] == "checkpoint" for r in records):
                raise RuntimeError("Crash before checkpoint commit")
            return put(records)
        with patch.object(self.store, "put_records", side_effect=interrupt_checkpoint), self.assertRaises(RuntimeError):
            self.learner.step(session)
        self.assertEqual(self.provider.calls, 1)
        checkpoint = self.learner.step(session)
        self.assertEqual(checkpoint["section_index"], 1)
        self.assertEqual(self.provider.calls, 1)

    def test_ambiguous_call_never_automatically_retried(self):
        calls = []
        def timeout(request, limit):
            calls.append(1)
            raise TimeoutError("private prompt or credential")
        self.learner = Learner(self.store, self.make_model(timeout))
        session = self.freeze()
        with self.assertRaises(TimeoutError):
            self.learner.step(session)
        with self.assertRaises(AmbiguousCall):
            self.learner.step(session)
        self.assertEqual(len(calls), 1)
        failure = self.store.events(EXP, "model.failed")[0]
        self.assertNotIn("credential", json.dumps(failure))

    def test_usage_cap_is_persisted_across_restart(self):
        self.learner = Learner(self.store, self.make_model(self.provider, max_calls=1))
        session = self.freeze()
        self.learner.step(session)
        with self.assertRaises(UsageExhausted):
            self.learner.step(session)
        self.learner = Learner(self.store, self.make_model(self.provider, max_calls=2))
        with self.assertRaises(ContractError):
            self.learner.step(session)
        self.assertEqual(self.provider.calls, 1)

    def test_token_limit_prevents_provider_call(self):
        self.learner = Learner(self.store, self.make_model(self.provider, max_tokens=1))
        session = self.freeze()
        with self.assertRaises(UsageExhausted):
            self.learner.step(session)
        self.assertEqual(self.provider.calls, 0)


if __name__ == "__main__":
    unittest.main()
