from copy import deepcopy
import json
from pathlib import Path
import unittest

from trade_theorist.adapters.alpaca_market_data import (
    AlpacaBarsAdapter, AlpacaError, EntitlementDenied, Response, quality_report,
)
from trade_theorist.contracts import digest
from trade_theorist.ingest import (
    CSVMarketAdapter, RevisionBook, SessionCalendar, validate_capability,
)


def capability():
    return dict(
        source_id="source:alpaca-market-data", feed="sip",
        instruments="Explicit US equity symbols", sessions="Pinned experiment calendar",
        intervals="Bars requested with a pinned timeframe", event_timestamps=True,
        publication_timestamps=False, ingestion_timestamps=True,
        point_in_time_revisions=False, corporate_actions=True, dividends=True,
        delisted_instruments=False, historical_constituents=False,
        venue_coverage=True, storage_retention=False, automated_access=True,
        internal_replay=False, derived_publication=False, raw_redistribution=False,
        evidence="Official Alpaca documentation reviewed 2026-09-06; unresolved rights are false",
        checked_at="2026-09-06T12:00:00Z",
    )


def bar(close=101):
    return {"t": "2026-09-04T20:00:00Z", "o": 100, "h": 102,
            "l": 99, "c": close, "v": 1000, "n": 50, "vw": 100.5}


class Transport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, method, url, params):
        self.requests.append((method, url, params))
        return self.responses.pop(0)


def response(body, status=200, headers=None, received="2026-09-04T20:01:00Z"):
    return Response(status, headers or {}, body, received)


class AlpacaAdapterTests(unittest.TestCase):
    def normalizer(self, book=None):
        return CSVMarketAdapter(
            experiment_id="experiment:alpaca-fixture", contamination="fixture",
            universe=[{"instrument_id": "instrument:aapl", "symbol": "AAPL",
                       "asset_class": "us_equity", "sector": "Technology"}],
            calendar=SessionCalendar("fixture-calendar", ("2026-09-04", "2026-09-05")),
            capability=capability(), revision_book=book or RevisionBook(),
        )

    def test_pagination_resume_and_feed_identity(self):
        transport = Transport([
            response({"bars": {"AAPL": [bar()]}, "next_page_token": "page-2"}),
            response({"bars": {"AAPL": []}, "next_page_token": None}),
        ])
        adapter = AlpacaBarsAdapter(transport, feed="sip", offline=True)
        first = next(adapter.pages(symbols=["AAPL"], start="2026-09-04T00:00:00Z",
                                   end="2026-09-06T00:00:00Z", max_pages=1))
        pages = list(adapter.pages(symbols=["AAPL"], start="2026-09-04T00:00:00Z",
                                   end="2026-09-06T00:00:00Z", resume=first.resume))
        self.assertEqual(pages[0].number, 2)
        self.assertEqual(transport.requests[1][2]["page_token"], "page-2")
        self.assertTrue(all(req[2]["feed"] == "sip" and req[2]["adjustment"] == "raw"
                            for req in transport.requests))

    def test_bounded_retry_and_entitlement_denial_never_falls_back(self):
        delays = []
        transport = Transport([
            response({}, 429, {"Retry-After": "7"}),
            response({"bars": {}, "next_page_token": None}),
        ])
        adapter = AlpacaBarsAdapter(transport, feed="sip", offline=True, sleeper=delays.append)
        list(adapter.pages(symbols=["AAPL"], start="2026-09-04T00:00:00Z",
                           end="2026-09-06T00:00:00Z"))
        self.assertEqual(delays, [7.0])
        denied = Transport([response({}, 403)])
        with self.assertRaisesRegex(EntitlementDenied, "no fallback"):
            list(AlpacaBarsAdapter(denied, feed="sip", offline=True).pages(
                symbols=["AAPL"], start="2026-09-04T00:00:00Z",
                end="2026-09-06T00:00:00Z"))
        self.assertEqual([r[2]["feed"] for r in denied.requests], ["sip"])

    def test_idempotence_revisions_and_gaps_are_preserved(self):
        book = RevisionBook()
        normalizer = self.normalizer(book)
        adapter = AlpacaBarsAdapter(lambda *_: None, feed="sip", offline=True)
        page = response({}).received_at
        from trade_theorist.adapters.alpaca_market_data import Page
        original = Page(1, "sip", "a" * 64, page, ({**bar(), "symbol": "AAPL"},), None)
        accepted, rejected = adapter.ingest_page(original, normalizer)
        duplicate, _ = adapter.ingest_page(original, normalizer)
        revised = deepcopy(original.bars[0]); revised["c"] = 100.5
        changed, _ = adapter.ingest_page(Page(1, "sip", "b" * 64, page, (revised,), None), normalizer)
        self.assertEqual((len(accepted), len(duplicate), len(changed), len(rejected)), (1, 0, 1, 0))
        self.assertEqual(changed[0].observation["revision"], 2)
        self.assertEqual(changed[0].observation["supersedes_id"], accepted[0].observation["id"])
        report = quality_report(feed="sip", expected_sessions=("2026-09-04", "2026-09-05"),
                                normalized=book.records(), sample_kind="recorded_fixture")
        self.assertEqual(report.missing_sessions, ("2026-09-05",))
        self.assertEqual(report.revision_count, 1)
        self.assertEqual(report.coverage_status, "blocked")

    def test_repeated_page_token_and_malformed_bar_fail_closed(self):
        transport = Transport([
            response({"bars": {}, "next_page_token": "same"}),
            response({"bars": {}, "next_page_token": "same"}),
        ])
        with self.assertRaisesRegex(AlpacaError, "repeated"):
            list(AlpacaBarsAdapter(transport, feed="sip", offline=True).pages(
                symbols=["AAPL"], start="2026-09-04T00:00:00Z",
                end="2026-09-06T00:00:00Z"))
        adapter = AlpacaBarsAdapter(lambda *_: None, feed="sip", offline=True)
        from trade_theorist.adapters.alpaca_market_data import Page
        accepted, rejected = adapter.ingest_page(
            Page(1, "sip", "c" * 64, "2026-09-04T20:01:00Z",
                 ({"symbol": "AAPL", "t": "2026-09-04T20:00:00Z"},), None),
            self.normalizer(),
        )
        self.assertEqual(len(accepted), 0)
        self.assertEqual(len(rejected), 1)

    def test_checked_in_qualification_is_explicitly_conditional(self):
        root = Path(__file__).resolve().parents[1]
        saved = json.loads((root / "examples/ingest/source-capability.alpaca-conditional.json").read_text())
        validate_capability(saved)
        for unproved in ("publication_timestamps", "point_in_time_revisions",
                         "delisted_instruments", "historical_constituents",
                         "storage_retention", "internal_replay",
                         "derived_publication", "raw_redistribution"):
            self.assertFalse(saved[unproved])
        quality = json.loads((root / "examples/ingest/alpaca-quality.blocked.json").read_text())
        self.assertEqual(quality["coverage_status"], "blocked")
        self.assertEqual(quality["sample_kind"], "recorded_fixture")
        account = json.loads((root / "examples/ingest/alpaca-account-access.2026-09-06.json").read_text())
        self.assertEqual(account["content_hash"], digest({k: v for k, v in account.items() if k != "content_hash"}))
        self.assertTrue(account["historical_sip"]["delayed_sip_sample_verified"])
        self.assertFalse(account["latest_sip"]["entitled"])
        self.assertEqual(account["paper_account"]["orders_submitted"], 0)
        self.assertNotIn("account_id", json.dumps(account).lower())


if __name__ == "__main__":
    unittest.main()
