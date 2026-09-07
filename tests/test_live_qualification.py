"""Exercise the live runner with original offline data; no account or socket calls."""
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from qualify_step_09 import measure, operating_policy
from trade_theorist.adapters.alpaca_market_data import Response
from trade_theorist.adapters.alpaca_market_data.transport import SingleAttemptTransport
from trade_theorist.market_requests import Coordinator, stamp


class Clock:
    def __init__(self): self.start, self.elapsed = time.time(), 0
    def wall(self): return time.time() + self.elapsed
    def monotonic(self): return self.elapsed
    def sleep(self, seconds): self.elapsed += seconds


class Wire:
    def __init__(self, clock, plan): self.clock, self.plan, self.calls = clock, plan, 0
    def observed_attempts(self): return []
    def __call__(self, method, url, params):
        self.calls += 1
        all_bars = [(symbol, dict(t=day + "T04:00:00Z", o=10, h=12, l=9, c=11, v=50))
                    for symbol in self.plan["symbols"] for day in self.plan["expected_sessions"]]
        start = int(params.get("page_token", 0)); end = start + int(params["limit"])
        bars = {}
        for symbol, bar in all_bars[start:end]: bars.setdefault(symbol, []).append(bar)
        return Response(200, {}, dict(bars=bars, next_page_token=str(end) if end < len(all_bars) else None), stamp(self.clock.wall()))


class LiveQualificationTests(unittest.TestCase):
    def test_complete_sample_restored_replay_and_no_refetch(self):
        root_repo = Path(__file__).resolve().parents[1]
        plan = json.loads((root_repo / "examples/step-09/sample-plan.json").read_text())
        cap = json.loads((root_repo / "examples/step-09/source-capability.alpaca-conditional.json").read_text())
        cap.update(storage_retention=True, internal_replay=True)
        with tempfile.TemporaryDirectory() as temp, patch("socket.socket.connect", side_effect=AssertionError("Network forbidden")) as network:
            root = Path(temp); clock = Clock(); wire = Wire(clock, plan)
            with Coordinator(root / "data", operating_policy(), wire, synthetic=True, registry_root=root / "registry", clock=clock) as owner:
                result = measure(owner, wire, plan, cap, root / "state")
                self.assertEqual(result["status"], "qualified_scoped_daily_bars", (result.get("blocked_reason"), result.get("restored_replay_added_observations")))
                self.assertEqual(result["physical_attempts"], 6)
                self.assertEqual(result["changed_bar_pairs"], 0)
                self.assertEqual(result["restored_replay_added_observations"], 0)
                self.assertEqual(result["runs"][0]["initial_status"], "deferred")
                repeated = measure(owner, wire, plan, cap, root / "state")
                self.assertEqual((repeated["status"], wire.calls), ("qualified_scoped_daily_bars", 6))
                self.assertEqual(repeated["physical_attempts"], 6)
            network.assert_not_called()

    def test_transport_records_bounded_redacted_headers_without_changing_response(self):
        connection = MagicMock(); response = connection.getresponse.return_value
        response.status = 429
        response.getheaders.return_value = [("Retry-After", "120"), ("X-RateLimit-Limit", "200"), ("X-Private", "sensitive")]
        wire = SingleAttemptTransport("private-key", "private-secret")
        with patch("trade_theorist.adapters.alpaca_market_data.transport.HTTPSConnection", return_value=connection):
            result = wire("GET", "https://data.alpaca.markets/v2/stocks/bars", {})
            self.assertEqual(result.headers["Retry-After"], "120")
            response.read.assert_not_called()
            history = wire.observed_attempts()
            self.assertEqual(history[0]["http_status"], 429)
            self.assertEqual(history[0]["rate_headers"], {"retry-after": "120", "x-ratelimit-limit": "200"})
            self.assertNotIn("private", json.dumps(history)); self.assertNotIn("sensitive", json.dumps(history))
            history[0]["rate_headers"].clear()
            self.assertEqual(wire.observed_attempts()[0]["rate_headers"]["retry-after"], "120")
            wire._attempts.extend([{}] * 250)
            self.assertEqual(len(wire.observed_attempts()), 200)


if __name__ == "__main__": unittest.main()
