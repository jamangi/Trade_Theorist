"""Single-owner durable Market Data admission. Transport injection never grants account rights."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import random
import sqlite3
from threading import Lock, RLock
import time

from .contracts import ContractError, canonical, digest, utc
from .request_contracts import validate
from .storage_v2 import V2Store


def stamp(seconds):
    return (datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds)).isoformat(timespec="microseconds").replace("+00:00", "Z")


def not_before(seconds):
    # Keep very large but finite server waits enforceable without overflowing the
    # human-readable timestamp. The authoritative logical deadline is uncapped.
    return stamp(min(seconds, 253402300799.0))


class Clock:
    wall = staticmethod(time.time)
    monotonic = staticmethod(time.monotonic)
    sleep = staticmethod(time.sleep)


class Deferred(ContractError):
    pass


@contextmanager
def owner_lock(path, *, create=True):
    with path.open("a+b" if create else "r+b") as handle:
        if create and handle.tell() == 0:
            handle.write(b"0"); handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


class RequestStore(V2Store):
    schema_ceiling = 6

    def __init__(self, root, *, synthetic=False):
        super().__init__(root, synthetic=synthetic)
        self.connection.close()
        self.connection = sqlite3.connect(self.path, timeout=15, isolation_level=None, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA synchronous=FULL")


def query(value):
    value = json.loads(canonical(validate(value)))
    if value["record_type"] != "market_query":
        raise ContractError("A market query is required")
    for field in ("start", "end", "freshness_after", "information_cutoff"):
        value[field] = stamp(utc(value[field]).timestamp())
    value["symbols"].sort(); value["expected_sessions"].sort()
    return value


def compatibility(value):
    return digest({k: v for k, v in value.items() if k not in {"symbols", "start", "end", "expected_sessions", "page_limit"}})


class Coordinator:
    """One coordinator owns a quota principal; all consumers submit to that owner.

    A second process fails closed rather than creating another allowance. The
    registry's permanent root binding prevents moving a principal to an empty DB.
    Registry/clock overrides are only available for explicitly synthetic tests.
    """
    def __init__(self, root, policy, transport, *, synthetic=False, registry_root=None, clock=None, jitter=None):
        self._policy = json.loads(canonical(validate(policy)))
        if policy["record_type"] != "request_policy":
            raise ContractError("A request policy is required")
        if not synthetic and any(x is not None for x in (registry_root, clock, jitter)):
            raise ContractError("Production coordination uses the real clock and canonical owner registry")
        from .adapters.alpaca_market_data.transport import SingleAttemptTransport
        if not synthetic and type(transport) is not SingleAttemptTransport:
            raise ContractError("Production requires the single-attempt transport; SDK retries are not admitted")
        self.clock, self.jitter = clock or Clock(), jitter or random.random
        self.transport, self.synthetic = transport, synthetic
        root = Path(root).expanduser()
        if not root.is_absolute():
            raise ContractError("Select an absolute shared quota root")
        self.root = root.resolve()
        if not synthetic and any((p / ".git").exists() for p in (self.root, *self.root.parents)):
            raise ContractError("Real quota state must be private and outside Git")
        registry = Path(registry_root) if registry_root else Path(os.environ.get("LOCALAPPDATA", Path.home())) / "TradeTheorist" / "quota-owners"
        registry.mkdir(parents=True, exist_ok=True)
        key = digest(policy["quota_id"])
        self._owner = owner_lock(registry / (key + ".lock"))
        self._owner.__enter__()
        self.store = None
        try:
            binding = registry / (key + ".json")
            bound = binding.exists()
            if bound:
                if json.loads(binding.read_text()) != dict(root=str(self.root)) or not (self.root / "research.sqlite3").exists():
                    raise ContractError("Quota principal is bound to another or missing durable store; restore it")
            else:
                # Binding is intentionally never reset by normal shutdown.
                with binding.open("x", encoding="utf-8") as out:
                    out.write(canonical(dict(root=str(self.root)))); out.flush(); os.fsync(out.fileno())
            self.store = RequestStore(self.root, synthetic=synthetic)
            self.db, self.dispatch = RLock(), Lock()
            with self.store.transaction():
                row = self.store.connection.execute("SELECT * FROM market_quota WHERE id=1").fetchone()
                if row is None:
                    if bound:
                        raise ContractError("Bound quota state is missing; restore durable evidence")
                    self.store.connection.execute("INSERT INTO market_quota VALUES(1,?,0,0,0,?)", (canonical(self.policy), min(policy["hard_limit"], policy["operating_limit"])))
                elif json.loads(row["policy"]) != self.policy:
                    raise ContractError("Quota policy changed; review an explicit policy transition rather than resetting state")
                elif any(type(row[k]) not in (int, float) or not math.isfinite(row[k]) or row[k] < 0 for k in ("logical", "cooldown", "next_dispatch")) or not 1 <= row["effective_limit"] <= policy["operating_limit"]:
                    raise ContractError("Invalid durable admission state; restore verified evidence")
            self.base_logical = row["logical"] if row else 0
            self.base_mono = self.clock.monotonic()
            self.last_logical = self.base_logical
            # Do not trust wall-clock downtime to refill a rolling window or erase a
            # cooldown. Restart waits a full window, plus any longer remaining wait.
            self.recovery = self.base_logical + 60 if row else 0
            self.closed = False
        except BaseException:
            if self.store:
                self.store.close()
            self._owner.__exit__(None, None, None)
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    @property
    def policy(self):
        """Expose the reviewed policy without granting mutation of active limits/rights."""
        return deepcopy(self._policy)

    def close(self):
        with self.dispatch, self.db:
            if not self.closed:
                self.store.close(); self._owner.__exit__(None, None, None); self.closed = True

    def _time(self):
        current = self.clock.monotonic()
        if not math.isfinite(current) or current < self.base_mono:
            raise ContractError("Monotonic clock failed; no dispatch allowed")
        self.last_logical = max(self.last_logical, self.base_logical + current - self.base_mono)
        self.store.connection.execute("UPDATE market_quota SET logical=? WHERE id=1", (self.last_logical,))
        return self.last_logical

    def _work(self, identifier):
        row = self.store.connection.execute("SELECT query,body FROM market_work WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise ContractError("Unknown shared work item")
        return json.loads(row[0]), json.loads(row[1])

    def _save(self, identifier, work):
        if work["status"] in {"complete", "incomplete", "expired", "failed"} and work["finished_logical"] is None:
            work["finished_logical"] = self.last_logical
        self.store.connection.execute("UPDATE market_work SET body=? WHERE id=?", (canonical(work), identifier))

    def _missing(self, value):
        batches = {}
        for symbol in value["symbols"]:
            cursor, end = value["start"], value["end"]
            windows = self.store.connection.execute("SELECT start,end FROM market_windows WHERE compatibility=? AND symbol=? ORDER BY start,end", (compatibility(value), symbol))
            for begin, finish in windows:
                if finish <= cursor or begin >= end:
                    continue
                if begin > cursor:
                    batches.setdefault((cursor, min(begin, end)), []).append(symbol)
                cursor = max(cursor, finish)
                if cursor >= end:
                    break
            if cursor < end:
                batches.setdefault((cursor, end), []).append(symbol)
        return [dict(start=a, end=b, symbols=sorted(symbols)) for (a, b), symbols in sorted(batches.items())]

    def submit(self, value, *, consumer, max_attempts, deadline):
        value = query(value)
        if not isinstance(consumer, str) or not consumer or type(max_attempts) is not int or not 1 <= max_attempts <= self.policy["max_work_attempts"]:
            raise ContractError("A consumer and finite work attempt budget are required")
        deadline_time = utc(deadline).timestamp()
        if not deadline.endswith("Z") or not math.isfinite(deadline_time):
            raise ContractError("Use an explicit UTC completion deadline")
        if value["sharing_scope"] not in self.policy["sharing_scopes"] or value["rights_ref"] != self.policy["rights_ref"]:
            raise ContractError("Query sharing/rights differ from the reviewed policy")
        delay = self.policy["feed_delays"][value["feed"]]
        if delay is None or utc(value["end"]).timestamp() > self.clock.wall() - delay:
            raise ContractError("Explicit feed/window entitlement is not established; no fallback")
        identifier = "work:" + digest(value)
        with self.db, self.store.transaction():
            now = self._time()
            row = self.store.connection.execute("SELECT id FROM market_work WHERE query_hash=?", (digest(value),)).fetchone()
            if row:
                _, work = self._work(identifier)
                work["subscribers"] += 1
                if work["status"] in {"complete", "incomplete"}:
                    work["cache_hits"] += 1
                self._save(identifier, work)
                return identifier
            segments = self._missing(value)
            parent = None
            if segments:
                for candidate in self.store.connection.execute("SELECT id,query,body FROM market_work ORDER BY rowid"):
                    other, pending = json.loads(candidate["query"]), json.loads(candidate["body"])
                    if pending["status"] not in {"queued", "fetching", "deferred", "waiting"} or pending["shared_work_id"] is not None:
                        continue
                    if compatibility(other) == compatibility(value) and set(value["symbols"]) <= set(other["symbols"]) and other["start"] <= value["start"] and other["end"] >= value["end"]:
                        parent = candidate["id"]
                        pending["subscribers"] += 1
                        self._save(parent, pending)
                        break
            work = dict(status="queued", reason="none", max_attempts=max_attempts, attempts=0, retries=0, throttles=0,
                queued_logical=now, finished_logical=None,
                shared_work_id=parent,
                deadline=deadline, deadline_logical=now + max(0, deadline_time - self.clock.wall()),
                pages=0, subscribers=1, cache_hits=0 if segments else 1, wait_seconds=0, not_before=None,
                segments=segments, segment=0, token=None, page_number=0, page_retries=0, seen_tokens=[],
                record_ids=[], coverage_expected=len(value["symbols"]) * len(value["expected_sessions"]), coverage_observed=0)
            self.store.connection.execute("INSERT INTO market_work VALUES(?,?,?,?)", (identifier, digest(value), canonical(value), canonical(work)))
            if deadline_time <= self.clock.wall():
                work.update(status="expired", reason="deadline"); self._save(identifier, work)
            elif not segments:
                self._finish(value, work); self._save(identifier, work)
        return identifier

    def _finish(self, value, work, *, allowed_ids=None):
        rows = self.store.connection.execute("SELECT id,symbol,event_at,received_at FROM market_observations WHERE compatibility=? ORDER BY symbol,event_at,id", (compatibility(value),))
        rows = [r for r in rows if r["symbol"] in value["symbols"] and value["start"] <= r["event_at"] <= value["end"] and (allowed_ids is None or r["id"] in allowed_ids)]
        work["record_ids"] = [r["id"] for r in rows]
        observed = {(r["symbol"], r["event_at"][:10]) for r in rows if r["event_at"][:10] in value["expected_sessions"]}
        work["coverage_observed"] = len(observed)
        work["status"] = "complete" if len(observed) == work["coverage_expected"] else "incomplete"
        work["reason"] = "none" if work["status"] == "complete" else "coverage"
        work["not_before"] = None

    def telemetry(self, identifier):
        with self.db:
            value, work = self._work(identifier)
            result = dict(schema_version=1, record_type="request_telemetry", quota_id=self.policy["quota_id"],
                work_id=identifier, query_hash=digest(value), cooperating_callers_only=True,
                shared_work_id=work["shared_work_id"],
                remaining_attempts=max(0, work["max_attempts"] - work["attempts"]))
            current = work["finished_logical"] if work["finished_logical"] is not None else max(self.last_logical, self.base_logical + self.clock.monotonic() - self.base_mono)
            result["queue_seconds"] = max(0, current - work["queued_logical"])
            if work["shared_work_id"] is not None:
                _, parent = self._work(work["shared_work_id"])
                result["remaining_attempts"] = max(0, parent["max_attempts"] - parent["attempts"])
            for key in ("status", "reason", "attempts", "retries", "throttles", "pages", "subscribers", "cache_hits", "wait_seconds", "coverage_expected", "coverage_observed", "not_before"):
                result[key] = work[key]
            return validate(result)

    def observations(self, identifier):
        with self.db:
            _, work = self._work(identifier)
            return [json.loads(self.store.connection.execute("SELECT body FROM market_observations WHERE id=?", (i,)).fetchone()[0]) for i in work["record_ids"]]

    def evidence(self, identifier):
        """Private immutable identities plus bodies for experiment snapshot freezing."""
        with self.db:
            _, work = self._work(identifier)
            return [dict(id=i, **body) for i, body in zip(work["record_ids"], self.observations(identifier))]

    def normalize(self, identifier, csv_adapter):
        """Hand only a complete immutable download to existing revision ingestion.

        The caller persists the returned records with its experiment transaction;
        no network call or database write transaction is held during normalization.
        """
        from .adapters.alpaca_market_data import AlpacaBarsAdapter, Page
        with self.db:
            q, work = self._work(identifier)
            if work["status"] != "complete":
                raise ContractError("Only complete shared evidence can enter experiment ingestion")
            if q["adjustment"] != "raw" or csv_adapter.capability["feed"] != q["feed"]:
                raise ContractError("Revision ingestion requires raw bars and the pinned source feed")
            if not csv_adapter.capability["storage_retention"] or not csv_adapter.capability["internal_replay"]:
                raise ContractError("Experiment ingestion requires reviewed storage and replay rights")
            observations = self.observations(identifier)
        adapter = AlpacaBarsAdapter(None, feed=q["feed"])
        accepted, quarantined = [], []
        for item in observations:
            page = Page(1, q["feed"], item["request_hash"], item["received_at"], (item["bar"],), None, digest(q))
            new, bad = adapter.ingest_page(page, csv_adapter)
            accepted.extend(new); quarantined.extend(bad)
        return accepted, quarantined

    def resume(self, identifier):
        with self.db:
            value, _ = self._work(identifier)
            return dict(version="market-resume-v1", work_id=identifier, query_hash=digest(value))

    def _admit(self, identifier, request_hash, wait_left):
        while True:
            with self.db, self.store.transaction():
                value, work = self._work(identifier)
                now = self._time()
                if now >= work["deadline_logical"] or self.clock.wall() >= utc(work["deadline"]).timestamp():
                    work.update(status="expired", reason="deadline", not_before=None); self._save(identifier, work)
                    return None, wait_left
                if work["attempts"] >= work["max_attempts"]:
                    work.update(status="deferred", reason="attempt_budget", not_before=None); self._save(identifier, work)
                    return None, wait_left
                if work["page_retries"] > self.policy["max_retries"]:
                    work.update(status="failed", reason="retry_limit"); self._save(identifier, work)
                    return None, wait_left
                state = self.store.connection.execute("SELECT * FROM market_quota WHERE id=1").fetchone()
                recent = [r[0] for r in self.store.connection.execute("SELECT COALESCE(settled,dispatched) AS charged_at FROM market_attempts WHERE COALESCE(settled,dispatched)>? ORDER BY charged_at", (now - 60,))]
                limit = min(self.policy["hard_limit"], self.policy["operating_limit"], state["effective_limit"])
                ceiling = recent[-limit] + 60 if len(recent) >= limit else now
                when = max(now, self.recovery, state["cooldown"], state["next_dispatch"], ceiling)
                reason = "cooldown" if when == state["cooldown"] and when > now else "recovery" if when == self.recovery and when > now else "quota"
                delay = when - now
                if delay > 0:
                    work.update(status="deferred", reason=reason, not_before=not_before(self.clock.wall() + delay))
                    self._save(identifier, work)
                    if delay > wait_left or now + delay >= work["deadline_logical"]:
                        return None, wait_left
                else:
                    work["attempts"] += 1
                    if work["page_retries"]:
                        work["retries"] += 1
                    work["page_retries"] += 1  # Crash before receipt still consumes this page's retry allowance.
                    work.update(status="fetching", reason="none", not_before=None)
                    self._save(identifier, work)
                    cursor = self.store.connection.execute("INSERT INTO market_attempts(work_id,dispatched,request_hash,outcome) VALUES(?,?,?,'ambiguous')", (identifier, now, request_hash))
                    self.store.connection.execute("UPDATE market_quota SET next_dispatch=? WHERE id=1", (now + max(1 / 3, 60 / limit),))
                    return cursor.lastrowid, wait_left
            before = self.clock.monotonic()
            self.clock.sleep(delay)  # No database transaction or permit exists during wait.
            elapsed = self.clock.monotonic() - before
            if elapsed + 1e-6 < delay:
                raise ContractError("Sleeper did not advance the monotonic clock")
            wait_left -= delay
            with self.db, self.store.transaction():
                _, work = self._work(identifier); work["wait_seconds"] += elapsed
                self._save(identifier, work); self._time()

    def run(self, identifier, *, resume=None, value=None, max_pages=100, before_commit=None):
        from .adapters.alpaca_market_data import AlpacaBarsAdapter, Response
        if type(max_pages) is not int or max_pages < 1:
            raise ContractError("Use a finite page bound")
        if resume is not None and resume != self.resume(identifier) or value is not None and digest(query(value)) != self.resume(identifier)["query_hash"]:
            raise ContractError("Resume belongs to a different full canonical query")
        with self.db:
            _, work = self._work(identifier)
            parent = work["shared_work_id"]
        if parent is not None and work["status"] not in {"complete", "incomplete", "expired", "failed"}:
            # Compatible subset subscribers own no transport allowance. Progress
            # the same parent work, retaining its original budgets and cutoff.
            with self.db, self.store.transaction():
                now = self._time()
                if now >= work["deadline_logical"] or self.clock.wall() >= utc(work["deadline"]).timestamp():
                    work.update(status="expired", reason="deadline"); self._save(identifier, work)
                    return self.telemetry(identifier)
            self.run(parent, max_pages=max_pages, before_commit=before_commit)
            with self.db, self.store.transaction():
                q, work = self._work(identifier)
                _, shared = self._work(parent)
                now = self._time()
                if now >= work["deadline_logical"] or self.clock.wall() >= utc(work["deadline"]).timestamp():
                    work.update(status="expired", reason="deadline")
                elif shared["status"] in {"complete", "incomplete"}:
                    self._finish(q, work, allowed_ids=set(shared["record_ids"]))
                    work["cache_hits"] = 1
                elif shared["status"] in {"failed", "expired"}:
                    work.update(status=shared["status"], reason=shared["reason"], not_before=shared["not_before"])
                else:
                    work.update(status="deferred", reason=shared["reason"] if shared["reason"] != "none" else "busy", not_before=shared["not_before"])
                self._save(identifier, work)
                return self.telemetry(identifier)
        if not self.dispatch.acquire(blocking=False):
            return self.telemetry(identifier)  # Join the owning download; never dispatch independently.
        try:
            wait_left, committed = self.policy["max_wait_seconds"], 0
            while committed < max_pages:
                with self.db:
                    q, work = self._work(identifier)
                    if work["status"] in {"complete", "incomplete", "expired", "failed"}:
                        return self.telemetry(identifier)
                    if work["attempts"] == 0:
                        with self.store.transaction():
                            now = self._time()
                            if now >= work["deadline_logical"] or self.clock.wall() >= utc(work["deadline"]).timestamp():
                                work.update(status="expired", reason="deadline"); self._save(identifier, work)
                                return self.telemetry(identifier)
                        # Another queued work item may have populated the cache
                        # since submission. Recheck before the first admission.
                        work["segments"] = self._missing(q)
                        if not work["segments"]:
                            self._finish(q, work); work["cache_hits"] = 1
                            with self.store.transaction(): self._save(identifier, work)
                            return self.telemetry(identifier)
                        with self.store.transaction(): self._save(identifier, work)
                    segment = work["segments"][work["segment"]]
                    params = dict(symbols=",".join(segment["symbols"]), start=segment["start"], end=segment["end"],
                        timeframe=q["timeframe"], limit=str(q["page_limit"]), adjustment=q["adjustment"], feed=q["feed"], sort="asc")
                    if q["asof"] is not None: params["asof"] = q["asof"]
                    if work["token"]: params["page_token"] = work["token"]
                attempt_id, wait_left = self._admit(identifier, digest([AlpacaBarsAdapter.BASE_URL, params]), wait_left)
                if attempt_id is None:
                    raise Deferred()
                response = None
                try:
                    response = self.transport("GET", AlpacaBarsAdapter.BASE_URL, dict(params))
                except Exception:
                    pass  # An ambiguous outbound attempt remains charged; no exception payload is persisted.
                with self.db, self.store.transaction():
                    q, work = self._work(identifier); now = self._time()
                    status = response.status if isinstance(response, Response) and type(response.status) is int and isinstance(response.headers, dict) else 0
                    adapter = AlpacaBarsAdapter(lambda *_: None, feed=q["feed"], offline=True, delay_cap=self.policy["fallback_cap_seconds"], jitter=self.jitter)
                    headers = {str(k).lower(): str(v) for k, v in response.headers.items()} if status else {}
                    if self.policy["verified_rate_headers"]:
                        try:
                            hint = int(headers.get("x-ratelimit-limit", ""))
                            if 0 < hint < self.policy["operating_limit"]:
                                self.store.connection.execute("UPDATE market_quota SET effective_limit=MIN(effective_limit,?) WHERE id=1", (hint,))
                        except ValueError:
                            pass
                        if headers.get("x-ratelimit-remaining") == "0":
                            delay = adapter._delay(headers, max(0, work["page_retries"] - 1), now=self.clock.wall(), verified_reset=True)
                            self.store.connection.execute("UPDATE market_quota SET cooldown=MAX(cooldown,?) WHERE id=1", (now + delay,))
                    # Admission can precede the actual send by an arbitrary OS pause.
                    # Receipt/exception is a conservative upper bound on that send:
                    # retain its rolling charge and pace the next attempt from here.
                    # A crash before this transaction remains charged and recovers
                    # behind the full persisted restart window.
                    self.store.connection.execute("UPDATE market_attempts SET outcome=?,settled=? WHERE sequence=?", (str(status) if status else "ambiguous", now, attempt_id))
                    limit = self.store.connection.execute("SELECT effective_limit FROM market_quota WHERE id=1").fetchone()[0]
                    self.store.connection.execute("UPDATE market_quota SET next_dispatch=MAX(next_dispatch,?) WHERE id=1", (now + max(1 / 3, 60 / limit),))
                    if status == 429:
                        work["throttles"] += 1
                    if status in AlpacaBarsAdapter.RETRYABLE or status == 0:
                        delay = adapter._delay(headers, max(0, work["page_retries"] - 1), now=self.clock.wall(), verified_reset=self.policy["verified_rate_headers"])
                        self.store.connection.execute("UPDATE market_quota SET cooldown=MAX(cooldown,?) WHERE id=1", (now + delay,))
                        work.update(status="deferred", reason="cooldown", not_before=not_before(self.clock.wall() + delay))
                        if work["page_retries"] > self.policy["max_retries"]:
                            work.update(status="failed", reason="retry_limit")
                        self._save(identifier, work)
                    elif status != 200:
                        work.update(status="failed", reason="entitlement" if status == 403 else "transport")
                        self._save(identifier, work)
                    else:
                        try:
                            bars, token = AlpacaBarsAdapter.parse_page(response, segment["symbols"], seen=work["seen_tokens"])
                            receipt = stamp(utc(response.received_at).timestamp())
                            if not q["freshness_after"] <= receipt <= q["information_cutoff"]:
                                raise ContractError("Receipt outside frozen information bounds")
                            records = []
                            for bar in bars:
                                event = stamp(utc(bar["t"]).timestamp())
                                if not segment["start"] <= event <= segment["end"] or event > receipt:
                                    raise ContractError("Observation outside query or receipt")
                                canonical(bar)
                                records.append(("observation:" + digest([compatibility(q), bar]), compatibility(q), bar["symbol"], event, receipt,
                                    canonical(dict(bar=bar, received_at=receipt, request_hash=digest([AlpacaBarsAdapter.BASE_URL, params])))))
                        except (ContractError, KeyError, TypeError, ValueError):
                            work.update(status="failed", reason="response"); self._save(identifier, work)
                            continue
                        for record in records:
                            self.store.connection.execute("INSERT OR IGNORE INTO market_observations VALUES(?,?,?,?,?,?)", record)
                        checkpoint = dict(request_hash=digest(params), next_page_token=token, observation_ids=[r[0] for r in records])
                        self.store.connection.execute("INSERT INTO market_pages VALUES(?,?,?,?)", (identifier, work["segment"], work["page_number"] + 1, canonical(checkpoint)))
                        work["pages"] += 1; work["page_number"] += 1; work["page_retries"] = 0
                        work["token"] = token
                        if token: work["seen_tokens"].append(token)
                        if token is None:
                            for symbol in segment["symbols"]:
                                self.store.connection.execute("INSERT OR IGNORE INTO market_windows VALUES(?,?,?,?)", (compatibility(q), symbol, segment["start"], segment["end"]))
                            work["segment"] += 1
                            work.update(token=None, page_number=0, seen_tokens=[])
                            if work["segment"] == len(work["segments"]):
                                self._finish(q, work)
                        if now >= work["deadline_logical"] or self.clock.wall() >= utc(work["deadline"]).timestamp():
                            work.update(status="expired", reason="deadline")
                        self._save(identifier, work)
                        if before_commit: before_commit()
                        committed += 1
            with self.db, self.store.transaction():
                _, work = self._work(identifier)
                if work["status"] not in {"complete", "incomplete", "failed", "expired"}:
                    work.update(status="deferred", reason="page_limit"); self._save(identifier, work)
        except Deferred:
            pass
        finally:
            self.dispatch.release()
        return self.telemetry(identifier)

    def usage(self):
        with self.db:
            return dict(quota_id=self.policy["quota_id"], physical_attempts=self.store.connection.execute("SELECT COUNT(*) FROM market_attempts").fetchone()[0],
                cooperating_callers_only=True, guarantee="Only cooperating callers in this principal's single bound store; unrelated account traffic is not controlled.")
