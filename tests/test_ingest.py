from copy import deepcopy
import csv
import io
import unittest

from trade_theorist.contracts import ContractError, validate_bundle
from trade_theorist.fixtures import base_records
from trade_theorist.ingest import (
    CSVMarketAdapter, IngestionError, RevisionBook, SessionCalendar,
    allowed_tools, enforce_tool_access, freeze_snapshot, validate_capability,
)


HEADERS = [
    "kind", "instrument_id", "asset_class", "session", "event_at",
    "published_at", "ingested_at", "availability_evidence", "feed",
    "publication_eligibility", "adjustment", "open", "high", "low",
    "close", "volume",
]


def csv_text(rows):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=HEADERS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def bar(session="2026-09-05", instrument="instrument:fixture-fund", close="101", **changes):
    value = dict(
        kind="bar", instrument_id=instrument, asset_class="unleveraged_us_etf",
        session=session, event_at=f"{session}T20:00:00Z",
        published_at=f"{session}T20:01:00Z", ingested_at=f"{session}T20:02:00Z",
        availability_evidence="Synthetic fixture clock v1", feed="synthetic-csv-v1",
        publication_eligibility="raw_permitted", adjustment="raw",
        open="100", high="102", low="99", close=close, volume="1000",
    )
    value.update(changes)
    return value


def capability():
    return dict(
        source_id="source:synthetic-csv-v1", feed="synthetic-csv-v1",
        instruments="Explicit fixture identifiers", sessions="Explicit fixture calendar",
        intervals="Daily bars", event_timestamps=True, publication_timestamps=True,
        ingestion_timestamps=True, point_in_time_revisions=True,
        corporate_actions=True, dividends=True, delisted_instruments=True,
        historical_constituents=True, venue_coverage=True, storage_retention=True,
        automated_access=False, internal_replay=True, derived_publication=True,
        raw_redistribution=True, evidence="Project-authored deterministic fixture",
        checked_at="2026-09-05T12:00:00Z",
    )


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.records = base_records()
        self.policy = next(r for r in self.records if r["record_type"] == "policy")
        self.experiment = next(r for r in self.records if r["record_type"] == "experiment")
        self.calendar = SessionCalendar("synthetic-daily-v1", ("2026-09-05",))
        self.book = RevisionBook()
        self.adapter = CSVMarketAdapter(
            experiment_id=self.experiment["id"], contamination="fixture",
            universe=self.experiment["universe"], calendar=self.calendar,
            capability=capability(), revision_book=self.book,
        )

    def test_deduplication_revision_retention_and_cutoff(self):
        first, rejected = self.adapter.ingest(csv_text([bar()]))
        self.assertEqual((len(first), rejected), (1, []))
        duplicate, rejected = self.adapter.ingest(csv_text([bar()]))
        self.assertEqual((duplicate, rejected), ([], []))
        revised_row = bar(close="100.5", published_at="2026-09-06T01:00:00Z", ingested_at="2026-09-06T01:01:00Z")
        revised, rejected = self.adapter.ingest(csv_text([revised_row]))
        self.assertEqual((revised[0].observation["revision"], revised[0].observation["supersedes_id"]), (2, first[0].observation["id"]))
        self.assertEqual(first[0].payload["adjustment"], "raw")
        self.assertEqual(first[0].observation["units"], "USD/raw")
        frozen = freeze_snapshot(
            experiment=self.experiment, policy=self.policy, calendar=self.calendar,
            normalized=self.book.records(), cutoff="2026-09-05T23:00:00Z",
            created_at="2026-09-05T23:00:00Z",
        )
        self.assertEqual(frozen["snapshot"]["observation_ids"], [first[0].observation["id"]])
        validate_bundle(self.records + [item.observation for item in self.book.records()] + [frozen["snapshot"]])
        stale = deepcopy(frozen["snapshot"])
        stale.update(cutoff="2026-09-06T02:00:00Z", created_at="2026-09-06T02:00:00Z")
        with self.assertRaisesRegex(ContractError, "superseded"):
            validate_bundle(self.records + [item.observation for item in self.book.records()] + [stale])

    def test_archived_publication_uses_then_available_revision(self):
        first, _ = self.adapter.ingest(csv_text([bar(ingested_at="2026-09-08T00:00:00Z")]))
        revised, _ = self.adapter.ingest(csv_text([bar(close="100.5", published_at="2026-09-06T01:00:00Z", ingested_at="2026-09-08T00:01:00Z")]))
        policy = deepcopy(self.policy)
        policy["clock"] = dict(policy["clock"], eligibility="archived_publication")
        experiment = deepcopy(self.experiment)
        result = freeze_snapshot(
            experiment=experiment, policy=policy, calendar=self.calendar,
            normalized=self.book.records(), cutoff="2026-09-06T02:00:00Z",
            created_at="2026-09-08T01:00:00Z",
        )
        self.assertEqual(result["snapshot"]["observation_ids"], [revised[0].observation["id"]])
        self.assertNotIn(first[0].observation["id"], result["snapshot"]["observation_ids"])

    def test_malformed_unknown_time_and_mixed_adjustment_are_rejected(self):
        rows = [bar(low="103"), bar(availability_evidence="undocumented")]
        accepted, quarantine = self.adapter.ingest(csv_text(rows))
        self.assertEqual(accepted, [])
        self.assertEqual(len(quarantine), 2)
        with self.assertRaises(IngestionError):
            self.adapter.ingest(csv_text([bar(), bar(adjustment="split_adjusted")]))
        self.adapter.ingest(csv_text([bar()]))
        self.adapter.ingest(csv_text([bar(adjustment="split_adjusted")]))
        with self.assertRaisesRegex(IngestionError, "mix price adjustment"):
            freeze_snapshot(
                experiment=self.experiment, policy=self.policy, calendar=self.calendar,
                normalized=self.book.records(), cutoff="2026-09-05T23:00:00Z",
                created_at="2026-09-05T23:00:00Z",
            )

    def test_missing_session_halts_but_delisting_remains_visible(self):
        self.calendar = SessionCalendar("synthetic-daily-v1", ("2026-09-04", "2026-09-05"))
        self.adapter = CSVMarketAdapter(
            experiment_id=self.experiment["id"], contamination="fixture",
            universe=self.experiment["universe"], calendar=self.calendar,
            capability=capability(),
        )
        accepted, _ = self.adapter.ingest(csv_text([bar(session="2026-09-04")]))
        with self.assertRaisesRegex(IngestionError, "Missing expected sessions"):
            freeze_snapshot(
                experiment=self.experiment, policy=self.policy, calendar=self.calendar,
                normalized=accepted, cutoff="2026-09-05T23:00:00Z",
                created_at="2026-09-05T23:00:00Z",
            )
        delisting = bar(session="2026-09-04", kind="delisting", open="", high="", low="", close="", volume="")
        adapter = CSVMarketAdapter(
            experiment_id=self.experiment["id"], contamination="fixture",
            universe=self.experiment["universe"], calendar=self.calendar,
            capability=capability(),
        )
        events, quarantine = adapter.ingest(csv_text([bar(session="2026-09-04"), delisting]))
        self.assertFalse(quarantine)
        result = freeze_snapshot(
            experiment=self.experiment, policy=self.policy, calendar=self.calendar,
            normalized=events, cutoff="2026-09-05T23:00:00Z",
            created_at="2026-09-05T23:00:00Z",
        )
        self.assertEqual(result["coverage"]["instrument:fixture-fund"]["status"], "delisted")
        self.assertEqual(len(result["snapshot"]["observation_ids"]), 2)

    def test_source_capabilities_and_tool_boundary(self):
        record = capability()
        self.assertIs(validate_capability(record), record)
        self.assertEqual(allowed_tools("historical_restricted", ["calculator", "web"]), {"calculator"})
        with self.assertRaises(ContractError):
            enforce_tool_access("historical_restricted", ["web"])


if __name__ == "__main__":
    unittest.main()
