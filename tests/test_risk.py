from copy import deepcopy
from decimal import Decimal as D
import json
from pathlib import Path
import unittest

from trade_theorist.adapters.trader_user_sim import State
from trade_theorist.contracts import ContractError
from trade_theorist.fixtures import base_records
from trade_theorist.risk import Governor, validate_policy

FUND = "instrument:fixture-fund"
AT = "2099-01-03T21:02:00Z"


class RiskTests(unittest.TestCase):
    def setUp(self):
        self.policy = deepcopy(base_records()[1])
        self.policy["limits"].update(turnover=1.0)
        self.state = State(cash=D("10000"), initial_cash=D("10000"), peak=D("10000"), day_start=D("10000"))
        self.state.marks[FUND] = dict(price="100", session="2099-01-03", at="2099-01-03T21:00:00Z")
        self.order = dict(instrument_id=FUND, side="buy", quantity="10", expires_at="2099-01-08T00:00:00Z")

    def check(self, **kwargs):
        return Governor(self.policy).check(self.state, self.order, price=D("100"), fee=D("0"),
            session="2099-01-03", at=AT, sessions=["2099-01-03", "2099-01-04"], expected_session="2099-01-03", **kwargs)

    def test_every_numeric_portfolio_limit(self):
        cases = [("max_deployed_capital", "500.00", "deployed_capital"),
                 ("diversified_etf_weight", 0.05, "diversified_etf_weight"),
                 ("gross_exposure", 0.05, "gross_exposure"), ("turnover", 0.05, "turnover")]
        for key, value, reason in cases:
            with self.subTest(key=key):
                original = self.policy["limits"][key]
                self.policy["limits"][key] = value
                self.assertIn(reason, self.check())
                self.policy["limits"][key] = original
        self.state.submissions["2099-01-03"] = 5
        self.assertIn("order_frequency", self.check())
        self.state.submissions.clear()
        self.state.fills["2099-01-03"] = 5
        self.assertIn("order_frequency", self.check(execution=True))

    def test_single_company_etf_has_no_diversified_exception(self):
        self.order["quantity"] = "30"
        self.assertEqual(self.check(), [])
        self.policy["universe"][0].update(diversified=False, sector="technology")
        self.assertIn("company_weight", self.check())
        self.order["quantity"] = "50"
        self.assertIn("sector_weight", self.check())
        self.policy["universe"][0]["diversified"] = True
        self.assertIn("company_weight", self.check())
        self.policy["universe"][0].update(asset_class="us_equity", sector="diversified")
        self.assertIn("company_weight", self.check())

    def test_unknown_sector_universe_funds_expiry_and_position(self):
        self.policy["universe"][0]["sector"] = "unknown"
        self.assertIn("unknown_sector", self.check())
        self.policy["universe"][0]["sector"] = "diversified"
        self.order["instrument_id"] = "instrument:outside"
        self.assertEqual(self.check(), ["universe"])
        self.order["instrument_id"] = FUND
        self.order["quantity"] = "101"
        self.assertIn("funds", self.check())
        self.order.update(side="sell", quantity="1")
        self.assertIn("position", self.check())
        self.order["expires_at"] = AT
        self.assertIn("expired", self.check())

    def test_pending_orders_reserve_funds_exposure_and_turnover(self):
        self.state.orders["order:pending"] = dict(status="pending", instrument_id=FUND, side="buy", quantity="95", price_cap="100", reserved="9500")
        self.assertIn("funds", self.check())
        self.assertIn("gross_exposure", self.check())
        self.assertIn("turnover", self.check())
        self.state.orders["order:pending"]["side"] = "sell"
        self.state.orders["order:pending"]["reserved"] = "0"
        self.state.cash = D("500")
        self.assertIn("funds", self.check())

    def test_loss_drawdown_thresholds_and_reduction_safety(self):
        self.state.cash = D("9800")
        self.assertEqual(Governor(self.policy).loss_reasons(self.state, self.state.equity()), ["daily_loss"])
        self.assertIn("daily_loss", self.check())
        self.state.day_start = D("9800")
        self.state.peak = D("11000")
        self.assertIn("drawdown", self.check())
        self.state.halted = True
        self.order.update(side="sell", quantity="1")
        self.state.positions[FUND] = D("10")
        self.assertEqual(self.check(), [])
        self.state.marks.clear()
        self.assertIn("missing_mark", self.check())
        self.assertIn("unknown_equity", self.check())

    def test_sector_aggregation_and_pending_buys(self):
        first = self.policy["universe"][0]
        first.update(diversified=False, sector="technology")
        second = dict(first, instrument_id="instrument:second", symbol="SECOND")
        third = dict(first, instrument_id="instrument:third", symbol="THIRD")
        self.policy["universe"] += [second, third]
        self.state.cash = D("6400")
        for key in (second["instrument_id"], third["instrument_id"]):
            self.state.positions[key] = D("18")
            self.state.marks[key] = self.state.marks[FUND]
        self.assertIn("sector_weight", self.check())
        self.assertNotIn("company_weight", self.check())

    def test_quote_age_spread_and_malformed_quotes(self):
        governor = Governor(self.policy)
        good = dict(bid="100", ask="100.1", observed_at="2099-01-03T21:01:00Z", at=AT)
        self.assertEqual(governor.check_quote(**good), [])
        self.assertIn("quote_age", governor.check_quote(**dict(good, observed_at="2099-01-03T21:00:59Z")))
        self.assertIn("quote_age", governor.check_quote(**dict(good, observed_at="2099-01-03T21:03:00Z")))
        self.assertIn("spread", governor.check_quote(**dict(good, ask="101")))
        for value in ("NaN", "Infinity", "-1", "garbage"):
            self.assertEqual(governor.check_quote(**dict(good, bid=value)), ["invalid_quote"])

    def test_sell_fee_cannot_consume_another_orders_reserved_cash(self):
        self.state.cash = D("100")
        self.state.positions[FUND] = D("1")
        self.state.orders["order:pending"] = dict(status="pending", instrument_id=FUND, side="buy", quantity="1", price_cap="100", reserved="100")
        self.order.update(side="sell", quantity="1")
        reasons = Governor(self.policy).check(self.state, self.order, price=D("1"), fee=D("2"), session="2099-01-03", at=AT,
                    sessions=["2099-01-03"], expected_session="2099-01-03")
        self.assertIn("funds", reasons)

    def test_halt_all_requires_the_whole_universe_to_be_fresh(self):
        self.policy["universe"].append(dict(self.policy["universe"][0], instrument_id="instrument:second", symbol="SECOND"))
        self.assertIn("missing_mark", self.check())
        self.policy["clock"]["missing_data"] = "halt_affected"
        self.assertEqual(self.check(), [])

    def test_paper_policy_numeric_approval_and_nonfixture_gate(self):
        records = base_records()
        policy, experiment = records[1], records[3]
        self.assertEqual(validate_policy(policy, experiment), policy)
        experiment["regime"] = "forward_paper"
        with self.assertRaises(ContractError):
            validate_policy(policy, experiment)
        template = json.loads((Path(__file__).resolve().parents[1] / "examples/paper-policy.template.json").read_text())
        with self.assertRaises(ContractError):
            validate_policy(template, experiment)
        policy.update(stage="paper", synthetic=False, contamination="forward-insufficient", approval_ref="owner:recorded",
                      approved_at="2098-12-01T00:00:00Z", operator="owner", kill_switch_owner="owner",
                      reconciliation_owner="owner", incident_owner="owner")
        with self.assertRaises(ContractError):
            validate_policy(policy, experiment)
        policy["costs"].update(fill_model="raw-next-open-v1", corporate_actions="explicit_raw_events_v1")
        self.assertEqual(validate_policy(policy, experiment), policy)
        for key in policy["limits"]:
            broken = deepcopy(policy)
            broken["limits"][key] = None
            with self.subTest(key=key), self.assertRaises(ContractError):
                validate_policy(broken, experiment)
        for key in ("operator", "kill_switch_owner", "approval_ref"):
            broken = dict(policy, **{key: None})
            with self.subTest(key=key), self.assertRaises(ContractError):
                validate_policy(broken, experiment)


if __name__ == "__main__":
    unittest.main()
