"""Deterministic CSV normalization and point-in-time snapshot freezing."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import csv
import io

from ..contracts import ContractError, canonical, digest, utc, validate


class IngestionError(ContractError):
    pass


CAPABILITY_FIELDS = (
    "source_id", "feed", "instruments", "sessions", "intervals",
    "event_timestamps", "publication_timestamps", "ingestion_timestamps",
    "point_in_time_revisions", "corporate_actions", "dividends",
    "delisted_instruments", "historical_constituents", "venue_coverage",
    "storage_retention", "automated_access", "internal_replay",
    "derived_publication", "raw_redistribution", "evidence", "checked_at",
)


def validate_capability(record):
    if set(record) != set(CAPABILITY_FIELDS):
        raise IngestionError("Source capability record has missing or unknown fields")
    if not all(isinstance(record[name], bool) for name in CAPABILITY_FIELDS[5:-2]):
        # intervals is the last non-boolean before the explicit capability flags.
        raise IngestionError("Source capabilities must be explicit booleans")
    if not all(isinstance(record[name], str) and record[name].strip() for name in ("source_id", "feed", "instruments", "sessions", "intervals", "evidence", "checked_at")):
        raise IngestionError("Source capability identity and evidence are required")
    utc(record["checked_at"])
    return record


@dataclass(frozen=True)
class SessionCalendar:
    name: str
    sessions: tuple[str, ...]

    def __post_init__(self):
        if not self.name or not self.sessions or len(set(self.sessions)) != len(self.sessions):
            raise IngestionError("Calendar needs named, unique sessions")
        parsed = tuple(date.fromisoformat(value) for value in self.sessions)
        if tuple(sorted(parsed)) != parsed:
            raise IngestionError("Calendar sessions must be ordered")

    def through(self, cutoff):
        cutoff_date = utc(cutoff).date()
        return tuple(value for value in self.sessions if date.fromisoformat(value) <= cutoff_date)


@dataclass(frozen=True)
class Quarantine:
    row_number: int
    payload_hash: str
    reason: str


@dataclass(frozen=True)
class Normalized:
    observation: dict
    payload: dict


class RevisionBook:
    """Append-only in-memory revision index; durable callers persist returned records."""

    def __init__(self, records=()):
        self._series = {}
        self._by_id = {}
        for item in records:
            self.add_existing(item)

    @staticmethod
    def key(payload):
        return payload["feed"], payload["instrument_id"], payload["event_at"], payload["kind"], payload["adjustment"]

    def add_existing(self, item):
        key = self.key(item.payload)
        series = self._series.setdefault(key, [])
        if series and item.observation["revision"] != series[-1].observation["revision"] + 1:
            raise IngestionError("Revision history is not contiguous")
        series.append(item)
        self._by_id[item.observation["id"]] = item

    def append(self, *, base, payload):
        key = self.key(payload)
        series = self._series.setdefault(key, [])
        payload_hash = digest(payload)
        # Replaying an older saved receipt after a newer one is still a duplicate.
        # Receipt/provenance fields are part of the hash, so a genuinely new
        # observation (including a later return to an earlier price) is retained.
        for existing in reversed(series):
            if existing.observation["payload_hash"] == payload_hash:
                return existing, False
        previous = series[-1].observation if series else None
        revision = len(series) + 1
        observation = dict(
            base,
            id="observation:" + digest([key, revision, payload_hash]),
            record_type="observation",
            instrument_id=payload["instrument_id"],
            asset_class=payload["asset_class"],
            event_at=payload["event_at"],
            published_at=payload["published_at"],
            ingested_at=payload["ingested_at"],
            availability_evidence=payload["availability_evidence"],
            revision=revision,
            supersedes_id=previous["id"] if previous else None,
            superseded_at=None,
            feed=payload["feed"],
            units="event" if payload["kind"] == "delisting" else f"USD/{payload['adjustment']}",
            payload_hash=payload_hash,
            quality="eligible",
            publication_eligibility=payload["publication_eligibility"],
        )
        validate(observation)
        item = Normalized(observation, payload)
        series.append(item)
        self._by_id[observation["id"]] = item
        return item, True

    def records(self):
        return tuple(item for series in self._series.values() for item in series)


class CSVMarketAdapter:
    REQUIRED = {
        "kind", "instrument_id", "asset_class", "session", "event_at",
        "published_at", "ingested_at", "availability_evidence", "feed",
        "publication_eligibility", "adjustment", "open", "high", "low",
        "close", "volume",
    }
    ADJUSTMENTS = {"raw", "split_adjusted", "total_return_adjusted"}

    def __init__(self, *, experiment_id, contamination, universe, calendar,
                 capability, revision_book=None):
        self.experiment_id = experiment_id
        self.contamination = contamination
        self.universe = {item["instrument_id"]: item for item in universe}
        self.calendar = calendar
        self.capability = validate_capability(capability)
        self.revisions = revision_book or RevisionBook()

    def ingest(self, text):
        reader = csv.DictReader(io.StringIO(text))
        if set(reader.fieldnames or ()) != self.REQUIRED:
            raise IngestionError("CSV columns do not match the permitted adapter contract")
        rows = list(reader)
        adjustments = {row["adjustment"] for row in rows if row["kind"] == "bar"}
        if len(adjustments) > 1:
            raise IngestionError("A batch cannot mix price adjustment conventions")
        accepted, quarantine = [], []
        for row_number, row in enumerate(rows, start=2):
            try:
                payload = self._normalize(row)
                base = dict(
                    schema_version=1, experiment_id=self.experiment_id,
                    created_at=payload["ingested_at"], contamination=self.contamination,
                )
                item, created = self.revisions.append(base=base, payload=payload)
                if created:
                    accepted.append(item)
            except (IngestionError, InvalidOperation, ValueError, TypeError, AttributeError, KeyError) as exc:
                quarantine.append(Quarantine(row_number, digest(row), str(exc)))
        return accepted, quarantine

    def _normalize(self, row):
        instrument = self.universe.get(row["instrument_id"])
        if instrument is None or row["asset_class"] != instrument["asset_class"]:
            raise IngestionError("Unknown or mismatched instrument identity")
        if row["kind"] not in ("bar", "delisting"):
            raise IngestionError("Unsupported market event kind")
        if row["feed"] != self.capability["feed"]:
            raise IngestionError("CSV feed differs from its capability record")
        if row["session"] not in self.calendar.sessions:
            raise IngestionError("Row references an unknown market session")
        event, published, ingested = map(utc, (row["event_at"], row["published_at"], row["ingested_at"]))
        if event.date().isoformat() != row["session"] or event > published or published > ingested:
            raise IngestionError("Event, publication and ingestion clocks are inconsistent")
        if not row["availability_evidence"].strip() or row["availability_evidence"].strip().lower() in ("unknown", "undocumented", "none", "n/a"):
            raise IngestionError("Publication time needs documentary evidence")
        if row["publication_eligibility"] not in ("private_only", "derived_permitted", "raw_permitted"):
            raise IngestionError("Publication eligibility is unknown")
        if row["adjustment"] not in self.ADJUSTMENTS:
            raise IngestionError("Unknown adjustment convention")
        payload = {key: row[key] for key in self.REQUIRED}
        if row["kind"] == "bar":
            prices = {name: Decimal(row[name]) for name in ("open", "high", "low", "close")}
            volume = Decimal(row["volume"])
            if any(not value.is_finite() or value <= 0 for value in prices.values()) or not volume.is_finite() or volume < 0:
                raise IngestionError("Prices must be positive and volume nonnegative")
            if prices["low"] > min(prices["open"], prices["close"]) or prices["high"] < max(prices["open"], prices["close"]) or prices["low"] > prices["high"]:
                raise IngestionError("Malformed OHLC relationship")
            payload.update({name: format(value, "f") for name, value in prices.items()}, volume=format(volume, "f"))
        elif any(row[name].strip() for name in ("open", "high", "low", "close", "volume")):
            raise IngestionError("Delisting event cannot smuggle price fields")
        canonical(payload)
        return payload


def freeze_snapshot(*, experiment, policy, calendar, normalized, cutoff, created_at):
    """Select only then-knowable latest revisions and enforce full session coverage."""
    if experiment["policy_id"] != policy["id"] or experiment["universe"] != policy["universe"]:
        raise IngestionError("Experiment and policy inputs differ")
    if policy["clock"]["calendar"] != calendar.name:
        raise IngestionError("Snapshot calendar differs from pinned policy")
    cutoff_time = utc(cutoff)
    archived = policy["clock"]["eligibility"] == "archived_publication"
    eligible = []
    for item in normalized:
        observation = item.observation
        if utc(observation["event_at"]) > cutoff_time or utc(observation["published_at"]) > cutoff_time:
            continue
        if not archived and utc(observation["ingested_at"]) > cutoff_time:
            continue
        eligible.append(item)
    latest = {}
    for item in sorted(eligible, key=lambda value: value.observation["revision"]):
        latest[RevisionBook.key(item.payload)] = item
    selected = list(latest.values())
    adjustments = {item.payload["adjustment"] for item in selected if item.payload["kind"] == "bar"}
    if len(adjustments) > 1:
        raise IngestionError("Snapshot cannot mix price adjustment conventions")
    universe = {item["instrument_id"]: item for item in experiment["universe"]}
    expected_sessions = list(calendar.through(cutoff))
    if not expected_sessions:
        raise IngestionError("No expected sessions are available at the cutoff")
    coverage = {}
    for instrument_id in universe:
        events = [item for item in selected if item.payload["instrument_id"] == instrument_id]
        delistings = sorted(item.payload["session"] for item in events if item.payload["kind"] == "delisting")
        last_required = delistings[0] if delistings else expected_sessions[-1]
        required = [session for session in expected_sessions if session <= last_required]
        bars = {item.payload["session"] for item in events if item.payload["kind"] == "bar"}
        missing = sorted(set(required) - bars)
        if missing:
            raise IngestionError(f"Missing expected sessions for {instrument_id}")
        coverage[instrument_id] = {
            "status": "delisted" if delistings else "active",
            "last_required_session": last_required,
            "observed_sessions": sorted(bars),
        }
    observations = sorted((item.observation for item in selected), key=lambda value: value["id"])
    snapshot = dict(
        id="snapshot:" + digest([experiment["id"], cutoff, [item["id"] for item in observations]]),
        schema_version=1, record_type="snapshot", experiment_id=experiment["id"],
        created_at=created_at, contamination=experiment["contamination"], cutoff=cutoff,
        clock_policy=policy["clock"], observation_ids=[item["id"] for item in observations],
        exclusions=[], content_hash=digest(observations),
    )
    validate(snapshot)
    return {"snapshot": snapshot, "observations": observations, "coverage": coverage}
