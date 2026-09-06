"""Explicit v2 persistence; no accounting reducer or submission transport."""

import json
import secrets
import sqlite3
from decimal import Decimal as D

from .contracts import ContractError, canonical, digest, utc
from .contracts_v2 import validate, validate_references
from .storage import Store, now


class V2Store(Store):
    schema_ceiling = 3

    def v2_record(self, identifier):
        row = self.connection.execute("SELECT body FROM v2_records WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise ContractError("V2 record not found")
        return json.loads(row[0])

    def iter_v2(self, *, experiment_id=None, portfolio_id=None, kind=None):
        query, values = "SELECT body FROM v2_records WHERE 1=1", []
        for key, value in (("experiment_id", experiment_id), ("portfolio_id", portfolio_id), ("record_type", kind)):
            if value is not None:
                query += f" AND {key}=?"
                values.append(value)
        for row in self.connection.execute(query + " ORDER BY sequence", values):
            yield json.loads(row[0])

    def put_v2(self, records):
        records = list(records)
        additions = {}
        for r in records:
            validate(r)
            if r["id"] in additions and additions[r["id"]] != r:
                raise ContractError("Conflicting v2 identity")
            if self.synthetic and r["contamination"] != "fixture":
                raise ContractError("Synthetic storage requires fixture evidence")
            additions[r["id"]] = r
        with self.transaction():
            def lookup(identifier):
                return additions[identifier] if identifier in additions else self.v2_record(identifier)
            for r in additions.values():
                validate_references(r, lookup)
                old = self.connection.execute("SELECT body FROM v2_records WHERE id=?", (r["id"],)).fetchone()
                if old:
                    if canonical(r) != old[0]:
                        raise ContractError("Immutable v2 identity conflict")
                    continue
                if r["record_type"] == "submission_mapping":
                    initial = [o for o in additions.values() if o["record_type"] == "outbox" and o["mapping_id"] == r["id"] and o["revision"] == 1]
                    if len(initial) != 1:
                        raise ContractError("Mapping and initial outbox must be committed atomically")
                tip = self.connection.execute("SELECT content_hash FROM v2_records ORDER BY sequence DESC LIMIT 1").fetchone()
                previous_hash = tip[0] if tip else "0" * 64
                try:
                    self.connection.execute("INSERT INTO v2_records(id,record_type,experiment_id,portfolio_id,body,previous_hash,content_hash) VALUES (?,?,?,?,?,?,?)",
                        (r["id"], r["record_type"], r["experiment_id"], r.get("portfolio_id"), canonical(r), previous_hash,
                         digest(dict(record=r, previous_hash=previous_hash))))
                except sqlite3.IntegrityError as exc:
                    raise ContractError("Duplicate or conflicting v2 identity constraint") from exc
            # Check cumulative updates after the full atomic batch is visible.
            for r in additions.values():
                if r["record_type"] == "broker_update":
                    self._check_update(r)

    def _check_update(self, record):
        mapping_id = record["mapping_id"]
        try:
            self.connection.execute("INSERT OR IGNORE INTO v2_broker_bindings VALUES (?,?)", (mapping_id, record["broker_order_id"]))
        except sqlite3.IntegrityError as exc:
            raise ContractError("Conflicting broker binding") from exc
        bound = self.connection.execute("SELECT broker_order_id FROM v2_broker_bindings WHERE mapping_id=?", (mapping_id,)).fetchone()
        if bound is None or bound[0] != record["broker_order_id"]:
            raise ContractError("Unknown replacement or reused broker ID")
        updates = [r for r in self.iter_v2(portfolio_id=record["portfolio_id"], kind="broker_update") if r["mapping_id"] == mapping_id]
        updates.sort(key=lambda r: (utc(r["effective_at"]), utc(r["observed_at"]), r["provider_event_id"]))
        prior = (D(0), D(0), D(0))
        for update in updates:
            current = tuple(D(update[k]) for k in ("cumulative_quantity", "cumulative_notional", "cumulative_fees"))
            if any(a < b for a, b in zip(current, prior)):
                raise ContractError("Decreasing cumulative broker update requires reconciliation")
            prior = current

    def record_update(self, record):
        """Quarantine a hash and fixed reason, never propagate an invalid payload."""
        try:
            if record.get("record_type") != "broker_update":
                raise ContractError("Expected broker update")
            self.put_v2([record])
            return "accepted"
        except ContractError:
            with self.transaction():
                self.connection.execute("INSERT OR IGNORE INTO v2_quarantine VALUES (?,?,?)",
                    (digest(record), "broker_update_requires_reconciliation", now()))
            return "quarantined"

    def prepare_submission(self, order_id, *, at):
        """Persist an opaque identity and outbox only. Never contacts a broker."""
        with self.transaction():
            existing = self.connection.execute("SELECT body FROM v2_records WHERE record_type='submission_mapping' AND json_extract(body, '$.internal_order_id')=?", (order_id,)).fetchone()
            if existing:
                return json.loads(existing[0])
            order = self.v2_record(order_id)
            if order["record_type"] != "order":
                raise ContractError("Submission requires internal order")
            common = {k: order[k] for k in ("schema_version", "experiment_id", "portfolio_id", "segment_id", "contamination", "provenance")}
            common.update(created_at=at, field_class="private_attribution")
            mapping = dict(common, id="mapping:" + digest(order_id), record_type="submission_mapping",
                           internal_order_id=order_id, client_order_id=secrets.token_hex(16), policy_approval_ref=order["policy_approval_ref"])
            outbox = dict(common, id="outbox:" + digest(order_id), record_type="outbox", mapping_id=mapping["id"],
                          internal_order_id=order_id, state="prepared", revision=1, previous_outbox_id=None,
                          request_hash=digest(order), action="submit_once")
            self.put_v2([mapping, outbox])
            return mapping

    def verify_v2(self):
        previous, count = "0" * 64, 0
        for row in self.connection.execute("SELECT * FROM v2_records ORDER BY sequence"):
            record = json.loads(row["body"])
            validate_references(record, self.v2_record)
            if (row["id"], row["record_type"], row["experiment_id"], row["portfolio_id"]) != (record["id"], record["record_type"], record["experiment_id"], record.get("portfolio_id")):
                raise ContractError("V2 storage identity mismatch")
            if row["previous_hash"] != previous or digest(dict(record=record, previous_hash=previous)) != row["content_hash"]:
                raise ContractError("V2 hash chain mismatch")
            previous, count = row["content_hash"], count + 1
        return dict(records=count, tip=previous)

    def verify(self):
        return dict(v1=super().verify(), v2=self.verify_v2())
