"""Build deterministic point-in-time CSV, revision and snapshot fixtures."""

import csv
import io
import json
from pathlib import Path

from trade_theorist.contracts import validate_bundle
from trade_theorist.fixtures import base_records
from trade_theorist.ingest import CSVMarketAdapter, RevisionBook, SessionCalendar, freeze_snapshot, validate_capability


ROOT = Path(__file__).resolve().parents[1]
HEADERS = [
    "kind", "instrument_id", "asset_class", "session", "event_at",
    "published_at", "ingested_at", "availability_evidence", "feed",
    "publication_eligibility", "adjustment", "open", "high", "low",
    "close", "volume",
]


def write_json(relative, value):
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def as_csv(rows):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=HEADERS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def bar(session, close, *, published=None, ingested=None):
    return dict(
        kind="bar", instrument_id="instrument:fixture-fund",
        asset_class="unleveraged_us_etf", session=session,
        event_at=f"{session}T20:00:00Z",
        published_at=published or f"{session}T20:01:00Z",
        ingested_at=ingested or f"{session}T20:02:00Z",
        availability_evidence="Synthetic fixture release clock v1",
        feed="synthetic-csv-v1", publication_eligibility="raw_permitted",
        adjustment="raw", open="100", high="103", low="98", close=close,
        volume="1000",
    )


def build():
    records = base_records()
    policy = next(record for record in records if record["record_type"] == "policy")
    experiment = next(record for record in records if record["record_type"] == "experiment")
    calendar = SessionCalendar("synthetic-daily-v1", ("2026-09-03", "2026-09-04", "2026-09-05"))
    capability = dict(
        source_id="source:synthetic-csv-v1", feed="synthetic-csv-v1",
        instruments="Explicit fixture identifiers", sessions="Explicit fixture calendar",
        intervals="Daily OHLCV bars", event_timestamps=True,
        publication_timestamps=True, ingestion_timestamps=True,
        point_in_time_revisions=True, corporate_actions=True, dividends=True,
        delisted_instruments=True, historical_constituents=True,
        venue_coverage=True, storage_retention=True, automated_access=False,
        internal_replay=True, derived_publication=True, raw_redistribution=True,
        evidence="Project-authored deterministic fixture; no vendor or market claim",
        checked_at="2026-09-05T12:00:00Z",
    )
    validate_capability(capability)
    book = RevisionBook()
    adapter = CSVMarketAdapter(
        experiment_id=experiment["id"], contamination="fixture",
        universe=experiment["universe"], calendar=calendar,
        capability=capability, revision_book=book,
    )
    initial_rows = [bar("2026-09-03", "100"), bar("2026-09-04", "101"), bar("2026-09-05", "102")]
    revision_rows = [bar("2026-09-05", "101.5", published="2026-09-06T01:00:00Z", ingested="2026-09-06T01:01:00Z")]
    accepted, quarantine = adapter.ingest(as_csv(initial_rows))
    revised, revision_quarantine = adapter.ingest(as_csv(revision_rows))
    if quarantine or revision_quarantine or len(accepted) != 3 or len(revised) != 1:
        raise RuntimeError("Fixture ingestion did not produce the expected revisions")
    before = freeze_snapshot(
        experiment=experiment, policy=policy, calendar=calendar,
        normalized=book.records(), cutoff="2026-09-05T23:00:00Z",
        created_at="2026-09-05T23:00:00Z",
    )
    after = freeze_snapshot(
        experiment=experiment, policy=policy, calendar=calendar,
        normalized=book.records(), cutoff="2026-09-06T02:00:00Z",
        created_at="2026-09-06T02:00:00Z",
    )
    bundle = records + [item.observation for item in book.records()] + [before["snapshot"], after["snapshot"]]
    bundle.sort(key=lambda value: value["id"])
    validate_bundle(bundle)
    directory = ROOT / "examples/ingest"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "market.synthetic.csv").write_text(as_csv(initial_rows), encoding="utf-8", newline="\n")
    (directory / "market-revision.synthetic.csv").write_text(as_csv(revision_rows), encoding="utf-8", newline="\n")
    write_json("examples/ingest/source-capability.synthetic.json", capability)
    write_json("examples/ingest/snapshots.bundle.json", bundle)
    write_json("examples/ingest/snapshot-coverage.synthetic.json", {
        "fixture_only": True,
        "before_revision": before["coverage"],
        "after_revision": after["coverage"],
        "before_snapshot_id": before["snapshot"]["id"],
        "after_snapshot_id": after["snapshot"]["id"],
    })


if __name__ == "__main__":
    build()
