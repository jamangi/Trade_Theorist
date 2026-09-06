"""Deterministic policy checks. No model text, network access, or policy promotion."""

from decimal import Decimal

from .contracts import ContractError, utc, validate

D = Decimal
ZERO = D("0")
UNKNOWN = {"unknown", "undocumented", "none", "n/a", ""}


def validate_policy(policy, experiment):
    validate(policy)
    if policy["id"] != experiment["policy_id"] or policy["experiment_id"] != experiment["id"]:
        raise ContractError("Policy must be the experiment's recorded policy")
    if policy["universe"] != experiment["universe"] or policy["costs"] != experiment["costs"]:
        raise ContractError("Execution differs from preregistered policy")
    if experiment["regime"] != "fixture":
        if policy["stage"] != "paper" or policy["synthetic"]:
            raise ContractError("Nonfixture execution requires recorded real paper policy")
        if utc(policy["approved_at"]) > utc(experiment["start_at"]):
            raise ContractError("Paper policy must be approved before the experiment")
        if any(policy[k].strip().lower() in UNKNOWN for k in ("approval_ref", "operator", "kill_switch_owner", "reconciliation_owner", "incident_owner")):
            raise ContractError("Paper approval and operational ownership cannot be placeholders")
        if policy["costs"]["fill_model"] != "raw-next-open-v1" or policy["costs"]["corporate_actions"] != "explicit_raw_events_v1":
            raise ContractError("Nonfixture execution requires real raw-bar assumptions")
    elif policy["stage"] != "fixture":
        raise ContractError("Fixture execution requires fixture policy")
    if policy["clock"]["cadence"] != "daily_session":
        raise ContractError("Only daily session execution is implemented")
    costs = policy["costs"]
    if costs["fill_model"] not in {"synthetic-next-open-v1", "raw-next-open-v1"}:
        raise ContractError("Unsupported fill model")
    if costs["corporate_actions"] not in {"explicit_fixture_events", "explicit_raw_events_v1"}:
        raise ContractError("Unsupported corporate action model")
    if D(costs["slippage_bps"]) + D(costs["spread_bps"]) / 2 >= 10000:
        raise ContractError("Adverse execution costs must be below 100 percent")
    return policy


class Governor:
    def __init__(self, policy):
        self.policy = policy
        self.limits = policy["limits"]
        self.universe = {i["instrument_id"]: i for i in policy["universe"]}

    def check_quote(self, *, bid, ask, observed_at, at):
        """Quote eligibility only; the daily-bar adapter never executes quotes."""
        if (not all(isinstance(v, str) for v in (bid, ask, observed_at, at))
                or not observed_at.endswith("Z") or not at.endswith("Z")):
            return ["invalid_quote"]
        try:
            bid, ask = D(bid), D(ask)
            age = (utc(at) - utc(observed_at)).total_seconds()
        except (ArithmeticError, ValueError, TypeError):
            return ["invalid_quote"]
        if not bid.is_finite() or not ask.is_finite() or bid <= 0 or ask < bid:
            return ["invalid_quote"]
        reasons = []
        if age < 0 or age > self.limits["max_quote_age_seconds"]:
            reasons.append("quote_age")
        if (ask - bid) / ((ask + bid) / 2) * 10000 > D(self.limits["max_spread_bps"]):
            reasons.append("spread")
        return reasons

    def loss_reasons(self, state, equity):
        if equity is None:
            return []
        reasons = []
        for label, baseline, limit in (("daily_loss", state.day_start, "daily_loss"),
                                       ("drawdown", state.peak, "drawdown")):
            if baseline > 0 and equity < baseline and (baseline - equity) / baseline >= D(str(self.limits[limit])):
                reasons.append(label)
        return reasons

    def check(self, state, order, *, price, fee, session, at, sessions, expected_session,
              exclude_order=None, execution=False):
        """Pending buys count in exposure/turnover; pending sells never free buying power."""
        reasons = []
        instrument, side, quantity = order["instrument_id"], order["side"], D(order["quantity"])
        if instrument not in self.universe:
            return ["universe"]
        if side not in {"buy", "sell"} or quantity <= 0:
            return ["invalid_order"]
        if utc(at) >= utc(order["expires_at"]):
            reasons.append("expired")
        if state.halted and side == "buy":
            reasons.append("halted")
        needed = {i for i, q in state.positions.items() if q > 0} | {instrument}
        if self.policy["clock"]["missing_data"] == "halt_all":
            needed.update(self.universe)
        for key in needed:
            mark = state.marks.get(key)
            if mark is None or expected_session is None:
                reasons.append("missing_mark")
            elif (utc(mark["at"]) > utc(at) or
                  sessions.index(expected_session) - sessions.index(mark["session"]) + (mark.get("phase") == "open") > self.policy["clock"]["max_stale_sessions"]):
                reasons.append("stale_mark")
            if self.universe.get(key, {}).get("sector", "unknown").strip().lower() in UNKNOWN:
                reasons.append("unknown_sector")
        equity = state.equity()
        if equity is None or equity <= 0:
            reasons.append("unknown_equity")
        if reasons:
            return sorted(set(reasons))
        loss = self.loss_reasons(state, equity)
        if loss and side == "buy":
            reasons.extend(loss)
        pending = [o for key, o in state.orders.items() if o["status"] == "pending" and key != exclude_order]
        notional = quantity * price
        if notional < D("0.01"):
            reasons.append("minimum_notional")
        reserved = sum((D(o["reserved"]) for o in pending), ZERO)
        if side == "buy" and notional + fee > state.cash - reserved:
            reasons.append("funds")
        if side == "sell":
            committed = sum((D(o["quantity"]) for o in pending if o["side"] == "sell" and o["instrument_id"] == instrument), ZERO)
            if quantity > state.positions.get(instrument, ZERO) - committed:
                reasons.append("position")
            if state.cash - reserved + notional - fee < 0:
                reasons.append("funds")
        # Count admitted orders at submission and fills in their actual execution session.
        count = (state.fills if execution else state.submissions).get(session, 0)
        if count >= self.limits["orders_per_session"]:
            reasons.append("order_frequency")
        committed_turnover = sum((D(o["quantity"]) * D(o["price_cap"]) for o in pending), ZERO)
        if (state.turnover.get(session, ZERO) + committed_turnover + notional) / equity > D(str(self.limits["turnover"])):
            reasons.append("turnover")
        values = {i: q * D(state.marks[i]["price"]) for i, q in state.positions.items() if q > 0}
        before = dict(values)
        for o in pending:
            if o["side"] == "buy":
                key = o["instrument_id"]
                values[key] = values.get(key, ZERO) + D(o["quantity"]) * D(o["price_cap"])
        values[instrument] = values.get(instrument, ZERO) + (notional if side == "buy" else -quantity * D(state.marks[instrument]["price"]))
        # Reductions may bring an already breached exposure toward compliance. They still
        # pass every identity, freshness, cash, quantity, expiry and activity check above.
        if side == "buy":
            post_equity = equity - fee - max(ZERO, (price - D(state.marks[instrument]["price"])) * quantity)
            gross = sum(values.values(), ZERO)
            if gross > D(self.limits["max_deployed_capital"]):
                reasons.append("deployed_capital")
            if post_equity <= 0 or gross > post_equity * D(str(self.limits["gross_exposure"])):
                reasons.append("gross_exposure")
            sectors = {}
            for key, value in values.items():
                info = self.universe[key]
                exempt = (info["asset_class"] == "unleveraged_us_etf" and info["diversified"]
                          and info["sector"] == "diversified" and not info["leveraged"] and not info["inverse"])
                limit = "diversified_etf_weight" if exempt else "company_weight"
                if value > post_equity * D(str(self.limits[limit])):
                    reasons.append(limit)
                if not exempt:
                    sectors[info["sector"]] = sectors.get(info["sector"], ZERO) + value
            if any(value > post_equity * D(str(self.limits["sector_weight"])) for value in sectors.values()):
                reasons.append("sector_weight")
        elif any(values.get(i, ZERO) > value for i, value in before.items() if i == instrument):
            reasons.append("not_a_reduction")
        return sorted(set(reasons))
