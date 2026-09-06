"""Explicit offline v2 commands. Immutable ledger effects; no submission transport."""
from copy import deepcopy
from decimal import Decimal as D

from ...contracts import ContractError, digest, utc
from ...contracts_v2 import CLASSES
from ...evaluate.ledger_v2 import money, replay


class SimulatorV2:
    def __init__(self, store, portfolio_id):
        self.store, self.portfolio_id = store, portfolio_id
        self.portfolio = store.v2_record(portfolio_id)
        plans = list(store.iter_v2(portfolio_id=portfolio_id, kind="accounting_plan"))
        if len(plans) != 1:
            raise ContractError("One frozen accounting/funding plan is required")
        self.plan = plans[0]

    def record(self, kind, identifier, at, **fields):
        p = self.portfolio
        return dict(id=identifier, schema_version=2, record_type=kind, experiment_id=p["experiment_id"],
            created_at=at, contamination=p["contamination"], field_class=CLASSES[kind], provenance=deepcopy(p["provenance"]), **fields)

    def event(self, identifier, kind, effective_at, *, observed_at=None, segment_id=None, **payload):
        sequence = self.store.connection.execute("SELECT COALESCE(MAX(json_extract(body,'$.sequence')),0)+1 FROM v2_records WHERE record_type='ledger_event' AND portfolio_id=?", (self.portfolio_id,)).fetchone()[0]
        if segment_id is None:
            segments = list(self.store.iter_v2(portfolio_id=self.portfolio_id, kind="funded_segment"))
            eligible = [s for s in segments if utc(s["start_at"]) <= utc(effective_at)]
            if not eligible: raise ContractError("Register a funded segment first")
            segment_id = max(eligible, key=lambda s: s["ordinal"])["id"]
        return self.record("ledger_event", identifier, observed_at or effective_at, portfolio_id=self.portfolio_id, segment_id=segment_id,
            idempotency_key=identifier, sequence=sequence, effective_at=effective_at, observed_at=observed_at or effective_at,
            event_type=kind, payload=payload)

    def state(self, *, effective_cutoff, receipt_cutoff, risk_event_ids=()):
        terms = {t["order_id"]: t for t in self.store.iter_v2(portfolio_id=self.portfolio_id, kind="execution_terms")}
        events = list(self.store.iter_v2(portfolio_id=self.portfolio_id, kind="ledger_event"))
        for event in events:
            if utc(event["effective_at"]) <= utc(effective_cutoff) and utc(event["observed_at"]) <= utc(receipt_cutoff):
                rights = self.store.v2_record(event["provenance"]["rights_id"])
                if rights["private_replay"] != "permitted":
                    raise ContractError("Source rights do not permit private accounting replay")
        return replay(self.portfolio, self.plan, events, self.store.v2_record, effective_cutoff=effective_cutoff,
                      receipt_cutoff=receipt_cutoff, terms=terms, risk_event_ids=risk_event_ids)

    def command(self, identifier, records, *, before_commit=None):
        records = list(records)
        input_hash = digest(records)
        with self.store.transaction():
            prior = self.store.connection.execute("SELECT body FROM v2_records WHERE id=?", (identifier,)).fetchone()
            if prior:
                command = self.store.v2_record(identifier)
                if command["record_type"] != "execution_command" or command["portfolio_id"] != self.portfolio_id or command["input_hash"] != input_hash:
                    raise ContractError("Command identity conflicts with saved inputs")
                return command
            if not records or any(r.get("portfolio_id") != self.portfolio_id for r in records):
                raise ContractError("Command records must belong to one portfolio")
            allowed = {"ledger_event", "decision", "order", "execution_terms", "funded_segment", "operating_expense"}
            if any(r["record_type"] not in allowed for r in records):
                raise ContractError("Unsupported execution command record")
            self.store.put_v2(records)
            events = [r for r in records if r["record_type"] == "ledger_event"]
            all_events = list(self.store.iter_v2(portfolio_id=self.portfolio_id, kind="ledger_event"))
            if not all_events: raise ContractError("Command needs funded history")
            cutoff = max((r["effective_at"] for r in all_events), key=utc)
            receipt = max((r["created_at"] for r in records + all_events), key=utc)
            if self.portfolio["execution_basis"] == "paper_broker":
                for e in events:
                    if e["event_type"] == "fill":
                        updates = [self.store.v2_record(i) for i in e["provenance"]["source_event_ids"]]
                        if len(updates) != 1 or updates[0]["record_type"] != "broker_update" or updates[0]["portfolio_id"] != self.portfolio_id:
                            raise ContractError("Paper fill requires one attributable stored broker update")
                        update = updates[0]
                        mapping = self.store.v2_record(update["mapping_id"])
                        if mapping["internal_order_id"] != e["payload"]["order_id"] or update["effective_at"] != e["effective_at"] or utc(update["observed_at"]) > utc(e["observed_at"]):
                            raise ContractError("Paper fill differs from its originating order/update timing")
                        if D(e["payload"]["quantity"]) > D(update["cumulative_quantity"]):
                            raise ContractError("Paper fill exceeds confirmed cumulative quantity")
            correction_replacements = {e["payload"]["replacement_id"] for e in events if e["event_type"] == "correction"}
            state, _ = self.state(effective_cutoff=cutoff, receipt_cutoff=receipt, risk_event_ids=[e["id"] for e in events if e["id"] not in correction_replacements])
            if state.halted and not any(e["event_type"] == "halt" for e in all_events):
                halt = self.event("risk-halt:" + digest(identifier), "halt", cutoff, observed_at=receipt, segment_id=state.segment,
                                  reason="Durable risk/data halt; later flows or corrections cannot clear it")
                halt["provenance"].update(source_event_ids=[identifier], source_hash=input_hash)
                self.store.put_v2([halt])
            command = self.record("execution_command", identifier, receipt, portfolio_id=self.portfolio_id, input_hash=input_hash,
                                  record_ids=[r["id"] for r in records], result_hash=digest(dict(cash=str(state.cash), halted=state.halted, segment=state.segment)))
            self.store.put_v2([command])
            if before_commit: before_commit()
            return command

    def fill_order(self, command_id, order_id, mark_id, quantity, *, at, before_commit=None):
        """Apply a deterministic fill only when the caller explicitly advances a market event."""
        if self.portfolio["execution_basis"] != "simulated":
            raise ContractError("Paper fills enter through offline reconciliation")
        old = self.store.connection.execute("SELECT 1 FROM v2_records WHERE id=?", (command_id,)).fetchone()
        identity = "fill-event:" + digest([command_id, order_id, mark_id, quantity, at])
        if old:
            saved = self.store.v2_record(command_id)
            if saved["record_ids"] != [identity]: raise ContractError("Fill retry inputs changed")
            return saved
        order, mark = self.store.v2_record(order_id), self.store.v2_record(mark_id)
        if mark["portfolio_id"] != self.portfolio_id or mark["payload"]["instrument_id"] != order["instrument_id"] or mark["event_type"] != "mark":
            raise ContractError("Fill mark scope mismatch")
        cost = (D(self.plan["slippage_bps"]) + D(self.plan["spread_bps"]) / 2) / 10000
        price = (D(mark["payload"]["price"]) * (1 + cost if order["side"] == "buy" else 1 - cost)).quantize(D(".00000001"))
        event = self.event(identity, "fill", at, segment_id=order["segment_id"], order_id=order_id,
            instrument_id=order["instrument_id"], side=order["side"], quantity=quantity, price=str(price),
            notional=str(money(D(quantity) * price)), fees=str(money(D(quantity) * D(self.plan["fee_per_share"]))),
            fee_treatment="included", incremental_fill_id="increment:" + digest(identity))
        return self.command(command_id, [event], before_commit=before_commit)

    def correct(self, command_id, target_id, payload, *, observed_at):
        existing = self.store.connection.execute("SELECT 1 FROM v2_records WHERE id=?", (command_id,)).fetchone()
        request_hash = digest([target_id, payload, observed_at])
        replacement_id = "replacement:" + request_hash
        correction_id = "correction:" + request_hash
        if existing:
            old = self.store.v2_record(command_id)
            expected = ([replacement_id] if payload is not None else []) + [correction_id]
            if old["record_ids"] != expected: raise ContractError("Correction inputs changed")
            return old
        target = self.store.v2_record(target_id)
        if target["portfolio_id"] != self.portfolio_id or target["record_type"] != "ledger_event":
            raise ContractError("Correction target scope mismatch")
        records = []
        if payload is not None:
            replacement = self.event(replacement_id, target["event_type"], target["effective_at"], observed_at=observed_at,
                                     segment_id=target["segment_id"], **payload)
            replacement["provenance"] = deepcopy(target["provenance"])
            if target["event_type"] == "fill":
                replacement["payload"]["incremental_fill_id"] = "corrected-fill:" + request_hash
            records.append(replacement)
        correction = self.event(correction_id, "correction", target["effective_at"], observed_at=observed_at,
            segment_id=target["segment_id"], corrects_id=target_id, replacement_id=replacement_id if payload is not None else None,
            reason="Explicit source correction", projection_revision=1 + len(list(self.store.iter_v2(portfolio_id=self.portfolio_id, kind="projection"))))
        correction["sequence"] += len(records)
        records.append(correction)
        return self.command(command_id, records)
