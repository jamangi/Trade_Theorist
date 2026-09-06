"""Private revisioned v2 reports built exclusively from persistent typed evidence."""
from decimal import Decimal as D, localcontext

from ..contracts import ContractError, digest, utc
from ..adapters.trader_user_sim.v2 import SimulatorV2


def number(value):
    return None if value is None else format(D(value).quantize(D(".00000001")), "f")


def value(amount=None, reason="Insufficient eligible evidence", unit="ratio"):
    return dict(value=number(amount), reason=reason if amount is None else None, unit=unit)


def evaluate(store, portfolio_id, *, effective_cutoff, receipt_cutoff, persist=True, include_baseline=True, before_commit=None):
    engine = SimulatorV2(store, portfolio_id)
    with store.transaction(), localcontext() as ctx:
        ctx.prec = 50
        state, sources = engine.state(effective_cutoff=effective_cutoff, receipt_cutoff=receipt_cutoff)
        if state.segment is None or not sources:
            raise ContractError("No funded v2 segment is available for evaluation")
        for event in sources:
            if store.v2_record(event["provenance"]["rights_id"])["private_read_model"] != "permitted":
                raise ContractError("Source rights do not permit private result publication")
        source_hash = digest(sources)
        segment_start = store.v2_record(state.segment)["start_at"]
        expenses = [r for r in store.iter_v2(portfolio_id=portfolio_id, kind="operating_expense")
                    if utc(segment_start) <= utc(r["effective_at"]) <= utc(effective_cutoff) and utc(r["created_at"]) <= utc(receipt_cutoff)]
        baseline = None
        if include_baseline and engine.plan["baseline_portfolio_id"]:
            bid = engine.plan["baseline_portfolio_id"]
            if bid == portfolio_id: raise ContractError("Baseline requires independent capital")
            baseline = evaluate(store, bid, effective_cutoff=effective_cutoff, receipt_cutoff=receipt_cutoff, persist=False, include_baseline=False)
        # Full provenance includes the plan and operating evidence as well as ledger events.
        evaluation_key = digest([portfolio_id, effective_cutoff, receipt_cutoff, source_hash, engine.plan, expenses, baseline])
        identifier = "performance:" + evaluation_key
        existing = store.connection.execute("SELECT 1 FROM v2_records WHERE id=?", (identifier,)).fetchone()
        if existing:
            return store.v2_record(identifier)
        prior = [r for r in store.iter_v2(portfolio_id=portfolio_id, kind="projection") if r["segment_id"] == state.segment]
        revision = max((r["revision"] for r in prior), default=0) + 1
        nav, wealth = state.equity(), state.wealth()
        pnl = None if nav is None else nav - state.initial - state.external
        unrealized = None if nav is None else nav - state.cash - state.receivable - state.basis
        if state.ended:
            pnl = state.realized + state.income - state.expenses
        points = state.history
        daily = []
        previous = D(1)
        for p in points:
            if p["wealth"] is not None and previous is not None and previous > 0:
                daily.append(p["wealth"] / previous - 1)
            previous = p["wealth"]
        volatility = None
        if not state.schedule_gap and len(daily) >= 2:
            mean = sum(daily) / len(daily)
            volatility = (sum((d - mean) ** 2 for d in daily) / (len(daily) - 1)).sqrt()
        equities = [p["equity"] for p in points]
        mean_equity = sum(equities) / len(equities) if equities and all(x is not None for x in equities) else None
        def costs(recurring):
            rows = [r for r in expenses if r["recurring"] == recurring]
            return None if any(r["amount"] is None for r in rows) else sum((D(r["amount"]) for r in rows), D(0))
        recurring, one_time = costs(True), costs(False)
        flow_data = [(r["event_type"], r["effective_at"], r["payload"]["amount"]) for r in sources if r["event_type"] in {"funding", "contribution", "withdrawal"}]
        policy = store.v2_record(engine.portfolio["policy_id"])
        exp = store.v2_record(engine.portfolio["experiment_id"])
        comparison = {k: engine.plan[k] for k in ("mark_schedule", "max_mark_age_seconds", "execution_model", "fee_per_share", "slippage_bps", "spread_bps", "fractional_shares", "corporate_actions")}
        comparison.update(instruments=exp["instrument_ids"], regime=exp["regime"], start_at=exp["start_at"], end_at=exp["end_at"], flows=flow_data,
                          execution_basis=engine.portfolio["execution_basis"], limits=policy["limits"])
        comparison["market_evidence"] = [{k: v for k, v in r["payload"].items() if k not in {"observation_id", "mark_policy_hash"}}
                                        for r in sources if r["event_type"] == "mark"]
        grade = {"fixture": "fixture", "hindsight": "hindsight-contaminated", "historical_restricted": "historical-qualified"}.get(exp["regime"], "forward-insufficient")
        blockers = ["No owner promotion review in this accounting path", "Preregistered matured forecast and forward-window review remain required"]
        if grade == "fixture": blockers.append("Original synthetic accounting evidence only")
        if state.gaps or state.return_gap or nav is None: blockers.append("Incomplete valuation or reconciliation")
        if state.halted: blockers.append("Risk or reconciliation halt remains active")
        report = engine.record("performance_result", identifier, receipt_cutoff, portfolio_id=portfolio_id, segment_id=state.segment,
            accounting_plan_id=engine.plan["id"], projection_revision=revision, effective_cutoff=effective_cutoff, receipt_cutoff=receipt_cutoff,
            source_event_ids=[r["id"] for r in sources], source_chain_hash=source_hash, publication_class="private-owner-v2",
            execution_basis=engine.portfolio["execution_basis"], mode=engine.portfolio["mode"], owner_character_version=engine.portfolio["owner_character_version"],
            evidence_grade=grade, promotion_eligible=False, review_blockers=blockers, cash=number(state.cash), reserved=number(state.reserved),
            available=number(state.cash - state.reserved), initial_funding=number(state.initial), net_external_flows=number(state.external),
            fifo_basis=number(state.basis), realized=number(state.realized), income=number(state.income), fees=number(state.fees),
            receivables=number(state.receivable), unallocated_expenses=number(state.expenses),
            equity=value(nav, "Missing eligible marks or unreconciled accounting", "USD"), unrealized=value(unrealized, unit="USD"), strategy_pnl=value(pnl, unit="USD"),
            twr=value(None if wealth is None else wealth - 1, "Missing eligible NAV or exact flow-boundary valuation"),
            max_drawdown=value(None if state.schedule_gap else state.max_dd, "Incomplete declared wealth schedule"),
            volatility=value(volatility, "At least two complete scheduled returns required"),
            turnover=value(state.traded / mean_equity if mean_equity and mean_equity > 0 else None, "Missing positive mean scheduled equity"),
            hit_rate=value(D(sum(g > 0 for g in state.closed_gains)) / len(state.closed_gains) if state.closed_gains else None, "No fully closed positions"),
            lot_relief_win_rate=value(D(sum(r["proceeds"] - r["fees"] - r["basis"] > 0 for r in state.reliefs)) / len(state.reliefs) if state.reliefs else None, "No FIFO reliefs"),
            recurring_expense=value(recurring, "Unknown recurring operating cost", "USD"), one_time_expense=value(one_time, "Unknown one-time cost", "USD"),
            economics_pnl=value(pnl - recurring if pnl is not None and recurring is not None else None, "Unknown P/L or recurring cost", "USD"),
            cash_baseline=value(0), broad_market_baseline=value(reason="No matched independently funded broad-market baseline"), benchmark_status="unmatched",
            holdings=[dict(instrument_id=k, quantity=number(q), fifo_basis=number(sum(l["basis"] for l in state.lots if l["instrument"] == k)),
                           value=number(q * D(state.eligible_mark(k)["price"])) if state.eligible_mark(k) and nav is not None else None) for k, q in state.positions.items() if q],
            history=[dict(at=p["at"], equity=number(p["equity"]), wealth=number(p["wealth"]), drawdown=number(p["drawdown"]), reason=p["reason"]) for p in points],
            flow_signature=digest(flow_data), comparison_hash=digest(comparison), halted=state.halted,
            gaps=sorted(state.gaps | ({"Missing exact flow-boundary NAV"} if state.return_gap else set())),
            closed_segments=[dict(segment_id=s["segment_id"], twr=number(s["twr"]), reason=s["reason"]) for s in state.closed_segments],
            order_outcomes=[dict(order_id=oid, filled_quantity=number(o["filled"]), remaining_quantity=number(o["remaining"]), status=o["status"]) for oid, o in state.orders.items()],
            baseline_result_hash=digest(baseline) if baseline else None, operating_expense_ids=[e["id"] for e in expenses],
            definitions=["FIFO basis includes acquisition fees; disposal fees reduce realized P/L once.",
                "TWR links exact eligible flow-boundary NAV; drawdown follows its wealth index.",
                "Turnover is gross traded notional / mean equity on the declared schedule; volatility is unannualized sample deviation.",
                "Closed-position hit rate and individual FIFO relief win rate are separate samples.",
                "Recurring operating costs are separate from trading TWR; economics P/L deducts them once.",
                "Baselines: zero-interest cash and " + engine.plan["baseline_construction"],
                "No aggregation across execution bases or funded/Character segments."])
        if baseline is not None:
            bid = engine.plan["baseline_portfolio_id"]
            bp = store.v2_record(bid)
            if bp["role"] == "baseline" and baseline["comparison_hash"] == report["comparison_hash"]:
                report["broad_market_baseline"] = baseline["twr"]
                report["benchmark_status"] = "matched flow timing, costs, window and execution basis"
            else:
                report["broad_market_baseline"] = value(reason="Baseline flow timing or frozen execution assumptions differ")
        if report["benchmark_status"] == "unmatched": report["review_blockers"].append("Comparable broad-market baseline missing")
        if not persist: return report
        rows, current_lots = [], {}
        old_lots = list(store.iter_v2(portfolio_id=portfolio_id, kind="lot"))
        for lot in state.lots:
            predecessors = [l for l in old_lots if l["lot_id"] == lot["lot_id"]]
            previous_lot = max(predecessors, key=lambda l: l["projection_revision"]) if predecessors else None
            lot_revision = previous_lot["projection_revision"] + 1 if previous_lot else 1
            lid = "lot-revision:" + digest([lot["lot_id"], identifier])
            current_lots[lot["lot_id"]] = lid
            rows.append(engine.record("lot", lid, receipt_cutoff, portfolio_id=portfolio_id, segment_id=state.segment,
                instrument_id=lot["instrument"], originating_fill_id=lot["fill_id"], originating_order_id=lot["order_id"], acquired_at=lot["acquired_at"],
                original_quantity=number(lot["original_quantity"]), remaining_quantity=number(lot["quantity"]), original_basis=format(lot["original_basis"], "f"),
                remaining_basis=format(lot["basis"], "f"), corporate_action_ids=lot["actions"], projection_revision=lot_revision,
                previous_lot_revision_id=previous_lot["id"] if previous_lot else None, lot_id=lot["lot_id"]))
        for index, relief in enumerate(state.reliefs):
            rows.append(engine.record("lot_relief", "relief:" + digest([identifier, index]), receipt_cutoff, portfolio_id=portfolio_id, segment_id=state.segment,
                sale_fill_id=relief["sale_fill_id"], lot_revision_id=current_lots[relief["lot_id"]], quantity=number(relief["quantity"]),
                allocated_basis=format(relief["basis"], "f"), proceeds=format(relief["proceeds"], "f"), disposal_fees=format(relief["fees"], "f"), projection_revision=revision))
        gaps = report["gaps"] + (["Missing eligible marks"] if nav is None else []) + (["Incomplete required wealth schedule"] if state.schedule_gap else [])
        projection = engine.record("projection", "projection:" + evaluation_key, receipt_cutoff, portfolio_id=portfolio_id, segment_id=state.segment,
            owner_character_version=engine.portfolio["owner_character_version"], mode=engine.portfolio["mode"], execution_basis=engine.portfolio["execution_basis"],
            currency="USD", policy_id=engine.portfolio["policy_id"], source_event_ids=report["source_event_ids"], source_chain_hash=source_hash,
            effective_cutoff=effective_cutoff, receipt_cutoff=receipt_cutoff, mark_policy_hash=digest([engine.plan["mark_schedule"], engine.plan["max_mark_age_seconds"]]),
            accounting_method="fifo-v2", return_method="exact-twr-v2", revision=revision,
            previous_projection_id=max(prior, key=lambda p: p["revision"])["id"] if prior else None, publication_class="private-owner-v2",
            status="gap" if gaps else "complete", null_reasons=gaps, result_hash=None if gaps else digest(report))
        rows.extend([report, projection])
        store.put_v2(rows)
        if before_commit: before_commit()
        return report


def compare(left, right):
    if left["comparison_hash"] != right["comparison_hash"] or left["effective_cutoff"] != right["effective_cutoff"] or left["receipt_cutoff"] != right["receipt_cutoff"]:
        raise ContractError("Comparison requires identical flows, window and execution basis/model")
    a, b = left["twr"]["value"], right["twr"]["value"]
    return dict(difference=value(None if a is None or b is None else D(a) - D(b)), promotion_eligible=False,
                interpretation="Matched descriptive comparison; sample uncertainty and independent forward review remain required")
