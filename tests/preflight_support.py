"""Independent Step 08 inputs and transport-side clock oracle; no prior test helpers."""
from datetime import datetime, timezone, timedelta
import json
import os
from threading import RLock

from trade_theorist.adapters.alpaca_market_data import Response


def iso(seconds):
    return (datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds)).isoformat(timespec="microseconds").replace("+00:00", "Z")


class AuditClock:
    def __init__(self):
        self.epoch = datetime(2099, 1, 3, 12, tzinfo=timezone.utc).timestamp()
        self.elapsed, self.wall_jump = 0.0, 0.0
        self.lock = RLock()
        self.on_sleep = None

    def wall(self): return self.epoch + self.elapsed + self.wall_jump
    def monotonic(self): return self.elapsed
    def sleep(self, seconds):
        if self.on_sleep: self.on_sleep(seconds)
        with self.lock: self.elapsed += seconds


def operating_policy(**changes):
    return dict(schema_version=1, record_type="request_policy", quota_id="quota:step08-independent",
        provider="alpaca", api="market_data", hard_limit=200, operating_limit=180, max_work_attempts=1000,
        max_retries=3, max_wait_seconds=300, fallback_cap_seconds=30, entitlement_ref="review:original-preflight",
        feed_delays={"iex": 0, "sip": 900}, sharing_scopes=["scope:preflight"], rights_ref="rights:preflight",
        private_storage=True, internal_replay=True, cooperating_callers_only=True, verified_rate_headers=False) | changes


def request(**changes):
    return dict(schema_version=1, record_type="market_query", provider="alpaca", endpoint="stock_bars",
        sharing_scope="scope:preflight", rights_ref="rights:preflight", feed="sip", symbols=["AAA", "ZZZ"],
        timeframe="1Day", start="2099-01-02T00:00:00Z", end="2099-01-03T00:00:00Z", adjustment="raw", asof=None,
        revision_policy="revision:preflight", freshness_after="2099-01-02T21:00:00Z", information_cutoff="2099-01-10T00:00:00Z",
        expected_sessions=["2099-01-02"], page_limit=1) | changes


class Wire:
    def __init__(self, clock, handler=None, log=None):
        self.clock, self.handler, self.log, self.trace = clock, handler, log, []

    def __call__(self, method, url, params):
        event = dict(at=self.clock.monotonic(), wall=self.clock.wall(), feed=params["feed"], symbols=params["symbols"], token=params.get("page_token"))
        self.trace.append(event)
        if self.log:
            with self.log.open("a", encoding="utf-8") as out:
                out.write(json.dumps(event) + "\n"); out.flush(); os.fsync(out.fileno())
        return self.handler(params, len(self.trace)) if self.handler else self.page(params)

    def page(self, params, *, token=None, symbols=None, status=200, headers=None, received=None):
        selected = symbols if symbols is not None else params["symbols"].split(",")
        return Response(status, headers or {}, dict(bars={s: [dict(t="2099-01-02T21:00:00Z", o=10, h=12, l=9, c=11, v=50)] for s in selected}, next_page_token=token), received or iso(self.clock.wall()))


def oracle(trace, limit=180):
    """Compute limits only from the independent transport trace, never DB counters."""
    times = sorted(e["at"] for e in trace)
    gaps = [b - a for a, b in zip(times, times[1:])]
    # Integer nanoseconds avoid counting a binary-rounding boundary twice.
    ns = [round(t * 1_000_000_000) for t in times]
    peak = max((sum(t - 60_000_000_000 < x <= t for x in ns) for t in ns), default=0)
    return dict(dispatches=len(times), minimum_gap=min(gaps) if gaps else None, peak_rolling_60s=peak,
                ceiling=limit, trace=trace)
