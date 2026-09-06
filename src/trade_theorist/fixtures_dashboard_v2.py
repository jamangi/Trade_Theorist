"""Original offline UI scenarios built through the production accounting path."""
from .contracts import digest
from .fixtures_accounting_v2 import FixtureV2, golden, broad_market, at
from .evaluate.portfolio_v2 import evaluate
from .adapters.trader_user_sim.broker_v2 import BrokerReconcilerV2


def seed_dashboard(store):
    baseline = broad_market(store)
    individual = golden(store, name="individual", baseline=baseline.portfolio)
    monarchy = golden(store, name="monarchy", mode="council", baseline=baseline.portfolio)
    control = FixtureV2(store, "control", mode="council", role="matched_control")
    paper = FixtureV2(store, "paper", mode="council", basis="paper_broker")
    cash = FixtureV2(store, "cash", flows=[("funding", at(1), "1000.00")])
    for f in (control, paper, cash):
        f.event("funding", 1, amount="1000.00", boundary_mark_ids=[])
        f.mark(1,"100")
    order=paper.order(1,"3","100")
    control_order=control.order(1,"3","100")
    mapping=store.prepare_submission(order,at=at(1,1))
    broker=BrokerReconcilerV2(store,paper.portfolio)
    update=paper.engine.record("broker_update","broker-update:private-demo",at(2),portfolio_id=paper.portfolio,segment_id=paper.segment,
        mapping_id=mapping["id"],provider_event_id="provider:original-private-demo",broker_order_id="SENSITIVE-BROKER-ID-NOT-FOR-BROWSER",
        effective_at=at(2),observed_at=at(2),cumulative_quantity="1",cumulative_notional="100.00",cumulative_fees="1.00",
        incremental_fill_id="increment:private-demo",status="partially_filled")
    broker.update(update)
    for f in (control,paper):
        for day in range(2,13):
            mark_id=f.mark(day,"100")
            if f is control and day==2: f.fill(control_order,mark_id,day,"1")
            if day==9:f.event("contribution",day,amount="500.00",boundary_mark_ids=[next(reversed(list(store.iter_v2(portfolio_id=f.portfolio,kind="ledger_event"))))["id"]])
    broker.account("account:private-demo",effective_at=at(11),observed_at=at(11),cash="1399.00",positions=[dict(instrument_id="instrument:fixture-fund",quantity="1")],evidence_hash=digest("original aggregate check"))
    scenarios=[(individual,"Index Steward · original fixture"),(monarchy,"Monarchy · original fixture"),(control,"Monarchy · simulated control"),(paper,"Monarchy · broker paper fixture"),(cash,"Cash observer · no trades")]
    for f,label in scenarios:
        context=f.engine.record("inspection_context","context:"+f.name,at(11),portfolio_id=f.portfolio,segment_id=f.segment,character_version=f.character,
            as_of=at(11),label=label,horizon="One synthetic session",advice="bounded" if f is monarchy else "none",
            belief="Original scenario: hold a diversified synthetic fund while keeping risk evidence inspectable.",
            rationale="The saved arithmetic scenario traces cash, lots and fees. It is authored test analysis, not a claim about real markets.",
            invalidation="No real preregistered investment thesis is supplied. A missing eligible mark or unresolved attribution prevents new admission.",
            learning_statement="Original fixture learning context. No real book completion or ready Character is established here.",learning_completed=1,learning_total=3,
            source_citations=[dict(title="Original accounting scenario",edition="v2",locator="Golden arithmetic vector, steps 1–12")],
            advice_log=[dict(author_version=f.character,kind="objection",status="Unresolved",summary="The sample cannot establish an edge.")] if f is monarchy else [],
            forecasts=dict(matured=0,pending=1,unscorable=0,brier=dict(value=None,reason="Awaiting a matured outcome",unit="ratio")),abstentions=1 if f is cash else 0,
            heartbeat_status="failed" if f is paper else "completed",last_successful_heartbeat=at(10))
        store.put_v2([context])
        if f is paper:
            expense=f.engine.record("operating_expense","expense:private-unknown-hosting",at(11),portfolio_id=f.portfolio,
                effective_at=at(11),category="hosting",recurring=True,amount=None,reason="Provider invoice not recorded")
            f.engine.command("command:private-unknown-cost",[expense])
        for day in (11,12): evaluate(store,f.portfolio,effective_cutoff=at(day),receipt_cutoff=at(day))
    # Same frozen owner, distinct as-known and restated valuation; no new fill.
    mark=next(e for e in store.iter_v2(portfolio_id=individual.portfolio,kind="ledger_event") if e["event_type"]=="mark" and e["effective_at"]==at(11))
    payload=dict(mark["payload"],price="61",received_at=at(13),eligibility_cutoff=at(13),observation_revision=2)
    individual.engine.correct("command:private-correction",mark["id"],payload,observed_at=at(13))
    evaluate(store,individual.portfolio,effective_cutoff=at(11),receipt_cutoff=at(13))
    # An unready registered version has no funded report, rather than a zero return.
    FixtureV2(store,"unready",flows=[],readiness="not_ready")
    return dict(individual=individual.portfolio,monarchy=monarchy.portfolio,paper=paper.portfolio,cash=cash.portfolio)
