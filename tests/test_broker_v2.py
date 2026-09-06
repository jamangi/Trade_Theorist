from copy import deepcopy
from decimal import Decimal as D
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from trade_theorist.contracts import ContractError, digest
from trade_theorist.fixtures_accounting_v2 import FixtureV2, at
from trade_theorist.fixtures_v2 import INSTRUMENT
from trade_theorist.storage_v2 import V2Store
from trade_theorist.adapters.trader_user_sim.broker_v2 import BrokerReconcilerV2
from trade_theorist.evaluate.portfolio_v2 import evaluate


class BrokerV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.store = V2Store(self.temp.name, synthetic=True); self.addCleanup(self.store.close)
        self.f = FixtureV2(self.store, "broker", mode="council", basis="paper_broker")
        self.f.event("funding", 1, amount="1000.00", boundary_mark_ids=[])
        self.f.mark(1, "100")
        self.order = self.f.order(1, "3", "100")
        self.mapping = self.store.prepare_submission(self.order, at=at(1,1))
        self.broker = BrokerReconcilerV2(self.store, self.f.portfolio)

    def update(self, name, quantity, *, minute=0, received_minute=None, notional=None, fee=None, status="partially_filled"):
        return self.f.engine.record("broker_update", "broker-update:" + name, at(2, received_minute if received_minute is not None else minute),
            portfolio_id=self.f.portfolio, segment_id=self.f.segment, mapping_id=self.mapping["id"], provider_event_id="provider:" + name,
            broker_order_id="original-synthetic-account-order", effective_at=at(2,minute), observed_at=at(2, received_minute if received_minute is not None else minute),
            cumulative_quantity=str(quantity), cumulative_notional=notional or f"{quantity * 100}.00", cumulative_fees=fee or f"{quantity}.00",
            incremental_fill_id="provider-fill:" + name if status in {"filled", "partially_filled"} else None, status=status)

    def report(self, minute=0, receipt_minute=None):
        return evaluate(self.store, self.f.portfolio, effective_cutoff=at(2,minute), receipt_cutoff=at(2,receipt_minute if receipt_minute is not None else minute))

    def test_partial_cancellation_retains_executions_and_is_idempotent_offline(self):
        partial = self.update("one", 1)
        with patch("socket.create_connection", side_effect=AssertionError("No account traffic")):
            self.assertEqual(self.broker.update(partial), "applied")
        r = self.report()
        self.assertEqual(D(r["cash"]), 899)
        self.assertEqual(D(r["reserved"]), 202)
        before = self.store.verify_v2()
        self.assertEqual(self.broker.update(partial), "reused")
        self.assertEqual(before, self.store.verify_v2())
        cancel = self.update("cancel", 1, minute=1, status="cancelled")
        self.assertEqual(self.broker.update(cancel), "applied")
        r = self.report(1)
        self.assertEqual(D(r["cash"]), 899)
        self.assertEqual(D(r["reserved"]), 0)
        self.assertEqual(r["order_outcomes"][0]["status"], "cancelled")
        self.assertEqual(D(r["order_outcomes"][0]["filled_quantity"]), 1)
        self.assertEqual(len(list(self.store.iter_v2(kind="submission_mapping"))), 1)

    def test_late_earlier_update_restates_attribution_without_second_cash_movement(self):
        later = self.update("later", 3, minute=2, status="filled")
        self.assertEqual(self.broker.update(later), "applied")
        before = self.report(2)
        earlier = self.update("earlier", 1, minute=1, received_minute=3)
        self.assertEqual(self.broker.update(earlier), "applied")
        after = self.report(2,3)
        self.assertEqual(before["cash"], after["cash"])
        self.assertEqual(D(after["cash"]), 697)
        self.assertEqual(D(after["fifo_basis"]), 303)
        self.assertEqual(self.report(2), before)
        self.assertEqual(sum(e["event_type"] == "correction" for e in self.store.iter_v2(kind="ledger_event")), 1)

    def test_conflicting_update_halts_without_erasing_confirmed_fill(self):
        update = self.update("one", 1)
        self.broker.update(update)
        bad = dict(update, cumulative_notional="90.00")
        self.assertEqual(self.broker.update(bad), "quarantined")
        r = self.report()
        self.assertEqual(D(r["cash"]), 899)
        self.assertTrue(r["halted"])
        self.assertIsNone(r["equity"]["value"])
        self.assertEqual(D(r["order_outcomes"][0]["filled_quantity"]), 1)

    def test_timeout_keeps_identity_and_reservation_then_accepts_reconciled_fill(self):
        self.broker.timeout(self.order, at=at(2))
        r = self.report()
        self.assertTrue(r["halted"])
        self.assertEqual(D(r["reserved"]), 303)
        self.assertEqual(self.store.prepare_submission(self.order, at=at(2,1)), self.mapping)
        self.assertEqual(self.broker.update(self.update("after-timeout", 1, minute=1)), "applied")
        r = self.report(1)
        self.assertEqual(D(r["cash"]), 899)
        self.assertTrue(r["halted"])
        self.assertEqual(len(list(self.store.iter_v2(kind="submission_mapping"))), 1)

    def test_account_reset_and_unknown_aggregate_cash_do_not_refund_capital(self):
        r = self.broker.account("reconcile:reset", effective_at=at(2), observed_at=at(2), cash="100000.00", positions=[], reset=True, evidence_hash=digest("original reset fixture"))
        self.assertEqual(r["status"], "halted")
        report = self.report()
        self.assertEqual(D(report["cash"]), 1000)
        self.assertEqual(D(report["initial_funding"]), 1000)
        self.assertIsNone(report["equity"]["value"])

    def test_interrupted_update_retries_without_duplicate_fill_or_outbox(self):
        before = self.store.verify_v2()
        def fail(): raise RuntimeError("Interrupted update")
        update = self.update("one", 1)
        with self.assertRaises(RuntimeError): self.broker.update(update, before_commit=fail)
        self.assertEqual(before, self.store.verify_v2())
        self.assertEqual(self.broker.update(update), "applied")
        self.assertEqual(D(self.report()["cash"]), 899)

    def test_individual_and_cross_portfolio_broker_mapping_denied(self):
        individual = FixtureV2(self.store, "individual")
        with self.assertRaises(ContractError): BrokerReconcilerV2(self.store, individual.portfolio)
        bad = dict(self.update("cross", 1), portfolio_id=individual.portfolio)
        with self.assertRaises(ContractError): self.broker.update(bad)
        self.assertEqual(list(self.store.iter_v2(portfolio_id=individual.portfolio, kind="ledger_event")), [])


if __name__ == "__main__": unittest.main()
