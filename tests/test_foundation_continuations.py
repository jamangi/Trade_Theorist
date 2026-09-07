"""Saved full-source readiness rejects incomplete, relabeled or altered evidence."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from trade_theorist.contracts import ContractError, digest
from trade_theorist.learn.continuation import audit_foundation, check_saved_readiness_v2, POLICY
from trade_theorist.learn.readiness import check_saved_readiness

ROOT = Path(__file__).resolve().parents[1]


class FoundationContinuationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for folder in ('characters', 'examples/step-10', 'examples/step-11', 'library/catalog'):
            shutil.copytree(ROOT / folder, self.root / folder)
        self.name = 'systematic_trend_operator'
        self.folder = self.root / 'characters' / self.name / 'checkpoints/foundation-v2'
        self.as_of = self.read(self.root / POLICY)['recorded_at']

    def read(self, path):
        return json.loads(path.read_text(encoding='utf-8'))

    def write(self, path, value):
        path.write_text(json.dumps(value), encoding='utf-8')

    def audit(self):
        return audit_foundation(self.root, self.name, as_of=self.as_of)

    def rehash_bundle(self, bundle):
        self.write(self.folder / 'bundle.json', bundle)
        completion = self.read(self.folder / 'completion.json')
        completion['bundle_hash'] = digest(bundle)
        self.write(self.folder / 'completion.json', completion)

    def test_complete_gate_preserves_historical_block(self):
        self.assertEqual(check_saved_readiness(self.root)['participant_gate'], 'blocked')
        current = check_saved_readiness_v2(self.root)
        self.assertEqual(current['participant_gate'], 'passed')
        self.assertEqual([p['sections_reviewed'] for p in current['participants']], [21,28,17])
        self.assertTrue(all(p['books_completed'] == 1 and p['evaluation_status'] == 'not_run' for p in current['participants']))

    def test_future_completion_cannot_be_admitted(self):
        self.as_of = '2026-09-07T00:00:00Z'
        with self.assertRaises(ContractError): self.audit()

    def test_rehashed_incomplete_chain_cannot_be_admitted(self):
        bundle = self.read(self.folder / 'bundle.json')
        bundle = [r for r in bundle if not (r['record_type'] == 'checkpoint' and r['section_index'] == 17)]
        self.rehash_bundle(bundle)
        with self.assertRaises(ContractError): self.audit()

    def test_rehashed_cross_character_ancestry_rejected(self):
        bundle = self.read(self.folder / 'bundle.json')
        checkpoint = next(r for r in bundle if r['record_type'] == 'checkpoint' and r['section_index'] == 1)
        checkpoint['prior_hash'] = digest({'other_character_memory': []})
        self.rehash_bundle(bundle)
        with self.assertRaises(ContractError): self.audit()

    def test_rehashed_claim_disposition_rejected(self):
        bundle = self.read(self.folder / 'bundle.json')
        checkpoint = next(r for r in bundle if r['record_type'] == 'checkpoint' and r['section_index'] == 17)
        checkpoint['accepted_claims'].append(checkpoint['rejected_claims'].pop())
        self.rehash_bundle(bundle)
        with self.assertRaises(ContractError): self.audit()

    def test_forged_complete_coverage_rejected_after_rehashing(self):
        review = self.read(self.folder / 'reading-review.json')
        coverage = self.read(self.folder / 'coverage-map.json')
        review['sections'][-1]['pdf_end'] = 230
        coverage['sections'][-1]['pdf_end'] = 230
        review['coverage_hash'] = digest(coverage)
        budget = self.read(self.folder / 'import-budget.json')
        budget['review_hash'] = digest(review)
        completion = self.read(self.folder / 'completion.json')
        for key,value in [('review',review),('coverage',coverage),('budget',budget)]:
            completion[key + '_hash'] = digest(value)
        self.write(self.folder / 'reading-review.json', review)
        self.write(self.folder / 'coverage-map.json', coverage)
        self.write(self.folder / 'import-budget.json', budget)
        self.write(self.folder / 'completion.json', completion)
        with self.assertRaises(ContractError): self.audit()

    def test_original_opening_cannot_be_rewritten(self):
        path = self.folder.parent / 'foundation-reading-review.json'
        value = self.read(path)
        value['sections'][0]['claims'][0]['text'] = 'Invented hindsight claim'
        self.write(path, value)
        with self.assertRaises(ContractError): self.audit()

    def test_eligible_version_pin_cannot_drift(self):
        path = self.root / 'characters' / self.name / 'versions/pilot-foundation-v2.bundle.json'
        value = self.read(path)
        next(r for r in value if r['record_type'] == 'character')['constitution_hash'] = '0' * 64
        self.write(path, value)
        with self.assertRaises(ContractError): check_saved_readiness_v2(self.root)


if __name__ == '__main__': unittest.main()
