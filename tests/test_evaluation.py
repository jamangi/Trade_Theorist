from copy import deepcopy
from decimal import Decimal as D
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from trade_theorist.contracts import ContractError
from trade_theorist.evaluate import Evaluator, series_metrics
from trade_theorist.operations import run_demo, FINAL_CUTOFF, demo_setups
from trade_theorist.storage import Store


class MetricTests(unittest.TestCase):
    def test_manual_returns_drawdown_turnover_and_roundtrip_hit_rate(self):
        import json
        expected = json.loads((Path(__file__).resolve().parents[1] / "examples/evaluation/metric-checks.json").read_text())["daily_series"]
        points = [dict(equity=v) for v in ("1000", "1100", "990")]
        result = series_metrics(points, initial_cash="1000", traded_notional=D("500"), closed_gains=[D("5"), D("-1")])
        self.assertEqual(D(result["net_return"]["value"]), D("-.01"))
        self.assertEqual(D(result["max_drawdown"]["value"]), D(".1"))
        self.assertAlmostEqual(D(result["turnover"]["value"]), D(500) / (D(3090) / 3), places=8)
        self.assertEqual(D(result["hit_rate"]["value"]), D(".5"))
        for key in ("net_return", "max_drawdown", "turnover"):
            self.assertEqual(D(result[key]["value"]), D(expected[key]))

    def test_missing_sessions_do_not_create_zero_risk_or_bridge_returns(self):
        points = [dict(equity=v) for v in ("1000", None, "1100")]
        result = series_metrics(points, initial_cash="1000")
        self.assertEqual(D(result["net_return"]["value"]), D(".1"))
        for key in ("max_drawdown", "turnover", "daily_volatility", "worst_session", "hit_rate"):
            self.assertIsNone(result[key]["value"])
            self.assertTrue(result[key]["reason"])
        self.assertIsNone(points[1]["drawdown"])
        self.assertIsNone(series_metrics([], initial_cash="1000")["net_return"]["value"])


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = TemporaryDirectory()
        run_demo(Path(cls.base.name) / "base")
        with Store(Path(cls.base.name) / "base", synthetic=True) as store:
            cls.backup = store.backup(store.root / "backup.sqlite3")

    @classmethod
    def tearDownClass(cls):
        cls.base.cleanup()

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store.restore(self.backup, Path(self.temp.name) / "restored", synthetic=True)
        self.addCleanup(self.store.close)
        self.evaluator = Evaluator(self.store)

    def report(self, name="index", as_of=FINAL_CUTOFF):
        return self.evaluator.evaluate("trial:demo-" + name, as_of=as_of)

    def test_fees_and_dividends_count_once_against_cash_and_index(self):
        report = self.report()
        self.assertEqual(D(report["equity"]), D("9999"))
        self.assertEqual(D(report["cash"]), D("9009"))
        self.assertEqual(D(report["fees"]), D("1"))
        self.assertEqual(D(report["income"]), D("10"))
        self.assertEqual(D(report["metrics"]["net_return"]["value"]), D("-.0001"))
        self.assertEqual(report["index_baseline"]["value"], report["metrics"]["net_return"]["value"])
        self.assertEqual(D(report["cash_baseline"]["value"]), D(0))

    def test_zero_trades_valid_cash_return_unavailable_hit_rate(self):
        report = self.report("council")
        self.assertEqual(report["fills"], 0)
        self.assertEqual(report["rejected_decisions"], 1)
        self.assertEqual(D(report["metrics"]["net_return"]["value"]), D(0))
        self.assertIsNone(report["metrics"]["hit_rate"]["value"])

    def test_historical_cutoff_stale_marks_and_pending_forecasts(self):
        earlier = self.report("trend", "2099-01-04T21:02:00Z")
        later = self.report("trend")
        self.assertEqual(D(earlier["equity"]), D("10019"))
        self.assertIsNone(later["equity"])
        self.assertIsNone(later["metrics"]["net_return"]["value"])
        self.assertEqual(later["forecasts"]["matured"], 1)
        self.assertEqual(later["forecasts"]["pending"], 1)
        self.assertEqual(D(later["metrics"]["brier"]["value"]), D(".2025"))
        before = self.report("index", "2099-01-03T21:10:00Z")
        self.assertEqual(before["forecasts"]["matured"], 0)
        self.assertEqual(before["forecasts"]["pending"], 2)
        self.assertEqual(before["fills"], 0)

    def test_immature_missing_and_repeated_evaluation(self):
        before = self.store.verify()
        report = self.report()
        self.assertEqual(report, self.report())
        self.assertEqual(before, self.store.verify())
        later = self.evaluator.forecasts(report["experiment_id"], report["portfolio_id"], "2099-01-07T00:00:00Z")
        self.assertEqual(later["unscorable"], 1)
        self.assertEqual(later["matured"], 1)

    def test_matched_advice_comparison_and_cross_regime_rejection(self):
        no_mail, mail = self.report("no-mail"), self.report("council")
        self.assertEqual(D(self.evaluator.compare_advice(no_mail, mail)["difference"]["value"]), D(0))
        changed = dict(mail, comparison_hash="different", regime="hindsight")
        with self.assertRaises(ContractError):
            self.evaluator.compare_advice(no_mail, changed)
        with self.assertRaises(ContractError):
            self.evaluator.compare_advice(self.report(), mail)

    def test_counterfactual_has_separate_capital_and_obeys_original_limits(self):
        counter, council = self.report("counterfactual"), self.report("council")
        self.assertNotEqual(counter["experiment_id"], council["experiment_id"])
        self.assertNotEqual(counter["portfolio_id"], council["portfolio_id"])
        self.assertEqual(counter["fills"], 0)
        self.assertEqual(D(counter["cash"]), D("10000"))
        decision = demo_setups()[0]["final"]["id"]
        local = self.evaluator.local_counterfactual(decision, "observation:demo-council-4", as_of=FINAL_CUTOFF)
        self.assertEqual(D(local["raw_price_change"]["value"]), D(".02"))
        self.assertIn("Never add", local["label"])

    def test_all_trials_and_failures_remain_visible_without_promotion(self):
        self.evaluator.trial_status("trial:demo-no-mail", "failed", at="2099-01-05T21:01:00Z")
        report = self.report("council")
        self.assertEqual(report["trial_count"], 7)
        # Query the earlier status without erasing the later partial window.
        registry = self.evaluator.registry(as_of="2099-01-05T21:01:30Z")
        self.assertEqual(next(t for t in registry if t["trial_id"] == "trial:demo-no-mail")["status"], "failed")
        self.assertFalse(report["promotion_eligible"])
        with self.assertRaises(ContractError):
            self.evaluator.approve_forward_review(report["report_id"], owner="fixture-owner", approval_ref="promote me", at=FINAL_CUTOFF)
        with self.assertRaisesRegex(ContractError, "window is still open"):
            self.evaluator.trial_status("trial:demo-council", "completed", at=FINAL_CUTOFF)

    def test_registration_cannot_reuse_capital_or_start_after_outcomes(self):
        setup = demo_setups()[1]
        for trial, clock in (("trial:duplicate", "2098-12-01T00:00:00Z"), (setup["trial_id"], FINAL_CUTOFF)):
            with self.subTest(trial=trial), self.assertRaises(ContractError):
                self.evaluator.register_trial(trial, setup["experiment"]["id"], setup["portfolio"]["id"], sessions=[], family_id="family:test", at=clock)
        with self.assertRaises(ContractError):
            self.evaluator.register_forecast("forecast:invalid", setup["final"]["id"], outcome_at="2099-01-06T21:00:00Z",
                                             threshold="100", probability="NaN", at="2099-01-03T21:09:00Z")

    def test_external_funding_is_not_misreported_as_return(self):
        from trade_theorist.adapters.trader_user_sim import VERSION
        report = self.report()
        self.store.append("event:extra-funding", report["experiment_id"], "simulation",
                          dict(version=VERSION, portfolio_id=report["portfolio_id"], type="funding", at=FINAL_CUTOFF, amount="10000.00"), created_at=FINAL_CUTOFF)
        with self.assertRaisesRegex(ContractError, "flow-adjusted"):
            self.report()

    def test_late_ingestion_cannot_retroactively_mature_a_forecast(self):
        from trade_theorist.operations import save_market
        from trade_theorist.ingest.market import Normalized
        from trade_theorist.contracts import digest
        setup = demo_setups()[1]
        clock = "2099-01-06T21:00:00Z"
        ingested = "2099-01-07T01:00:00Z"
        bar = dict(setup["payload"], event_at=clock, published_at=clock, ingested_at=ingested, session="2099-01-06")
        obs = dict(setup["observation"], id="observation:late-outcome", created_at=ingested, event_at=clock,
                   published_at=clock, ingested_at=ingested, payload_hash=digest(bar))
        save_market(self.store, Normalized(obs, bar))
        before = self.evaluator.forecasts(setup["experiment"]["id"], setup["portfolio"]["id"], "2099-01-06T22:00:00Z")
        after = self.evaluator.forecasts(setup["experiment"]["id"], setup["portfolio"]["id"], ingested)
        self.assertEqual(before["unscorable"], 1)
        self.assertEqual(after["matured"], 2)

    def test_hindsight_and_historical_results_never_enter_promotion(self):
        from trade_theorist.fixtures import base_records, EXP
        from trade_theorist.adapters.trader_user_sim import Simulator
        from trade_theorist.heartbeat.fixture import SESSIONS
        for regime, grade in (("hindsight", "hindsight-contaminated"), ("historical_restricted", "historical-qualified")):
            with self.subTest(regime=regime), TemporaryDirectory() as directory, Store(directory) as store:
                records = base_records()
                for record in records[1:]:
                    record["contamination"] = grade
                records[1].update(stage="paper", synthetic=False, approval_ref="owner:fixture-test", approved_at="2098-01-01T00:00:00Z",
                                  operator="owner", kill_switch_owner="owner", reconciliation_owner="owner", incident_owner="owner")
                records[1]["costs"].update(fill_model="raw-next-open-v1", corporate_actions="explicit_raw_events_v1")
                records[3]["regime"] = regime
                store.put_records(records)
                Simulator(store, EXP, records[4]["id"], SESSIONS)
                evaluator = Evaluator(store)
                evaluator.register_trial("trial:historical", EXP, records[4]["id"], sessions=SESSIONS, family_id="family:historical", at="2098-12-01T00:00:00Z")
                report = evaluator.evaluate("trial:historical", as_of=FINAL_CUTOFF)
                self.assertEqual(report["evidence_grade"], grade)
                self.assertFalse(report["promotion_eligible"])
                with self.assertRaises(ContractError):
                    evaluator.approve_forward_review(report["report_id"], owner="owner", approval_ref="approve", at=FINAL_CUTOFF)


if __name__ == "__main__":
    unittest.main()
