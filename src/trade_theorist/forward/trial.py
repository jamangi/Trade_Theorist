"""Original prospective identities and a single, finite initial-allocation trial.

No fixture records are imported or relabeled. All market data stays in the
owner's private Coordinator store. No Trading adapter is reachable here.
"""
from datetime import date, timedelta
from decimal import Decimal as D, ROUND_DOWN
from pathlib import Path

from ..contracts import ContractError, digest, utc
from ..contracts_v2 import CLASSES
from ..adapters.trader_user_sim.v2 import SimulatorV2
from ..evaluate.ledger_v2 import money
from ..learn.continuation import read
from ..market_requests import stamp
from .prospective import binding, load_learning, runtime_hash, read_audit, save_audit
from .shared import freeze_round

INSTRUMENT = 'instrument:vti'
TRIAL = 'step11-20260907'
END = '2026-09-15T22:00:00Z'
FUTURE = ['2026-09-08','2026-09-09','2026-09-10','2026-09-11','2026-09-14']
BASELINE = 'Buy the same capped VTI allocation at the next eligible daily close; cash baseline earns zero. Initial funding only; no reinvestment or terminal liquidation.'


def calendar():
    day, days = date(2026,8,6), []
    while day <= date(2026,9,14):
        if day.weekday() < 5 and day != date(2026,9,7):
            s = day.isoformat()
            days.append(dict(session=s,open_at=s+'T13:30:00Z',close_at=s+'T20:00:00Z'))
        day += timedelta(days=1)
    return days


def identities(store, root, *, at, start, end=END):
    """Construct separate Individual, council and market-baseline v2 scopes."""
    register, learning = load_learning(root,cutoff=at)
    groups = [('index','index_steward','character_portfolio'),
              ('value','value_rationalist','character_portfolio'),
              ('trend','systematic_trend_operator','character_portfolio'),
              ('council','index_steward','council'),('market','index_steward','character_portfolio')]
    peers, ancestry, records = [], [], []
    market = 'portfolio:'+TRIAL+'-market'
    for label,name,mode in groups:
        suffix = TRIAL+'-'+label
        exp,rights,policy,char,portfolio,segment,plan = [kind+':'+suffix for kind in ('experiment','rights','policy','character','portfolio','segment','plan')]
        provenance = dict(rights_id=rights,source_event_ids=[],source_hash=digest(['owner-private-operating-interpretation',TRIAL]))
        def record(kind,identifier,**fields):
            return dict(schema_version=2,record_type=kind,id=identifier,experiment_id=exp,created_at=at,
                contamination='forward-insufficient',field_class=CLASSES[kind],provenance=provenance,**fields)
        eligible = learning[name]['eligible_character']
        character = record('character',char,character_id='character:'+name,version='step11-scoped-'+label,
            constitution_hash=eligible['constitution_hash'],curriculum_hash=eligible['curriculum_hash'],readiness='ready')
        universe = [dict(instrument_id=INSTRUMENT,symbol='VTI',asset_class='unleveraged_us_etf',liquid=True,leveraged=False,inverse=False,sector='broad_us_equity',diversified=True)]
        records.extend([
            record('source_rights',rights,source_id='source:alpaca-owner-private',origin='licensed',private_storage='permitted',
                private_replay='permitted',private_read_model='permitted',public_output='denied',reviewed_at=at,
                evidence=['decisions/APPROVALS.md: standing owner private local operating interpretation; no public redistribution.',
                          'examples/step-09/qualification.json','examples/step-11/corporate-action-qualification.json']),
            character,
            record('policy',policy,version=TRIAL,stage='paper',synthetic=False,universe=universe,
                limits=dict(initial_cash='10000.00',max_deployed_capital='10000.00',company_weight=1.0,sector_weight=1.0,
                    diversified_etf_weight=1.0,gross_exposure=1.0,daily_loss=0.10,drawdown=0.20,turnover=1.0,
                    orders_per_session=1,max_quote_age_seconds=345600,max_spread_bps='10'),
                clock=dict(calendar='NYSE-2026-frozen',cadence='one-initial-round-five-session-observation',max_stale_sessions=0,
                    eligibility='publication_and_ingestion',missing_data='halt_all'),
                costs=dict(fee_per_order='0.00',slippage_bps='5',spread_bps='2',fill_model='eligible-next-event-v2',corporate_actions='explicit-raw-v2'),
                long_only=True,cash_only=True,approval_ref='decisions/APPROVALS.md: finite shadow simulation only; no broker orders',
                approved_at=at,operator='owner',kill_switch_owner='owner',reconciliation_owner='owner',incident_owner='owner'),
            record('experiment',exp,mode=mode,execution_basis='simulated',character_versions=[char],policy_id=policy,
                instrument_ids=[INSTRUMENT],start_at=at,end_at=end,regime='forward_shadow'),
            record('portfolio',portfolio,mode=mode,execution_basis='simulated',owner_character_version=char,policy_id=policy,currency='USD',
                role='baseline' if label=='market' else 'strategy',accounting_method='fifo-v2',return_method='exact-twr-v2',initialization='new',legacy_portfolio_id=None),
            record('funded_segment',segment,portfolio_id=portfolio,owner_character_version=char,ordinal=1,previous_segment_id=None,start_at=at,reason='initial'),
            record('accounting_plan',plan,portfolio_id=portfolio,approved_at=at,approval_ref='decisions/APPROVALS.md: finite shadow simulation only; no broker orders',
                flows=[dict(segment_id=segment,event_type='funding',effective_at=at,amount='10000.00')],
                mark_schedule=[at]+[s+'T20:00:00Z' for s in FUTURE],max_mark_age_seconds=345600,
                execution_model='eligible-next-event-v2',fee_per_share='0.00',slippage_bps='5',spread_bps='2',fractional_shares=False,
                corporate_actions='explicit-raw-v2',baseline_portfolio_id=None if label=='market' else market,baseline_construction=BASELINE)
        ])
        if label != 'market':
            peers.append((portfolio,plan,segment)); ancestry.append(binding(character,learning[name]))
    store.put_v2(records)
    for label,_,_ in groups:
        pid='portfolio:'+TRIAL+'-'+label
        engine=SimulatorV2(store,pid)
        funding=engine.event('funding:'+digest(pid),'funding',at,amount='10000.00',boundary_mark_ids=[])
        engine.command('command:'+digest(funding['id']),[funding])
        expenses=[]
        for category,recurring,amount,reason in [('model',True,'0.00',None),('data',True,'0.00',None),
                ('hosting',True,None,'Existing local electricity/hardware cost is unmetered.'),
                ('learning',False,None,'One-time foundation authoring subscription usage unavailable.'),
                ('development',False,None,'One-time implementation effort unmetered; not strategy return.')]:
            expenses.append(engine.record('operating_expense','expense:'+digest([pid,category]),at,portfolio_id=pid,
                effective_at=at,category=category,recurring=recurring,amount=amount,reason=reason))
        engine.command('command:'+digest([pid,'expenses']),expenses)
    return register,peers,ancestry,(market,'plan:'+TRIAL+'-market')


def freeze(owner,root,action_receipts):
    now=owner.clock.wall(); at=stamp(now); start=stamp(now+2); deadline=stamp(now+600); decision=stamp(now+900)
    if at[:10] != '2026-09-07': raise ContractError('This named trial must be registered on its declared date; do not move its window')
    with owner.db,owner.store.transaction():
        register,peers,ancestry,baseline=identities(owner.store,root,at=at,start=start)
        context=dict(readiness_register_hash=digest(register),ancestry=ancestry,
            bars_qualification_hash=digest(read(Path(root)/'examples/step-09/qualification.json')),
            actions_qualification_hash=digest(read(Path(root)/'examples/step-11/corporate-action-qualification.json')),
            action_receipts_hash=digest(action_receipts),runtime_id='foundation-rules-v1',runtime_hash=runtime_hash(),information_tools=[],
            public_facts=read(Path(root)/'examples/step-11/public-research.json'),
            advice_policy='independent-initials-then-three-bounded-messages-index-leads',calendar=calendar(),
            forecast=dict(horizon_sessions=5,resolves_at=FUTURE[-1]+'T20:00:00Z',
                event='VTI raw close on fifth future session exceeds the frozen last historical close; uncalibrated 0.5 control forecast, unscorable across an intervening split.',probability=0.5),
            order_expiry=FUTURE[0]+'T20:01:00Z',allocation_fraction='0.25',trend_lookback=20,
            operating_cost_policy='Per portfolio: recurring model/data incremental USD0; local hardware/hosting unknown. Learning/development separate unknown one-time costs; economics net remains null.',
            external_flow_policy='initial-funding-only',trial_variant='one-fixed-policy-no-tuning')
        q=dict(schema_version=1,record_type='market_query',provider='alpaca',endpoint='stock_bars',
            sharing_scope=owner.policy['sharing_scopes'][0],rights_ref=owner.policy['rights_ref'],symbols=['VTI'],feed='sip',timeframe='1Day',
            start='2026-08-06T00:00:00Z',end='2026-09-05T00:00:00Z',adjustment='raw',asof=None,revision_policy='revision:retain-receipts',
            freshness_after=at,information_cutoff=deadline,expected_sessions=[s['session'] for s in calendar() if s['session']<'2026-09-07'],page_limit=1000)
        from .observe import queries, REVIEW_AT
        context['observation_policy']=dict(review_at=REVIEW_AT,max_total_attempts=8,queries=queries(dict(query=q,end_at=END)))
        return freeze_round(owner,manifest_id='forward:'+TRIAL,participants=peers,baseline=baseline,value=q,start_at=start,end_at=END,
            data_deadline=deadline,decision_at=decision,max_request_attempts=4,
            model_budget=dict(model_ref='model:deterministic-foundation-rules-v1',max_calls=4,max_tokens=4,max_output_tokens=1),
            stopping_rule=dict(horizon_sessions=5,min_completed_sessions=5,min_matured_forecasts=1,stop_at=END,stop_on_data_failure=True),
            real_context=context,repo_root=root)


def commit_allocations(round):
    """Commit sized orders before outcomes. A crash cannot create a late order."""
    m=round.manifest; store=round.store; result=round._existing('forward-result:'+digest(m['id']))
    old=read_audit(round,'allocations')
    if old: return old
    if not result or result['status'] != 'decided': return None
    at=stamp(round.owner.clock.wall())
    if utc(at)>=utc(m['decision_at']): raise ContractError('Order commitment deadline passed; preserve decisions without backfilling orders')
    snapshot=store.v2_record(m['snapshot_ref'])
    last=max(snapshot['observations'],key=lambda i:i['bar']['t'])
    cap=(D(str(last['bar']['c']))*D('1.10')).quantize(D('.00000001'))
    quantity=str((D('10000')*D(m['real_context']['allocation_fraction'])/cap).to_integral_value(rounding=ROUND_DOWN))
    outcomes=result['outcomes']+[dict(portfolio_ref=m['baseline_ref'],action='buy')]
    order_ids=[]
    with round.owner.db,store.transaction():
        for outcome in outcomes:
            pid=outcome['portfolio_ref']; engine=SimulatorV2(store,pid)
            segment=next(store.iter_v2(portfolio_id=pid,kind='funded_segment'))['id']
            mid='mark:'+digest([pid,m['snapshot_ref']]); event_at='2026-09-04T20:00:00Z'
            mark=engine.event(mid,'mark',at,segment_id=segment,instrument_id=INSTRUMENT,price=str(last['bar']['c']),
                event_at=event_at,published_at=last['received_at'],received_at=last['received_at'],feed='sip',adjustment='raw',
                observation_id=last['id'],observation_revision=1,eligibility_cutoff=at,status='eligible',reason=None,
                mark_policy_hash=digest([engine.plan['mark_schedule'],engine.plan['max_mark_age_seconds']]))
            engine.command('command:'+digest(mid),[mark])
            if outcome['action']!='buy' or D(quantity)<=0: continue
            oid='order:'+digest([pid,m['id']]); did='decision:'+digest(oid)
            decision=engine.record('decision',did,at,portfolio_id=pid,segment_id=segment,character_version=engine.portfolio['owner_character_version'],
                snapshot_hash=digest(snapshot),instrument_id=INSTRUMENT,side='buy',quantity=quantity,final=True)
            order=engine.record('order',oid,at,portfolio_id=pid,segment_id=segment,final_recommendation_id=did,instrument_id=INSTRUMENT,
                execution_basis='simulated',side='buy',quantity=quantity,policy_approval_ref='decisions/APPROVALS.md: finite shadow simulation only; no broker orders',replaces_order_id=None)
            terms=engine.record('execution_terms','terms:'+digest(oid),at,portfolio_id=pid,segment_id=segment,order_id=oid,
                earliest_fill_at=FUTURE[0]+'T20:00:00Z',expires_at=m['real_context']['order_expiry'],price_cap=str(cap))
            event=engine.event('admitted:'+digest(oid),'order',at,segment_id=segment,order_id=oid)
            reservation=engine.event('reserved:'+digest(oid),'reservation',at,segment_id=segment,order_id=oid,cash=str(money(D(quantity)*cap)),quantity='0')
            reservation['sequence']+=1
            engine.command('command:'+digest(oid),[decision,order,terms,event,reservation]); order_ids.append(oid)
        return save_audit(round,'allocations',dict(manifest_hash=digest(m),created_at=at,order_ids=order_ids,
            rule='Whole shares at 25% of initial cash divided by 110% of historical close. Limit includes 5bp slippage + 1bp half-spread; expires after first future close. Hold through fifth close; no liquidation.',
            cash_baseline=dict(initial_cash='10000.00',interest='0.00',flows='initial-only'),broker_orders=0))
