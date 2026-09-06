"""FIFO cash ledger and exact flow-neutral wealth, independent of v1 accounting."""
from copy import deepcopy
from decimal import Decimal as D, localcontext, ROUND_HALF_UP
from types import SimpleNamespace

from ..contracts import ContractError, utc
from ..risk import Governor

ZERO = D(0)
ONE = D(1)
CENT = D(".01")
RESIDUAL = D("1e-28")


def money(value):
    return D(value).quantize(CENT, rounding=ROUND_HALF_UP)


def allocation(total, quantity, remaining):
    return total if quantity == remaining else (total * quantity / remaining).quantize(RESIDUAL, rounding=ROUND_HALF_UP)


class Ledger:
    def __init__(self, portfolio, plan, lookup, risk_event_ids=()):
        self.portfolio, self.plan, self.lookup = portfolio, plan, lookup
        self.policy = lookup(portfolio["policy_id"])
        self.governor = Governor(self.policy)
        self.risk_event_ids = set(risk_event_ids)
        self.cash = self.initial = self.external = self.realized = self.income = self.fees = self.expenses = ZERO
        self.lots, self.reliefs, self.orders, self.reservations, self.entitlements = [], [], {}, {}, {}
        self.marks, self.mark_ids, self.actions, self.used_flows, self.fills_seen = {}, {}, set(), set(), {}
        self.segment = None
        self.ended = False
        self.closed_segments, self.history, self.closed_groups = [], [], []
        self.fill_gains, self.trade_fill_ids = {}, {}
        self.trade_gains = {}
        self.factor, self.start_nav, self.wealth_peak, self.day_wealth = ONE, None, ONE, ONE
        self.max_dd, self.traded = ZERO, ZERO
        self.return_gap = self.schedule_gap = False
        self.halted, self.gaps = False, set()
        self.session = None
        self.submissions, self.fill_counts, self.turnover = {}, {}, {}
        self.at = None
        self.last_segment_return = None

    @property
    def closed_gains(self):
        return [sum((self.fill_gains[i] for i in ids), ZERO) for ids in self.closed_groups]

    @property
    def positions(self):
        values = {}
        for lot in self.lots:
            values[lot["instrument"]] = values.get(lot["instrument"], ZERO) + lot["quantity"]
        return values

    @property
    def basis(self):
        return sum((l["basis"] for l in self.lots), ZERO)

    @property
    def reserved(self):
        return sum((r["cash"] for r in self.reservations.values()), ZERO)

    @property
    def receivable(self):
        return sum((e["remaining"] for e in self.entitlements.values()), ZERO)

    def eligible_mark(self, key, at=None):
        mark = self.marks.get(key)
        if not mark or mark["status"] != "eligible" or mark["adjustment"] != "raw":
            return None
        age = (utc(at or self.at) - utc(mark["event_at"])).total_seconds()
        return mark if 0 <= age <= self.plan["max_mark_age_seconds"] else None

    def equity(self):
        if self.gaps:
            return None
        value = self.cash + self.receivable
        for key, q in self.positions.items():
            if q:
                mark = self.eligible_mark(key)
                if mark is None:
                    return None
                value += q * D(mark["price"])
        return value

    def wealth(self):
        nav = self.equity()
        if self.ended or (self.start_nav == 0 and self.last_segment_return is not None):
            return self.last_segment_return
        return None if self.return_gap or nav is None or not self.start_nav or self.start_nav <= 0 else self.factor * nav / self.start_nav

    def sample(self, at):
        self.at = at
        nav, wealth = self.equity(), self.wealth()
        if self.initial == 0:
            return
        reason = None
        if nav is None or wealth is None:
            self.schedule_gap = True
            self.halted = True
            reason = "Missing eligible mark, flow-boundary NAV or reconciled accounting"
        if wealth is not None:
            self.wealth_peak = max(self.wealth_peak, wealth)
            dd = ONE - wealth / self.wealth_peak
            self.max_dd = max(self.max_dd, dd)
            if (self.day_wealth > 0 and (ONE - wealth / self.day_wealth) >= D(str(self.policy["limits"]["daily_loss"]))) or dd >= D(str(self.policy["limits"]["drawdown"])):
                self.halted = True
        else:
            dd = None
        self.history.append(dict(at=at, equity=nav, wealth=wealth, drawdown=dd, reason=reason))
        if wealth is not None:
            self.day_wealth = wealth

    def gap(self, reason):
        self.gaps.add(reason)
        self.halted = True

    def check_order(self, order, quantity, price, fee, terms, *, execution=False):
        day = self.at[:10]
        if self.portfolio["execution_basis"] == "paper_broker" and execution:
            # Actual attributed fills are evidence, even if they breach a risk limit.
            return
        if self.wealth() is None:
            raise ContractError("Unknown flow-neutral risk denominator")
        marks = {}
        for key in self.policy["universe"]:
            name = key["instrument_id"]
            mark = self.eligible_mark(name)
            if mark:
                marks[name] = dict(price=mark["price"], at=mark["event_at"], session=day, phase="close")
        pending = {}
        for oid, o in self.orders.items():
            held = [r for r in self.reservations.values() if r["order_id"] == oid]
            if o["remaining"] and o["status"] == "pending":
                pending[oid] = dict(o["record"], quantity=str(o["remaining"]), reserved=str(sum((r["cash"] for r in held), ZERO)),
                                    status="pending", price_cap=o["terms"]["price_cap"])
        wealth, nav = self.wealth(), self.equity()
        adapter = SimpleNamespace(positions=self.positions, cash=self.cash + self.receivable, orders=pending, marks=marks,
            halted=self.halted, fills=self.fill_counts, submissions=self.submissions, turnover=self.turnover,
            peak=nav * self.wealth_peak / wealth if wealth else nav,
            day_start=nav * self.day_wealth / wealth if wealth else nav, equity=self.equity)
        # Receivables contribute to NAV/exposure but are never buying power.
        adapter.cash = self.cash
        request = dict(order, quantity=str(quantity), expires_at=terms["expires_at"])
        reasons = self.governor.check(adapter, request, price=price, fee=fee, session=day, at=self.at,
            sessions=[day], expected_session=day, exclude_order=order["id"] if execution else None, execution=execution)
        if reasons:
            raise ContractError("Independent v2 governor rejected: " + ", ".join(reasons))

    def flow(self, e):
        p, kind = e["payload"], e["event_type"]
        grant = (e["segment_id"], kind, e["effective_at"], p["amount"])
        allowed = {(f["segment_id"], f["event_type"], f["effective_at"], f["amount"]) for f in self.plan["flows"]}
        if grant not in allowed or grant in self.used_flows:
            raise ContractError("Funding policy does not authorize this exact unused flow")
        amount = D(p["amount"])
        if kind == "funding":
            segment = self.lookup(e["segment_id"])
            if self.segment is None and amount != D(self.policy["limits"]["initial_cash"]):
                raise ContractError("Initial funding differs from the frozen policy capital")
            if self.segment is not None:
                if not self.ended or segment["previous_segment_id"] != self.segment:
                    raise ContractError("New funding needs an ended predecessor segment")
                saved_halt, saved_closed, used = self.halted, self.closed_segments, self.used_flows
                self.__init__(self.portfolio, self.plan, self.lookup, self.risk_event_ids)
                self.halted, self.closed_segments, self.used_flows = saved_halt, saved_closed, used
                self.at = e["effective_at"]
            if self.initial or self.cash or any(self.positions.values()):
                raise ContractError("Initial funding cannot overwrite a balance")
            self.segment = e["segment_id"]
            self.cash = self.initial = self.start_nav = amount
        else:
            if self.segment != e["segment_id"] or self.ended:
                raise ContractError("External flow requires its active funded segment")
            if self.start_nav == 0:
                raise ContractError("Refunding after full withdrawal requires a new funded segment")
            nav = self.equity()
            provided = set(p["boundary_mark_ids"])
            if nav is None or any(q and self.mark_ids.get(key) not in provided for key, q in self.positions.items()):
                self.return_gap = True
                self.halted = True
            elif self.start_nav and not self.return_gap:
                self.factor *= nav / self.start_nav
            delta = -amount if kind == "withdrawal" else amount
            if delta < 0 and amount > self.cash - self.reserved:
                raise ContractError("Withdrawal exceeds available cash")
            self.cash += delta
            self.external += delta
            self.start_nav = None if nav is None else nav + delta
            if self.start_nav == 0:
                if any(self.positions.values()) or self.receivable or self.reserved:
                    raise ContractError("Full withdrawal requires settled, unreserved cash")
                self.last_segment_return = None if self.return_gap else self.factor
        self.used_flows.add(grant)

    def apply(self, e, terms_by_order):
        p, kind, self.at = e["payload"], e["event_type"], e["effective_at"]
        if kind in {"funding", "contribution", "withdrawal"}:
            self.flow(e)
            return
        if self.segment is None or e["segment_id"] != self.segment or self.ended:
            if kind == "halt" and e["segment_id"] == self.segment:
                self.halted = True
                return
            raise ContractError("Event requires the active funded segment")
        if kind == "mark":
            self.marks[p["instrument_id"]] = dict(p)
            self.mark_ids[p["instrument_id"]] = e["id"]
        elif kind == "order":
            order = self.lookup(p["order_id"])
            if order["id"] in self.orders or order["id"] not in terms_by_order:
                raise ContractError("Duplicate order or missing frozen execution terms")
            terms = terms_by_order[order["id"]]
            if utc(order["created_at"]) > utc(e["effective_at"]) or utc(terms["created_at"]) > utc(e["observed_at"]):
                raise ContractError("Decision/terms unavailable at order admission")
            q = D(order["quantity"])
            if not self.plan["fractional_shares"] and q % 1:
                raise ContractError("Frozen plan requires whole-share orders")
            if e["id"] in self.risk_event_ids:
                self.check_order(order, q, D(terms["price_cap"]), money(q * D(self.plan["fee_per_share"])), terms)
            self.orders[order["id"]] = dict(record=order, remaining=q, filled=ZERO, status="pending", terms=terms)
            day = self.at[:10]
            self.submissions[day] = self.submissions.get(day, 0) + 1
        elif kind == "reservation":
            o = self.orders[p["order_id"]]
            cash, quantity = D(p["cash"]), D(p["quantity"])
            if any(r["order_id"] == p["order_id"] for r in self.reservations.values()):
                raise ContractError("Order already has a reservation")
            if cash > self.cash - self.reserved or quantity > self.positions.get(o["record"]["instrument_id"], ZERO) - sum((r["quantity"] for r in self.reservations.values() if self.orders[r["order_id"]]["record"]["instrument_id"] == o["record"]["instrument_id"]), ZERO):
                raise ContractError("Reservation exceeds uncommitted cash or shares")
            if (o["record"]["side"] == "buy" and quantity) or (o["record"]["side"] == "sell" and cash):
                raise ContractError("Reservation side mismatch")
            self.reservations[e["id"]] = dict(order_id=p["order_id"], cash=cash, quantity=quantity)
        elif kind == "release":
            r = self.reservations[p["reservation_id"]]
            if r["order_id"] != p["order_id"] or D(p["cash"]) > r["cash"] or D(p["quantity"]) > r["quantity"]:
                raise ContractError("Release exceeds its order reservation")
            r["cash"] -= D(p["cash"]); r["quantity"] -= D(p["quantity"])
            if p["reason"] in {"cancelled", "rejected", "expired"}:
                if r["cash"] or r["quantity"]:
                    raise ContractError("Cancellation must release all remaining reservation")
                self.orders[p["order_id"]]["status"] = p["reason"]
        elif kind == "fill":
            self.fill(e)
        elif kind == "fee":
            fee = D(p["amount"])
            if fee > self.cash - self.reserved:
                raise ContractError("Fee exceeds available cash")
            self.cash -= fee; self.fees += fee
            if p["allocation"] == "unallocated": self.expenses += fee
            elif p["allocation"] == "disposal":
                self.realized -= fee
                if p["fill_id"] not in self.fill_gains:
                    raise ContractError("Disposal fee requires an applied sale")
                self.fill_gains[p["fill_id"]] -= fee
                affected = [r for r in self.reliefs if r["sale_fill_id"] == p["fill_id"]]
                remaining_q, remaining_fee = sum((r["quantity"] for r in affected), ZERO), fee
                for relief in affected:
                    amount = allocation(remaining_fee, relief["quantity"], remaining_q)
                    relief["fees"] += amount; remaining_fee -= amount; remaining_q -= relief["quantity"]
            else:
                lot = next((l for l in self.lots if l["fill_id"] == p["fill_id"]), None)
                if lot is None or lot["quantity"] != lot["adjusted_quantity"]:
                    raise ContractError("Late acquisition fee after relief needs an explicit fill correction")
                lot["basis"] += fee; lot["original_basis"] += fee
        elif kind == "dividend_entitlement":
            from ..contracts import digest
            if p["policy_hash"] != digest(self.plan["corporate_actions"]):
                raise ContractError("Dividend policy differs from the frozen corporate-action plan")
            if p["action_id"] in self.actions or p["ex_at"] != self.at:
                raise ContractError("Duplicate dividend or inconsistent ex-date")
            key = p["instrument_id"]
            mark = self.lookup(p["mark_id"])
            if mark["effective_at"] != self.at or mark["payload"]["instrument_id"] != key or self.mark_ids.get(key) != p["mark_id"] or not self.eligible_mark(key):
                raise ContractError("Dividend needs an explicit eligible ex-date raw mark")
            if D(p["eligible_quantity"]) != self.positions.get(key, ZERO) or money(D(p["per_share"]) * D(p["eligible_quantity"])) != D(p["amount"]):
                raise ContractError("Dividend entitlement differs from eligible holdings")
            amount = D(p["amount"])
            self.entitlements[e["id"]] = dict(remaining=amount)
            self.income += amount; self.actions.add(p["action_id"])
        elif kind == "dividend_payment":
            entitlement = self.entitlements[p["entitlement_id"]]
            amount = D(p["amount"])
            if amount > entitlement["remaining"]:
                raise ContractError("Dividend payment exceeds unpaid entitlement")
            self.cash += amount; entitlement["remaining"] -= amount
        elif kind == "split":
            if p["action_id"] in self.actions:
                raise ContractError("Duplicate split")
            key, ratio = p["instrument_id"], D(p["numerator"]) / D(p["denominator"])
            pending = any(o["remaining"] and o["status"] == "pending" and o["record"]["instrument_id"] == key for o in self.orders.values())
            if pending:
                self.gap("Split with pending orders requires explicit cancellation/replacement reconciliation")
            mark = self.lookup(p["mark_id"])
            if mark["effective_at"] != self.at or mark["payload"]["instrument_id"] != key or self.mark_ids.get(key) != p["mark_id"]:
                raise ContractError("Split needs an explicit post-split mark")
            for lot in self.lots:
                if lot["instrument"] == key:
                    lot["quantity"] *= ratio; lot["adjusted_quantity"] *= ratio
                    lot["actions"].append(e["id"])
                    if not self.plan["fractional_shares"] and lot["quantity"] % 1:
                        self.gap("Fractional split cash-in-lieu unsupported; explicit settlement review required")
            self.actions.add(p["action_id"])
        elif kind == "cash_in_lieu":
            self.gap("Cash-in-lieu accounting unsupported; amount retained as evidence, never invented as cash")
        elif kind in {"halt", "reconciliation_gap"}:
            self.halted = True
            if kind == "reconciliation_gap": self.gap(p["reason"])
        elif kind == "segment_end":
            if self.cash or any(self.positions.values()) or self.receivable or self.reserved:
                raise ContractError("Cannot end a funded segment with unsettled assets")
            if self.last_segment_return is None:
                self.last_segment_return = self.wealth()
            self.ended = True
            self.closed_segments.append(dict(segment_id=self.segment, twr=None if self.last_segment_return is None else self.last_segment_return - 1,
                                             reason="Missing flow boundary" if self.last_segment_return is None else None))
        else:
            raise ContractError("Unsupported v2 reducer event")
        if self.cash < 0 or self.reserved > self.cash:
            if self.portfolio["execution_basis"] == "paper_broker": self.gap("Broker cash exceeds authorized funding")
            else: raise ContractError("Cash invariant violated")

    def fill(self, e):
        p, oid = e["payload"], e["payload"]["order_id"]
        o = self.orders[oid]
        quantity, notional, fee = D(p["quantity"]), D(p["notional"]), D(p["fees"])
        key, side, terms = p["instrument_id"], p["side"], o["terms"]
        if o["status"] != "pending" or quantity > o["remaining"] or p["incremental_fill_id"] in self.fills_seen:
            raise ContractError("Duplicate, excess or cancelled fill")
        if money(quantity * D(p["price"])) != notional:
            raise ContractError("Fill notional differs from price and quantity")
        if not self.plan["fractional_shares"] and quantity % 1:
            if self.portfolio["execution_basis"] == "paper_broker":
                self.gap("Broker fractional execution differs from the whole-share plan")
            else:
                raise ContractError("Frozen plan requires whole-share fills")
        # Validate new executions at admission. Later mark corrections must not
        # rewrite or reject fills already accepted using then-known evidence.
        if self.portfolio["execution_basis"] == "simulated" and e["id"] in self.risk_event_ids and not e.get("_corrected"):
            if not utc(terms["earliest_fill_at"]) <= utc(self.at) < utc(terms["expires_at"]):
                raise ContractError("Fill outside eligible execution interval")
            mark = self.eligible_mark(key)
            if mark is None or utc(mark["event_at"]) < utc(terms["earliest_fill_at"]):
                raise ContractError("Fill requires a new eligible raw market event")
            cost = (D(self.plan["slippage_bps"]) + D(self.plan["spread_bps"]) / 2) / 10000
            price = (D(mark["price"]) * (1 + cost if side == "buy" else 1 - cost)).quantize(D(".00000001"))
            if D(p["price"]) != price or fee != money(quantity * D(self.plan["fee_per_share"])):
                raise ContractError("Fill differs from frozen simulated price/fee model")
            if (side == "buy" and price > D(terms["price_cap"])) or (side == "sell" and price < D(terms["price_cap"])):
                raise ContractError("Execution violates order limit")
        if e["id"] in self.risk_event_ids:
            self.check_order(o["record"], quantity, D(p["price"]), fee, terms, execution=True)
        held = [r for r in self.reservations.values() if r["order_id"] == oid]
        if len(held) != 1:
            raise ContractError("Fill requires one order reservation")
        reservation = held[0]
        # Reservations remain spendable cents; FIFO basis retains finer residuals.
        released_cash = money(allocation(reservation["cash"], quantity, o["remaining"]))
        if side == "buy":
            if notional + fee > self.cash - self.reserved + released_cash and self.portfolio["execution_basis"] == "simulated":
                raise ContractError("Partial fill exceeds its available funding")
            self.cash -= notional + fee
            self.lots.append(dict(lot_id="lot:" + e["id"], fill_id=e["id"], order_id=oid, instrument=key, acquired_at=self.at,
                original_quantity=quantity, adjusted_quantity=quantity, quantity=quantity, original_basis=notional + fee,
                basis=notional + fee, actions=[]))
        else:
            if quantity > reservation["quantity"] or quantity > self.positions.get(key, ZERO):
                raise ContractError("Sale exceeds reserved owned shares")
            remaining, gain, remaining_proceeds, remaining_fee = quantity, ZERO, notional, fee
            for lot in self.lots:
                if lot["instrument"] != key or not lot["quantity"] or not remaining: continue
                take = min(remaining, lot["quantity"])
                basis = allocation(lot["basis"], take, lot["quantity"])
                proceeds, disposal_fee = allocation(remaining_proceeds, take, remaining), allocation(remaining_fee, take, remaining)
                lot["quantity"] -= take; lot["basis"] -= basis
                self.reliefs.append(dict(sale_fill_id=e["id"], lot_id=lot["lot_id"], quantity=take, basis=basis, proceeds=proceeds, fees=disposal_fee))
                gain += proceeds - disposal_fee - basis
                remaining -= take; remaining_proceeds -= proceeds; remaining_fee -= disposal_fee
            self.cash += notional - fee; self.realized += gain
            self.fill_gains[e["id"]] = gain
            self.trade_fill_ids.setdefault(key, []).append(e["id"])
            self.trade_gains[key] = self.trade_gains.get(key, ZERO) + gain
            if not self.positions.get(key, ZERO): self.closed_groups.append(self.trade_fill_ids.pop(key))
        self.fees += fee; self.traded += notional
        reservation["cash"] -= released_cash
        reservation["quantity"] -= quantity if side == "sell" else ZERO
        o["remaining"] -= quantity; o["filled"] += quantity
        if not o["remaining"]:
            o["status"] = "filled"; reservation["cash"] = reservation["quantity"] = ZERO
        self.fills_seen[p["incremental_fill_id"]] = e["id"]
        day = self.at[:10]
        self.fill_counts[day] = self.fill_counts.get(day, 0) + 1
        self.turnover[day] = self.turnover.get(day, ZERO) + notional


def replay(portfolio, plan, records, lookup, *, effective_cutoff, receipt_cutoff, terms, risk_event_ids=()):
    """Two cutoffs preserve as-known reports; corrections restate only explicit targets."""
    selected = [r for r in records if utc(r["effective_at"]) <= utc(effective_cutoff) and utc(r["observed_at"]) <= utc(receipt_cutoff)]
    replacements, replacement_ids = {}, set()
    by_id = {r["id"]: r for r in selected}
    for correction in sorted((r for r in selected if r["event_type"] == "correction"), key=lambda r: r["sequence"]):
        p = correction["payload"]
        if p["corrects_id"] not in by_id: raise ContractError("Correction source unavailable at cutoff")
        target = by_id[p["corrects_id"]]
        if p["replacement_id"]:
            if p["replacement_id"] not in by_id: raise ContractError("Correction replacement unavailable")
            replacement = deepcopy(by_id[p["replacement_id"]])
            if replacement["effective_at"] != target["effective_at"]:
                raise ContractError("Correction replacement must retain target effective time")
            replacement_ids.add(replacement["id"])
        else:
            replacement = deepcopy(target)
            if target["event_type"] == "mark": replacement["payload"].update(price=None, status="missing", reason="Source correction withdrew mark")
            else: replacement.update(event_type="reconciliation_gap", payload=dict(reason="Unreplaced accounting correction", evidence_hash=correction["provenance"]["source_hash"]))
        replacement["sequence"] = target["sequence"]
        replacement["_corrected"] = True
        replacements[target["id"]] = replacement
    events = []
    for record in selected:
        if record["event_type"] == "correction" or record["id"] in replacement_ids: continue
        current, seen = record, set()
        while current["id"] in replacements:
            if current["id"] in seen: raise ContractError("Cyclic correction lineage")
            seen.add(current["id"])
            replacement = replacements[current["id"]]
            if replacement["id"] == current["id"]:
                current = replacement
                break
            current = replacement
        current = dict(current, sequence=record["sequence"])
        events.append(current)
    events.sort(key=lambda r: (utc(r["effective_at"]), r["sequence"]))
    state = Ledger(portfolio, plan, lookup, risk_event_ids)
    if portfolio["initialization"] == "conversion_gap": state.gap("Legacy history needs separately reviewed accounting reconstruction")
    schedule = [at for at in plan["mark_schedule"] if utc(at) <= utc(effective_cutoff)]
    index = 0
    with localcontext() as ctx:
        ctx.prec = 50
        for at in sorted(set(schedule + [effective_cutoff]), key=utc):
            while index < len(events) and utc(events[index]["effective_at"]) <= utc(at):
                state.apply(events[index], terms)
                index += 1
            state.sample(at)
        nav = state.equity()
        if nav is not None and state.initial:
            unrealized = nav - state.cash - state.receivable - state.basis
            if abs(nav - state.initial - state.external - state.realized - unrealized - state.income + state.expenses) > D("1e-24"):
                raise ContractError("V2 component P/L does not reconcile")
    return state, selected
