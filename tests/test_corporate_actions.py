import tempfile
from pathlib import Path
import unittest

from trade_theorist.adapters.alpaca_market_data import Response
from trade_theorist.adapters.alpaca_market_data.actions import URL, parse_page, accounting_action
from trade_theorist.contracts import ContractError
from trade_theorist.market_requests import Coordinator, stamp, query
from trade_theorist.request_contracts import policy
from test_market_requests import FakeClock


def action_query():
    return dict(schema_version=1,record_type='market_query',provider='alpaca',endpoint='corporate_actions',
        sharing_scope='scope:original-fixture',rights_ref='rights:original-fixture',symbols=['VTI'],
        start='2024-01-01T00:00:00Z',end='2024-01-31T00:00:00Z',revision_policy='revision:receipts',
        freshness_after='2024-02-01T00:00:00Z',information_cutoff='2024-02-02T00:00:00Z',
        data_quality='all',region='us',page_limit=1)


def dividend(identifier='action-1', **changes):
    return dict(id=identifier,symbol='VTI',process_date='2024-01-15',ex_date='2024-01-17',
                payable_date='2024-01-19',rate=0.5,currency='USD',foreign=False,**changes)


class CorporateActionTests(unittest.TestCase):
    def test_action_throttle_blocks_bars_and_survives_owner_restart(self):
        from datetime import datetime
        clock=FakeClock(); clock.epoch=datetime.fromisoformat('2024-02-01T00:00:00+00:00').timestamp()
        calls=[]
        def wire(method,url,params):
            calls.append(url)
            if len(calls)==1: return Response(429,{'Retry-After':'120'},{},stamp(clock.wall()))
            if url==URL: return Response(200,{},dict(corporate_actions={}),stamp(clock.wall()))
            return Response(200,{},dict(bars={'VTI':[dict(t='2024-01-31T21:00:00Z',o=100,h=102,l=99,c=101,v=100)]}),stamp(clock.wall()))
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); p=policy(max_wait_seconds=0)
            q=action_query()
            bars={k:q[k] for k in ('schema_version','record_type','provider','sharing_scope','rights_ref','symbols','revision_policy','freshness_after','information_cutoff','page_limit')}
            bars.update(endpoint='stock_bars',start='2024-01-31T00:00:00Z',end='2024-01-31T21:00:00Z',timeframe='1Day',feed='sip',adjustment='raw',asof=None,expected_sessions=['2024-01-31'])
            with Coordinator(root/'data',p,wire,synthetic=True,registry_root=root/'registry',clock=clock) as owner:
                action=owner.submit(q,consumer='actions',max_attempts=3,deadline=q['information_cutoff'])
                self.assertEqual(owner.run(action)['reason'],'cooldown')
                bar=owner.submit(bars,consumer='bars',max_attempts=3,deadline=q['information_cutoff'])
                self.assertEqual(owner.run(bar)['reason'],'cooldown')
                self.assertEqual(len(calls),1)
            with Coordinator(root/'data',p,wire,synthetic=True,registry_root=root/'registry',clock=clock) as owner:
                self.assertIn(owner.run(bar)['reason'],['cooldown','recovery'])
                self.assertEqual(len(calls),1)
                clock.sleep(120)
                self.assertEqual(owner.run(action)['status'],'complete')
                clock.sleep(1)
                self.assertEqual(owner.run(bar)['status'],'complete')
                self.assertEqual((len(calls),owner.usage()['physical_attempts']),(3,3))

    def test_shared_pagination_receipt_and_cache(self):
        clock = FakeClock()
        # Existing clock's default date is unrelated to these deliberately fixed inputs.
        clock.epoch = __import__('datetime').datetime.fromisoformat('2024-02-01T00:00:00+00:00').timestamp()
        calls = []
        def wire(method,url,params):
            calls.append((url,params))
            return Response(200,{},dict(corporate_actions={'cash_dividends':[dividend(str(len(calls)))]},
                next_page_token='page-2' if len(calls) == 1 else None),stamp(clock.wall()))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with Coordinator(root/'data',policy(),wire,synthetic=True,registry_root=root/'registry',clock=clock) as owner:
                q = action_query()
                work = owner.submit(q,consumer='actions',max_attempts=3,deadline=q['information_cutoff'])
                self.assertEqual(owner.run(work,max_pages=1)['status'],'deferred')
                self.assertEqual(owner.run(work,resume=owner.resume(work),value=q)['status'],'complete')
                self.assertEqual(len(owner.evidence(work)),2)
                self.assertTrue(all(x['published_at'] is None and 'bar' not in x for x in owner.evidence(work)))
                self.assertEqual(accounting_action(owner.evidence(work)[0])['rate'],'0.5')
                owner.submit(q,consumer='paired',max_attempts=3,deadline=q['information_cutoff'])
                owner.run(work)
                self.assertEqual(len(calls),2)
                self.assertEqual(owner.usage()['physical_attempts'],2)
                self.assertTrue(all(c[0] == URL for c in calls))

    def test_canonical_query_and_inclusive_process_date_boundary(self):
        from datetime import datetime
        q=action_query()
        self.assertEqual(query(query(q)),query(q))
        clock=FakeClock(); clock.epoch=datetime.fromisoformat('2024-02-01T00:00:00+00:00').timestamp()
        row=dividend(); row['process_date']='2024-01-31'
        def wire(*_): return Response(200,{},dict(corporate_actions={'cash_dividends':[row]}),stamp(clock.wall()))
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with Coordinator(root/'data',policy(),wire,synthetic=True,registry_root=root/'registry',clock=clock) as owner:
                work=owner.submit(q,consumer='boundary',max_attempts=2,deadline=q['information_cutoff'])
                self.assertEqual(owner.run(work)['status'],'complete')
                self.assertEqual(len(owner.evidence(work)),1)

    def test_missing_economics_and_unsupported_actions_fail_closed(self):
        row = dividend(); row.pop('payable_date')
        receipt = dict(action=dict(kind='cash_dividends',symbol='VTI',process_date='2024-01-15',raw=row),received_at='2024-02-01T00:00:00Z')
        with self.assertRaises(ContractError): accounting_action(receipt)
        receipt['action']['kind'] = 'spin_offs'
        with self.assertRaises(ContractError): accounting_action(receipt)

    def test_repeated_page_token_and_unrequested_symbol_rejected(self):
        response = Response(200,{},dict(corporate_actions={'cash_dividends':[dividend()]},next_page_token='again'),'2024-02-01T00:00:00Z')
        with self.assertRaises(ContractError): parse_page(response,['VTI'],seen=['again'])
        with self.assertRaises(ContractError): parse_page(response,['SPY'])

    def test_incomplete_data_is_retained_before_accounting_rejection(self):
        row = dividend(); row.pop('ex_date')
        response = Response(200,{},dict(corporate_actions={'cash_dividends':[row]},next_page_token=None),'2024-02-01T00:00:00Z')
        records,token = parse_page(response,['VTI'])
        self.assertEqual(len(records),1)
        self.assertIsNone(token)
        with self.assertRaises(ContractError): accounting_action(dict(action=records[0],received_at=response.received_at))


if __name__ == '__main__': unittest.main()
