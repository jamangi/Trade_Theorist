from copy import deepcopy
from decimal import Decimal as D
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from unittest.mock import patch

from trade_theorist.contracts import ContractError, digest
from trade_theorist.fixtures_accounting_v2 import FixtureV2, golden, at
from trade_theorist.fixtures_v2 import INSTRUMENT
from trade_theorist.storage_v2 import V2Store
from trade_theorist.evaluate.portfolio_v2 import evaluate, compare


class AccountingV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.store = V2Store(self.temp.name, synthetic=True); self.addCleanup(self.store.close)

    def report(self, fixture, day, *, receipt=None, **kwargs):
        return evaluate(self.store, fixture.portfolio, effective_cutoff=at(day), receipt_cutoff=receipt or at(day), **kwargs)

    def simple(self, name="simple", *, flows=None, **kwargs):
        f = FixtureV2(self.store, name, flows=flows or [("funding", at(1), "1000.00")], **kwargs)
        f.event("funding", 1, amount="1000.00", boundary_mark_ids=[])
        f.mark(1, "100")
        return f

    def test_golden_production_persistence_and_stale_values(self):
        with patch("socket.create_connection", side_effect=AssertionError("Network forbidden")):
            f = golden(self.store)
            r = self.report(f, 11)
        expected = json.loads((Path(__file__).resolve().parents[1] / "examples/meta-001/performance-v2.fixture.json").read_text())["expected"]["before_stale"]
        for field, gold in (("cash", "cash"), ("reserved", "reserved"), ("fifo_basis", "basis"), ("realized", "realized"), ("income", "income"), ("fees", "fees")):
            self.assertEqual(D(r[field]), D(expected[gold]))
        for field, gold in (("equity", "equity"), ("strategy_pnl", "strategy_pnl"), ("twr", "twr"), ("max_drawdown", "max_drawdown")):
            self.assertEqual(D(r[field]["value"]), D(expected[gold]))
        lots = list(self.store.iter_v2(portfolio_id=f.portfolio, kind="lot"))
        self.assertEqual([(D(l["remaining_quantity"]), D(l["remaining_basis"])) for l in lots], [(D(2), D(101)), (D(4), D(242))])
        stale = self.report(f, 12)
        for field in ("equity", "unrealized", "strategy_pnl", "twr", "max_drawdown"):
            self.assertIsNone(stale[field]["value"])
            self.assertTrue(stale[field]["reason"])
        self.assertEqual(stale["cash"], r["cash"])
        self.assertEqual(stale["realized"], r["realized"])
        self.assertFalse(stale["promotion_eligible"])
        self.store.verify()

    def test_withdrawals_are_not_losses_and_missing_flow_nav_is_null(self):
        flows = [("funding", at(1), "1000.00"), ("withdrawal", at(3), "100.00")]
        for name, boundary in (("exact", True), ("missing", False)):
            f = self.simple(name, flows=flows, fee="0.00")
            order = f.order(1, "2", "100")
            mark = f.mark(2, "100"); f.fill(order, mark, 2, "2")
            mark = f.mark(3, "110")
            f.event("withdrawal", 3, amount="100.00", boundary_mark_ids=[mark] if boundary else [])
            r = self.report(f, 3)
            self.assertEqual(D(r["cash"]), D(700))
            self.assertEqual(D(r["strategy_pnl"]["value"]), D(20))
            if boundary: self.assertEqual(D(r["twr"]["value"]), D(".02"))
            else:
                self.assertIsNone(r["twr"]["value"])
                self.assertTrue(r["halted"])

    def test_full_withdrawal_requires_end_and_distinct_funded_segment(self):
        f = self.simple(flows=[("funding", at(1), "1000.00"), ("withdrawal", at(2), "1000.00")])
        # Refunding requires a preregistered second segment; the initial plan remains immutable.
        f.event("withdrawal", 2, amount="1000.00", boundary_mark_ids=[])
        f.event("segment_end", 2, reason="Fully withdrawn")
        r = self.report(f, 2)
        self.assertEqual(D(r["twr"]["value"]), 0)
        self.assertEqual(r["closed_segments"][0]["segment_id"], f.segment)
        with self.assertRaises(ContractError): f.event("funding", 3, amount="1000.00", boundary_mark_ids=[])

    def test_refunded_segment_does_not_stitch_returns(self):
        from trade_theorist.fixtures_v2 import bundle
        # Build plan and both segments atomically before any funding.
        original = FixtureV2(self.store, "refunded", flows=[])
        # Use a fresh independent store because an approved plan is never rewritten.
        with TemporaryDirectory() as root, V2Store(root, synthetic=True) as s:
            records = list(self.store.iter_v2(portfolio_id=original.portfolio))
            core = list(self.store.iter_v2())
            segment = next(r for r in core if r["record_type"] == "funded_segment")
            second = dict(segment, id="segment:refunded-second", ordinal=2, previous_segment_id=segment["id"], start_at=at(3), reason="refunding")
            plan = next(r for r in core if r["record_type"] == "accounting_plan")
            plan["flows"] = [dict(segment_id=segment["id"], event_type="funding", effective_at=at(1), amount="1000.00"),
                dict(segment_id=segment["id"], event_type="withdrawal", effective_at=at(2), amount="1000.00"),
                dict(segment_id=second["id"], event_type="funding", effective_at=at(3), amount="500.00")]
            s.put_v2(core + [second])
            from trade_theorist.adapters.trader_user_sim.v2 import SimulatorV2
            e = SimulatorV2(s, original.portfolio)
            for n, (kind, when, sid, payload) in enumerate([
                ("funding", at(1), segment["id"], dict(amount="1000.00", boundary_mark_ids=[])),
                ("halt", at(1,1), segment["id"], dict(reason="Owner review required")),
                ("withdrawal", at(2), segment["id"], dict(amount="1000.00", boundary_mark_ids=[])),
                ("segment_end", at(2), segment["id"], dict(reason="Fully withdrawn")),
                ("funding", at(3), second["id"], dict(amount="500.00", boundary_mark_ids=[]))]):
                e.command(f"command:refunding-{n}", [e.event(f"event:refunding-{n}", kind, when, segment_id=sid, **payload)])
            r = evaluate(s, e.portfolio_id, effective_cutoff=at(3), receipt_cutoff=at(3))
            self.assertEqual(r["segment_id"], second["id"])
            self.assertEqual(D(r["initial_funding"]), 500)
            self.assertEqual(len(r["closed_segments"]), 1)
            self.assertTrue(r["halted"])

    def test_funding_policy_and_available_cash_are_enforced(self):
        f = self.simple(flows=[("funding", at(1), "1000.00"), ("withdrawal", at(2), "900.00")])
        f.order(1, "2", "100")
        before = self.store.verify_v2()
        with self.assertRaises(ContractError): f.event("contribution", 2, amount="500.00", boundary_mark_ids=[])
        with self.assertRaises(ContractError): f.event("withdrawal", 2, amount="900.00", boundary_mark_ids=[])
        self.assertEqual(before, self.store.verify_v2())

    def test_partial_fills_release_only_own_reservation_and_fees_once(self):
        f = self.simple()
        a, b = f.order(1, "3", "100"), f.order(1, "1", "100")
        mark = f.mark(2, "100")
        first = f.fill(a, mark, 2, "1")
        before = self.store.verify_v2()
        self.assertEqual(f.fill(a, mark, 2, "1"), first)
        self.assertEqual(before, self.store.verify_v2())
        r = self.report(f, 2)
        self.assertEqual(D(r["cash"]), 899)
        self.assertEqual(D(r["reserved"]), 303)
        mark = f.mark(3, "100"); f.fill(a, mark, 3, "2")
        r = self.report(f, 3)
        self.assertEqual(D(r["fees"]), 3)
        self.assertEqual(D(r["reserved"]), 101)
        self.assertEqual(next(o for o in r["order_outcomes"] if o["order_id"] == b)["remaining_quantity"], "1.00000000")
        with self.assertRaises(ContractError): f.fill(a, mark, 3, "1")

    def test_multiple_instruments_and_fifo_residuals(self):
        f = self.simple(extra_instrument=True, fee="0.00")
        f.mark(1, "1", instrument="instrument:fixture-second")
        first = f.order(1, "3", "100")
        other = f.order(1, "3", "1", instrument="instrument:fixture-second")
        mark = f.mark(2, "100"); f.fill(first, mark, 2, "3")
        mark = f.mark(2, "1", instrument="instrument:fixture-second"); f.fill(other, mark, 2, "3")
        # A cent acquisition fee divided across three later FIFO sales retains its residual.
        fill_id = next(e["id"] for e in self.store.iter_v2(portfolio_id=f.portfolio, kind="ledger_event") if e["event_type"] == "fill" and e["payload"]["instrument_id"] == INSTRUMENT)
        corrected = deepcopy(self.store.v2_record(fill_id)["payload"])
        corrected["fees"] = "0.01"
        f.engine.correct("command:cent-fee", fill_id, corrected, observed_at=at(2,1))
        for day in (3, 4, 5):
            f.mark(day - 1, "100", minute=2)
            f.mark(day - 1, "1", instrument="instrument:fixture-second", minute=2)
            order = f.order(day - 1, "1", "100", side="sell", minute=3)
            mark = f.mark(day, "100"); f.mark(day, "1", instrument="instrument:fixture-second")
            f.fill(order, mark, day, "1")
        r = self.report(f, 5)
        self.assertEqual(D(r["fifo_basis"]), 3)
        self.assertEqual(D(r["realized"]), D("-.01"))
        self.assertEqual(D(r["hit_rate"]["value"]), 0)
        self.assertEqual(r["holdings"][0]["instrument_id"], "instrument:fixture-second")

    def test_missing_intermediate_mark_keeps_endpoint_twr_but_not_drawdown(self):
        f = self.simple(fee="0.00")
        order = f.order(1, "2", "100")
        mark = f.mark(2, "100"); f.fill(order, mark, 2, "2")
        f.mark(3, None, status="missing")
        f.mark(4, "110")
        r = self.report(f, 4)
        self.assertEqual(D(r["twr"]["value"]), D(".02"))
        self.assertIsNone(r["max_drawdown"]["value"])
        self.assertIsNone(r["volatility"]["value"])

    def test_mark_correction_as_known_and_restated(self):
        f = self.simple(fee="0.00")
        order = f.order(1, "2", "100")
        mark = f.mark(2, "100"); f.fill(order, mark, 2, "2")
        close = f.mark(3, "110")
        original = self.report(f, 3)
        payload = dict(self.store.v2_record(close)["payload"], price="105", observation_revision=2, received_at=at(4), eligibility_cutoff=at(4))
        f.engine.correct("command:correct-mark", close, payload, observed_at=at(4))
        self.assertEqual(self.report(f, 3), original)
        revised = self.report(f, 3, receipt=at(4))
        self.assertEqual(D(original["equity"]["value"]), 1020)
        self.assertEqual(D(revised["equity"]["value"]), 1010)
        self.assertNotEqual(original["id"], revised["id"])
        self.assertEqual(revised["projection_revision"], 2)
        f.engine.correct("command:withdraw-mark", close, None, observed_at=at(5))
        self.assertIsNone(self.report(f, 3, receipt=at(5))["equity"]["value"])

    def test_projection_and_execution_crash_recover_without_cash_duplication(self):
        f = golden(self.store)
        before = self.store.verify_v2()
        def fail(): raise RuntimeError("Interrupted")
        with self.assertRaises(RuntimeError): self.report(f, 11, before_commit=fail)
        self.assertEqual(self.store.verify_v2(), before)
        r = self.report(f, 11)
        after = self.store.verify_v2()
        self.assertEqual(self.report(f, 11), r)
        self.assertEqual(self.store.verify_v2(), after)
        g = self.simple("crash")
        order = g.order(1, "1", "100"); mark = g.mark(2, "100")
        before = self.store.verify_v2()
        with self.assertRaises(RuntimeError): g.engine.fill_order("command:crash-fill", order, mark, "1", at=at(2), before_commit=fail)
        self.assertEqual(self.store.verify_v2(), before)
        g.engine.fill_order("command:crash-fill", order, mark, "1", at=at(2))
        self.assertEqual(D(self.report(g, 2)["cash"]), 899)

    def test_dividend_timing_duplicates_and_unsupported_cash_in_lieu(self):
        f = golden(self.store)
        before, paid = self.report(f, 5), self.report(f, 6)
        self.assertEqual(D(before["receivables"]), 3)
        self.assertEqual(D(paid["income"]), 3)
        self.assertEqual(D(paid["receivables"]), 0)
        entitlement = next(e for e in self.store.iter_v2(portfolio_id=f.portfolio, kind="ledger_event") if e["event_type"] == "dividend_entitlement")
        with self.assertRaises(ContractError): f.event("dividend_payment", 6, entitlement_id=entitlement["id"], amount="3.00")
        split = next(e for e in self.store.iter_v2(portfolio_id=f.portfolio, kind="ledger_event") if e["event_type"] == "split")
        f.event("cash_in_lieu", 12, action_event_id=split["id"], instrument_id=INSTRUMENT, quantity="0.5", price="60", amount="30.00")
        r = self.report(f, 12)
        self.assertEqual(D(r["cash"]), 1188)
        self.assertTrue(r["halted"])
        self.assertTrue(any("Cash-in-lieu" in g for g in r["gaps"]))

    def test_expenses_are_separate_from_trading_and_cross_basis_comparison_denied(self):
        f = golden(self.store)
        for recurring, amount, category in ((True, "2.00", "model"), (False, "100.00", "learning")):
            expense = f.engine.record("operating_expense", "expense:" + category, at(11), portfolio_id=f.portfolio,
                effective_at=at(11), category=category, recurring=recurring, amount=amount, reason=None)
            f.engine.command("command:expense-" + category, [expense])
        r = self.report(f, 11)
        self.assertEqual(D(r["economics_pnl"]["value"]), 46)
        self.assertEqual(D(r["strategy_pnl"]["value"]), 48)
        self.assertEqual(D(r["twr"]["value"]), D(".05750570"))
        self.assertEqual(D(r["one_time_expense"]["value"]), 100)
        other = dict(r, comparison_hash=digest("different paper execution"))
        with self.assertRaises(ContractError): compare(r, other)
        self.assertFalse(compare(r, r)["promotion_eligible"])

    def test_matching_broad_market_baseline_and_flow_mismatch(self):
        from trade_theorist.fixtures_accounting_v2 import broad_market
        b = broad_market(self.store)
        f = golden(self.store, baseline=b.portfolio)
        r = self.report(f, 11)
        self.assertIn("matched flow", r["benchmark_status"])
        self.assertEqual(D(r["broad_market_baseline"]["value"]), D(".20542373"))
        self.assertEqual(D(r["cash_baseline"]["value"]), 0)
        g = self.simple("different-flows", baseline=b.portfolio)
        r = self.report(g, 11)
        self.assertIsNone(r["broad_market_baseline"]["value"])
        self.assertEqual(r["benchmark_status"], "unmatched")

    def test_deposit_does_not_hide_loss_or_clear_recorded_halt(self):
        f = self.simple("loss", flows=[("funding", at(1), "1000.00"), ("contribution", at(3), "500.00")], fee="0.00")
        order = f.order(1, "9", "100")
        mark = f.mark(2, "100"); f.fill(order, mark, 2, "9")
        loss_mark = f.mark(3, "40")
        f.event("contribution", 3, amount="500.00", boundary_mark_ids=[loss_mark])
        r = self.report(f, 3)
        self.assertEqual(D(r["equity"]["value"]), 960)
        self.assertEqual(D(r["twr"]["value"]), D("-.54"))
        self.assertEqual(D(r["max_drawdown"]["value"]), D(".54"))
        self.assertTrue(r["halted"])
        with self.assertRaises(ContractError): f.order(3, "1", "40")
        correction = dict(self.store.v2_record(loss_mark)["payload"], price="100", received_at=at(4), eligibility_cutoff=at(4), observation_revision=2)
        f.engine.correct("command:restore-price", loss_mark, correction, observed_at=at(4))
        self.assertTrue(self.report(f, 3, receipt=at(4))["halted"])

    def test_fractional_split_requires_cash_in_lieu_review_when_disabled(self):
        f = self.simple("whole-shares", fractional=False, fee="0.00")
        order = f.order(1, "1", "100")
        mark = f.mark(2, "100"); f.fill(order, mark, 2, "1")
        post = f.mark(3, "200")
        f.event("split", 3, action_id="action:reverse", instrument_id=INSTRUMENT, numerator=1, denominator=2, mark_id=post, pending_orders="none")
        r = self.report(f, 3)
        self.assertTrue(r["halted"])
        self.assertIsNone(r["equity"]["value"])
        self.assertEqual(D(r["cash"]), 900)

    def test_no_cross_portfolio_event_or_future_order_admission(self):
        a, b = self.simple("a"), self.simple("b")
        e = b.engine.event("event:foreign", "halt", at(2), reason="Foreign event")
        before = self.store.verify_v2()
        with self.assertRaises(ContractError): a.engine.command("command:foreign", [e])
        self.assertEqual(self.store.verify_v2(), before)

    def test_separate_disposal_fee_changes_closed_trade_hit_rate_once(self):
        f = self.simple("separate-fee", fee="0.00")
        buy = f.order(1, "1", "100")
        mark = f.mark(2, "100"); f.fill(buy, mark, 2, "1")
        sale = f.order(2, "1", "100.01", side="sell")
        f.mark(3, "100.01")
        fill = f.engine.event("event:separate-sale", "fill", at(3), order_id=sale, instrument_id=INSTRUMENT,
            side="sell", quantity="1", price="100.01", notional="100.01", fees="0.00", fee_treatment="separate", incremental_fill_id="fill:separate-sale")
        f.engine.command("command:separate-sale", [fill])
        fee = f.engine.event("event:separate-fee", "fee", at(3), amount="0.02", allocation="disposal", fill_id=fill["id"])
        f.engine.command("command:separate-fee", [fee])
        f.engine.command("command:separate-fee", [fee])
        r = self.report(f, 3)
        self.assertEqual(D(r["realized"]), D("-.01"))
        self.assertEqual(D(r["fees"]), D(".02"))
        self.assertEqual(D(r["hit_rate"]["value"]), 0)
        self.assertEqual(D(r["lot_relief_win_rate"]["value"]), 0)

    def test_partial_reservation_rounding_allows_exact_cent_cancellation(self):
        f = self.simple("reserve-cents", fee="0.00")
        order = f.order(1, "3", "100", reserve="301.00")
        mark = f.mark(2, "100"); f.fill(order, mark, 2, "1")
        self.assertEqual(D(self.report(f, 2)["reserved"]), D("200.67"))
        reservation = next(e for e in self.store.iter_v2(portfolio_id=f.portfolio, kind="ledger_event") if e["event_type"] == "reservation")
        f.event("release", 2, order_id=order, reservation_id=reservation["id"], cash="200.67", quantity="0", reason="cancelled")
        r = self.report(f, 2)
        self.assertEqual(D(r["reserved"]), 0)
        self.assertEqual(D(r["cash"]), 900)

    def test_whole_share_policy_and_same_segment_refunding_are_rejected(self):
        f = self.simple("whole-policy", fractional=False, flows=[("funding", at(1), "1000.00"),
            ("withdrawal", at(2), "1000.00"), ("contribution", at(3), "500.00")])
        with self.assertRaises(ContractError): f.order(1, "0.5", "100")
        f.event("withdrawal", 2, amount="1000.00", boundary_mark_ids=[])
        with self.assertRaises(ContractError): f.event("contribution", 3, amount="500.00", boundary_mark_ids=[])

    def test_corrected_execution_mark_preserves_previously_accepted_fill(self):
        f = self.simple("execution-mark", fee="0.00")
        order = f.order(1, "2", "100")
        mark = f.mark(2, "100"); f.fill(order, mark, 2, "2")
        original = self.report(f, 2)
        payload = dict(self.store.v2_record(mark)["payload"], price="105", observation_revision=2,
            received_at=at(3), eligibility_cutoff=at(3))
        f.engine.correct("command:execution-mark", mark, payload, observed_at=at(3))
        self.assertEqual(self.report(f, 2), original)
        restated = self.report(f, 2, receipt=at(3))
        self.assertEqual(D(restated["cash"]), 800)
        self.assertEqual(D(restated["fifo_basis"]), 200)
        self.assertEqual(D(restated["equity"]["value"]), 1010)


if __name__ == "__main__": unittest.main()
