from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from trade_theorist.contracts import ContractError
from trade_theorist.library import AccessChecker, validate_catalog
from trade_theorist.storage import Store


ROOT = Path(__file__).resolve().parents[1]


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT / "library/catalog/pilot.json").read_text())

    def test_twelve_slots_exact_or_explicitly_unresolved(self):
        index = validate_catalog(self.catalog)
        self.assertEqual(len(index), 13)  # Original hardcover candidate survives the format resolution.
        self.assertEqual(sum(s["isbn"] is not None for s in index.values()), 12)
        acquired = index["book:9781119404521"]
        self.assertEqual(acquired["access"], "user_supplied")
        self.assertEqual(acquired["ingestion_status"], "complete")
        self.assertEqual(acquired["rights"]["redistribution"], "unknown")
        self.assertTrue(all(s["ingestion_status"] == "blocked" for s in index.values() if s is not acquired))

    def test_deduplication_and_missing_evidence(self):
        bad = deepcopy(self.catalog)
        bad["sources"].append(bad["sources"][0])
        with self.assertRaises(ContractError):
            validate_catalog(bad)
        bad = deepcopy(self.catalog)
        bad["evidence"] = []
        with self.assertRaises(ContractError):
            validate_catalog(bad)

    def test_cached_head_cannot_grant_full_text_or_permissions(self):
        calls = []
        result = dict(status=200, final_url=self.catalog["sources"][0]["locator"], etag='"v1"', last_modified=None, content_length="1234", content_type="text/html", error=None)
        def fetch(url, previous):
            calls.append(url)
            return dict(result, final_url=url)
        source = deepcopy(self.catalog["sources"][0])
        source["access"] = "sample_only"
        original = deepcopy(source)
        with TemporaryDirectory() as directory, Store(directory) as store:
            checker = AccessChecker(store, fetch)
            checker.check(source, checked_at="2026-09-05T21:00:00Z")
            cached = checker.check(source, checked_at="2026-09-06T21:00:00Z")
            self.assertTrue(cached["cached"])
            self.assertEqual(len(calls), 1)
            self.assertEqual(source, original)
            source["locator"] += "&revision=2"
            changed = checker.check(source, checked_at="2026-09-06T22:00:00Z")
            self.assertIn("catalog_url_changed", changed["review_reasons"])
            self.assertEqual(len(calls), 2)
            self.assertTrue(checker.review_queue())

    def test_changed_etag_redirect_and_network_failure_request_review(self):
        source = self.catalog["sources"][0]
        response = dict(status=200, final_url=source["locator"], etag="v1", last_modified=None, content_length="123", content_type="text/html", error=None)
        with TemporaryDirectory() as directory, Store(directory) as store:
            checker = AccessChecker(store, lambda *_: dict(response))
            checker.check(source, checked_at="2026-09-05T21:00:00Z")
            response["etag"] = "v2"
            checked = checker.check(source, checked_at="2026-09-05T22:00:00Z", force=True)
            self.assertIn("remote_metadata_changed", checked["review_reasons"])
            response.update(status=302, final_url="https://publisher.example/new")
            checked = checker.check(source, checked_at="2026-09-05T23:00:00Z", force=True)
            self.assertIn("redirect_requires_review", checked["review_reasons"])
            response.update(status=None, error="network_unavailable")
            checked = checker.check(source, checked_at="2026-09-06T00:00:00Z", force=True)
            self.assertIn("availability_unverified", checked["review_reasons"])
            self.assertEqual(source["rights"]["machine_ingestion"], "unknown")


if __name__ == "__main__":
    unittest.main()
