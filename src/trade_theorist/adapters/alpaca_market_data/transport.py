"""One HTTP attempt per invocation; no SDK retries, redirects or persisted keys."""
from datetime import datetime, timezone
from http.client import HTTPSConnection
import json
import math
from urllib.parse import urlencode

from . import AlpacaError, AlpacaBarsAdapter, Response


class SingleAttemptTransport:
    def __init__(self, key, secret, *, timeout=10):
        if not all(isinstance(v, str) and v and "\r" not in v and "\n" not in v for v in (key, secret)):
            raise AlpacaError("Private transport credentials are missing or invalid")
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 30:
            raise AlpacaError("Transport timeout must be finite and at most 30 seconds")
        self._headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
        self.timeout = timeout

    def __call__(self, method, url, params):
        if method != "GET" or url != AlpacaBarsAdapter.BASE_URL:
            raise AlpacaError("Transport only permits the pinned historical bars endpoint")
        connection = HTTPSConnection("data.alpaca.markets", timeout=self.timeout)
        try:
            connection.request("GET", "/v2/stocks/bars?" + urlencode(params), headers=self._headers)
            result = connection.getresponse()
            # Bound memory before parsing, including malformed/error bodies.
            # Error status/headers are sufficient; do not lose a 429 cooldown to
            # a slow, oversized or broken error-body download.
            raw = result.read(16 * 1024 * 1024 + 1) if result.status == 200 else b""
            if len(raw) > 16 * 1024 * 1024:
                raise AlpacaError("Response exceeds the bounded page size")
            received = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            try:
                body = json.loads(raw) if raw else {}
            except (ValueError, UnicodeError):
                body = {}  # Preserve status/headers, especially throttles with a non-JSON body.
            return Response(result.status, dict(result.getheaders()), body, received)
        finally:
            connection.close()
