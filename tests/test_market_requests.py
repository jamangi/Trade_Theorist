"""Recorded transport only: no credentials, sockets, real sleeps or provider calls."""
from copy import deepcopy
from contextlib import redirect_stdout
from datetime import datetime, timezone
from email.utils import format_datetime
import json
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Event, Thread
import unittest
from unittest.mock import patch, MagicMock

from trade_theorist.adapters.alpaca_market_data import AlpacaBarsAdapter, Response
from trade_theorist.contracts import ContractError, validate
from trade_theorist.market_requests import Coordinator, stamp
from trade_theorist.request_contracts import policy


class FakeClock:
    def __init__(self):
        self.seconds = 0.0
        self.epoch = datetime(2026, 9, 6, tzinfo=timezone.utc).timestamp()

    def wall(self): return self.epoch + self.seconds
    def monotonic(self): return self.seconds
    def sleep(self, seconds): self.seconds += seconds


def query(**changes):
    return dict(schema_version=1, record_type="market_query", provider="alpaca", endpoint="stock_bars",
        sharing_scope="scope:original-fixture", rights_ref="rights:original-fixture", feed="sip",
        symbols=["AAPL", "MSFT"], timeframe="1Day", start="2026-09-04T00:00:00Z", end="2026-09-05T00:00:00Z",
        adjustment="raw", asof=None, revision_policy="revision:fixture", freshness_after="2026-09-04T20:00:00Z",
        information_cutoff="2026-09-07T00:00:00Z", expected_sessions=["2026-09-04"], page_limit=1000) | changes


def bar():
    return dict(t="2026-09-04T20:00:00Z", o=100, h=102, l=99, c=101, v=1000)


def response(symbols=("AAPL", "MSFT"), token=None, status=200, headers=None):
    return Response(status, headers or {}, dict(bars={s: [bar()] for s in symbols}, next_page_token=token), "2026-09-06T00:00:00Z")


class Transport:
    def __init__(self, responses, clock):
        self.responses, self.clock, self.calls = list(responses), clock, []

    def __call__(self, method, url, params):
        self.calls.append((self.clock.monotonic(), params.copy()))
        if not self.responses: raise AssertionError("Unexpected transport attempt")
        item = self.responses.pop(0)
        if isinstance(item, Exception): raise item
        return item


class MarketRequestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clock = FakeClock()

    def coordinator(self, responses=(), **changes):
        transport = Transport(responses, self.clock)
        owner = Coordinator(self.root / "data", policy(**changes), transport, synthetic=True,
            registry_root=self.root / "registry", clock=self.clock, jitter=lambda: 0.25)
        self.addCleanup(owner.close)
        return owner, transport

    def submit(self, owner, value=None, attempts=30, deadline=None):
        return owner.submit(value or query(), consumer="test", max_attempts=attempts,
            deadline=deadline or stamp(self.clock.wall() + 3600))

    def test_three_consumers_share_pages_and_later_symbol_coverage(self):
        owner, transport = self.coordinator([response(["AAPL"], "next"), response(["MSFT"])])
        work = self.submit(owner)
        self.assertEqual(work, self.submit(owner, query(symbols=["MSFT", "AAPL"])))
        self.assertEqual(work, self.submit(owner))
        first = owner.run(work, max_pages=1)
        self.assertEqual((first["status"], first["coverage_observed"]), ("deferred", 0))
        self.assertEqual(owner.observations(work), [])
        result = owner.run(work, resume=owner.resume(work))
        self.assertEqual((result["status"], result["attempts"], result["subscribers"], result["coverage_observed"]), ("complete", 2, 3, 2))
        self.assertEqual(transport.calls[1][1]["page_token"], "next")
        self.assertEqual({o["bar"]["symbol"] for o in owner.observations(work)}, {"AAPL", "MSFT"})
        subset = self.submit(owner, query(symbols=["MSFT"]))
        self.assertEqual(owner.run(subset)["cache_hits"], 1)
        self.assertEqual(len(transport.calls), 2)

    def test_cached_overlap_batches_only_missing_symbols_and_window(self):
        owner, transport = self.coordinator([response(), response(["GOOG", "IBM"])])
        owner.run(self.submit(owner))
        result = owner.run(self.submit(owner, query(symbols=["AAPL", "GOOG", "IBM"])))
        self.assertEqual(result["status"], "complete")
        self.assertEqual(transport.calls[1][1]["symbols"], "GOOG,IBM")

    def test_compatible_pending_subsets_share_parent_limits_and_frozen_ids(self):
        owner, transport = self.coordinator([response(["AAPL"], "next"), response(["MSFT"])])
        parent = self.submit(owner)
        first = self.submit(owner, query(symbols=["AAPL"], page_limit=100))
        second = self.submit(owner, query(symbols=["MSFT"], page_limit=500))
        self.assertEqual(owner.telemetry(first)["shared_work_id"], parent)
        self.assertEqual(owner.run(first, max_pages=1)["status"], "deferred")
        self.assertEqual(owner.run(second)["status"], "complete")
        result = owner.run(first)
        self.assertEqual((result["status"], result["attempts"]), ("complete", 0))
        self.assertEqual(owner.telemetry(parent)["subscribers"], 3)
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual([x["bar"]["symbol"] for x in owner.observations(first)], ["AAPL"])
        self.assertEqual(owner.usage()["physical_attempts"], 2)

    def test_subset_cannot_top_up_exhausted_parent_or_cross_its_own_deadline(self):
        owner, transport = self.coordinator([response(["AAPL"], "next")])
        parent = self.submit(owner, attempts=1)
        child = self.submit(owner, query(symbols=["AAPL"]), attempts=30)
        result = owner.run(child)
        self.assertEqual((result["status"], result["reason"], result["attempts"]), ("deferred", "attempt_budget", 0))
        self.assertEqual(len(transport.calls), 1)
        self.clock.sleep(3600)
        self.assertEqual(owner.run(child)["status"], "expired")
        self.assertEqual(len(transport.calls), 1)

    def test_same_request_during_transport_joins_without_second_dispatch(self):
        owner, transport = self.coordinator([response()])
        entered, release = Event(), Event()
        def blocked(*args):
            entered.set()
            if not release.wait(5): raise RuntimeError("Test synchronization failed")
            return transport(*args)
        owner.transport = blocked
        work = self.submit(owner)
        results = []
        thread = Thread(target=lambda: results.append(owner.run(work)))
        thread.start()
        try:
            self.assertTrue(entered.wait(5))
            self.assertEqual(self.submit(owner), work)
            self.assertEqual(owner.run(work)["attempts"], 1)
        finally:
            release.set(); thread.join(5)
        self.assertEqual(results[0]["status"], "complete")
        self.assertEqual(len(transport.calls), 1)

    def test_final_429_cooldown_survives_restart_and_wall_clock_jump(self):
        owner, transport = self.coordinator([response(status=429, headers={"retry-after": "120"})], max_retries=0)
        result = owner.run(self.submit(owner))
        self.assertEqual((result["status"], result["throttles"]), ("failed", 1))
        another = self.submit(owner, query(symbols=["GOOG"]))
        self.assertEqual(owner.run(another)["reason"], "cooldown")
        owner.close()
        self.clock.epoch += 100  # Wall time alone cannot refill persisted admission.
        restarted, again = self.coordinator([response(["GOOG"])], max_retries=0)
        self.assertEqual(restarted.run(another)["reason"], "cooldown")
        self.assertEqual(len(again.calls), 0)
        self.clock.sleep(120)
        self.assertEqual(restarted.run(another)["status"], "complete")
        self.assertEqual(restarted.usage()["physical_attempts"], 2)

    def test_all_attempts_include_timeout_retries_and_pages(self):
        owner, transport = self.coordinator([TimeoutError("secret payload"), response(["AAPL"], "next"), response(["MSFT"])], max_wait_seconds=10)
        work = self.submit(owner, attempts=2)
        result = owner.run(work)
        self.assertEqual((result["attempts"], result["retries"], result["pages"], result["reason"]), (2, 1, 1, "attempt_budget"))
        self.assertEqual(len(transport.calls), 2)
        self.assertNotIn("secret payload", json.dumps(result))
        self.assertEqual(owner.run(work)["attempts"], 2)

    def test_checkpoint_rollback_replays_page_but_never_refunds_attempt(self):
        owner, transport = self.coordinator([response(["AAPL"], "next"), response(["AAPL"], "next"), response(["MSFT"])])
        work = self.submit(owner)
        def crash(): raise RuntimeError("Interrupted commit")
        with self.assertRaises(RuntimeError): owner.run(work, before_commit=crash)
        self.assertEqual(owner.telemetry(work)["attempts"], 1)
        self.assertEqual(owner.store.connection.execute("SELECT COUNT(*) FROM market_pages").fetchone()[0], 0)
        self.assertEqual(owner.store.connection.execute("SELECT COUNT(*) FROM market_observations").fetchone()[0], 0)
        owner.close()
        reopened, transport = self.coordinator([response(["AAPL"], "next"), response(["MSFT"])], max_wait_seconds=2)
        self.assertEqual(reopened.run(work)["reason"], "recovery")
        self.clock.sleep(60)
        result = reopened.run(work)
        self.assertEqual((result["status"], result["attempts"], result["pages"], result["retries"]), ("complete", 3, 2, 1))

    def test_default_rolling_limit_and_pacing_survive_idle_burst(self):
        owner, transport = self.coordinator([response(token=str(i)) for i in range(181)], max_work_attempts=200, max_wait_seconds=100)
        work = self.submit(owner, attempts=200)
        owner.run(work, max_pages=181)
        times = [t for t, _ in transport.calls]
        self.assertEqual(len(times), 181)
        self.assertTrue(all(b - a >= 1 / 3 - 1e-8 for a, b in zip(times, times[1:])))
        self.assertTrue(all(sum(t - 60 < x <= t for x in times) <= 180 for t in times))
        self.clock.sleep(100)
        transport.responses.extend([response(token="idle1"), response(token="idle2")])
        owner.run(work, max_pages=2)
        self.assertGreaterEqual(transport.calls[-1][0] - transport.calls[-2][0], 1 / 3 - 1e-8)

    def test_downward_limit_verified_headers_and_reset(self):
        owner, transport = self.coordinator([response(["AAPL"], "next", headers={"X-RateLimit-Limit": "2", "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(self.clock.wall() + 90)}), response(["MSFT"])], verified_rate_headers=True)
        work = self.submit(owner)
        self.assertEqual(owner.run(work)["reason"], "cooldown")
        self.clock.sleep(90)
        self.assertEqual(owner.run(work)["status"], "complete")
        self.assertEqual(owner.store.connection.execute("SELECT effective_limit FROM market_quota").fetchone()[0], 2)

    def test_full_numeric_date_wait_and_invalid_fallback(self):
        adapter = AlpacaBarsAdapter(lambda *_: None, feed="sip", offline=True, jitter=lambda: .25)
        now = self.clock.wall()
        date = format_datetime(datetime.fromtimestamp(now + 120, timezone.utc), usegmt=True)
        for headers in ({"retry-after": "120"}, {"RETRY-AFTER": date}):
            self.assertEqual(adapter._delay(headers, 0, now=now), 120)
        for bad in ("NaN", "Infinity", "-1", "garbage"):
            self.assertEqual(adapter._delay({"Retry-After": bad}, 0, now=now), 1.25)
        self.assertEqual(adapter._delay({}, 10, now=now), 30)

    def test_query_resume_and_entitlement_are_bound_without_fallback(self):
        owner, transport = self.coordinator([response(["AAPL"], "next")])
        work = self.submit(owner)
        owner.run(work, max_pages=1)
        for change in (dict(feed="iex"), dict(symbols=["AAPL"]), dict(adjustment="split"), dict(asof="2026-09-03"), dict(information_cutoff="2026-09-08T00:00:00Z"), dict(page_limit=50)):
            with self.assertRaises(ContractError): owner.run(work, resume=owner.resume(work), value=query(**change))
        with self.assertRaises(ContractError):
            self.submit(owner, query(end=stamp(self.clock.wall() - 899)))
        self.assertEqual(len(transport.calls), 1)

    def test_missing_or_malformed_coverage_never_becomes_complete(self):
        owner, transport = self.coordinator([response(["AAPL"]), Response(200, {}, {"bars": {"GOOG": [{"t": "bad"}]}}, "2026-09-06T00:00:00Z")])
        result = owner.run(self.submit(owner))
        self.assertEqual((result["status"], result["coverage_observed"]), ("incomplete", 1))
        result = owner.run(self.submit(owner, query(symbols=["GOOG"])))
        self.assertEqual((result["status"], result["reason"]), ("failed", "response"))

    def test_deadline_and_noop_sleeper_do_not_dispatch(self):
        owner, transport = self.coordinator([response(["AAPL"], "next")])
        expired = self.submit(owner, deadline=stamp(self.clock.wall() - 1))
        self.assertEqual(owner.run(expired)["status"], "expired")
        work = self.submit(owner, query(revision_policy="revision:other"))
        self.clock.sleep = lambda _: None
        with self.assertRaisesRegex(ContractError, "Sleeper"):
            owner.run(work)
        self.assertEqual(len(transport.calls), 1)

    def test_duplicate_process_and_root_rebinding_fail_closed(self):
        owner, transport = self.coordinator()
        code = "from trade_theorist.market_requests import Coordinator; from trade_theorist.request_contracts import policy; import sys; Coordinator(sys.argv[1],policy(),lambda *a: None,synthetic=True,registry_root=sys.argv[2])"
        result = subprocess.run([sys.executable, "-c", code, str(self.root / "data"), str(self.root / "registry")], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PermissionError" if sys.platform == "win32" else "BlockingIOError", result.stderr)
        owner.close()
        with self.assertRaisesRegex(ContractError, "bound"):
            Coordinator(self.root / "other", policy(), transport, synthetic=True, registry_root=self.root / "registry", clock=self.clock)

    def test_strict_nonsecret_contracts_and_production_bypass(self):
        for value in (policy() | {"key": "secret"}, policy() | {"operating_limit": 201}, policy() | {"feed_delays": {"iex": 0, "sip": 1}}, query() | {"symbols": ["AAPL", "AAPL"]}):
            with self.assertRaises(ContractError): validate(value)
        adapter = AlpacaBarsAdapter(lambda *_: self.fail("Bypassed coordinator"), feed="sip")
        with self.assertRaises(ContractError): list(adapter.pages(symbols=["AAPL"], start=query()["start"], end=query()["end"]))

    def test_cache_does_not_cross_feed_adjustment_or_cutoff(self):
        owner, transport = self.coordinator([response() for _ in range(4)])
        for change in ({}, dict(feed="iex"), dict(adjustment="split"), dict(information_cutoff="2026-09-08T00:00:00Z")):
            result = owner.run(self.submit(owner, query(**change)))
            self.assertEqual((result["status"], result["cache_hits"]), ("complete", 0))
        self.assertEqual(len(transport.calls), 4)

    def test_bound_store_cannot_silently_recreate_missing_quota_state(self):
        owner, transport = self.coordinator([response()])
        owner.run(self.submit(owner))
        owner.store.connection.execute("DELETE FROM market_quota")
        owner.close()
        with self.assertRaisesRegex(ContractError, "missing"):
            self.coordinator()

    def test_late_response_and_expired_cache_request_remain_expired(self):
        owner, transport = self.coordinator([response()])
        def slow(*args):
            self.clock.sleep(2)
            return transport(*args)
        owner.transport = slow
        work = self.submit(owner, deadline=stamp(self.clock.wall() + 1))
        self.assertEqual(owner.run(work)["status"], "expired")
        work = self.submit(owner, query(symbols=["AAPL"]), deadline=stamp(self.clock.wall() - 1))
        self.assertEqual(owner.run(work)["status"], "expired")
        with self.assertRaises(ContractError): owner.normalize(work, None)

    def test_extreme_finite_cooldown_stays_durable(self):
        owner, transport = self.coordinator([response(status=429, headers={"retry-after": "1e300"})], max_retries=0)
        owner.run(self.submit(owner))
        result = owner.run(self.submit(owner, query(symbols=["GOOG"])))
        self.assertEqual(result["reason"], "cooldown")
        self.assertTrue(result["not_before"].startswith("9999-"))
        self.assertEqual(len(transport.calls), 1)

    def test_heartbeat_adapter_and_revision_ingestion_use_same_work(self):
        from trade_theorist.heartbeat import prepare_market_data
        from trade_theorist.ingest import CSVMarketAdapter, SessionCalendar
        from test_alpaca_adapter import capability
        owner, transport = self.coordinator([response(["AAPL"])])
        args = dict(consumer="heartbeat", max_attempts=30, deadline=stamp(self.clock.wall() + 3600))
        result = prepare_market_data(owner, query(symbols=["AAPL"]), **args)
        adapter = AlpacaBarsAdapter(None, feed="sip")
        again = adapter.fetch_shared(owner, query(symbols=["AAPL"]), **args)
        self.assertEqual(result["work_id"], again["work_id"])
        self.assertEqual(len(transport.calls), 1)
        normalizer = CSVMarketAdapter(experiment_id="experiment:fixture", contamination="fixture",
            universe=[dict(instrument_id="instrument:aapl", symbol="AAPL", asset_class="us_equity", sector="Technology")],
            calendar=SessionCalendar("fixture-calendar", ("2026-09-04",)), capability=capability() | dict(storage_retention=True, internal_replay=True))
        accepted, bad = owner.normalize(result["work_id"], normalizer)
        self.assertEqual((len(accepted), len(bad)), (1, 0))
        accepted, bad = owner.normalize(result["work_id"], normalizer)
        self.assertEqual((len(accepted), len(bad)), (0, 0))
        normalizer.capability["feed"] = "iex"
        with self.assertRaises(ContractError): owner.normalize(result["work_id"], normalizer)

    def test_doctor_reports_owner_and_policy_without_changing_database(self):
        from trade_theorist.request_operations import status
        self.assertEqual(status()["reason"], "missing_request_configuration")
        owner, transport = self.coordinator([response()])
        owner.run(self.submit(owner))
        path = self.root / "policy.json"
        path.write_text(json.dumps(policy()))
        before = owner.store.connection.total_changes
        report = status(str(self.root / "data"), path, fixture=True, registry_root=self.root / "registry")
        self.assertEqual((report["status"], report["physical_attempts"]), ("ready", 1))
        self.assertEqual(owner.store.connection.total_changes, before)
        owner.close()
        before_bytes = (self.root / "data/research.sqlite3").read_bytes()
        self.assertEqual(status(self.root / "data", path, fixture=True, registry_root=self.root / "registry")["reason"], "owner_stopped")
        self.assertEqual((self.root / "data/research.sqlite3").read_bytes(), before_bytes)
        path.write_text(json.dumps(policy(operating_limit=100)))
        self.assertEqual(status(self.root / "data", path, fixture=True, registry_root=self.root / "registry")["reason"], "request_state_unverified")

    def test_transport_uses_one_http_request_without_redirect_or_sdk_retry(self):
        from trade_theorist.adapters.alpaca_market_data.transport import SingleAttemptTransport
        wire = SingleAttemptTransport("fixture-key", "fixture-secret")
        connection = MagicMock()
        connection.getresponse.return_value.status = 429
        connection.getresponse.return_value.read.return_value = b"not json"
        connection.getresponse.return_value.getheaders.return_value = [("Retry-After", "120")]
        with patch("trade_theorist.adapters.alpaca_market_data.transport.HTTPSConnection", return_value=connection):
            result = wire("GET", AlpacaBarsAdapter.BASE_URL, {"feed": "sip"})
        self.assertEqual(result.status, 429)
        self.assertEqual(result.headers["Retry-After"], "120")
        connection.request.assert_called_once()
        connection.close.assert_called_once()
        with self.assertRaises(ContractError): Coordinator(self.root / "production", policy(), lambda *_: None)

    def test_recorded_manual_cli_reuses_completed_shared_work_without_network(self):
        from trade_theorist.cli import main
        path = self.root
        (path / "policy.json").write_text(json.dumps(policy()))
        (path / "query.json").write_text(json.dumps(query()))
        (path / "responses.json").write_text(json.dumps([response().__dict__]))
        args = ["market-recorded", "--fixture", "--quota-root", str(path / "manual"), "--quota-policy", str(path / "policy.json"),
            "--query", str(path / "query.json"), "--responses", str(path / "responses.json"), "--max-attempts", "2", "--deadline", "2099-01-01T00:00:00Z"]
        with patch.dict(os.environ, {"LOCALAPPDATA": str(path / "appdata")}), patch("trade_theorist.adapters.alpaca_market_data.transport.HTTPSConnection", side_effect=AssertionError("Network forbidden")):
            for expected_cache_hits in (0, 1):
                output = io.StringIO()
                with redirect_stdout(output): code = main(args)
                self.assertEqual(code, 0, output.getvalue())
                result = json.loads(output.getvalue())
                self.assertEqual(result["telemetry"]["cache_hits"], expected_cache_hits)
                self.assertEqual(result["usage"]["physical_attempts"], 1)
                self.assertEqual(result["account_calls"], 0)


if __name__ == "__main__": unittest.main()
