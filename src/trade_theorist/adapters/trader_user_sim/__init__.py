"""Versioned, event-derived daily-bar simulation with an independent governor.

The trusted runner supplies normalized market evidence and an explicit UTC session
schedule. Recommendations are read by ID from the immutable store, never executed
as instructions. No broker, quote, live endpoint, or automatic promotion exists.
"""

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
import json

from ...contracts import ContractError, digest, utc, validate
from ...risk import Governor, validate_policy

D = Decimal
ZERO = D("0")
VERSION = "raw-next-open-ledger-v1"


def decimal(value, *, positive=False):
    if not isinstance(value, str):
        raise ContractError("Decimal inputs must be strings")
    try:
        number = D(value)
    except ArithmeticError as exc:
        raise ContractError("Invalid decimal") from exc
    if not number.is_finite() or number < 0 or (positive and number == 0) or number.as_tuple().exponent < -8:
        raise ContractError("Decimal must be finite, nonnegative and at most eight places")
    return number


def money(value):
    return value.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def timestamp(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ContractError("UTC timestamp required")
    try:
        return utc(value)
    except ValueError as exc:
        raise ContractError("Invalid UTC timestamp") from exc


@dataclass
class State:
    cash: Decimal = ZERO
    positions: dict = field(default_factory=dict)
    basis: dict = field(default_factory=dict)
    marks: dict = field(default_factory=dict)
    orders: dict = field(default_factory=dict)
    receivables: dict = field(default_factory=dict)
    entitlement_instruments: dict = field(default_factory=dict)
    submissions: dict = field(default_factory=dict)
    fills: dict = field(default_factory=dict)
    turnover: dict = field(default_factory=dict)
    realized: Decimal = ZERO
    income: Decimal = ZERO
    fees: Decimal = ZERO
    initial_cash: Decimal = ZERO
    peak: Decimal = ZERO
    day_start: Decimal = ZERO
    session: str | None = None
    at: str | None = None
    recorded_at: str | None = None
    snapshot_id: str | None = None
    halted: bool = False

    @property
    def reserved(self):
        return sum((D(o["reserved"]) for o in self.orders.values() if o["status"] == "pending"), ZERO)

    def equity(self):
        if any(i not in self.marks for i, q in self.positions.items() if q):
            return None
        return self.cash + sum(self.receivables.values(), ZERO) + sum(
            (q * D(self.marks[i]["price"]) for i, q in self.positions.items() if q), ZERO)

    def apply(self, e):
        kind = e["type"]
        if kind in {"command", "rejection"}:
            return
        if e.get("session") and e["session"] != self.session:
            self.day_start = self.equity() or self.initial_cash
            self.session = e["session"]
        if kind == "funding":
            self.cash = self.initial_cash = self.peak = self.day_start = D(e["amount"])
        elif kind == "order":
            self.orders[e["order_id"]] = dict(e["order"], status="pending")
            self.submissions[e["session"]] = self.submissions.get(e["session"], 0) + 1
        elif kind == "cancellation":
            self.orders[e["order_id"]]["status"] = e["reason"]
        elif kind == "fill":
            order = self.orders[e["order_id"]]
            key, quantity, notional, fee = order["instrument_id"], D(order["quantity"]), D(e["notional"]), D(e["fee"])
            old_quantity = self.positions.get(key, ZERO)
            if order["side"] == "buy":
                self.cash -= notional + fee
                self.positions[key] = old_quantity + quantity
                self.basis[key] = self.basis.get(key, ZERO) + notional + fee
            else:
                removed_basis = self.basis[key] if quantity == old_quantity else self.basis[key] * quantity / old_quantity
                self.basis[key] -= removed_basis
                self.positions[key] = old_quantity - quantity
                self.cash += notional - fee
                self.realized += notional - fee - removed_basis
            self.fees += fee
            order["status"] = "filled"
            self.fills[e["session"]] = self.fills.get(e["session"], 0) + 1
            self.turnover[e["session"]] = self.turnover.get(e["session"], ZERO) + notional
        elif kind == "mark":
            self.marks.update(e["marks"])
            if "snapshot_id" in e:
                self.snapshot_id = e["snapshot_id"]
        elif kind == "dividend_ex":
            self.receivables[e["action_id"]] = D(e["amount"])
            self.entitlement_instruments[e["action_id"]] = e["instrument_id"]
            self.income += D(e["amount"])
            # Carry the known ex-distribution adjustment until the next raw mark.
            # Otherwise the old cum-dividend mark and receivable inflate the peak.
            key = e["instrument_id"]
            if key in self.marks:
                adjusted = D(self.marks[key]["price"]) - D(e["per_share"])
                if adjusted <= 0:
                    del self.marks[key]
                else:
                    self.marks[key] = dict(self.marks[key], price=str(adjusted), action_id=e["action_id"])
        elif kind == "dividend_pay":
            self.cash += self.receivables.pop(e["action_id"])
        elif kind == "split":
            key, ratio = e["instrument_id"], D(e["ratio"])
            self.positions[key] = self.positions.get(key, ZERO) * ratio
            if key in self.marks:
                self.marks[key] = dict(self.marks[key], price=str(D(self.marks[key]["price"]) / ratio))
        elif kind == "halt":
            self.halted = True
        elif kind == "owner_reset":
            self.halted = False
            self.peak = self.day_start = self.equity() or self.initial_cash
        else:
            raise ContractError("Unknown simulation event version or type")
        self.at = e["at"]
        if kind in {"mark", "fill", "dividend_ex", "split"}:
            self.peak = max(self.peak, self.equity() or ZERO)
        if self.cash < 0 or self.reserved > self.cash or any(q < 0 for q in self.positions.values()):
            raise ContractError("Ledger reconciliation failed: cash, reservation or short position")


class Simulator:
    def __init__(self, store, experiment_id, portfolio_id, sessions, *, endpoint="simulation"):
        if endpoint != "simulation":
            raise ContractError("Only the simulation endpoint exists")
        self.store, self.experiment_id, self.portfolio_id = store, experiment_id, portfolio_id
        self.experiment = store.record(experiment_id, "experiment")
        self.portfolio = store.record(portfolio_id, "portfolio")
        self.policy = validate_policy(store.record(self.experiment["policy_id"], "policy"), self.experiment)
        if (self.portfolio["experiment_id"] != experiment_id or self.portfolio["mode"] != self.experiment["mode"]
                or self.portfolio["owner_character_version"] not in self.experiment["character_versions"]):
            raise ContractError("Portfolio mode, owner and experiment must agree")
        if self.portfolio["initial_cash"] != self.policy["limits"]["initial_cash"]:
            raise ContractError("Every sleeve must use the policy's equal seed capital")
        self.governor = Governor(self.policy)
        self.sessions = json.loads(json.dumps(sessions))
        previous = None
        for s in self.sessions:
            if set(s) != {"session", "open_at", "close_at"}:
                raise ContractError("Session requires its ID and explicit UTC open and close")
            opened, closed = timestamp(s["open_at"]), timestamp(s["close_at"])
            if opened >= closed or opened.date().isoformat() != s["session"] or closed.date().isoformat() != s["session"] or (previous and opened <= previous):
                raise ContractError("Sessions must be ordered and nonoverlapping")
            previous = closed
        self.session_ids = [s["session"] for s in self.sessions]
        if not self.sessions or len(set(self.session_ids)) != len(self.session_ids):
            raise ContractError("Unique sessions required")
        self.schedule = {s["session"]: s for s in self.sessions}
        self.setup = dict(version=VERSION, policy_hash=digest(self.policy), portfolio_hash=digest(self.portfolio),
                          experiment_hash=digest(self.experiment), sessions=self.sessions,
                          rounding="USD cents half-up per fill; average cost basis; fractional shares",
                          spread="half configured spread plus full adverse slippage",
                          corporate_actions="raw prices; ex-date receivable then pay-date cash; split cancels open orders")
        self._run("initialize", self.setup, self.experiment["start_at"],
                  lambda state: self._emit(state, "funding", self.experiment["start_at"], amount=self.portfolio["initial_cash"]))

    def state(self):
        state = State()
        for event in self.store.iter_events(self.experiment_id, "simulation", portfolio_id=self.portfolio_id):
            payload = event["payload"]
            if payload["version"] != VERSION:
                raise ContractError("Unknown simulation version")
            state.apply(payload)
            state.recorded_at = event["created_at"]
        return state

    def _emit(self, state, kind, at, **fields):
        timestamp(at)
        if kind not in {"rejection", "command"} and state.at and timestamp(at) < timestamp(state.at):
            raise ContractError("Out-of-order ledger time; process executions/actions before later marks or decisions")
        payload = dict(version=VERSION, portfolio_id=self.portfolio_id, type=kind, at=at, **fields)
        identifier = "sim:" + digest([self.portfolio_id, self._command, self._counter])
        self._counter += 1
        self.store.append(identifier, self.experiment_id, "simulation", payload, created_at=self._recorded_at)
        state.apply(payload)
        return {"status": kind}

    def _run(self, command_id, request, at, operation):
        timestamp(at)
        if digest(self.policy) != self.setup["policy_hash"]:
            raise ContractError("Pinned policy changed; create a new experiment")
        identifier = "sim-command:" + digest([self.portfolio_id, command_id])
        with self.store.transaction():
            row = self.store.connection.execute("SELECT body FROM events WHERE id=?", (identifier,)).fetchone()
            request_hash = digest(request)
            if row:
                payload = json.loads(row[0])
                if payload["request_hash"] != request_hash:
                    raise ContractError("Command identity reused with changed inputs")
                return payload["result"]
            self._command, self._counter, self._recorded_at = command_id, 0, at
            state = self.state()
            if state.recorded_at and timestamp(at) < timestamp(state.recorded_at):
                raise ContractError("Processing clock cannot move backward into already observed outcomes")
            result = operation(state)
            self.store.append(identifier, self.experiment_id, "simulation",
                              dict(version=VERSION, portfolio_id=self.portfolio_id, type="command",
                                   request_hash=request_hash, result=result, at=at), created_at=at)
            return result

    def _reject(self, state, at, reasons, **context):
        self._emit(state, "rejection", at, reasons=sorted(set(reasons)), policy_id=self.policy["id"], **context)
        return {"status": "rejected", "reasons": sorted(set(reasons))}

    def _expected(self, at):
        completed = [s["session"] for s in self.sessions if timestamp(s["close_at"]) <= timestamp(at)]
        return completed[-1] if completed else None

    def _halt(self, state, at):
        reasons = self.governor.loss_reasons(state, state.equity())
        if reasons and not state.halted:
            self._emit(state, "halt", at, reasons=reasons, policy_id=self.policy["id"])

    def _market(self, item, at):
        observation, payload = item.observation, item.payload
        validate(observation)
        if self.store.record(observation["id"], "observation") != observation:
            raise ContractError("Market evidence differs from immutable observation")
        if (observation["experiment_id"] != self.experiment_id or observation["quality"] != "eligible"
                or digest(payload) != observation["payload_hash"] or payload["instrument_id"] != observation["instrument_id"]
                or payload["event_at"] != observation["event_at"] or payload["feed"] not in self.experiment["data_feeds"]
                or payload["adjustment"] != "raw" or payload["kind"] != "bar"
                or payload["session"] not in self.schedule):
            raise ContractError("Need eligible raw bars in the registered experiment, feed and calendar")
        for key in ("event_at", "published_at", "ingested_at"):
            if timestamp(observation[key]) > timestamp(at):
                raise ContractError("Market evidence is not yet available")
        for row in self.store.connection.execute(
                "SELECT body FROM records WHERE record_type='observation' AND experiment_id=? AND json_extract(body, '$.supersedes_id')=?",
                (self.experiment_id, observation["id"])):
            later = json.loads(row[0])
            if timestamp(later["published_at"]) <= timestamp(at) and timestamp(later["ingested_at"]) <= timestamp(at):
                raise ContractError("Market evidence has a known superseding revision")
        s = self.schedule[payload["session"]]
        if timestamp(payload["event_at"]) != timestamp(s["close_at"]):
            raise ContractError("Daily bar must refer to the scheduled close")
        prices = {key: decimal(payload[key], positive=True) for key in ("open", "close", "high", "low")}
        decimal(payload["volume"])
        if prices["low"] > min(prices["open"], prices["close"]) or prices["high"] < max(prices["open"], prices["close"]):
            raise ContractError("Invalid OHLC prices")
        return observation, payload

    def mark(self, snapshot_id, items, *, at):
        snapshot = self.store.record(snapshot_id, "snapshot")
        request = dict(snapshot_id=snapshot_id, observations=[i.observation["id"] for i in items], at=at)
        def operation(state):
            if snapshot["experiment_id"] != self.experiment_id or timestamp(snapshot["cutoff"]) > timestamp(at):
                raise ContractError("Snapshot scope or clock mismatch")
            expected = self._expected(snapshot["cutoff"])
            if expected is None:
                raise ContractError("No completed session")
            marks = {}
            for item in items:
                observation, payload = self._market(item, snapshot["cutoff"])
                if observation["id"] not in snapshot["observation_ids"]:
                    raise ContractError("Mark is outside frozen snapshot")
                key = payload["instrument_id"]
                if key in marks:
                    raise ContractError("Select one raw mark per instrument")
                marks[key] = dict(price=payload["close"], session=payload["session"], at=observation["event_at"], observation_id=observation["id"], phase="close")
            self._emit(state, "mark", snapshot["cutoff"], session=expected, marks=marks, snapshot_id=snapshot_id)
            self._halt(state, snapshot["cutoff"])
            return self._report(state, snapshot["cutoff"])
        return self._run("mark:" + snapshot_id, request, at, operation)

    def submit(self, recommendation_id, *, at, price_cap, endpoint="simulation"):
        cap = decimal(price_cap, positive=True)
        recommendation = self.store.record(recommendation_id, "recommendation")
        request = dict(recommendation_id=recommendation_id, at=at, price_cap=price_cap, endpoint=endpoint)
        def operation(state):
            if endpoint != "simulation":
                return self._reject(state, at, ["live_endpoint"], decision_id=recommendation_id)
            if (recommendation["experiment_id"] != self.experiment_id or recommendation["portfolio_id"] != self.portfolio_id
                    or recommendation["character_version"] != self.portfolio["owner_character_version"]):
                return self._reject(state, at, ["authority"], decision_id=recommendation_id)
            if (recommendation["snapshot_id"] != state.snapshot_id or timestamp(recommendation["created_at"]) > timestamp(at)
                    or not timestamp(self.experiment["start_at"]) <= timestamp(at) < timestamp(self.experiment["end_at"])):
                return self._reject(state, at, ["decision_context"], decision_id=recommendation_id)
            snapshot = self.store.record(recommendation["snapshot_id"], "snapshot")
            if timestamp(snapshot["cutoff"]) > timestamp(recommendation["created_at"]):
                return self._reject(state, at, ["lookahead"], decision_id=recommendation_id)
            session = self._expected(at)
            order = dict(decision_id=recommendation_id, instrument_id=recommendation["instrument_id"], side=recommendation["action"],
                         quantity=recommendation["quantity"], expires_at=recommendation["expires_at"], decision_at=at,
                         decision_session=session, price_cap=price_cap, reserved="0")
            fee = D(self.policy["costs"]["fee_per_order"])
            if order["side"] == "buy":
                order["reserved"] = str(money(D(order["quantity"]) * cap) + fee)
            self._halt(state, at)
            reasons = self.governor.check(state, order, price=cap, fee=fee, session=session, at=at,
                                          sessions=self.session_ids, expected_session=session)
            if reasons:
                return self._reject(state, at, reasons, decision_id=recommendation_id)
            order_id = "order:" + digest([self.portfolio_id, recommendation_id])
            self._emit(state, "order", at, session=session, order_id=order_id, order=order)
            return {"status": "pending", "order_id": order_id, "reserved": order["reserved"]}
        return self._run("submit:" + recommendation_id, request, at, operation)

    def cancel(self, order_id, *, at, reason="owner_cancelled"):
        def operation(state):
            if order_id not in state.orders:
                raise ContractError("Order not in this portfolio")
            if state.orders[order_id]["status"] != "pending":
                return {"status": state.orders[order_id]["status"]}
            return self._emit(state, "cancellation", at, order_id=order_id, reason=reason)
        return self._run("cancel:" + order_id, dict(order_id=order_id, at=at, reason=reason), at, operation)

    def expire(self, *, at):
        def operation(state):
            count = 0
            for key, order in state.orders.items():
                if order["status"] == "pending" and timestamp(order["expires_at"]) <= timestamp(at):
                    self._emit(state, "cancellation", at, order_id=key, reason="expired")
                    count += 1
            return {"expired": count}
        return self._run("expiry:" + at, dict(at=at), at, operation)

    def process_bar(self, item, *, at):
        observation, payload = self._market(item, at)
        request = dict(observation_id=observation["id"], payload_hash=digest(payload), at=at)
        # Identity is the economic session/instrument, not the observation revision.
        command = "bar:" + payload["instrument_id"] + ":" + payload["session"]
        def operation(state):
            session, key = payload["session"], payload["instrument_id"]
            opened = self.schedule[session]["open_at"]
            if not timestamp(self.experiment["start_at"]) <= timestamp(opened) < timestamp(self.experiment["end_at"]):
                raise ContractError("Execution is outside experiment window")
            if decimal(payload["volume"]) == 0:
                return {"status": "pending", "reason": "no_volume"}
            self._emit(state, "mark", opened, session=session,
                       marks={key: dict(price=payload["open"], session=session, at=opened, observation_id=observation["id"], phase="open")})
            self._halt(state, opened)
            results = []
            for order_id, order in state.orders.items():
                if order["status"] != "pending" or order["instrument_id"] != key:
                    continue
                if timestamp(opened) <= timestamp(order["decision_at"]) or session <= order["decision_session"]:
                    continue
                if timestamp(opened) >= timestamp(order["expires_at"]):
                    self._emit(state, "cancellation", opened, order_id=order_id, reason="expired")
                    continue
                costs = self.policy["costs"]
                adverse = (D(costs["slippage_bps"]) + D(costs["spread_bps"]) / 2) / 10000
                price = D(payload["open"]) * (1 + adverse if order["side"] == "buy" else 1 - adverse)
                price = price.quantize(D("0.00000001"), rounding=ROUND_HALF_UP)
                fee, notional = D(costs["fee_per_order"]), money(D(order["quantity"]) * price)
                if order["side"] == "buy" and (price > D(order["price_cap"]) or notional + fee > D(order["reserved"])):
                    results.append(self._reject(state, opened, ["reservation_gap"], order_id=order_id))
                    continue
                reasons = self.governor.check(state, order, price=price, fee=fee, session=session, at=opened,
                                              sessions=self.session_ids, expected_session=self._expected(opened),
                                              exclude_order=order_id, execution=True)
                if reasons:
                    results.append(self._reject(state, opened, reasons, order_id=order_id))
                    continue
                self._emit(state, "fill", opened, session=session, order_id=order_id, price=str(price),
                           notional=str(notional), fee=str(fee), observation_id=observation["id"], model=VERSION)
                self._halt(state, opened)
                results.append({"status": "filled", "order_id": order_id})
            return {"results": results}
        return self._run(command, request, at, operation)

    def corporate_action(self, action_id, *, kind, instrument_id, at, value=None, evidence, recorded_at=None):
        """Trusted raw-action input. IDs identify an economic action across revisions.

        dividend_ex fixes entitlement before ex-date trading; dividend_pay uses that
        entitlement even after a sale. Splits cancel unexecuted orders for re-advice.
        """
        if instrument_id not in self.governor.universe or not isinstance(evidence, str) or not evidence.strip():
            raise ContractError("Corporate action needs universe identity and source evidence")
        if kind not in {"split", "dividend_ex", "dividend_pay"}:
            raise ContractError("Unsupported corporate action; no implicit corrections")
        amount = decimal(value, positive=kind == "split") if kind != "dividend_pay" else None
        recorded_at = recorded_at or at
        if timestamp(recorded_at) < timestamp(at):
            raise ContractError("Corporate action cannot be recorded before its effective time")
        request = dict(action_id=action_id, kind=kind, instrument_id=instrument_id, at=at, value=value, evidence=evidence, recorded_at=recorded_at)
        def operation(state):
            if kind == "split":
                resulting_quantity = state.positions.get(instrument_id, ZERO) * amount
                if resulting_quantity.normalize().as_tuple().exponent < -8:
                    raise ContractError("Split fractional remainder needs an explicit cash-in-lieu implementation")
                for key, order in state.orders.items():
                    if order["status"] == "pending" and order["instrument_id"] == instrument_id:
                        self._emit(state, "cancellation", at, order_id=key, reason="split_cancelled")
                return self._emit(state, kind, at, action_id=action_id, instrument_id=instrument_id, ratio=str(amount), evidence=evidence)
            if kind == "dividend_ex":
                entitlement = money(state.positions.get(instrument_id, ZERO) * amount)
                return self._emit(state, kind, at, action_id=action_id, instrument_id=instrument_id, amount=str(entitlement), per_share=str(amount), evidence=evidence)
            if action_id not in state.receivables or state.entitlement_instruments[action_id] != instrument_id:
                raise ContractError("Dividend payment needs an unpaid ex-date entitlement")
            return self._emit(state, kind, at, action_id=action_id, instrument_id=instrument_id, evidence=evidence)
        return self._run("action:" + action_id + ":" + kind, request, recorded_at, operation)

    def reset_halt(self, reset_id, *, owner, approval_ref, at):
        # This runner/admin API is intentionally absent from recommendation schemas.
        expected_owner = self.policy["kill_switch_owner"] or "fixture-owner"
        if owner != expected_owner or not approval_ref or not approval_ref.strip():
            raise ContractError("Recorded kill-switch owner and reset approval required")
        def operation(state):
            if self._report(state, at)["equity"] is None:
                raise ContractError("Fresh reconciled marks required before reset")
            return self._emit(state, "owner_reset", at, owner=owner, approval_ref=approval_ref,
                              policy_id=self.policy["id"], prior_peak=str(state.peak), prior_day_start=str(state.day_start))
        return self._run("reset:" + reset_id, dict(owner=owner, approval_ref=approval_ref, at=at), at, operation)

    def _report(self, state, at):
        expected = self._expected(at)
        stale = [i for i, q in state.positions.items() if q and (i not in state.marks or expected is None or
                 timestamp(state.marks[i]["at"]) > timestamp(at) or
                 self.session_ids.index(expected) - self.session_ids.index(state.marks[i]["session"]) + (state.marks[i].get("phase") == "open") > self.policy["clock"]["max_stale_sessions"])]
        equity = None if stale else state.equity()
        unrealized = None if equity is None else sum((q * D(state.marks[i]["price"]) - state.basis[i] for i, q in state.positions.items() if q), ZERO)
        if equity is not None and abs(equity - state.initial_cash - state.realized - unrealized - state.income) > D("0.00000001"):
            raise ContractError("Equity does not reconcile to realized gain, unrealized gain and income")
        return dict(cash=str(state.cash), reserved=str(state.reserved), available_cash=str(state.cash - state.reserved),
                    positions={i: str(q) for i, q in state.positions.items()}, equity=None if equity is None else str(equity),
                    realized=str(state.realized), unrealized=None if unrealized is None else str(unrealized),
                    income=str(state.income), fees=str(state.fees), receivables=str(sum(state.receivables.values(), ZERO)),
                    stale_instruments=stale, halted=state.halted, model=VERSION)

    def reconcile(self, *, at):
        timestamp(at)
        state = self.state()
        if state.at and timestamp(at) < timestamp(state.at):
            raise ContractError("Cannot report latest ledger at an earlier clock")
        if state.recorded_at and timestamp(at) < timestamp(state.recorded_at):
            raise ContractError("Cannot report latest ledger before its recorded availability")
        return self._report(state, at)
