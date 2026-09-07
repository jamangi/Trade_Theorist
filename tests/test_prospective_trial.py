from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from trade_theorist.adapters.alpaca_market_data import Response
from trade_theorist.adapters.alpaca_market_data.transport import SingleAttemptTransport
from trade_theorist.contracts import ContractError, digest, utc
from trade_theorist.contracts_v2 import validate_references
from trade_theorist.forward.fixtures import FixtureClock
from trade_theorist.forward.shared import ForwardRound
from trade_theorist.forward.prospective import FoundationRules, check_runtime_inputs, opinion_request, read_audit
from trade_theorist.forward.trial import freeze, commit_allocations, FUTURE
from trade_theorist.forward.observe import observe, REVIEW_AT
from trade_theorist.market_requests import Coordinator, stamp
from trade_theorist.request_contracts import policy

ROOT=Path(__file__).resolve().parents[1]


class ProspectiveTrialTests(unittest.TestCase):
    def make(self,*,action_body=None):
        temp=tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        root=Path(temp.name); clock=FixtureClock(); clock.advance_to('2026-09-07T23:00:00Z')
        transport=SingleAttemptTransport('original-test-key','original-test-secret')
        owner=Coordinator(root/'data',policy(max_work_attempts=8),transport,synthetic=True,registry_root=root/'registry',clock=clock,jitter=lambda:0)
        # Test-only seam: the production constructor rejects injected clocks and
        # registries. The patched transport below never reaches an account.
        owner.synthetic=False
        owner.store.synthetic=False
        self.addCleanup(owner.close)
        m=freeze(owner,ROOT,[])
        round=ForwardRound(owner,m['id'],repo_root=ROOT)
        clock.sleep(3)
        calls=[]
        def wire(_,method,url,params):
            calls.append((url,params))
            if url.endswith('corporate-actions'):
                return Response(200,{},dict(corporate_actions=action_body or {}),stamp(clock.wall()))
            days=FUTURE if params['start'][:10]=='2026-09-08' else m['query']['expected_sessions']
            bars=[dict(t=d+'T04:00:00Z',o=100,h=102,l=99,c=101,v=1000) for d in days]
            return Response(200,{},dict(bars={'VTI':bars}),stamp(clock.wall()))
        patcher=patch.object(SingleAttemptTransport,'__call__',wire); patcher.start(); self.addCleanup(patcher.stop)
        return owner,m,round,calls

    def execute(self):
        owner,m,round,calls=self.make()
        result=round.execute(FoundationRules(ROOT,round))
        self.assertEqual((result['status'],result['reason']),('decided','none'))
        commit_allocations(round)
        return owner,m,round,calls,result

    def test_original_ancestry_independence_zero_tools_and_replay(self):
        owner,m,round,calls,result=self.execute()
        self.assertEqual(len(calls),1)
        self.assertEqual(len(set(o['snapshot_hash'] for o in result['outcomes'])),1)
        opinions=list(owner.store.iter_v2(kind='forward_opinion'))
        self.assertEqual(len(opinions),4)
        for opinion in opinions:
            request=read_audit(round,'request',opinion['id'])
            self.assertEqual(request['tools'],[])
            self.assertNotEqual(request['knowledge']['experiment_id'],m['experiment_id'])
            self.assertEqual(request['knowledge']['id'],opinion['knowledge_id'])
            if opinion['phase']=='independent': self.assertNotIn('advice',request)
            else: self.assertEqual(len(request['advice']),3)
        report=observe(round,retrieve=True)
        self.assertEqual((report['completed_real_sessions'],report['matured_forecasts'],report['immature_forecasts']),(0,0,1))
        self.assertEqual(len(calls),1)
        self.assertEqual(round.execute(FoundationRules(ROOT,round)),result)
        first=commit_allocations(round); self.assertEqual(commit_allocations(round),first)
        self.assertEqual(len(calls),1)
        owner.store.verify_v2()

    def test_roster_ancestry_future_research_and_tools_fail_closed(self):
        owner,m,round,calls=self.make()
        for change in ('roster','ancestry','future','tools'):
            altered=deepcopy(m)
            if change=='roster': altered['participants'].pop(1)
            if change=='ancestry': altered['real_context']['ancestry'][0]['knowledge_hash']='0'*64
            if change=='future': altered['real_context']['public_facts'][0]['ingested_at']='2026-09-09T00:00:00Z'
            if change=='tools': altered['real_context']['information_tools']=['mail']
            with self.assertRaises(ContractError):
                validate_references(altered,owner.store.v2_record); check_runtime_inputs(ROOT,altered)
        runtime=FoundationRules(ROOT,round)
        a=m['real_context']['ancestry'][0]
        for tool in ['repository','mail','retrieval','filesystem','web']:
            with self.assertRaises(ContractError): opinion_request(m['participants'][0],{},a,runtime.learning[a['character_id']],m['real_context'],provided_tools=[tool])
        self.assertEqual(calls,[])

    def test_deadline_prevents_order_backfill(self):
        owner,m,round,calls=self.make()
        result=round.execute(FoundationRules(ROOT,round)); self.assertEqual(result['status'],'decided')
        owner.clock.advance_to(m['decision_at'])
        with self.assertRaises(ContractError): commit_allocations(round)
        self.assertEqual(list(owner.store.iter_v2(kind='order')),[])

    def test_post_horizon_observation_simulates_saved_orders_and_matures_only_then(self):
        owner,m,round,calls,result=self.execute()
        owner.clock.advance_to(REVIEW_AT); owner.clock.sleep(1)
        report=observe(round,retrieve=True)
        self.assertEqual(report['gaps'],[])
        self.assertEqual((report['status'],report['completed_real_sessions'],report['matured_forecasts']),('window_observed',5,1))
        self.assertEqual(report['brier'],0.25)
        self.assertEqual(len(calls),3)
        fills=[e for e in owner.store.iter_v2(kind='ledger_event') if e['event_type']=='fill']
        self.assertEqual(len(fills),3)
        self.assertTrue(all(utc(e['effective_at'])<utc(e['observed_at']) for e in fills))
        self.assertEqual(observe(round,retrieve=True)['matured_forecasts'],1)
        self.assertEqual(len(calls),3)
        owner.store.verify_v2()

    def test_dividend_receivable_and_payment_are_matched_and_not_double_counted(self):
        action=dict(id='original-dividend',symbol='VTI',process_date='2026-09-09',ex_date='2026-09-10',payable_date='2026-09-11',rate=0.5,currency='USD',foreign=False)
        owner,m,round,calls=self.make(action_body={'cash_dividends':[action]})
        round.execute(FoundationRules(ROOT,round)); commit_allocations(round)
        owner.clock.advance_to(REVIEW_AT); owner.clock.sleep(1)
        report=observe(round,retrieve=True)
        self.assertEqual(report['gaps'],[])
        self.assertEqual(report['status'],'window_observed')
        events=list(owner.store.iter_v2(kind='ledger_event'))
        self.assertEqual(sum(e['event_type']=='dividend_entitlement' for e in events),3)
        self.assertEqual(sum(e['event_type']=='dividend_payment' for e in events),3)
        self.assertTrue(all(p['receivables']=='0.00000000' for p in report['performance']))
        owner.store.verify_v2()

    def test_incomplete_actions_remain_a_visible_gap_on_read_only_report(self):
        action=dict(id='original-incomplete',symbol='VTI',process_date='2026-09-09',ex_date='2026-09-10')
        owner,m,round,calls=self.make(action_body={'cash_dividends':[action]})
        round.execute(FoundationRules(ROOT,round)); commit_allocations(round)
        owner.clock.advance_to(REVIEW_AT); owner.clock.sleep(1)
        report=observe(round,retrieve=True)
        self.assertEqual(report['completed_real_sessions'],0)
        self.assertTrue(report['gaps'])
        self.assertEqual(observe(round)['gaps'],report['gaps'])
        self.assertEqual(len(calls),3)

    def test_missing_review_deadline_does_not_restart_or_backfill_window(self):
        owner,m,round,calls,result=self.execute()
        owner.clock.advance_to(m['end_at']); owner.clock.sleep(1)
        report=observe(round,retrieve=True)
        self.assertEqual((report['status'],report['completed_real_sessions'],report['matured_forecasts']),('stopped_incomplete',0,0))
        self.assertEqual(len(calls),1)


if __name__=='__main__': unittest.main()
