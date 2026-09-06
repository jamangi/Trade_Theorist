"""Offline broker evidence reconciliation. There is deliberately no HTTP/client transport."""
from copy import deepcopy
from decimal import Decimal as D

from ...contracts import ContractError, digest, utc
from .v2 import SimulatorV2


class BrokerReconcilerV2:
    def __init__(self, store, portfolio_id):
        self.engine = SimulatorV2(store, portfolio_id)
        self.store, self.portfolio_id = store, portfolio_id
        if self.engine.portfolio["mode"] != "council" or self.engine.portfolio["execution_basis"] != "paper_broker":
            raise ContractError("Offline broker evidence requires one Monarchy paper ledger")

    def halt(self, identifier, reason, at, evidence_hash):
        if self.store.connection.execute("SELECT 1 FROM v2_records WHERE id=?", (identifier,)).fetchone(): return
        e = self.engine.event(identifier, "reconciliation_gap", at, reason=reason, evidence_hash=evidence_hash)
        self.engine.command("halt-command:" + digest(identifier), [e])

    def update(self, update, *, before_commit=None):
        command_id = "broker-command:" + digest(update)
        if self.store.connection.execute("SELECT 1 FROM v2_records WHERE id=?", (command_id,)).fetchone():
            return "reused"
        at = update["observed_at"]
        if update.get("portfolio_id") != self.portfolio_id:
            raise ContractError("Broker update belongs to another portfolio")
        with self.store.transaction():
            status = self.store.record_update(update)
            if status == "quarantined":
                self.halt("broker-gap:" + digest(update), "Conflicting or unmapped broker update requires reconciliation", at, digest(update))
                return status
            mapping = self.store.v2_record(update["mapping_id"])
            oid = mapping["internal_order_id"]
            order = self.store.v2_record(oid)
            updates = [u for u in self.store.iter_v2(portfolio_id=self.portfolio_id, kind="broker_update") if u["mapping_id"] == mapping["id"]]
            updates.sort(key=lambda u: (utc(u["effective_at"]), utc(u["observed_at"]), u["provider_event_id"]))
            records, previous = [], (D(0), D(0), D(0))
            next_sequence = self.engine.event("event:sequence-probe", "halt", at, reason="probe")["sequence"]
            def append(event):
                event["sequence"] = next_sequence + len(records)
                records.append(event)
            corrections = {e["payload"]["corrects_id"]: e["payload"]["replacement_id"] for e in self.store.iter_v2(portfolio_id=self.portfolio_id, kind="ledger_event") if e["event_type"] == "correction"}
            try:
                for u in updates:
                    cumulative = tuple(D(u[k]) for k in ("cumulative_quantity", "cumulative_notional", "cumulative_fees"))
                    quantity, notional, fee = tuple(a - b for a, b in zip(cumulative, previous))
                    previous = cumulative
                    if quantity == 0:
                        if notional or fee: raise ContractError("Fee/notional-only broker correction needs explicit review")
                        continue
                    if quantity < 0 or notional <= 0 or fee < 0:
                        raise ContractError("Invalid incremental broker fill")
                    identifier = "broker-fill:" + digest(u["id"])
                    payload = dict(order_id=oid, instrument_id=order["instrument_id"], side=order["side"], quantity=str(quantity),
                        price=format((notional / quantity).quantize(D(".00000001")), "f"), notional=format(notional, ".2f"),
                        fees=format(fee, ".2f"), fee_treatment="included", incremental_fill_id="increment:" + digest(u["id"]))
                    prior = self.store.connection.execute("SELECT 1 FROM v2_records WHERE id=?", (identifier,)).fetchone()
                    latest_id = identifier
                    while latest_id in corrections and corrections[latest_id]: latest_id = corrections[latest_id]
                    if prior:
                        old = self.store.v2_record(latest_id)
                        comparable = {k: v for k, v in old["payload"].items() if k != "incremental_fill_id"}
                        if comparable == {k: v for k, v in payload.items() if k != "incremental_fill_id"}: continue
                        identifier = "broker-restated:" + digest([u["id"], update["id"]])
                        payload["incremental_fill_id"] = "increment:" + digest(identifier)
                    fill = self.engine.event(identifier, "fill", u["effective_at"], observed_at=at, segment_id=order["segment_id"], **payload)
                    fill["provenance"] = dict(rights_id=update["provenance"]["rights_id"], source_event_ids=[u["id"]], source_hash=digest(u))
                    append(fill)
                    if prior:
                        correction = self.engine.event("broker-correction:" + digest([latest_id, update["id"]]), "correction", u["effective_at"], observed_at=at,
                            segment_id=order["segment_id"], corrects_id=latest_id, replacement_id=identifier,
                            reason="Earlier broker observation refines cumulative fill attribution", projection_revision=1 + len(list(self.store.iter_v2(portfolio_id=self.portfolio_id, kind="projection"))))
                        append(correction)
                # A savepoint permits preserving valid raw updates when derived effects need review.
                with self.store.transaction():
                    self.store.put_v2(records)
                    cutoff = max((e["effective_at"] for e in self.store.iter_v2(portfolio_id=self.portfolio_id, kind="ledger_event")), key=utc)
                    state, _ = self.engine.state(effective_cutoff=cutoff, receipt_cutoff=at)
                    latest = updates[-1]
                    if latest["status"] in {"cancelled", "rejected"}:
                        held = [(rid, r) for rid, r in state.reservations.items() if r["order_id"] == oid]
                        if held and state.orders[oid]["status"] == "pending":
                            rid, r = held[0]
                            release = self.engine.event("broker-release:" + digest(latest["id"]), "release", latest["effective_at"], observed_at=at,
                                segment_id=order["segment_id"], order_id=oid, reservation_id=rid, cash=format(r["cash"], ".2f"), quantity=str(r["quantity"]), reason=latest["status"])
                            records.append(release)
                    if not records:
                        command = self.engine.record("execution_command", command_id, at, portfolio_id=self.portfolio_id,
                            input_hash=digest(update), record_ids=[], result_hash=digest(update))
                        self.store.put_v2([command])
                    else:
                        self.engine.command(command_id, records, before_commit=before_commit)
                    outboxes = [o for o in self.store.iter_v2(portfolio_id=self.portfolio_id, kind="outbox") if o["mapping_id"] == mapping["id"]]
                    old = max(outboxes, key=lambda o: o["revision"])
                    new = deepcopy(old)
                    new.update(id="outbox-update:" + digest(update), created_at=at, revision=old["revision"] + 1, previous_outbox_id=old["id"],
                        state=latest["status"] if latest["status"] in {"cancelled", "rejected", "unknown"} else "acknowledged")
                    self.store.put_v2([new])
            except ContractError:
                self.halt("broker-derived-gap:" + digest(update), "Broker attribution needs explicit correction or reconciliation", at, digest(update))
                return "halted"
            return "applied"

    def timeout(self, order_id, *, at):
        mappings = [m for m in self.store.iter_v2(portfolio_id=self.portfolio_id, kind="submission_mapping") if m["internal_order_id"] == order_id]
        if len(mappings) != 1: raise ContractError("Timeout requires one existing submission identity")
        mapping = mappings[0]
        identifier = "timeout:" + digest([order_id, at])
        if self.store.connection.execute("SELECT 1 FROM v2_records WHERE id=?", (identifier,)).fetchone(): return
        with self.store.transaction():
            old = max((o for o in self.store.iter_v2(portfolio_id=self.portfolio_id, kind="outbox") if o["mapping_id"] == mapping["id"]), key=lambda o: o["revision"])
            update = dict(old, id=identifier, created_at=at, state="unknown", revision=old["revision"] + 1, previous_outbox_id=old["id"])
            self.store.put_v2([update])
            self.halt("timeout-gap:" + digest(identifier), "Unknown submission outcome; reservation retained and no resubmission allowed", at, digest(update))

    def account(self, identifier, *, effective_at, observed_at, cash, positions, reset=False, evidence_hash):
        if self.store.connection.execute("SELECT 1 FROM v2_records WHERE id=?", (identifier,)).fetchone():
            existing = self.store.v2_record(identifier)
            expected = (effective_at, observed_at, cash, positions, reset, evidence_hash)
            actual = tuple(existing[k] for k in ("effective_at", "observed_at", "broker_cash", "broker_positions", "account_reset", "evidence_hash"))
            if actual != expected: raise ContractError("Conflicting aggregate evidence identity")
            return existing
        with self.store.transaction():
            state, _ = self.engine.state(effective_cutoff=effective_at, receipt_cutoff=observed_at)
            quantities = {p["instrument_id"]: D(p["quantity"]) for p in positions if D(p["quantity"])}
            differences = []
            if D(cash) != state.cash: differences.append("Unexplained broker/economic cash difference (including possible distribution omissions)")
            if quantities != {k: q for k, q in state.positions.items() if q}: differences.append("Unattributed aggregate positions")
            if reset: differences.append("Broker account reset needs a new owner-reviewed funding/reconciliation decision")
            report = self.engine.record("account_reconciliation", identifier, observed_at, portfolio_id=self.portfolio_id, segment_id=state.segment,
                effective_at=effective_at, observed_at=observed_at, evidence_hash=evidence_hash, broker_cash=cash, economic_cash=str(state.cash),
                broker_positions=positions, account_reset=reset, status="halted" if differences else "matched", differences=differences)
            self.store.put_v2([report])
            if differences: self.halt("account-gap:" + digest(identifier), "; ".join(differences), observed_at, evidence_hash)
            return report
