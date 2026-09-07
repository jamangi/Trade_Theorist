"""Manual, bounded post-window observation; never recompute an initial opinion.

Daily-close simulated fills are mechanical applications of pre-outcome orders.
Their economic time is the scheduled close; their receipt/creation time remains
the actual later receipt. This is research simulation, not available live fills.
"""
from decimal import Decimal as D
from fractions import Fraction

from ..contracts import ContractError, digest, utc
from ..market_requests import stamp, query
from ..adapters.alpaca_market_data.actions import accounting_action
from ..adapters.trader_user_sim.v2 import SimulatorV2
from ..evaluate.ledger_v2 import money
from ..evaluate.portfolio_v2 import evaluate
from .trial import INSTRUMENT, FUTURE
from .prospective import read_audit, save_audit

REVIEW_AT='2026-09-15T00:20:01Z'


def queries(manifest):
    """Two fixed jobs, four sends each. Never slide cutoffs on a later invocation."""
    base={k:manifest['query'][k] for k in ('schema_version','record_type','provider','sharing_scope','rights_ref','symbols','revision_policy')}
    base.update(freshness_after=REVIEW_AT,information_cutoff=manifest['end_at'],page_limit=1000)
    bars=dict(base,endpoint='stock_bars',feed='sip',timeframe='1Day',adjustment='raw',asof=None,
        start=FUTURE[0]+'T00:00:00Z',end=FUTURE[-1]+'T20:00:00Z',expected_sessions=FUTURE)
    actions=dict(base,endpoint='corporate_actions',start='2026-01-01T00:00:00Z',end='2026-09-15T00:00:00Z',data_quality='all',region='us')
    return [bars,actions]


def _commit(engine, event):
    return engine.command('command:'+digest(event['id']),[event])


def settle(round,bars,actions,*,observed_at):
    """Atomic replay of the complete frozen outcome window; no partial winner bias."""
    m=round.manifest; store=round.store
    existing=read_audit(round,'settled')
    if existing: return existing
    if utc(observed_at)<utc(REVIEW_AT): raise ContractError('Observation horizon has not elapsed')
    if {b['bar']['t'][:10] for b in bars}!=set(FUTURE) or len(bars)!=len(FUTURE): raise ContractError('Incomplete outcome sessions')
    for b in bars:
        if (b['bar']['symbol']!='VTI' or not utc(b['bar']['t'][:10]+'T20:00:00Z')<=utc(b['received_at'])<=utc(observed_at)
                or utc(b['received_at'])>utc(m['end_at'])):
            raise ContractError('Outcome is future, late or outside the opportunity set')
    relevant=[a for a in actions if FUTURE[0]<=a['ex_date']<=FUTURE[-1]]
    if any(a['symbol']!='VTI' or utc(a['ingested_at'])>utc(observed_at) for a in actions): raise ContractError('Invalid action receipt')
    # Same-day split/dividend sequencing and non-session ex dates need explicit
    # event-time evidence; daily bars cannot establish it.
    if any(a['ex_date'] not in FUTURE for a in relevant) or len({a['ex_date'] for a in relevant})!=len(relevant):
        raise ContractError('Ambiguous daily corporate-action ordering')
    portfolios=[p['portfolio_ref'] for p in m['participants']]+[m['baseline_ref']]
    with round.owner.db,store.transaction():
        for pid in portfolios:
            engine=SimulatorV2(store,pid)
            payments=[]
            for b in sorted(bars,key=lambda b:b['bar']['t']):
                day=b['bar']['t'][:10]; at=day+'T20:00:00Z'
                mid='mark:'+digest([pid,b['id'],'outcome'])
                mark=engine.event(mid,'mark',at,observed_at=observed_at,instrument_id=INSTRUMENT,price=str(b['bar']['c']),
                    event_at=at,published_at=b['received_at'],received_at=b['received_at'],feed='sip',adjustment='raw',
                    observation_id=b['id'],observation_revision=1,eligibility_cutoff=observed_at,status='eligible',reason=None,
                    mark_policy_hash=digest([engine.plan['mark_schedule'],engine.plan['max_mark_age_seconds']]))
                daily=[mark]
                for a in (a for a in relevant if a['ex_date']==day):
                    state,_=engine.state(effective_cutoff=at,receipt_cutoff=observed_at)
                    aid='action:'+digest(a['source_action_id'])
                    if a['kind']=='cash_dividends':
                        quantity=state.positions.get(INSTRUMENT,D(0))
                        if quantity:
                            entitlement=engine.event('entitlement:'+digest([pid,aid]),'dividend_entitlement',at,observed_at=observed_at,
                                action_id=aid,instrument_id=INSTRUMENT,eligible_quantity=str(quantity),per_share=a['rate'],amount=str(money(quantity*D(a['rate']))),
                                ex_at=at,mark_id=mid,policy_hash=digest(engine.plan['corporate_actions']))
                            entitlement['sequence']=mark['sequence']+len(daily)
                            daily.append(entitlement)
                            if a['payable_date']<=FUTURE[-1]:
                                payment=engine.event('payment:'+digest([pid,aid]),'dividend_payment',a['payable_date']+'T20:00:00Z',observed_at=observed_at,
                                    entitlement_id=entitlement['id'],amount=entitlement['payload']['amount'])
                                payments.append(payment)
                    else:
                        ratio=Fraction(D(a['new_rate']))/Fraction(D(a['old_rate']))
                        split=engine.event('split:'+digest([pid,aid]),'split',at,observed_at=observed_at,action_id=aid,instrument_id=INSTRUMENT,
                            numerator=ratio.numerator,denominator=ratio.denominator,mark_id=mid,pending_orders='requires_reconciliation' if day==FUTURE[0] else 'none')
                        split['sequence']=mark['sequence']+len(daily)
                        daily.append(split)
                engine.command('command:'+digest(mid),daily)
                if day==FUTURE[0]:
                    for order in store.iter_v2(portfolio_id=pid,kind='order'):
                        state,_=engine.state(effective_cutoff=at,receipt_cutoff=observed_at)
                        terms=next(store.iter_v2(portfolio_id=pid,kind='execution_terms'))
                        price=(D(str(b['bar']['c']))*D('1.0006')).quantize(D('.00000001'))
                        if state.halted or price>D(terms['price_cap']): continue
                        oid=order['id']; quantity=order['quantity']
                        fill=engine.event('fill:'+digest(oid),'fill',at,observed_at=observed_at,order_id=oid,instrument_id=INSTRUMENT,
                            side='buy',quantity=quantity,price=str(price),notional=str(money(D(quantity)*price)),fees='0.00',fee_treatment='included',incremental_fill_id='increment:'+digest(oid))
                        _commit(engine,fill)
            for payment in payments:
                payment=engine.event(payment['id'],'dividend_payment',payment['effective_at'],observed_at=observed_at,**payment['payload'])
                _commit(engine,payment)
            # Expired unfilled orders release cash via the existing reducer.
        payload=dict(manifest_hash=digest(m),bars_hash=digest(bars),actions_hash=digest(actions),observed_at=observed_at,
            completed_real_sessions=5,corporate_actions=len(relevant),split_crossed=any(a['kind']!='cash_dividends' for a in relevant))
        save_audit(round,'settled',payload)
        return payload


def observe(round,*,retrieve=False):
    m=round.manifest; owner=round.owner; now=stamp(owner.clock.wall())
    result=round._existing('forward-result:'+digest(m['id']))
    snapshot=round._existing(m['snapshot_ref'])
    elapsed=sum(utc(d+'T20:00:00Z')<=utc(now) for d in FUTURE)
    settled=read_audit(round,'settled')
    previous=[r for r in owner.store.iter_v2(kind='forward_audit') if r['manifest_ref']==m['id'] and r['purpose']=='observation_attempt']
    import json
    last_attempt=json.loads(previous[-1]['payload_json']) if previous else {}
    gaps=list(last_attempt.get('gaps',[])) if not settled else []
    usage=last_attempt.get('usage',[]); bars=[]; actions=[]
    if retrieve and not settled and utc(REVIEW_AT)<=utc(now)<utc(m['end_at']):
        gaps=[]; usage=[]
        for q in queries(m):
            work=owner.submit(q,consumer=m['id']+':observe',max_attempts=4,deadline=m['end_at'])
            progress=owner.run(work); usage.append(progress)
            evidence=owner.evidence(work)
            if progress['status']!='complete': gaps.append(q['endpoint']+':'+progress['reason'])
            elif q['endpoint']=='stock_bars': bars=evidence
            else:
                for receipt in evidence:
                    try: actions.append(accounting_action(receipt))
                    except ContractError: gaps.append('unsupported_or_incomplete_action:'+receipt['id'])
        now=stamp(owner.clock.wall())
        if not gaps:
            try: settled=settle(round,bars,actions,observed_at=now)
            except ContractError:
                gaps.append('settlement_requires_review')
        save_audit(round,'observation_attempt',dict(at=now,usage=usage,gaps=gaps,bars_hash=digest(bars),actions_hash=digest(actions)),now)
    # Saved outcome observations, including their original receipt times, supply
    # the score on replay. The original initial decision is never re-executed.
    if settled and not bars:
        bars=owner.evidence('work:'+digest(query(queries(m)[0])))
    opinions=list(owner.store.iter_v2(kind='forward_opinion'))
    forecasts=[o for o in opinions if o['manifest_ref']==m['id'] and o['forecast_probability'] is not None]
    eligible_forecasts=forecasts if result and result['status']=='decided' else []
    matured=len(eligible_forecasts) if settled and not settled['split_crossed'] else 0
    score=None
    if matured:
        last=max(snapshot['observations'],key=lambda b:b['bar']['t'])['bar']['c']
        end=max(bars,key=lambda b:b['bar']['t'])['bar']['c']
        score=(eligible_forecasts[0]['forecast_probability']-int(end>last))**2
    unscorable=len(eligible_forecasts) if settled and settled['split_crossed'] else 0
    portfolios=[p['portfolio_ref'] for p in m['participants']]+[m['baseline_ref']]
    performance=[]
    for pid in portfolios:
        p=evaluate(owner.store,pid,effective_cutoff=min(now,m['end_at'],key=utc),receipt_cutoff=now)
        performance.append(p)
    gaps.extend(sorted({gap for p in performance for gap in p['gaps']}))
    complete=bool(settled) and not gaps and matured>=m['stopping_rule']['min_matured_forecasts']
    return dict(status='window_observed' if complete else 'stopped_incomplete' if utc(now)>=utc(m['end_at']) else 'in_progress',
        manifest_id=m['id'],manifest_hash=digest(m),as_of=now,elapsed_sessions=elapsed,
        completed_real_sessions=settled['completed_real_sessions'] if settled else 0,
        matured_forecasts=matured,immature_forecasts=len(eligible_forecasts)-matured-unscorable,unscorable_forecasts=unscorable,brier=score,
        round=round.report(),performance=performance,cash_baseline=dict(initial_cash='10000.00',ending_cash='10000.00',return_value='0',interest='0.00'),
        gaps=gaps,observation_usage=usage,broker_orders=0,external_model_calls=0,promotion_eligible=False,evidence_grade='forward-insufficient',
        review_at=REVIEW_AT,stop_at=m['end_at'],
        limitations=['One preregistered five-session trial; not the 60-session/30-forecast paper-review evidence floor.',
            'Deterministic foundation-informed rules, not new model deliberation or validated skill. Council equals its fixed lead rule; no advice alpha inference.',
            'Daily-close simulated fills applied after receipt to precommitted orders; these are not contemporaneously available live fills.',
            'Provider does not guarantee timely corporate-action creation. Terminal pagination does not certify absence; total-return vintages remain provisional.',
            'Unknown local operating and one-time authoring costs keep full economics net unavailable. No unattended continuation.'])
