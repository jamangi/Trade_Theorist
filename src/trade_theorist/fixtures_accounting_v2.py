"""Original production-ledger golden vector. No reference reducer is imported."""
from copy import deepcopy
from decimal import Decimal as D

from .contracts import digest
from .fixtures_v2 import bundle, INSTRUMENT
from .adapters.trader_user_sim.v2 import SimulatorV2
from .evaluate.ledger_v2 import money


def at(day, minute=0):
    return f"2099-01-{day:02d}T21:{minute:02d}:00Z"


class FixtureV2:
    def __init__(self, store, name="golden", *, mode="character_portfolio", basis="simulated", flows=None,
                 baseline=None, role="strategy", fee="1.00", fractional=True, extra_instrument=False, readiness="fixture_only"):
        records = [r for r in bundle(mode=mode, basis=basis) if r["record_type"] in {"source_rights", "policy", "character", "experiment", "portfolio", "funded_segment"}]
        identities = {r["id"]: r["id"] + "-" + name for r in records}
        def replace(v):
            if isinstance(v, dict): return {k: replace(x) for k, x in v.items()}
            if isinstance(v, list): return [replace(x) for x in v]
            return identities.get(v, v) if isinstance(v, str) else v
        records = [replace(r) for r in records]
        next(r for r in records if r["record_type"] == "character")["readiness"] = readiness
        policy = next(r for r in records if r["record_type"] == "policy")
        policy["limits"].update(initial_cash="1000.00", max_deployed_capital="1000.00", turnover=1.0, daily_loss=0.5, drawdown=0.5)
        policy["costs"].update(fee_per_order="0.00", slippage_bps="0", spread_bps="0")
        experiment = next(r for r in records if r["record_type"] == "experiment")
        if extra_instrument:
            other = dict(policy["universe"][0], instrument_id="instrument:fixture-second", symbol="SECOND")
            policy["universe"].append(other); experiment["instrument_ids"].append(other["instrument_id"])
        portfolio = next(r for r in records if r["record_type"] == "portfolio")
        portfolio["role"] = role
        self.portfolio, self.segment = portfolio["id"], next(r for r in records if r["record_type"] == "funded_segment")["id"]
        self.character = portfolio["owner_character_version"]
        self.name, self.store, self.serial = name, store, 0
        self.scope = portfolio
        common = {k: portfolio[k] for k in ("schema_version", "experiment_id", "contamination", "provenance")}
        plan = dict(common, id="plan:" + name, record_type="accounting_plan", field_class="private_strategy", created_at=at(1),
            portfolio_id=self.portfolio, approved_at=at(1), approval_ref="original-fixture-only",
            flows=[dict(segment_id=self.segment, event_type=kind, effective_at=when, amount=amount) for kind, when, amount in
                   (flows if flows is not None else [("funding", at(1), "1000.00"), ("contribution", at(9), "500.00")])],
            mark_schedule=[at(day) for day in range(1, 13)], max_mark_age_seconds=90000,
            execution_model="eligible-next-event-v2", fee_per_share=fee, slippage_bps="0", spread_bps="0", fractional_shares=fractional,
            corporate_actions="explicit-raw-v2", baseline_portfolio_id=baseline,
            baseline_construction="Independent broad-market synthetic basket; buy at next eligible event, retain later contributions as cash")
        store.put_v2(records + [plan])
        self.engine = SimulatorV2(store, self.portfolio)

    def identifier(self, label):
        self.serial += 1
        return f"fixture:{self.name}-{label}-{self.serial}"

    def event(self, kind, day, *, minute=0, observed_at=None, **payload):
        identifier = self.identifier(kind)
        e = self.engine.event(identifier, kind, at(day, minute), observed_at=observed_at, segment_id=self.segment, **payload)
        self.engine.command("command:" + digest(identifier), [e])
        return e["id"]

    def mark(self, day, price, *, instrument=INSTRUMENT, minute=0, status="eligible", observed_at=None):
        when = at(day, minute)
        return self.event("mark", day, minute=minute, observed_at=observed_at, instrument_id=instrument,
            price=price if status == "eligible" else None, event_at=when, published_at=when, received_at=observed_at or when,
            feed="original-synthetic-v2", adjustment="raw", observation_id=self.identifier("observation"), observation_revision=1,
            eligibility_cutoff=observed_at or when, status=status, reason=None if status == "eligible" else "Missing current session",
            mark_policy_hash=digest([self.engine.plan["mark_schedule"], self.engine.plan["max_mark_age_seconds"]]))

    def order(self, day, quantity, cap, *, side="buy", instrument=INSTRUMENT, minute=1, reserve=None):
        when, oid, did = at(day, minute), self.identifier("order"), self.identifier("decision")
        engine = self.engine
        decision = engine.record("decision", did, when, portfolio_id=self.portfolio, segment_id=self.segment,
            character_version=self.character, snapshot_hash=digest("original shared snapshot " + when), instrument_id=instrument,
            side=side, quantity=quantity, final=True)
        order = engine.record("order", oid, when, portfolio_id=self.portfolio, segment_id=self.segment,
            final_recommendation_id=did, instrument_id=instrument, execution_basis=self.scope["execution_basis"], side=side,
            quantity=quantity, policy_approval_ref="original-fixture-only", replaces_order_id=None)
        terms = engine.record("execution_terms", self.identifier("terms"), when, portfolio_id=self.portfolio, segment_id=self.segment,
            order_id=oid, earliest_fill_at=at(day + 1), expires_at="2099-02-01T00:00:00Z", price_cap=cap)
        submitted = engine.event(self.identifier("admitted"), "order", when, segment_id=self.segment, order_id=oid)
        reserved = engine.event(self.identifier("reserved"), "reservation", when, segment_id=self.segment, order_id=oid,
            cash=reserve or str(money(D(quantity) * (D(cap) + D(engine.plan["fee_per_share"])))) if side == "buy" else "0.00",
            quantity=quantity if side == "sell" else "0")
        reserved["sequence"] += 1
        engine.command("command:" + digest(oid), [decision, order, terms, submitted, reserved])
        return oid

    def fill(self, order, mark, day, quantity):
        return self.engine.fill_order("command:" + digest([order, mark, quantity]), order, mark, quantity, at=at(day))


def golden(store, *, name="golden", baseline=None, role="strategy", mode="character_portfolio"):
    f = FixtureV2(store, name, baseline=baseline, role=role, mode=mode)
    f.event("funding", 1, amount="1000.00", boundary_mark_ids=[])
    f.mark(1, "100")
    first = f.order(1, "2", "100")
    mark = f.mark(2, "100"); f.fill(first, mark, 2, "2")
    second = f.order(2, "2", "120")
    mark = f.mark(3, "120"); f.fill(second, mark, 3, "2")
    sale = f.order(3, "1", "130", side="sell")
    mark = f.mark(4, "130"); f.fill(sale, mark, 4, "1")
    exmark = f.mark(5, "129")
    entitlement = f.event("dividend_entitlement", 5, action_id="action:" + name + "-dividend", instrument_id=INSTRUMENT,
        eligible_quantity="3", per_share="1", amount="3.00", ex_at=at(5), mark_id=exmark, policy_hash=digest(f.engine.plan["corporate_actions"]))
    f.mark(6, "129")
    f.event("dividend_payment", 6, entitlement_id=entitlement, amount="3.00")
    splitmark = f.mark(7, "64.5")
    f.event("split", 7, action_id="action:" + name + "-split", instrument_id=INSTRUMENT, numerator=2, denominator=1,
            mark_id=splitmark, pending_orders="none")
    f.mark(8, "65")
    boundary = f.mark(9, "65")
    f.event("contribution", 9, amount="500.00", boundary_mark_ids=[boundary])
    f.mark(10, "65")
    f.order(10, "1", "99", reserve="100.00")
    f.mark(11, "60")
    f.mark(12, None, status="stale")
    return f


def broad_market(store, name="benchmark"):
    f = FixtureV2(store, name, role="baseline")
    f.event("funding", 1, amount="1000.00", boundary_mark_ids=[])
    f.mark(1, "100")
    order = f.order(1, "9", "100")
    mark = f.mark(2, "100"); f.fill(order, mark, 2, "9")
    f.mark(3, "120"); f.mark(4, "130")
    exmark = f.mark(5, "129")
    entitlement = f.event("dividend_entitlement", 5, action_id="action:" + name + "-dividend", instrument_id=INSTRUMENT,
        eligible_quantity="9", per_share="1", amount="9.00", ex_at=at(5), mark_id=exmark, policy_hash=digest(f.engine.plan["corporate_actions"]))
    f.mark(6, "129"); f.event("dividend_payment", 6, entitlement_id=entitlement, amount="9.00")
    splitmark = f.mark(7, "64.5")
    f.event("split", 7, action_id="action:" + name + "-split", instrument_id=INSTRUMENT, numerator=2, denominator=1,
            mark_id=splitmark, pending_orders="none")
    f.mark(8, "65"); boundary = f.mark(9, "65")
    f.event("contribution", 9, amount="500.00", boundary_mark_ids=[boundary])
    f.mark(10, "65"); f.mark(11, "60"); f.mark(12, None, status="stale")
    return f
