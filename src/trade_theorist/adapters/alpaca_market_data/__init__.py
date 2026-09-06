"""Feed-pinned Alpaca Market Data adapter.

The transport is injected so credentials stay outside this package and recorded
responses can exercise every control without network access.  The adapter never
chooses a replacement feed after a denial.
"""

from dataclasses import dataclass
from decimal import InvalidOperation

from ...contracts import canonical, digest, utc
from ...ingest.market import IngestionError, Quarantine


class AlpacaError(IngestionError):
    pass


class EntitlementDenied(AlpacaError):
    pass


@dataclass(frozen=True)
class Response:
    status: int
    headers: dict
    body: dict
    received_at: str


@dataclass(frozen=True)
class Page:
    number: int
    requested_feed: str
    request_hash: str
    received_at: str
    bars: tuple
    next_page_token: str | None

    @property
    def resume(self):
        return {
            "version": "alpaca-bars-resume-v1",
            "next_page_token": self.next_page_token,
            "completed_pages": self.number,
            "last_request_hash": self.request_hash,
            "feed": self.requested_feed,
        }


@dataclass(frozen=True)
class QualityReport:
    sample_kind: str
    feed: str
    expected_sessions: tuple
    observed_sessions: tuple
    missing_sessions: tuple
    revision_count: int
    quarantine_count: int
    coverage_status: str
    blockers: tuple

    def as_dict(self):
        return {name: list(value) if isinstance(value, tuple) else value
                for name, value in self.__dict__.items()}


class AlpacaBarsAdapter:
    """Read explicitly selected bars with bounded retry and resumable pagination."""

    BASE_URL = "https://data.alpaca.markets/v2/stocks/bars"
    FEEDS = frozenset({"iex", "sip", "otc", "boats"})
    RETRYABLE = frozenset({429, 500, 502, 503, 504})

    def __init__(self, transport, *, feed, sleeper=lambda _: None,
                 max_retries=3, delay_cap=30):
        if feed not in self.FEEDS:
            raise AlpacaError("An explicit supported Alpaca feed is required")
        if max_retries < 0 or delay_cap <= 0:
            raise AlpacaError("Retry bounds must be positive")
        self.transport = transport
        self.feed = feed
        self.sleeper = sleeper
        self.max_retries = max_retries
        self.delay_cap = delay_cap

    def pages(self, *, symbols, start, end, timeframe="1Day", limit=10000,
              resume=None, max_pages=100):
        symbols = tuple(sorted(set(symbols)))
        if not symbols or not (1 <= limit <= 10000) or max_pages < 1:
            raise AlpacaError("Symbols, page size and page bound are required")
        utc(start); utc(end)
        token, page_number = None, 0
        if resume:
            if resume.get("version") != "alpaca-bars-resume-v1" or resume.get("feed") != self.feed:
                raise AlpacaError("Resume state belongs to a different adapter or feed")
            token = resume.get("next_page_token")
            page_number = int(resume.get("completed_pages", 0))
            if token is None:
                return
        seen = set()
        for _ in range(max_pages):
            params = {
                "symbols": ",".join(symbols), "start": start, "end": end,
                "timeframe": timeframe, "limit": str(limit),
                "adjustment": "raw", "feed": self.feed, "sort": "asc",
            }
            if token:
                params["page_token"] = token
            request_hash = digest([self.BASE_URL, params])
            response = self._request(params)
            body = response.body
            if not isinstance(body, dict) or not isinstance(body.get("bars", {}), dict):
                raise AlpacaError("Alpaca bars response has an unexpected shape")
            flattened = []
            for symbol, bars in sorted(body.get("bars", {}).items()):
                if symbol not in symbols or not isinstance(bars, list):
                    raise AlpacaError("Alpaca response contains an unrequested symbol")
                flattened.extend(dict(item, symbol=symbol) for item in bars)
            next_token = body.get("next_page_token")
            if next_token is not None and (not isinstance(next_token, str) or not next_token):
                raise AlpacaError("Invalid pagination token")
            if next_token in seen:
                raise AlpacaError("Alpaca repeated a pagination token")
            if next_token:
                seen.add(next_token)
            page_number += 1
            yield Page(page_number, self.feed, request_hash, response.received_at,
                       tuple(flattened), next_token)
            if next_token is None:
                return
            token = next_token
        # The last yielded page carries its continuation state. Stopping at the
        # configured bound is resumable, not permission to fetch an unbounded run.
        return

    def _request(self, params):
        for attempt in range(self.max_retries + 1):
            response = self.transport("GET", self.BASE_URL, dict(params))
            if not isinstance(response, Response):
                raise AlpacaError("Transport must return an Alpaca Response")
            utc(response.received_at)
            if response.status == 200:
                return response
            if response.status == 403:
                raise EntitlementDenied(
                    f"Alpaca denied entitlement for explicit feed {self.feed}; no fallback attempted"
                )
            if response.status not in self.RETRYABLE or attempt == self.max_retries:
                raise AlpacaError(f"Alpaca request failed with status {response.status}")
            self.sleeper(self._delay(response.headers, attempt))
        raise AssertionError("unreachable")

    def _delay(self, headers, attempt):
        # Retry-After is authoritative when it is a bounded numeric delay.  A
        # missing/invalid header uses deterministic capped exponential backoff.
        try:
            delay = float(headers.get("Retry-After", ""))
            if delay < 0:
                raise ValueError
        except (TypeError, ValueError):
            delay = 2 ** attempt
        return min(delay, self.delay_cap)

    def ingest_page(self, page, csv_adapter):
        """Normalize a page through the shared revision engine without filling gaps."""
        if page.requested_feed != self.feed:
            raise AlpacaError("Page feed identity changed before normalization")
        accepted, quarantined = [], []
        for offset, bar in enumerate(page.bars, start=1):
            try:
                row = self._csv_row(bar, page.received_at, page.request_hash, csv_adapter)
                # Reuse the canonical validator/revision book instead of weakening
                # it for a provider-specific payload.
                payload = csv_adapter._normalize(row)
                base = dict(schema_version=1, experiment_id=csv_adapter.experiment_id,
                            created_at=payload["ingested_at"],
                            contamination=csv_adapter.contamination)
                item, created = csv_adapter.revisions.append(base=base, payload=payload)
                if created:
                    accepted.append(item)
            except (IngestionError, InvalidOperation, ValueError, TypeError, KeyError) as exc:
                quarantined.append(Quarantine(offset, digest(bar), str(exc)))
        return accepted, quarantined

    def _csv_row(self, bar, received_at, request_hash, csv_adapter):
        required = {"symbol", "t", "o", "h", "l", "c", "v"}
        if not required <= set(bar):
            raise AlpacaError("Alpaca bar is missing required fields")
        instrument_id = "instrument:" + bar["symbol"].lower()
        instrument = csv_adapter.universe.get(instrument_id)
        if instrument is None:
            raise AlpacaError("Alpaca symbol is outside the frozen universe")
        event = utc(bar["t"])
        received = utc(received_at)
        if event > received:
            raise AlpacaError("Bar timestamp is later than receipt")
        row = {
            "kind": "bar", "instrument_id": instrument_id,
            "asset_class": instrument["asset_class"],
            "session": event.date().isoformat(), "event_at": bar["t"],
            # Alpaca bars do not carry a publication clock. Receipt is the first
            # conservatively demonstrated availability time for forward work.
            "published_at": received_at, "ingested_at": received_at,
            "availability_evidence": f"Received from explicit Alpaca {self.feed} feed; request {request_hash}",
            "feed": self.feed, "publication_eligibility": "private_only",
            "adjustment": "raw", "open": str(bar["o"]), "high": str(bar["h"]),
            "low": str(bar["l"]), "close": str(bar["c"]), "volume": str(bar["v"]),
        }
        canonical(row)
        return row


def quality_report(*, feed, expected_sessions, normalized, quarantine=(),
                   sample_kind="authorized_account"):
    """Report gaps/revisions; a fixture can validate mechanics but not coverage."""
    expected = tuple(expected_sessions)
    observed = tuple(sorted({item.payload["session"] for item in normalized
                             if item.payload["kind"] == "bar"}))
    missing = tuple(sorted(set(expected) - set(observed)))
    revisions = sum(1 for item in normalized if item.observation["revision"] > 1)
    blockers = []
    if sample_kind != "authorized_account":
        blockers.append("No account-authorized Alpaca sample was supplied; fixture evidence cannot qualify required coverage.")
    if missing:
        blockers.append("Expected market sessions are missing; no bars were synthesized.")
    return QualityReport(sample_kind, feed, expected, observed, missing, revisions,
                         len(tuple(quarantine)), "qualified" if not blockers else "blocked",
                         tuple(blockers))


__all__ = ["AlpacaBarsAdapter", "AlpacaError", "EntitlementDenied", "Page",
           "QualityReport", "Response", "quality_report"]
