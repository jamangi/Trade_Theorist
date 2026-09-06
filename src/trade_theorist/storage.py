"""Private SQLite single-writer store with immutable records and hash-chained events."""

from contextlib import contextmanager
from datetime import datetime, timezone
from importlib.resources import files
import json
import os
from pathlib import Path
import sqlite3

from jsonschema import Draft202012Validator, FormatChecker

from .contracts import ContractError, canonical, digest, validate_bundle
from .schema import ID, UTC


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def private_root(path=None, *, synthetic=False):
    configured = path or os.environ.get("TRADE_THEORIST_DATA_ROOT")
    if not configured:
        raise ValueError("Set TRADE_THEORIST_DATA_ROOT to an absolute private directory outside Git")
    root = Path(configured).expanduser()
    if not root.is_absolute():
        raise ValueError("Private data root must be absolute")
    root = root.resolve()
    if not synthetic and any((ancestor / ".git").exists() for ancestor in (root, *root.parents)):
        raise ValueError("Private data root must be outside every Git checkout")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    return root


class Store:
    def __init__(self, root=None, *, synthetic=False):
        self.root = private_root(root, synthetic=synthetic)
        self.synthetic = synthetic
        self.path = self.root / "research.sqlite3"
        self.connection = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        self._depth = 0
        try:
            self._migrate()
        except BaseException:
            self.close()
            raise

    def _migrate(self):
        with self.transaction():
            self.connection.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, content_hash TEXT NOT NULL)")
            installed = dict(self.connection.execute("SELECT version, content_hash FROM schema_migrations"))
            migrations = sorted(files("trade_theorist").joinpath("migrations").iterdir(), key=lambda p: p.name)
            known = {int(p.name.split("_")[0]) for p in migrations if p.name.endswith(".sql")}
            if set(installed) - known:
                raise ContractError("Database version is newer than this application")
            for migration in migrations:
                if not migration.name.endswith(".sql"):
                    continue
                version = int(migration.name.split("_")[0])
                sql = migration.read_text(encoding="utf-8")
                checksum = digest(sql)
                if version in installed:
                    if installed[version] != checksum:
                        raise ContractError("Installed migration checksum mismatch")
                    continue
                statement = ""
                for line in sql.splitlines(keepends=True):
                    statement += line
                    if sqlite3.complete_statement(statement):
                        self.connection.execute(statement)
                        statement = ""
                if statement.strip():
                    raise ContractError("Incomplete migration")
                self.connection.execute("INSERT INTO schema_migrations VALUES (?, ?)", (version, checksum))

    @contextmanager
    def transaction(self):
        nested = self._depth > 0
        savepoint = f"nested_{self._depth}"
        self.connection.execute(f"SAVEPOINT {savepoint}" if nested else "BEGIN IMMEDIATE")
        self._depth += 1
        try:
            yield self
            self.connection.execute(f"RELEASE {savepoint}" if nested else "COMMIT")
        except BaseException:
            self.connection.execute(f"ROLLBACK TO {savepoint}" if nested else "ROLLBACK")
            if nested:
                self.connection.execute(f"RELEASE {savepoint}")
            raise
        finally:
            self._depth -= 1

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def records(self):
        return [json.loads(row[0]) for row in self.connection.execute("SELECT body FROM records ORDER BY id")]

    def record(self, identifier, kind=None):
        """Read one immutable record without loading the library or learning history."""
        row = self.connection.execute("SELECT body FROM records WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise ContractError("Record not found")
        record = json.loads(row[0])
        if kind is not None and record["record_type"] != kind:
            raise ContractError("Unexpected record type")
        return record

    def put_records(self, records):
        records = list(records)
        with self.transaction():
            existing = {r["id"]: r for r in self.records()}
            additions = {}
            for record in records:
                old = existing.get(record["id"], additions.get(record["id"]))
                if old is not None and canonical(old) != canonical(record):
                    raise ContractError("Record ID cannot be reused with different content")
                if self.synthetic and record["contamination"] != "fixture":
                    raise ContractError("Synthetic store accepts fixture records only")
                additions[record["id"]] = record
            validate_bundle({**existing, **additions}.values())
            for record in additions.values():
                if record["id"] not in existing:
                    self.connection.execute("INSERT INTO records VALUES (?, ?, ?, ?, ?)", (record["id"], record["record_type"], record["experiment_id"], canonical(record), digest(record)))

    def append(self, event_id, experiment_id, kind, payload, *, created_at=None):
        for identifier in (event_id, experiment_id, kind):
            if not Draft202012Validator(ID).is_valid(identifier):
                raise ContractError("Invalid event identity")
        canonical(payload)
        with self.transaction():
            previous = self.connection.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
            if previous:
                if previous["experiment_id"] != experiment_id or previous["kind"] != kind or previous["body"] != canonical(payload) or (created_at and previous["created_at"] != created_at):
                    raise ContractError("Event ID cannot be reused with different content")
                return previous["content_hash"]
            experiment = self.connection.execute("SELECT body FROM records WHERE id=? AND record_type IN ('experiment', 'learning_session')", (experiment_id,)).fetchone()
            if not experiment:
                raise ContractError("Event experiment must be registered")
            timestamp = created_at or now()
            if not Draft202012Validator(UTC, format_checker=FormatChecker()).is_valid(timestamp):
                raise ContractError("Event needs UTC timestamp")
            tip = self.connection.execute("SELECT content_hash FROM events ORDER BY sequence DESC LIMIT 1").fetchone()
            previous_hash = tip[0] if tip else "0" * 64
            envelope = dict(id=event_id, experiment_id=experiment_id, kind=kind, created_at=timestamp, payload=payload, previous_hash=previous_hash)
            content_hash = digest(envelope)
            self.connection.execute("INSERT INTO events(id,experiment_id,kind,created_at,body,previous_hash,content_hash) VALUES (?,?,?,?,?,?,?)", (event_id, experiment_id, kind, timestamp, canonical(payload), previous_hash, content_hash))
            return content_hash

    def events(self, experiment_id=None, kind=None):
        return list(self.iter_events(experiment_id, kind))

    def iter_events(self, experiment_id=None, kind=None, *, portfolio_id=None):
        """Stream events; optional portfolio filtering happens in SQLite."""
        query, values = "SELECT * FROM events WHERE 1=1", []
        for name, value in (("experiment_id", experiment_id), ("kind", kind)):
            if value is not None:
                query += f" AND {name}=?"
                values.append(value)
        if portfolio_id is not None:
            query += " AND json_extract(body, '$.portfolio_id')=?"
            values.append(portfolio_id)
        for row in self.connection.execute(query + " ORDER BY sequence", values):
            item = dict(row)
            item["payload"] = json.loads(item.pop("body"))
            yield item

    def verify(self):
        if self.connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ContractError("Database integrity failure")
        records = self.records()
        validate_bundle(records)
        for row in self.connection.execute("SELECT body, content_hash FROM records"):
            if digest(json.loads(row[0])) != row[1]:
                raise ContractError("Record hash mismatch")
        previous_hash = "0" * 64
        event_count = 0
        for event in self.iter_events():
            envelope = {k: event[k] for k in ("id", "experiment_id", "kind", "created_at", "payload", "previous_hash")}
            if event["previous_hash"] != previous_hash or digest(envelope) != event["content_hash"]:
                raise ContractError("Event hash chain mismatch")
            previous_hash = event["content_hash"]
            event_count += 1
        return {"records": len(records), "events": event_count, "tip": previous_hash}

    def replay(self, experiment_id, reducer, initial):
        self.verify()
        for event in self.iter_events(experiment_id):
            initial = reducer(initial, event)
        return initial

    def run_phase(self, run_id, experiment_id, phase, input_hash, operation):
        """Only deterministic local operations belong inside this writer transaction."""
        if not self.connection.execute("SELECT 1 FROM records WHERE id=? AND experiment_id=? AND record_type='run_manifest'", (run_id, experiment_id)).fetchone():
            raise ContractError("Phase requires a persisted run manifest")
        phase_id = "phase:" + digest([run_id, phase])
        try:
            with self.transaction():
                prior = [e for e in self.events(experiment_id, "phase.complete") if e["payload"]["phase_id"] == phase_id]
                if prior:
                    if prior[0]["payload"]["input_hash"] != input_hash:
                        raise ContractError("Phase inputs changed; create a new run")
                    return prior[0]["payload"]["output"]
                attempt = len([e for e in self.events(experiment_id, "phase.failed") if e["payload"]["phase_id"] == phase_id])
                self.append(f"{phase_id}:start:{attempt}", experiment_id, "phase.running", {"phase_id": phase_id, "input_hash": input_hash})
                output = operation(self)
                self.append(phase_id + ":complete", experiment_id, "phase.complete", {"phase_id": phase_id, "input_hash": input_hash, "output": output, "output_hash": digest(output)})
                return output
        except Exception:
            # Exceptions may contain secrets; persist a fixed public failure code.
            self.append("failure:" + digest([phase_id, now()]), experiment_id, "phase.failed", {"phase_id": phase_id, "failure": "operation_failed"})
            raise

    def backup(self, destination):
        destination = Path(destination).resolve()
        if not destination.is_relative_to(self.root) or destination == self.path.resolve():
            raise ValueError("Backup must be a new path under the private root")
        self.verify()
        with destination.open("xb"):
            pass
        target = sqlite3.connect(destination)
        try:
            self.connection.backup(target)
        finally:
            target.close()
        return destination

    @classmethod
    def restore(cls, backup, root, *, synthetic=False):
        destination_root = private_root(root, synthetic=synthetic)
        destination = destination_root / "research.sqlite3"
        with destination.open("xb"):
            pass
        source = sqlite3.connect(Path(backup).resolve().as_uri() + "?mode=ro", uri=True)
        target = sqlite3.connect(destination)
        try:
            source.backup(target)
        finally:
            source.close()
            target.close()
        restored = cls(destination_root, synthetic=synthetic)
        try:
            restored.verify()
        except BaseException:
            restored.close()
            raise
        return restored
