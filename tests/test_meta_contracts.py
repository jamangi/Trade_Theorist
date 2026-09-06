"""Executable META-001 reference vectors, not the production v2 ledger.

TASK-025 must replay the same golden values through the real persistent engine.
This deliberately small reducer independently checks the hand-worked contract.
"""

from copy import deepcopy
from datetime import datetime
from decimal import Decimal as D
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[1]
ZERO = D("0")


def load(name, kind):
    directory = "schemas" if kind == "schema" else "examples"
    return json.loads((ROOT / directory / "meta-001" / f"{name}.{kind}.json").read_text())


def check(name, value):
    validator = Draft202012Validator(load(name, "schema"), format_checker=FormatChecker())
    validator.validate(value)


def reference_replay(value):
    check("performance-v2", value)
    cash = initial = external = realized = income = fees = ZERO
    factor, start, peak = D("1"), None, D("1")
    lots, dividends, reserved, seen, actions = [], {}, {}, {}, set()
    mark, instrument, previous = None, None, None
    max_dd, gap, history = ZERO, False, []

    def equity():
        quantity = sum((lot["quantity"] for lot in lots), ZERO)
        return None if quantity and mark is None else cash + sum(dividends.values(), ZERO) + quantity * (mark or ZERO)

    for e in value["events"]:
        if e["id"] in seen:
            if seen[e["id"]] != e:
                raise ValueError("Conflicting duplicate event")
            continue
        if (e["portfolio_id"], e["experiment_id"]) != (value["portfolio"]["id"], value["portfolio"]["experiment_id"]):
            raise ValueError("Portfolio isolation violation")
        at, observed = (datetime.fromisoformat(e[k].replace("Z", "+00:00")) for k in ("at", "observed_at"))
        if observed < at or (previous and at < previous):
            raise ValueError("Invalid effective/observed order")
        previous, seen[e["id"]] = at, deepcopy(e)
        if e.get("instrument_id"):
            if instrument and instrument != e["instrument_id"]:
                raise ValueError("This reference vector supports one instrument")
            instrument = e["instrument_id"]
        kind = e["kind"]
        if kind == "funding":
            if start is not None or D(e["amount"]) <= 0:
                raise ValueError("Exactly one positive initial funding is required")
            cash = initial = start = D(e["amount"])
        elif start is None:
            raise ValueError("Fund the portfolio first")
        elif kind in {"contribution", "withdrawal"}:
            amount = D(e["amount"])
            if amount <= 0:
                raise ValueError("Positive external amount required")
            if kind == "withdrawal":
                if amount > cash - sum(reserved.values(), ZERO):
                    raise ValueError("Withdrawal exceeds available cash")
                amount = -amount
            before = equity()
            factor = factor * before / start if before is not None and factor is not None and start > 0 else None
            cash += amount
            external += amount
            start = equity()
            if start is None:
                # Current marks can recover, but a missing flow valuation cannot.
                factor, start = None, ZERO
        elif kind in {"buy", "sell"}:
            q, price, fee = (D(e[k]) for k in ("quantity", "price", "fee"))
            if q <= 0 or price <= 0 or fee < 0:
                raise ValueError("Invalid fill")
            if kind == "buy":
                cash -= q * price + fee
                lots.append(dict(lot_id=e["id"], quantity=q, basis=q * price + fee))
            else:
                if q > sum((lot["quantity"] for lot in lots), ZERO):
                    raise ValueError("Sale exceeds owned quantity")
                remaining, relieved = q, ZERO
                for lot in lots:
                    take = min(remaining, lot["quantity"])
                    if take:
                        cost = lot["basis"] * take / lot["quantity"]
                        lot["quantity"] -= take
                        lot["basis"] -= cost
                        relieved += cost
                        remaining -= take
                cash += q * price - fee
                realized += q * price - fee - relieved
            fees += fee
            mark = price
        elif kind == "dividend_ex":
            if e["action_id"] in actions or D(e["per_share"]) < 0:
                raise ValueError("Invalid/repeated dividend entitlement")
            actions.add(e["action_id"])
            amount = sum((lot["quantity"] for lot in lots), ZERO) * D(e["per_share"])
            dividends[e["action_id"]] = amount
            income += amount
            mark = mark - D(e["per_share"]) if mark is not None else None
        elif kind == "dividend_pay":
            if e["action_id"] not in dividends:
                raise ValueError("No unpaid entitlement")
            cash += dividends.pop(e["action_id"])
        elif kind == "split":
            ratio = D(e["ratio"])
            if ratio <= 0 or e["action_id"] in actions:
                raise ValueError("Invalid/repeated split")
            actions.add(e["action_id"])
            for lot in lots:
                lot["quantity"] *= ratio
            mark = mark / ratio if mark is not None else None
        elif kind == "mark":
            mark = D(e["price"]) if e["status"] == "eligible" and e["price"] is not None else None
            if mark is not None and mark <= 0:
                raise ValueError("Positive eligible mark required")
        elif kind == "reserve":
            if e["order_id"] in reserved or D(e["amount"]) <= 0:
                raise ValueError("Invalid reservation")
            reserved[e["order_id"]] = D(e["amount"])
        elif kind == "release":
            if e["order_id"] not in reserved:
                raise ValueError("Unknown reservation")
            del reserved[e["order_id"]]
        if cash < sum(reserved.values(), ZERO):
            raise ValueError("Cash/reservation reconciliation failed")
        nav = equity()
        quantity, basis = (sum((lot[k] for lot in lots), ZERO) for k in ("quantity", "basis"))
        wealth = factor * nav / start if nav is not None and factor is not None and start > 0 else None
        gap = gap or nav is None
        if wealth is not None:
            peak = max(peak, wealth)
            max_dd = max(max_dd, 1 - wealth / peak)
        history.append(dict(cash=cash, reserved=sum(reserved.values(), ZERO), available=cash-sum(reserved.values(), ZERO),
                            quantity=quantity, basis=basis, realized=realized, income=income, fees=fees, equity=nav,
                            unrealized=None if nav is None else quantity*(mark or ZERO)-basis,
                            strategy_pnl=None if nav is None else nav-initial-external,
                            twr=None if wealth is None else wealth-1, max_drawdown=None if gap else max_dd,
                            net_external_flows=external, lots=deepcopy([lot for lot in lots if lot["quantity"]]),
                            reason="stale_or_missing_mark" if nav is None else None))
    return history


def reference_attribution(value):
    check("broker-attribution-v1", value)
    order, portfolio, mapping = (value[k] for k in ("order", "portfolio", "mapping"))
    if (order["portfolio_id"], order["experiment_id"]) != (portfolio["id"], portfolio["experiment_id"]) or mapping["internal_order_id"] != order["id"]:
        raise ValueError("Ambiguous internal attribution")
    seen, last, increments, broker_id = {}, (ZERO, ZERO, ZERO), [], None
    for update in value["updates"]:
        if update["event_id"] in seen:
            if seen[update["event_id"]] != update:
                raise ValueError("Conflicting duplicate broker update")
            continue
        if update["client_order_id"] != mapping["client_order_id"] or (broker_id and broker_id != update["broker_order_id"]):
            raise ValueError("Unknown broker mapping")
        current = tuple(D(update[k]) for k in ("cumulative_quantity", "cumulative_notional", "cumulative_fees"))
        if any(new < old for new, old in zip(current, last)) or current[0] > D(order["quantity"]):
            raise ValueError("Quarantine impossible or out-of-order cumulative fills")
        increments.append(tuple(new-old for new, old in zip(current, last)))
        seen[update["event_id"]], last, broker_id = update, current, update["broker_order_id"]
    return increments


class MetaContractTests(unittest.TestCase):
    def test_hand_worked_fifo_cash_receivable_flows_and_stale_mark(self):
        value = load("performance-v2", "fixture")
        history = reference_replay(value)
        before = history[-2]
        for key, expected in value["expected"]["before_stale"].items():
            if key == "lots":
                self.assertEqual(before[key], [{k: D(v) if k != "lot_id" else v for k, v in lot.items()} for lot in expected])
            else:
                self.assertAlmostEqual(before[key], D(expected), places=8, msg=key)
        for key, expected in value["expected"]["after_stale"].items():
            self.assertEqual(history[-1][key], D(expected) if key == "cash" else expected)
        self.assertEqual(history[4]["equity"], history[5]["equity"])
        self.assertEqual(history[5]["income"], D("3"))
        self.assertEqual(before["strategy_pnl"], before["realized"] + before["unrealized"] + before["income"])

    def test_duplicate_replay_is_idempotent_and_conflicts_fail(self):
        value = load("performance-v2", "fixture")
        repeated = deepcopy(value)
        repeated["events"] += deepcopy(value["events"])
        self.assertEqual(reference_replay(value), reference_replay(repeated))
        repeated["events"][-1]["price"] = "1"
        with self.assertRaisesRegex(ValueError, "Conflicting duplicate"):
            reference_replay(repeated)

    def test_portfolio_partition_and_unknown_fields_fail_closed(self):
        value = load("performance-v2", "fixture")
        value["events"][1]["portfolio_id"] = "portfolio:another-character"
        with self.assertRaisesRegex(ValueError, "isolation"):
            reference_replay(value)
        value = load("performance-v2", "fixture")
        value["events"][1]["hidden_fee"] = "2"
        with self.assertRaises(ValidationError):
            check("performance-v2", value)

    def test_external_flows_do_not_create_cash_baseline_profit(self):
        value = load("performance-v2", "fixture")
        value["events"] = [value["events"][0], value["events"][8]]
        withdrawal = deepcopy(value["events"][-1])
        withdrawal.update(id="event:withdrawal", kind="withdrawal", amount="250")
        value["events"].append(withdrawal)
        final = reference_replay(value)[-1]
        self.assertEqual((final["cash"], final["strategy_pnl"], final["twr"], final["max_drawdown"]), (D("1250"), ZERO, ZERO, ZERO))

    def test_missing_flow_boundary_never_turns_into_endpoint_return(self):
        value = load("performance-v2", "fixture")
        value["events"][7].update(price=None, status="missing")
        self.assertIsNone(reference_replay(value)[-2]["twr"])

    def test_broker_partial_updates_deduplicate_and_trace_one_order(self):
        value = load("broker-attribution-v1", "fixture")
        self.assertEqual(reference_attribution(value), [(D("1"), D("100"), D("1")), (D("2"), D("202"), D("1"))])
        value["updates"] += deepcopy(value["updates"])
        self.assertEqual(len(reference_attribution(value)), 2)
        value["mapping"]["internal_order_id"] = "order:another"
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            reference_attribution(value)

    def test_individual_or_identifying_client_id_cannot_enter_broker_mapping(self):
        value = load("broker-attribution-v1", "fixture")
        value["portfolio"]["mode"] = "character_portfolio"
        with self.assertRaises(ValidationError):
            check("broker-attribution-v1", value)
        value = load("broker-attribution-v1", "fixture")
        value["mapping"]["client_order_id"] = "character-index-portfolio-123"
        with self.assertRaises(ValidationError):
            check("broker-attribution-v1", value)

    def test_out_of_order_broker_fill_is_quarantined(self):
        value = load("broker-attribution-v1", "fixture")
        value["updates"].reverse()
        with self.assertRaisesRegex(ValueError, "out-of-order"):
            reference_attribution(value)


if __name__ == "__main__":
    unittest.main()
