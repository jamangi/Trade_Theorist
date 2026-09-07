"""Explicit learning ancestry and tools-free, foundation-informed shadow policies.

This deterministic runtime is not a new LLM deliberation or a validated strategy.
The source reviews inform its fixed rules; historical learning retains its own
identities and contamination labels in every request.
"""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import json

from ..contracts import ContractError, canonical, digest, utc
from ..learn.continuation import check_saved_readiness_v2, read
from ..ingest.tool_policy import enforce_tool_access

ROSTER = {'index_steward','value_rationalist','systematic_trend_operator'}


def audit_id(round,purpose,key=None):
    return 'forward-audit:'+digest([round.manifest['id'],purpose,key])


def read_audit(round,purpose,key=None):
    record=round._existing(audit_id(round,purpose,key))
    return json.loads(record['payload_json']) if record else None


def save_audit(round,purpose,payload,key=None):
    record=round._record('forward_audit',audit_id(round,purpose,key),snapshot_ref=round.manifest['snapshot_ref'],
        purpose=purpose,payload_json=canonical(payload),payload_hash=digest(payload))
    round.store.put_v2([record])
    return payload


def runtime_hash():
    folder=Path(__file__).parent
    files=['forward/'+name for name in ('prospective.py','trial.py','observe.py','shared.py','validation.py','schema.py')]
    files+=['schema_v2.py','contracts_v2.py','storage_v2.py','market_requests.py','request_contracts.py',
        'adapters/alpaca_market_data/actions.py','adapters/alpaca_market_data/transport.py',
        'adapters/trader_user_sim/v2.py','evaluate/ledger_v2.py','evaluate/portfolio_v2.py']
    return digest({name:(folder.parent/name).read_text(encoding='utf-8') for name in files})


def load_learning(root, *, cutoff):
    """Resolve immutable originals; do not transplant records into the trial."""
    root = Path(root)
    register = check_saved_readiness_v2(root)
    if utc(register['recorded_at']) > utc(cutoff):
        raise ContractError('Learning eligibility was unavailable at decision registration')
    result = {}
    for entry in register['participants']:
        name = entry['character_id']
        folder = root / 'characters' / name
        bundle = read(folder / ('checkpoints/bogle-2017.bundle.json' if name == 'index_steward' else 'checkpoints/foundation-v2/bundle.json'))
        checkpoint = next(r for r in bundle if r['id'] == entry['knowledge_checkpoint'])
        character = next(r for r in bundle if r['id'] == entry['learning_character_version'])
        eligible_bundle = read(folder / ('versions/pilot-foundation-v1.bundle.json' if name == 'index_steward' else 'versions/pilot-foundation-v2.bundle.json'))
        eligible = next(r for r in eligible_bundle if r['record_type'] == 'character')
        if (digest(checkpoint) != entry['knowledge_hash'] or digest(character) != entry['learning_character_hash']
                or digest(eligible) != entry['version_hash'] or utc(checkpoint['created_at']) > utc(cutoff)):
            raise ContractError('Immutable learning ancestry changed or is future information')
        result[name] = dict(entry=entry,knowledge=checkpoint,learning_character=character,eligible_character=eligible)
    return register,result


def binding(local_character, learning):
    e = learning['entry']; eligible = learning['eligible_character']; cp = learning['knowledge']
    return dict(local_character_ref=local_character['id'],character_id=e['character_id'],
        eligible_version_id=eligible['id'],eligible_version_hash=digest(eligible),
        learning_version_id=learning['learning_character']['id'],learning_version_hash=digest(learning['learning_character']),
        knowledge_id=cp['id'],knowledge_hash=digest(cp),constitution_hash=eligible['constitution_hash'],
        curriculum_hash=eligible['curriculum_hash'],foundation_completed_at=cp['created_at'])


def validate_real_context(manifest, lookup):
    context = manifest.get('real_context')
    if not context or context['information_tools'] != []:
        raise ContractError('Real round requires frozen eligibility and a tools-free runtime')
    if Decimal(context['allocation_fraction']) <= 0 or Decimal(context['allocation_fraction']) > Decimal('0.25'):
        raise ContractError('Initial shadow allocation exceeds the bounded experiment')
    if context['trend_lookback'] != 20 or context['forecast']['horizon_sessions'] != 5:
        raise ContractError('Unreviewed trend variant')
    from .observe import queries, REVIEW_AT
    if context['observation_policy'] != dict(review_at=REVIEW_AT,max_total_attempts=8,queries=queries(manifest)):
        raise ContractError('Finite observation schedule or budget changed')
    ancestors = context['ancestry']
    if len(ancestors)!=4 or len({a['local_character_ref'] for a in ancestors}) != len(ancestors) or {a['character_id'] for a in ancestors} != ROSTER:
        raise ContractError('Incomplete or duplicate learning roster')
    by_local = {a['local_character_ref']:a for a in ancestors}
    individuals = []
    for peer in manifest['participants']:
        a = by_local.get(peer['character_ref'])
        if not a:
            raise ContractError('Participant lacks immutable ancestry')
        if peer['mode'] == 'character_portfolio': individuals.append(a['character_id'])
        elif a['character_id'] != 'index_steward': raise ContractError('Initial council lead changed')
    if sorted(individuals) != sorted(ROSTER) or len(manifest['participants']) != 4:
        raise ContractError('Every independent Character and the council must participate')
    if [p['mode'] for p in manifest['participants']]!=['character_portfolio']*3+['council']:
        raise ContractError('All independent opinions must precede the council')
    for a in ancestors:
        character = lookup(a['local_character_ref'])
        if (character['record_type'] != 'character' or character['character_id'] != 'character:' + a['character_id']
                or character['readiness'] != 'ready' or character['constitution_hash'] != a['constitution_hash']
                or character['curriculum_hash'] != a['curriculum_hash']
                or utc(a['foundation_completed_at']) > utc(manifest['created_at'])):
            raise ContractError('Local Character differs from its eligible ancestor')
    sessions = context['calendar']
    if [s['session'] for s in sessions] != sorted({s['session'] for s in sessions}):
        raise ContractError('Calendar must be unique and ordered')
    for s in sessions:
        if not s['session'] == s['open_at'][:10] == s['close_at'][:10] or not utc(s['open_at']) < utc(s['close_at']):
            raise ContractError('Invalid frozen market session')
    expected = set(manifest['query']['expected_sessions'])
    if not expected <= {s['session'] for s in sessions}:
        raise ContractError('Observation calendar is missing sessions')
    future = [s for s in sessions if utc(s['open_at']) > utc(manifest['decision_at'])]
    forecast = context['forecast']
    if (not future or forecast['horizon_sessions'] != manifest['stopping_rule']['horizon_sessions']
            or len(future) < forecast['horizon_sessions']
            or forecast['resolves_at'] != future[forecast['horizon_sessions']-1]['close_at']
            or not utc(forecast['resolves_at']) < utc(manifest['end_at'])
            or not utc(manifest['decision_at']) < utc(context['order_expiry']) <= utc(manifest['end_at'])):
        raise ContractError('Forecast or execution horizon is not prospective')
    for fact in context['public_facts']:
        if (fact['payload_hash'] != digest(fact['text']) or utc(fact['ingested_at']) > utc(manifest['created_at'])
                or fact['published_at'] is not None and utc(fact['published_at']) > utc(fact['ingested_at'])):
            raise ContractError('Public research is unpinned or future information')


def check_runtime_inputs(root, manifest):
    context = manifest['real_context']
    register,learning = load_learning(root,cutoff=manifest['created_at'])
    if context['public_facts'] != read(Path(root)/'examples/step-11/public-research.json'):
        raise ContractError('Public research differs from the reviewed input')
    if digest(register) != context['readiness_register_hash'] or context['runtime_hash'] != runtime_hash():
        raise ContractError('Frozen eligibility or executable runtime changed')
    for a in context['ancestry']:
        expected = binding({'id':a['local_character_ref']},learning[a['character_id']])
        if a != expected: raise ContractError('Forged or relabeled knowledge ancestry')
    for path,key,status in [('examples/step-09/qualification.json','bars_qualification_hash',None),
                           ('examples/step-11/corporate-action-qualification.json','actions_qualification_hash','qualified_scoped_corporate_action_receipts')]:
        evidence = read(Path(root)/path)
        if digest(evidence) != context[key] or (status and evidence['status'] != status):
            raise ContractError('Source qualification is missing or changed')
        if key == 'bars_qualification_hash' and (evidence.get('decision') != 'selected_for_private_local_delayed_daily_bars' or not evidence.get('production_selected')):
            raise ContractError('Daily bars have not been qualified')
    return learning


def opinion_request(peer,snapshot,ancestor,learning,context,*,provided_tools=()):
    enforce_tool_access('forward_shadow',provided_tools)
    if provided_tools: raise ContractError('This runtime has no tools')
    if ancestor['knowledge_hash'] != digest(learning['knowledge']) or ancestor['knowledge_id'] != learning['knowledge']['id']:
        raise ContractError('Knowledge does not match immutable ancestry')
    return dict(runtime_id='foundation-rules-v1',runtime_hash=context['runtime_hash'],tools=[],
        character_ref=peer['character_ref'],portfolio_ref=peer['portfolio_ref'],ancestry=deepcopy(ancestor),
        knowledge=deepcopy(learning['knowledge']),snapshot=deepcopy(snapshot),snapshot_hash=digest(snapshot),
        public_facts=deepcopy(context['public_facts']),allocation_fraction=context['allocation_fraction'],
        rule='Initial-only allocation: Index buy a bounded broad-fund sleeve; Value abstain without valuation evidence; Trend buy only if last completed close exceeds preceding 20 highs, otherwise abstain. No intrawindow discretion; future evaluation after five sessions.',
        forecast=deepcopy(context['forecast']))


def validate_opinion(record,manifest,lookup):
    if manifest['contamination'] != 'forward-insufficient': raise ContractError('Prospective opinion cannot belong to fixture')
    snapshot = lookup(record['snapshot_ref'])
    peer = next((p for p in manifest['participants'] if p['portfolio_ref'] == record['portfolio_ref']),None)
    a = next((a for a in manifest['real_context']['ancestry'] if a['local_character_ref'] == record['character_ref']),None)
    if (not peer or not a or peer['character_ref'] != record['character_ref'] or snapshot['status'] != 'ready'
            or record['snapshot_hash'] != digest(snapshot) or record['knowledge_id'] != a['knowledge_id']
            or record['knowledge_hash'] != a['knowledge_hash'] or not utc(snapshot['created_at']) <= utc(record['created_at']) < utc(manifest['decision_at'])
            or record['forecast_resolves_at'] != manifest['real_context']['forecast']['resolves_at']):
        raise ContractError('Opinion is late, ungrounded or has wrong ancestry')
    phase = 'independent' if peer['mode'] == 'character_portfolio' else 'council'
    if record['phase'] != phase or phase == 'independent' and record['advice_refs']:
        raise ContractError('Independent initial opinion received council advice')
    context=manifest['real_context']
    if (record['allocation_fraction']!=(context['allocation_fraction'] if record['action']=='buy' else '0')
            or record['forecast_probability']!=(context['forecast']['probability'] if a['character_id']=='systematic_trend_operator' else None)):
        raise ContractError('Opinion differs from the preregistered allocation or forecast')
    trace=lookup('forward-audit:'+digest([manifest['id'],'request',record['id']]))
    request=json.loads(trace['payload_json'])
    if (digest(request)!=record['request_hash'] or request['tools'] or digest(request['knowledge'])!=a['knowledge_hash']
            or digest(request['snapshot'])!=record['snapshot_hash'] or request['ancestry']!=a
            or request['public_facts']!=context['public_facts'] or request['portfolio_ref']!=record['portfolio_ref']
            or utc(trace['created_at'])>utc(record['created_at'])
            or phase=='independent' and 'advice' in request):
        raise ContractError('Opinion request differs from its sealed information boundary')
    if phase == 'council':
        advice = [lookup(i) for i in record['advice_refs']]
        if len(advice) != 3 or len({a['portfolio_ref'] for a in advice}) != 3 or any(
            a['record_type'] != 'forward_opinion' or a['phase'] != 'independent' or a['manifest_ref'] != manifest['id']
            or a['snapshot_hash'] != record['snapshot_hash'] or utc(a['created_at']) > utc(record['created_at']) for a in advice):
            raise ContractError('Council advice is incomplete, future or from another opportunity set')
        if request.get('advice')!=[{k:a[k] for k in ('id','character_ref','action','rationale','snapshot_hash')} for a in advice]:
            raise ContractError('Council request did not contain its declared bounded advice')


class FoundationRules:
    """One fixed, initial-only deterministic policy; zero external model calls."""
    def __init__(self, root, round):
        self.round = round
        self.context = round.manifest['real_context']
        self.learning = check_runtime_inputs(root,round.manifest)
        self.initials = []
        self.calls = 0

    def complete(self, peer, snapshot):
        a = next(a for a in self.context['ancestry'] if a['local_character_ref'] == peer['character_ref'])
        request = opinion_request(peer,snapshot,a,self.learning[a['character_id']],self.context)
        name = a['character_id']
        action,reason = 'abstain','Daily bars do not establish underlying value or a margin of safety.'
        if name == 'index_steward':
            if not self.context['public_facts']: raise ContractError('Broad-fund role needs qualified fund evidence')
            action,reason = 'buy','Initial bounded broad-fund allocation; long-horizon cost/diversification rationale, no short-term alpha claim.'
        if name == 'systematic_trend_operator':
            bars = sorted((i['bar'] for i in snapshot['observations'] if i['bar']['symbol'] == 'VTI'),key=lambda b:b['t'])
            reason = 'No completed-close breakout over the preceding 20-session highs; abstain.'
            if len(bars) < 21: reason = 'Insufficient complete sessions for the frozen 20-session breakout.'
            elif bars[-1]['c'] > max(b['h'] for b in bars[-21:-1]):
                action,reason = 'buy','Completed close exceeds preceding 20-session highs; initial bounded research allocation, not a validated Turtle transfer.'
        council = peer['mode'] == 'council'
        if council:
            if len(self.initials) != 3: raise ContractError('Independent opinions must precede council decision')
            request['advice'] = [{k:self.round.store.v2_record(i)[k] for k in ('id','character_ref','action','rationale','snapshot_hash')} for i in self.initials]
            reason += ' Three bounded initial opinions reviewed; Value uncertainty and Trend condition retained. Lead policy fixes allocation; no causal advice benefit claimed.'
        opinion = self.round._record('forward_opinion','forward-opinion:'+digest([self.round.manifest['id'],peer['portfolio_ref']]),
            snapshot_ref=snapshot['id'],snapshot_hash=digest(snapshot),portfolio_ref=peer['portfolio_ref'],character_ref=peer['character_ref'],
            knowledge_id=a['knowledge_id'],knowledge_hash=a['knowledge_hash'],phase='council' if council else 'independent',action=action,
            rationale=reason,request_hash=digest(request),advice_refs=list(self.initials) if council else [],
            allocation_fraction=self.context['allocation_fraction'] if action == 'buy' else '0',
            forecast_probability=self.context['forecast']['probability'] if name == 'systematic_trend_operator' else None,
            forecast_resolves_at=self.context['forecast']['resolves_at'],model_calls=0,runtime_id='foundation-rules-v1')
        # Requests are private immutable events, including the original learning
        # record with its original Character/experiment and hindsight label.
        with self.round.owner.db,self.round.store.transaction():
            trace=self.round._record('forward_audit',audit_id(self.round,'request',opinion['id']),snapshot_ref=snapshot['id'],
                purpose='request',payload_json=canonical(request),payload_hash=digest(request))
            trace['created_at']=opinion['created_at']
            self.round.store.put_v2([trace])
            self.round.store.put_v2([opinion])
        if not council: self.initials.append(opinion['id'])
        self.calls += 1
        return dict(action=action,rationale=reason,tokens=0)
