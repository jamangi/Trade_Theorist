"""Step 08 independent executable audit. Expected results come from wire traces."""
from copy import deepcopy
from datetime import datetime, timezone
from email.utils import format_datetime
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from threading import Event, Thread
import time
import unittest
from unittest.mock import patch

from preflight_support import AuditClock, Wire, iso, operating_policy, request, oracle
from trade_theorist.adapters.alpaca_market_data import AlpacaBarsAdapter, Response
from trade_theorist.adapters.alpaca_market_data.transport import SingleAttemptTransport
from trade_theorist.contracts import ContractError, digest
from trade_theorist.market_requests import Clock, Coordinator, RequestStore
from trade_theorist.storage import Store
from trade_theorist.storage_v2 import V2Store
from trade_theorist.fixtures_accounting_v2 import FixtureV2
from trade_theorist.forward.shared import ForwardRound, RecordedDecisions, freeze_round
from trade_theorist.export_v2 import build_private, validate_private
from trade_theorist.request_operations import status as request_status


class RequestPreflight(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="independent-preflight-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.evidence = {}
        guard = patch.object(socket.socket, "connect", side_effect=AssertionError("Account networking forbidden"))
        socket_calls = guard.start()
        self.addCleanup(guard.stop)
        self.addCleanup(socket_calls.assert_not_called)

    def owner(self, name="case", **policy_changes):
        clock = AuditClock(); wire = Wire(clock)
        owner = Coordinator(self.root / name / "data", operating_policy(**policy_changes), wire, synthetic=True,
            registry_root=self.root / name / "registry", clock=clock, jitter=lambda: .5)
        self.addCleanup(owner.close)
        return owner, wire, clock

    def submit(self, owner, value=None, budget=1000):
        return owner.submit(value or request(), consumer="independent-manual", max_attempts=budget, deadline=iso(owner.clock.wall() + 86400))

    def assert_wire(self, wire, limit=180):
        result = oracle(wire.trace, limit)
        self.assertLessEqual(result["peak_rolling_60s"], limit)
        if result["minimum_gap"] is not None: self.assertGreaterEqual(result["minimum_gap"], max(1 / 3, 60 / limit) - 1e-8)
        return result

    def test_01_rolling_boundaries_idle_and_lower_ceiling(self):
        self.evidence = {"runs": []}
        for limit, pages in ((180, 365), (7, 20)):
            owner, wire, clock = self.owner(str(limit), operating_limit=limit)
            wire.handler = lambda p, n: wire.page(p, token=str(n))
            work = self.submit(owner)
            owner.run(work, max_pages=pages)
            clock.sleep(300)
            owner.run(work, max_pages=5)
            result = self.assert_wire(wire, limit)
            self.assertEqual(result["dispatches"], pages + 5)
            self.assertEqual(owner.usage()["physical_attempts"], result["dispatches"])
            self.evidence["runs"].append(result)

    def test_02_pause_between_admission_and_send_cannot_burst(self):
        owner, wire, clock = self.owner()
        wire.handler = lambda p, n: wire.page(p, token=str(n))
        admit = owner._admit
        def descheduled(*args):
            permit = admit(*args)
            if permit[0] is not None and not wire.trace: clock.sleep(10)
            return permit
        owner._admit = descheduled
        owner.run(self.submit(owner), max_pages=4)
        self.evidence = oracle(wire.trace)
        self.assert_wire(wire)

    def test_03_concurrent_manual_scheduler_and_adapter_instances_share(self):
        owner, wire, clock = self.owner()
        entered, release = Event(), Event()
        def blocking(p, n):
            if n == 1:
                entered.set()
                if not release.wait(5): raise AssertionError("Missing release")
                return wire.page(p, symbols=["AAA"], token="later-symbol")
            return wire.page(p, symbols=["ZZZ"])
        wire.handler = blocking
        work = self.submit(owner)
        outcomes, errors = [], []
        def run():
            try: outcomes.append(owner.run(work))
            except BaseException as exc: errors.append(type(exc).__name__)
        thread = Thread(target=run); thread.start()
        try:
            self.assertTrue(entered.wait(5))
            for consumer in ("manual", "scheduled", "character"):
                adapter = AlpacaBarsAdapter(None, feed="sip")
                result = adapter.fetch_shared(owner, request(), consumer=consumer, max_attempts=1000, deadline=iso(clock.wall() + 86400))
                self.assertEqual(result["work_id"], work)
        finally:
            release.set(); thread.join(5)
        self.assertFalse(thread.is_alive()); self.assertEqual(errors, [])
        self.assertEqual(outcomes[0]["status"], "complete")
        self.assertEqual({o["bar"]["symbol"] for o in owner.evidence(work)}, {"AAA", "ZZZ"})
        subset = self.submit(owner, request(symbols=["ZZZ"]))
        self.assertEqual(owner.run(subset)["status"], "complete")
        self.evidence = self.assert_wire(wire) | dict(subscribers=owner.telemetry(work)["subscribers"], cache_added_calls=len(wire.trace) - 2)
        self.assertEqual(len(wire.trace), 2)

    def test_04_query_isolation_and_full_resume_binding(self):
        owner, wire, clock = self.owner()
        work = self.submit(owner)
        wire.handler = lambda p, n: wire.page(p, token="pending")
        owner.run(work, max_pages=1)
        for change in (dict(feed="iex"), dict(adjustment="split"), dict(asof="2099-01-01"), dict(symbols=["AAA"]), dict(page_limit=10), dict(information_cutoff="2099-01-11T00:00:00Z"), dict(revision_policy="revision:other")):
            with self.assertRaises(ContractError): owner.run(work, resume=owner.resume(work), value=request(**change))
        self.assertEqual(len(wire.trace), 1)
        wire.handler = None
        owner.run(work)
        for change in (dict(feed="iex"), dict(adjustment="split"), dict(information_cutoff="2099-01-11T00:00:00Z"), dict(revision_policy="revision:other")):
            self.assertEqual(owner.run(self.submit(owner, request(**change)))["status"], "complete")
        self.assertEqual(len(wire.trace), 6)
        self.evidence = self.assert_wire(wire)

    def test_05_retry_ambiguity_and_page_budget_charge_each_wire_attempt(self):
        owner, wire, clock = self.owner()
        def responses(p, n):
            if n == 1: raise TimeoutError("original-error-sentinel")
            if n == 2: return wire.page(p, status=503)
            return wire.page(p, symbols=["AAA"], token="later-symbol")
        wire.handler = responses
        result = owner.run(self.submit(owner, budget=3))
        self.assertEqual((result["attempts"], result["retries"], result["pages"], result["reason"]), (3, 2, 1, "attempt_budget"))
        self.assertEqual(len(wire.trace), 3)
        self.assertEqual(owner.evidence(result["work_id"]), [])
        self.assertNotIn("original-error-sentinel", json.dumps(result))
        self.evidence = self.assert_wire(wire) | {"usage": result}

    def test_06_server_wait_formats_final_retry_and_fallback(self):
        self.evidence = {"runs": []}
        for i, value in enumerate(("120", "http-date", None, "broken", "NaN", "Infinity", "-1")):
            owner, wire, clock = self.owner(str(i), max_retries=0, max_wait_seconds=0)
            headers = {} if value is None else {"rEtRy-AfTeR": format_datetime(datetime.fromtimestamp(clock.wall() + 120, timezone.utc), usegmt=True) if value == "http-date" else value}
            wire.handler = lambda p, n: wire.page(p, status=429, headers=headers) if n == 1 else wire.page(p)
            failed = owner.run(self.submit(owner))
            self.assertEqual((failed["status"], failed["throttles"]), ("failed", 1))
            work = self.submit(owner, request(symbols=["OTHER"]))
            delay = 120 if value in ("120", "http-date") else 1.5
            clock.sleep(delay - .01)
            self.assertEqual(owner.run(work)["reason"], "cooldown")
            self.assertEqual(len(wire.trace), 1)
            clock.sleep(.02)
            self.assertEqual(owner.run(work)["status"], "complete")
            self.assertGreaterEqual(wire.trace[-1]["at"] - wire.trace[0]["at"], delay)
            self.evidence["runs"].append(dict(header=value, required_delay=delay, **self.assert_wire(wire)))

    def test_07_oversized_verified_hint_cannot_erase_429_cooldown(self):
        owner, wire, clock = self.owner(verified_rate_headers=True, max_retries=0, max_wait_seconds=0)
        wire.handler = lambda p, n: wire.page(p, status=429, headers={"Retry-After": "120", "X-RateLimit-Limit": "9" * 100}) if n == 1 else wire.page(p)
        self.evidence = {"trace": wire.trace}
        result = owner.run(self.submit(owner))
        self.assertEqual(result["status"], "failed")
        work = self.submit(owner, request(symbols=["OTHER"]))
        self.assertEqual(owner.run(work)["reason"], "cooldown")
        clock.sleep(120)
        self.assertEqual(owner.run(work)["status"], "complete")
        self.evidence = self.assert_wire(wire)

    def test_08_real_process_death_and_recovery(self):
        self.evidence = {"runs": []}
        for mode in ("dispatch", "commit", "page", "wait", "owner"):
            root = self.root / mode; root.mkdir()
            log = (root / "child.log").open("w")
            child = subprocess.Popen([sys.executable, str(Path(__file__).with_name("preflight_worker.py")), str(root), mode], stdout=log, stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            try:
                until = time.monotonic() + 10
                while not (root / "ready.json").exists() and child.poll() is None and time.monotonic() < until: time.sleep(.01)
                self.assertTrue((root / "ready.json").exists(), "Child failed to reach the requested boundary")
                with self.assertRaises((OSError, ContractError)):
                    Coordinator(root / "other", operating_policy(), lambda *_: None, synthetic=True, registry_root=root / "registry")
            finally:
                if child.poll() is None: child.terminate()
                child.wait(5); log.close()
            clock = AuditClock(); clock.wall_jump = 3600 if mode in {"dispatch", "wait"} else -3600
            wire = Wire(clock)
            wire.handler = lambda p, n: wire.page(p, symbols=["ZZZ"] if p.get("page_token") else ["AAA"], token=None if p.get("page_token") else "later-symbol")
            release_deadline = time.monotonic() + 2
            while True:
                try:
                    recovered = Coordinator(root / "data", operating_policy(), wire, synthetic=True, registry_root=root / "registry", clock=clock, jitter=lambda: .5)
                    break
                except PermissionError:
                    # Windows may signal process exit just before releasing its byte-range lock.
                    if time.monotonic() >= release_deadline: raise
                    time.sleep(.01)
            with recovered as owner:
                work = self.submit(owner, budget=10)
                # max_wait=300 can satisfy recovery internally; observe the actual wire time.
                result = owner.run(work)
                minimum = 120 if mode == "wait" else 60
                self.assertGreaterEqual(wire.trace[0]["at"], minimum)
                self.assertEqual(result["status"], "complete")
                prior = [json.loads(line) for line in (root / "wire.jsonl").read_text().splitlines()] if (root / "wire.jsonl").exists() else []
                combined = prior + wire.trace
                self.assertEqual(owner.usage()["physical_attempts"], len(combined))
                self.assertEqual(len(wire.trace), 1 if mode == "page" else 2)
                self.evidence["runs"].append(dict(boundary=mode, terminated_exit_code=child.returncode, minimum_recovery=minimum,
                    wall_jump=clock.wall_jump, accounted_attempts=owner.usage()["physical_attempts"], **oracle(combined)))

    def test_09_wall_jumps_and_frozen_policy(self):
        owner, wire, clock = self.owner()
        wire.handler = lambda p, n: wire.page(p, token=str(n))
        work = self.submit(owner)
        owner.run(work, max_pages=3)
        clock.wall_jump += 3600
        owner.run(work, max_pages=3)
        clock.wall_jump -= 7200
        owner.run(work, max_pages=3)
        self.evidence = self.assert_wire(wire)
        original = deepcopy(owner.policy)
        exposed = owner.policy
        exposed["feed_delays"]["sip"] = 0
        self.assertEqual(owner.policy, original, "A caller modified the active frozen entitlement policy")

    def paired(self, name, *, request_budget=10):
        owner, wire, clock = self.owner(name, max_wait_seconds=0)
        (owner.root.parent / "policy.json").write_text(json.dumps(owner.policy), encoding="utf-8")
        # Reuse only typed ledger input construction, not earlier forward setup or assertions.
        baseline = FixtureV2(owner.store, "audit-base-" + name, role="baseline", extra_instrument=True)
        peers = [FixtureV2(owner.store, "audit-" + mode + name, mode=mode, baseline=baseline.portfolio, extra_instrument=True)
                 for mode in ("character_portfolio", "council")]
        for peer in [baseline, *peers]: peer.event("funding", 1, amount="1000.00", boundary_mark_ids=[])
        symbols = sorted(x["symbol"] for x in owner.store.v2_record(peers[0].scope["policy_id"])["universe"])
        q = request(symbols=symbols, information_cutoff=iso(clock.wall() + 300))
        data_deadline, decision_at = iso(clock.wall() + 300), iso(clock.wall() + 600)
        clock.wall_jump = -136800  # Register Jan 1, after typed inputs, before the Jan 2 window.
        m = freeze_round(owner, manifest_id="forward:independent-" + name,
            participants=[(p.portfolio, "plan:" + p.name, p.segment) for p in peers], baseline=(baseline.portfolio, "plan:" + baseline.name), value=q,
            start_at="2099-01-02T00:00:00Z", end_at="2099-01-20T00:00:00Z", data_deadline=data_deadline, decision_at=decision_at,
            max_request_attempts=request_budget, model_budget=dict(model_ref="model:original-audit", max_calls=2, max_tokens=40, max_output_tokens=20),
            stopping_rule=dict(horizon_sessions=5, min_completed_sessions=5, min_matured_forecasts=30, stop_at="2099-01-20T00:00:00Z", stop_on_data_failure=True))
        clock.wall_jump = 0
        wire.handler = lambda p, n: wire.page(p, symbols=[symbols[1] if p.get("page_token") else symbols[0]], token=None if p.get("page_token") else "last-symbol")
        provider = RecordedDecisions({p.portfolio: dict(action="hold", rationale="Independent original audit opinion", tokens=7) for p in peers})
        return owner, wire, clock, m, ForwardRound(owner, m["id"]), provider

    def test_11_paired_merged_misses_cutoff_and_result_only_readers(self):
        self.evidence["runs"] = []
        for condition in ("complete", "deadline", "late-receipt", "budget", "reserved"):
            owner, wire, clock, m, paired, provider = self.paired(condition, request_budget=1 if condition == "budget" else 10)
            # Concurrent consumers queue both subsets before the parent populates the cache.
            shared = owner.submit(m["query"], consumer="scheduled", max_attempts=m["max_request_attempts"], deadline=m["data_deadline"])
            children = [owner.submit(m["query"] | {"symbols": [s]}, consumer="manual-" + s, max_attempts=1, deadline=m["data_deadline"]) for s in m["query"]["symbols"]]
            first = paired.execute(provider, max_pages=1)
            self.assertEqual(provider.calls, 0)
            self.assertEqual(len(wire.trace), 1)
            if condition != "budget":
                self.assertEqual(first["status"], "deferred")
                self.assertIsNone(paired._existing(m["snapshot_ref"]))
            if condition == "deadline": clock.sleep(301)
            else: clock.sleep(1)
            if condition == "late-receipt":
                old = wire.handler
                def late(p, n):
                    response = old(p, n)
                    return Response(response.status, response.headers, response.body, iso(clock.wall() + 500))
                wire.handler = late
            if condition == "reserved":
                def crash(): raise RuntimeError("Independent reservation interruption")
                with self.assertRaises(RuntimeError): paired.execute(provider, after_reserve=crash)
                paired = ForwardRound(owner, m["id"])
            result = paired.execute(provider)
            snapshot = owner.store.v2_record(m["snapshot_ref"])
            self.assertEqual({o["snapshot_hash"] for o in result["outcomes"]}, {digest(snapshot)})
            self.assertEqual({o["snapshot_ref"] for o in result["outcomes"]}, {m["snapshot_ref"]})
            self.assertEqual(snapshot["query_hash"], digest(m["query"]))
            self.assertTrue(all(o["received_at"] <= m["query"]["information_cutoff"] for o in snapshot["observations"]))
            if condition == "complete":
                self.assertEqual(result["status"], "decided")
                self.assertEqual({o["bar"]["symbol"] for o in snapshot["observations"]}, set(m["query"]["symbols"]))
                self.assertEqual(len(set(provider.snapshots)), 1)
                for child in children: self.assertEqual(owner.run(child)["status"], "complete")
                self.assertEqual(len(wire.trace), 2, "Queued subsets spent additional transport attempts")
            else:
                self.assertEqual(result["status"], "abstained")
                self.assertEqual(provider.calls, 0)
                if condition == "reserved":
                    self.assertEqual(result["reason"], "execution_ambiguous")
                    self.assertIsNone(result["model_calls"])
                else: self.assertEqual(snapshot["observations"], [])
            requests, callbacks = len(wire.trace), provider.calls
            with patch.object(owner, "transport", side_effect=AssertionError("Result-only reader attempted a request")):
                for _ in range(3):
                    self.assertEqual(paired.execute(provider), result)
                    self.assertFalse(paired.report()["promotion_eligible"])
                validate_private(build_private(owner.store, as_of=iso(clock.wall())))
                diagnostic = request_status(owner.root, owner.root.parent / "policy.json", fixture=True, registry_root=owner.root.parent / "registry")
                self.assertEqual(diagnostic["physical_attempts"], requests)
                owner.store.verify_v2()
            self.assertEqual((len(wire.trace), provider.calls), (requests, callbacks))
            self.evidence["runs"].append(dict(condition=condition, initial=first["status"], final=result["status"], reason=result["reason"],
                snapshot_hash=digest(snapshot), cutoff=m["query"]["information_cutoff"], consumers=len(result["outcomes"]), recorded_callbacks=callbacks,
                result_reader_added_calls=0, **oracle(wire.trace)))

    def test_12_forward_manifest_is_a_frozen_copy(self):
        _, _, _, m, paired, _ = self.paired("manifest")
        exposed = paired.manifest
        exposed["participants"][0]["portfolio_ref"] = exposed["participants"][1]["portfolio_ref"]
        exposed["model_budget"]["max_calls"] = 1000
        self.assertEqual(paired.manifest, m, "A caller modified frozen participants or spend policy")
        self.evidence = dict(frozen_manifest_hash=digest(m), external_mutations_applied=False)

    def test_13_verified_headers_only_reduce_capacity_and_reset_is_shared(self):
        owner, wire, clock = self.owner("verified", verified_rate_headers=True)
        def respond(p, n):
            headers = {"X-RateLimit-Limit": "2"} if n == 1 else {"X-RateLimit-Limit": "1000"}
            if n == 2: headers.update({"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(clock.wall() + 120)})
            return wire.page(p, token=str(n), headers=headers)
        wire.handler = respond
        owner.run(self.submit(owner), max_pages=4)
        self.evidence = self.assert_wire(wire, limit=2)
        self.assertEqual([r["at"] for r in wire.trace], [0, 30, 150, 180])
        self.assertEqual(owner.store.connection.execute("SELECT effective_limit FROM market_quota").fetchone()[0], 2)

    def test_14_upgrade_preserves_ambiguous_charge_and_v1_v2_readers(self):
        root, registry = self.root / "upgrade", self.root / "registry-upgrade"
        clock = AuditClock(); wire = Wire(clock)
        with patch.object(RequestStore, "schema_ceiling", 5):
            with Coordinator(root, operating_policy(), wire, synthetic=True, registry_root=registry, clock=clock) as old:
                work = self.submit(old, budget=10)
                with old.store.transaction():
                    _, body = old._work(work)
                    body.update(attempts=1, page_retries=1, status="fetching")
                    old._save(work, body)
                    old.store.connection.execute("INSERT INTO market_attempts(work_id,dispatched,request_hash,outcome) VALUES(?,?,?,'ambiguous')", (work, 0, digest("original-old-attempt")))
                original = list(map(tuple, old.store.connection.execute("SELECT * FROM schema_migrations")))
                self.assertEqual(len(original), 5)
        with Coordinator(root, operating_policy(), wire, synthetic=True, registry_root=registry, clock=clock) as upgraded:
            self.assertEqual(list(map(tuple, upgraded.store.connection.execute("SELECT * FROM schema_migrations WHERE version<=5"))), original)
            self.assertIsNone(upgraded.store.connection.execute("SELECT settled FROM market_attempts").fetchone()[0])
            result = upgraded.run(work)
            self.assertEqual(result["status"], "complete")
            self.assertEqual(result["attempts"], 2)
            self.assertGreaterEqual(wire.trace[0]["at"], 60)
            self.assertEqual(upgraded.store.connection.execute("SELECT settled FROM market_attempts WHERE sequence=2").fetchone()[0], clock.monotonic())
        for cls in (Store, V2Store):
            with cls(root, synthetic=True) as reader:
                self.assertEqual(reader.connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0], 6)
        self.evidence = dict(previous_migrations_unchanged=True, old_ambiguous_attempts=1, final_attempts=2, reader_versions=[1, 2], **oracle(wire.trace))

    def test_10_production_clock_http_attempts_and_api_separation(self):
        self.assertIs(Clock.sleep, time.sleep)
        self.assertIs(AlpacaBarsAdapter(None, feed="sip").sleeper, time.sleep)
        real_trace = []
        class Connection:
            def __init__(self, *_, **__): pass
            def request(self, method, path, headers): real_trace.append(time.monotonic())
            def getresponse(self):
                class Reply:
                    status = 200
                    def read(self, _): return json.dumps({"bars": {"AAA": [dict(t="2020-01-02T21:00:00Z", o=10, h=12, l=9, c=11, v=5)]}, "next_page_token": "next" if len(real_trace) == 1 else None}).encode()
                    def getheaders(self): return []
                return Reply()
            def close(self): pass
        policy = operating_policy()
        q = request(symbols=["AAA"], start="2020-01-02T00:00:00Z", end="2020-01-03T00:00:00Z", expected_sessions=["2020-01-02"], freshness_after="2020-01-02T00:00:00Z", information_cutoff="2200-01-01T00:00:00Z")
        transport = SingleAttemptTransport("original-key", "original-secret")
        with patch.dict(os.environ, {"LOCALAPPDATA": str(self.root / "appdata")}), patch("trade_theorist.adapters.alpaca_market_data.transport.HTTPSConnection", Connection):
            with Coordinator(self.root / "production", policy, transport) as owner:
                result = owner.run(owner.submit(q, consumer="production-wire-fixture", max_attempts=5, deadline="2200-01-01T00:00:00Z"))
                self.assertEqual((result["status"], result["attempts"], len(real_trace)), ("complete", 2, 2))
                self.assertGreaterEqual(real_trace[1] - real_trace[0], 1 / 3 - .005)
            with self.assertRaises(ContractError): Coordinator(self.root / "sdk", policy, lambda *_: None)
            with self.assertRaises(ContractError): transport("GET", "https://paper-api.alpaca.markets/v2/account", {})
            with self.assertRaises(ContractError): Coordinator(self.root / "trading", policy | {"api": "trading"}, transport)
        self.evidence = dict(real_monotonic_dispatches=real_trace, minimum_gap=real_trace[1] - real_trace[0],
            production_wait="time.sleep", http_requests=2, outside_socket_calls=0, trading_policy="rejected by Market Data schema; live Trading adapter remains unavailable")


if __name__ == "__main__": unittest.main()
