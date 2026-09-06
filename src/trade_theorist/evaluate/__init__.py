"""Deterministic ledger evaluation, preregistered forecasts and evidence review."""

from decimal import Decimal as D
import json

from ..adapters.trader_user_sim import State, VERSION, timestamp
from ..contracts import ContractError, digest

ZERO = D("0")


def metric(value=None, reason=None, *, unit="ratio"):
    if value is None:
        return {"value": None, "reason": reason or "Insufficient eligible evidence", "unit": unit}
    number = D(str(value))
    if not number.is_finite():
        raise ContractError("Metrics must be finite")
    return {"value": format(number.quantize(D("0.00000001")), "f"), "reason": None, "unit": unit}


def series_metrics(points, *, initial_cash, traded_notional=ZERO, closed_gains=()):
    """Daily schedule includes missing points; never bridge a gap with invented returns."""
    initial = D(initial_cash)
    if initial <= 0:
        raise ContractError("Positive initial capital required")
    values = [None if p["equity"] is None else D(p["equity"]) for p in points]
    complete = bool(values) and all(v is not None for v in values)
    peak, drawdowns, daily, previous = initial, [], [], initial
    for p, value in zip(points, values):
        if value is None:
            p["drawdown"] = None
            previous = None
            continue
        peak = max(peak, value)
        dd = 1 - value / peak
        p["drawdown"] = metric(dd)["value"]
        drawdowns.append(dd)
        if previous is not None and previous > 0:
            daily.append(value / previous - 1)
        previous = value
    mean = sum(values, ZERO) / len(values) if complete else None
    reason = "Missing closing marks in the declared schedule" if values else "No completed evaluation sessions"
    result = {
        "net_return": metric(values[-1] / initial - 1) if values and values[-1] is not None else metric(reason=reason),
        "max_drawdown": metric(max(drawdowns)) if complete else metric(reason=reason),
        "turnover": metric(D(traded_notional) / mean) if mean and mean > 0 else metric(reason=reason),
        "hit_rate": metric(D(sum(g > 0 for g in closed_gains)) / len(closed_gains)) if closed_gains else metric(reason="No fully closed positions"),
        "worst_session": metric(min(daily)) if complete and daily else metric(reason=reason),
        "daily_volatility": metric(reason="At least two complete daily returns required"),
    }
    if complete and len(daily) >= 2:
        average = sum(daily, ZERO) / len(daily)
        variance = sum(((v - average) ** 2 for v in daily), ZERO) / (len(daily) - 1)
        result["daily_volatility"] = metric(variance.sqrt())
    return result


class Evaluator:
    def __init__(self, store):
        self.store = store

    def _event(self, identifier):
        row = self.store.connection.execute("SELECT * FROM events WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise ContractError("Evaluation record not found")
        event = dict(row)
        event["payload"] = json.loads(event.pop("body"))
        return event

    def register_trial(self, trial_id, experiment_id, portfolio_id, *, sessions, family_id, at,
                       role="strategy", baseline_trial_id=None, rejected_decision_id=None):
        experiment = self.store.record(experiment_id, "experiment")
        portfolio = self.store.record(portfolio_id, "portfolio")
        if portfolio["experiment_id"] != experiment_id or portfolio["mode"] != experiment["mode"]:
            raise ContractError("Trial portfolio must belong to its experiment and mode")
        if role not in {"strategy", "index_baseline", "counterfactual"} or not family_id:
            raise ContractError("Explicit trial family and supported role required")
        for existing in self.store.iter_events(kind="evaluation.trial"):
            if existing["payload"]["portfolio_id"] == portfolio_id and existing["id"] != trial_id:
                raise ContractError("Each trial requires independent portfolio identity")
        if timestamp(at) >= timestamp(experiment["start_at"]):
            raise ContractError("Trial must be registered before its evaluation window")
        if role == "counterfactual":
            rejected = self.store.record(rejected_decision_id, "recommendation")
            if rejected["portfolio_id"] == portfolio_id or rejected["experiment_id"] == experiment_id:
                raise ContractError("Counterfactual needs independent capital and experiment identity")
        elif rejected_decision_id is not None:
            raise ContractError("Only counterfactual trials reference rejected decisions")
        if not sessions or any(set(s) != {"session", "open_at", "close_at"} for s in sessions):
            raise ContractError("Explicit UTC session schedule required")
        previous = None
        for session in sessions:
            opened, closed = timestamp(session["open_at"]), timestamp(session["close_at"])
            if opened >= closed or opened.date().isoformat() != session["session"] or closed.date().isoformat() != session["session"] or (previous and opened <= previous):
                raise ContractError("Invalid evaluation session schedule")
            if opened < timestamp(experiment["start_at"]) or closed > timestamp(experiment["end_at"]):
                raise ContractError("Session outside registered evaluation window")
            previous = closed
        policy = self.store.record(experiment["policy_id"], "policy")
        knowledge = [self.store.record(c, "character") for c in experiment["character_versions"]]
        comparison = {k: experiment[k] for k in ("mode", "regime", "universe", "start_at", "end_at", "data_feeds", "costs", "knowledge_cutoff", "decision_cadence", "sizing_rules", "retrieval_policy")}
        comparison.update(initial_cash=portfolio["initial_cash"], sessions=sessions, limits=policy["limits"], clock=policy["clock"],
                          knowledge=[{k: c[k] for k in ("constitution_hash", "curriculum_hash", "version")} for c in knowledge])
        trial = dict(trial_id=trial_id, experiment_id=experiment_id, portfolio_id=portfolio_id, sessions=sessions,
                     family_id=family_id, role=role, baseline_trial_id=baseline_trial_id,
                     rejected_decision_id=rejected_decision_id, comparison_hash=digest(comparison), version=1)
        self.store.append(trial_id, experiment_id, "evaluation.trial", trial, created_at=at)
        return trial

    def register_forecast(self, forecast_id, recommendation_id, *, outcome_at, threshold, probability, at):
        rec = self.store.record(recommendation_id, "recommendation")
        if timestamp(at) < timestamp(rec["created_at"]) or timestamp(at) >= timestamp(outcome_at):
            raise ContractError("Forecast must be recorded after its decision and before its outcome")
        try:
            threshold, probability = D(threshold), D(probability)
        except (ArithmeticError, TypeError) as exc:
            raise ContractError("Forecast numbers must be finite decimals") from exc
        if not probability.is_finite() or not 0 <= probability <= 1:
            raise ContractError("Forecast probability must be between zero and one")
        if not threshold.is_finite() or threshold <= 0 or rec["instrument_id"] is None:
            raise ContractError("Price-threshold forecast needs a positive threshold and instrument")
        snapshot = self.store.record(rec["snapshot_id"], "snapshot")
        feeds = {self.store.record(i, "observation")["feed"] for i in snapshot["observation_ids"]
                 if self.store.record(i, "observation")["instrument_id"] == rec["instrument_id"]}
        if len(feeds) != 1:
            raise ContractError("Forecast outcome feed must be unambiguous in its frozen snapshot")
        payload = dict(forecast_id=forecast_id, recommendation_id=recommendation_id, portfolio_id=rec["portfolio_id"],
                       instrument_id=rec["instrument_id"], probability=str(probability), outcome_at=outcome_at,
                       threshold=str(threshold), feed=next(iter(feeds)), event_definition="raw_close_strictly_above_threshold", version=1)
        self.store.append(forecast_id, rec["experiment_id"], "forecast.registered", payload, created_at=at)
        return payload

    def forecasts(self, experiment_id, portfolio_id, as_of):
        results, scores = [], []
        for event in self.store.iter_events(experiment_id, "forecast.registered"):
            f = event["payload"]
            if f["portfolio_id"] != portfolio_id or timestamp(event["created_at"]) > timestamp(as_of):
                continue
            result = dict(f, outcome=None, status="pending", reason="Outcome has not matured")
            if timestamp(f["outcome_at"]) <= timestamp(as_of):
                candidates = []
                for item in self.store.iter_events(experiment_id, "market.payload"):
                    p = item["payload"]
                    if p["instrument_id"] != f["instrument_id"] or p["event_at"] != f["outcome_at"]:
                        continue
                    observation = self.store.record(p["observation_id"], "observation")
                    if (observation["quality"] == "eligible" and p["bar"]["adjustment"] == "raw"
                            and observation["experiment_id"] == experiment_id and observation["instrument_id"] == f["instrument_id"]
                            and observation["event_at"] == f["outcome_at"] and observation["feed"] == f["feed"]
                            and p["bar"]["event_at"] == f["outcome_at"] and p["bar"]["feed"] == f["feed"]
                            and digest(p["bar"]) == observation["payload_hash"]
                            and all(timestamp(observation[k]) <= timestamp(as_of) for k in ("event_at", "published_at", "ingested_at"))
                            and timestamp(item["created_at"]) <= timestamp(as_of)):
                        candidates.append((observation["revision"], p["bar"]["close"], observation["id"]))
                if candidates:
                    _, close, observation_id = max(candidates)
                    y = int(D(close) > D(f["threshold"]))
                    score = (D(f["probability"]) - y) ** 2
                    scores.append(score)
                    result.update(outcome=y, status="matured", reason=None, score=str(score), observation_id=observation_id)
                else:
                    result.update(status="unscorable", reason="Matured, but eligible raw outcome data is missing")
            results.append(result)
        bins = []
        for index in range(5):
            members = [f for f in results if f["status"] == "matured" and min(4, int(D(f["probability"]) * 5)) == index]
            bins.append(dict(lower=str(D(index) / 5), upper=str(D(index + 1) / 5), count=len(members),
                             observed_rate=None if not members else str(D(sum(f["outcome"] for f in members)) / len(members))))
        return dict(items=results, matured=len(scores), pending=sum(f["status"] == "pending" for f in results),
                    unscorable=sum(f["status"] == "unscorable" for f in results), reliability_bins=bins,
                    brier=metric(sum(scores, ZERO) / len(scores)) if scores else metric(reason="No matured, scorable forecasts"))

    def registry(self, family_id=None, *, as_of=None):
        trials = []
        for event in self.store.iter_events(kind="evaluation.trial"):
            trial = event["payload"]
            if family_id is not None and trial["family_id"] != family_id:
                continue
            if as_of and timestamp(event["created_at"]) > timestamp(as_of):
                continue
            status = "registered"
            for update in self.store.iter_events(trial["experiment_id"], "evaluation.trial_status"):
                if update["payload"]["trial_id"] == trial["trial_id"] and (not as_of or timestamp(update["created_at"]) <= timestamp(as_of)):
                    status = update["payload"]["status"]
            trials.append(dict(trial_id=trial["trial_id"], experiment_id=trial["experiment_id"], role=trial["role"], status=status))
        return trials

    def trial_status(self, trial_id, status, *, at):
        trial = self._event(trial_id)["payload"]
        if status not in {"failed", "completed", "withdrawn", "partial"}:
            raise ContractError("Unknown trial status")
        if status == "completed" and timestamp(at) < timestamp(self.store.record(trial["experiment_id"], "experiment")["end_at"]):
            raise ContractError("Declared evaluation window is still open")
        self.store.append("trial-status:" + digest([trial_id, at]), trial["experiment_id"], "evaluation.trial_status",
                          dict(trial_id=trial_id, status=status), created_at=at)

    def evaluate(self, trial_id, *, as_of, persist=True, include_baseline=True):
        timestamp(as_of)
        event = self._event(trial_id)
        if event["kind"] != "evaluation.trial" or timestamp(event["created_at"]) > timestamp(as_of):
            raise ContractError("Trial is not available at this cutoff")
        trial = event["payload"]
        exp = self.store.record(trial["experiment_id"], "experiment")
        portfolio = self.store.record(trial["portfolio_id"], "portfolio")
        if timestamp(as_of) < timestamp(exp["start_at"]):
            raise ContractError("Evaluation has not started")
        events = (e for e in self.store.iter_events(exp["id"], "simulation", portfolio_id=portfolio["id"])
                  if timestamp(e["created_at"]) <= timestamp(as_of))
        state, points, traded, closed_gains, trade_gains = State(), [], ZERO, [], {}
        current, fills, rejected_ids = next(events, None), 0, set()
        for session in trial["sessions"]:
            if timestamp(session["close_at"]) > timestamp(as_of):
                break
            while current is not None and current["payload"]["at"][:10] <= session["session"]:
                effect = current["payload"]
                if effect["version"] != VERSION:
                    raise ContractError("Unsupported ledger version")
                old_realized = state.realized
                order = state.orders.get(effect.get("order_id"))
                if effect["type"] == "funding" and (state.initial_cash != 0 or D(effect["amount"]) != D(portfolio["initial_cash"])):
                    raise ContractError("External or changed funding requires flow-adjusted evaluation")
                state.apply(effect)
                if effect["type"] == "fill":
                    fills += 1
                    traded += D(effect["notional"])
                    instrument = order["instrument_id"]
                    trade_gains[instrument] = trade_gains.get(instrument, ZERO) + state.realized - old_realized
                    if state.positions[instrument] == 0:
                        closed_gains.append(trade_gains.pop(instrument))
                if effect["type"] == "rejection":
                    rejected_ids.add(effect.get("decision_id") or (order or {}).get("decision_id") or current["id"])
                current = next(events, None)
            missing = [i for i, q in state.positions.items() if q and (i not in state.marks or
                       state.marks[i]["session"] != session["session"] or state.marks[i].get("phase") != "close")]
            equity = None if missing or state.initial_cash == 0 else state.equity()
            if equity is not None:
                unrealized = sum((q * D(state.marks[i]["price"]) - state.basis[i] for i, q in state.positions.items() if q), ZERO)
                if abs(equity - state.initial_cash - state.realized - unrealized - state.income) > D("0.00000001"):
                    raise ContractError("Evaluation ledger does not reconcile")
            points.append(dict(session=session["session"], at=session["close_at"], equity=None if equity is None else str(equity),
                               reason="Missing closing mark" if missing else ("Portfolio not funded" if equity is None else None),
                               missing_instruments=missing))
        metrics = series_metrics(points, initial_cash=portfolio["initial_cash"], traded_notional=traded, closed_gains=closed_gains)
        final_equity = None if not points or points[-1]["equity"] is None else D(points[-1]["equity"])
        holdings, sectors = [], {}
        universe = {i["instrument_id"]: i for i in exp["universe"]}
        for key, quantity in state.positions.items():
            if not quantity:
                continue
            mark = state.marks.get(key)
            value = None if final_equity is None or not mark else quantity * D(mark["price"])
            holdings.append(dict(instrument_id=key, symbol=universe[key]["symbol"], quantity=str(quantity),
                                 value=None if value is None else str(value), sector=universe[key]["sector"]))
            if value is not None:
                sectors[universe[key]["sector"]] = sectors.get(universe[key]["sector"], ZERO) + value
        gross = sum((D(h["value"]) for h in holdings if h["value"] is not None), ZERO)
        metrics["gross_exposure"] = metric(gross / final_equity) if final_equity and final_equity > 0 else metric(reason="Missing or nonpositive equity")
        forecasts = self.forecasts(exp["id"], portfolio["id"], as_of)
        metrics["brier"] = forecasts["brier"]
        grade = {"fixture": "fixture", "hindsight": "hindsight-contaminated", "historical_restricted": "historical-qualified"}.get(exp["regime"], "forward-insufficient")
        trial_registry = self.registry(trial["family_id"], as_of=as_of)
        blockers = []
        if not exp["regime"].startswith("forward"):
            blockers.append("Only forward evidence can enter promotion review")
        if timestamp(as_of) < timestamp(exp["end_at"]):
            blockers.append("Declared evaluation window is incomplete")
        if len(points) < max(60, exp["minimum_sessions"]):
            blockers.append("Too few completed market sessions")
        if forecasts["matured"] < max(30, exp["minimum_forecasts"]):
            blockers.append("Too few matured forecasts")
        if any(p["equity"] is None for p in points):
            blockers.append("Incomplete marks")
        if state.halted:
            blockers.append("Portfolio is halted")
        decisions = []
        for row in self.store.connection.execute("SELECT body FROM records WHERE record_type='recommendation' AND experiment_id=?", (exp["id"],)):
            rec = json.loads(row[0])
            if rec["portfolio_id"] == portfolio["id"] and timestamp(rec["created_at"]) <= timestamp(as_of):
                decisions.append(rec)
        decisions.sort(key=lambda r: (r["created_at"], r["id"]))
        available_decisions = {r["id"] for r in decisions}
        for e in self.store.iter_events(exp["id"], "phase.complete"):
            if timestamp(e["created_at"]) <= timestamp(as_of):
                for check in e["payload"].get("output", {}).get("checks", []):
                    if check["status"] == "rejected" and check["recommendation_id"] in available_decisions:
                        rejected_ids.add(check["recommendation_id"])
        source_runs = [json.loads(r[0])["id"] for r in self.store.connection.execute("SELECT body FROM records WHERE record_type='run_manifest' AND experiment_id=?", (exp["id"],))
                       if timestamp(json.loads(r[0])["created_at"]) <= timestamp(as_of)]
        report = dict(schema_version=1, trial_id=trial_id, experiment_id=exp["id"], portfolio_id=portfolio["id"], role=trial["role"],
                      family_id=trial["family_id"], mode=exp["mode"], regime=exp["regime"], evidence_grade=grade,
                      advice=exp["advice"], owner_version=portfolio["owner_character_version"], as_of=as_of,
                      window_start=exp["start_at"], window_end=exp["end_at"], initial_cash=portfolio["initial_cash"],
                      equity=None if final_equity is None else str(final_equity), cash=str(state.cash), reserved=str(state.reserved),
                      fees=str(state.fees), income=str(state.income), realized=str(state.realized), holdings=holdings,
                      sectors={k: str(v) for k, v in sectors.items()}, history=points, metrics=metrics, forecasts=forecasts,
                      fills=fills, closed_positions=len(closed_gains), abstentions=sum(r["action"] in {"wait", "abstain"} for r in decisions),
                      decision_ids=[r["id"] for r in decisions], rejected_decisions=len(rejected_ids), halted=state.halted,
                      cash_baseline=metric(0), index_baseline=metric(reason="No matched index portfolio registered"),
                      trial_registry=trial_registry, trial_count=len(trial_registry), source_run_ids=source_runs,
                      comparison_hash=trial["comparison_hash"], review_blockers=blockers, promotion_eligible=False,
                      limitations=["Bar-based simulation omits intraday liquidity and queue priority", "Small samples do not establish skill", "All trials, including failures, must remain in the registry"],
                      calculation="Returns include fees and dividends once; turnover is absolute traded notional / mean daily equity; volatility is daily, not annualized")
        if include_baseline and trial["baseline_trial_id"]:
            baseline = self.evaluate(trial["baseline_trial_id"], as_of=as_of, persist=False, include_baseline=False)
            base_exp = self.store.record(baseline["experiment_id"], "experiment")
            base_trial = self._event(trial["baseline_trial_id"])["payload"]
            if baseline["role"] != "index_baseline" or baseline["regime"] != report["regime"] or any(exp[k] != base_exp[k] for k in ("universe", "costs", "start_at", "end_at", "data_feeds")) or baseline["initial_cash"] != report["initial_cash"] or base_trial["sessions"] != trial["sessions"]:
                raise ContractError("Index baseline is not comparable to this experiment")
            report["index_baseline"] = baseline["metrics"]["net_return"]
            report["baseline_trial_id"] = baseline["trial_id"]
        report["report_id"] = "evaluation:" + digest(report)
        if persist:
            self.store.append(report["report_id"], exp["id"], "evaluation.report", report, created_at=as_of)
        return report

    def compare_advice(self, left, right):
        if (left["comparison_hash"] != right["comparison_hash"] or left["as_of"] != right["as_of"] or
                left["role"] != "strategy" or right["role"] != "strategy" or {left["advice"], right["advice"]} != {"none", "bounded"}):
            raise ContractError("Advice comparison requires matched frozen trials with opposite advice access")
        none, mail = (left, right) if left["advice"] == "none" else (right, left)
        values = [r["metrics"]["net_return"]["value"] for r in (none, mail)]
        return dict(no_mail=none["trial_id"], mail=mail["trial_id"], regime=left["regime"],
                    difference=metric(D(values[1]) - D(values[0])) if all(v is not None for v in values) else metric(reason="Incomplete matched outcomes"),
                    interpretation="One matched ablation; uncertainty is not estimable from a single pair. No causal skill claim.")

    def approve_forward_review(self, report_id, *, owner, approval_ref, at):
        report = self._event(report_id)["payload"]
        exp = self.store.record(report["experiment_id"], "experiment")
        policy = self.store.record(exp["policy_id"], "policy")
        if report["review_blockers"] or owner != policy["operator"] or not approval_ref or timestamp(at) < timestamp(report["as_of"]):
            raise ContractError("Forward review requires complete evidence and a recorded owner decision")
        self.store.append("review:" + digest(report_id), exp["id"], "evaluation.owner_review",
                          dict(report_id=report_id, owner=owner, approval_ref=approval_ref, evidence_grade="forward-reviewed"), created_at=at)

    def local_counterfactual(self, recommendation_id, outcome_observation_id, *, as_of):
        rec = self.store.record(recommendation_id, "recommendation")
        outcome = self.store.record(outcome_observation_id, "observation")
        if outcome["experiment_id"] != rec["experiment_id"] or outcome["instrument_id"] != rec["instrument_id"]:
            raise ContractError("Counterfactual observation scope differs from decision")
        if timestamp(outcome["event_at"]) <= timestamp(rec["created_at"]) or any(timestamp(outcome[k]) > timestamp(as_of) for k in ("event_at", "published_at", "ingested_at")):
            raise ContractError("Counterfactual outcome is not eligible")
        snapshot = self.store.record(rec["snapshot_id"], "snapshot")
        payloads = {e["payload"]["observation_id"]: e["payload"]["bar"] for e in self.store.iter_events(rec["experiment_id"], "market.payload")
                    if timestamp(e["created_at"]) <= timestamp(as_of)}
        starts = [payloads[i] for i in snapshot["observation_ids"] if i in payloads and payloads[i]["instrument_id"] == rec["instrument_id"] and payloads[i]["adjustment"] == "raw"]
        end = payloads.get(outcome_observation_id)
        if len(starts) != 1 or end is None or end["adjustment"] != "raw" or digest(end) != outcome["payload_hash"]:
            raise ContractError("Need exact eligible raw start and outcome prices")
        return dict(recommendation_id=recommendation_id, outcome_observation_id=outcome_observation_id,
                    raw_price_change=metric(D(end["close"]) / D(starts[0]["close"]) - 1),
                    label="Local price-only counterfactual; excludes costs, sizing and portfolio constraints. Never add to strategy return.")
