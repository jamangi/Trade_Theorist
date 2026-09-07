"""Finite private corporate-action qualification through the existing quota owner."""
import json
import os
from pathlib import Path
import time

from qualify_step_09 import credentials, operating_policy, save
from trade_theorist.adapters.alpaca_market_data.actions import accounting_action
from trade_theorist.adapters.alpaca_market_data.transport import SingleAttemptTransport
from trade_theorist.contracts import ContractError, digest
from trade_theorist.market_requests import Coordinator, stamp
from trade_theorist.learn.reviewed import write_once

ROOT = Path(__file__).resolve().parents[1]


def measure(owner, wire, directory):
    path = directory / 'manifest.json'
    if path.exists():
        manifest = json.loads(path.read_text())
    else:
        at = time.time()
        queries = []
        for symbols,start,end in [(['VTI','QQQ','SPY'],'2026-01-01','2026-09-04'),(['NVDA'],'2024-06-01','2024-06-30')]:
            queries.append(dict(schema_version=1,record_type='market_query',provider='alpaca',endpoint='corporate_actions',
                sharing_scope=owner.policy['sharing_scopes'][0],rights_ref=owner.policy['rights_ref'],symbols=symbols,
                start=start+'T00:00:00Z',end=end+'T00:00:00Z',revision_policy='revision:retain-receipts',
                freshness_after=stamp(at),information_cutoff=stamp(at+600),data_quality='all',region='us',page_limit=1000))
        manifest = dict(created_at=stamp(at),deadline=stamp(at+600),queries=queries,max_attempts_per_query=4,
            maximum_total_attempts=8,initial_attempts=owner.usage()['physical_attempts'],broker_orders=0,
            scope='Private VTI daily-pilot dividend qualification; QQQ/SPY bars controls and NVDA historical split control only. No control is a trading opportunity.',
            authority='Standing owner free Alpaca/private storage and finite agent-selected research authority in decisions/APPROVALS.md.')
        write_once(path,manifest)
    report = dict(status='blocked',runs=[],broker_orders=0,external_model_calls=0,manifest_hash=digest(manifest),
        publication_time='unknown; use actual receipt as earliest observed availability',
        limitation='Terminal pagination does not certify absence of late announcements. Raw prices only; incomplete or unsupported events block dependent accounting. No prospective return evidence.',
        docs=['https://docs.alpaca.markets/us/reference/corporateactions-1',
              'https://github.com/alpacahq/alpaca-py/blob/master/alpaca/data/models/corporate_actions.py'])
    all_actions = []
    for number,q in enumerate(manifest['queries']):
        work = owner.submit(q,consumer='step-11-actions',max_attempts=4,deadline=manifest['deadline'])
        usage = owner.run(work)
        receipts = owner.evidence(work)
        save(directory / f'receipts-{number}.json',receipts)
        normalized, gaps = [], []
        for receipt in receipts:
            try:
                normalized.append(accounting_action(receipt))
            except ContractError:
                gaps.append(dict(receipt_id=receipt['id'],reason='unsupported_or_incomplete_action'))
        save(directory / f'accounting-actions-{number}.json',dict(actions=normalized,gaps=gaps))
        all_actions.extend(normalized)
        report['runs'].append(dict(status=usage['status'],reason=usage['reason'],attempts=usage['attempts'],
            pages=usage['pages'],throttles=usage['throttles'],retries=usage['retries'],receipts=len(receipts),
            supported_actions=len(normalized),gaps=len(gaps),symbols=q['symbols'],work_id=work))
        before = owner.usage()['physical_attempts']
        owner.submit(q,consumer='step-11-actions-replay',max_attempts=4,deadline=manifest['deadline'])
        owner.run(work)
        if owner.usage()['physical_attempts'] != before:
            raise ContractError('Exact completed query replay unexpectedly dispatched')
    report['physical_attempts'] = owner.usage()['physical_attempts'] - manifest['initial_attempts']
    if report['physical_attempts'] > 8:
        raise ContractError('Corporate-action workload exceeded its finite budget')
    dividends = {a['symbol'] for a in all_actions if a['kind'] == 'cash_dividends'}
    split = any(a['symbol'] == 'NVDA' and a['kind'] == 'forward_splits' for a in all_actions)
    if all(r['status'] == 'complete' and not r['gaps'] for r in report['runs']) and {'VTI','QQQ','SPY'} <= dividends and split:
        report['status'] = 'qualified_scoped_corporate_action_receipts'
    report.update(dividend_controls_passed={'VTI','QQQ','SPY'} <= dividends,split_control_passed=split,
                  completed_at=stamp(time.time()),zero_additional_replay_requests=True)
    save(directory / 'report.json',report)
    save(directory / 'transport-attempts.json',wire.observed_attempts())
    return report


if __name__ == '__main__':
    root = Path(os.environ['LOCALAPPDATA']) / 'TradeTheorist/alpaca-market-data'
    wire = SingleAttemptTransport(*credentials())
    with Coordinator(root,operating_policy(),wire) as owner:
        report = measure(owner,wire,root/'step-11-actions')
    # Explicit counts/operational metadata allowlist: no rates, prices or raw rows.
    public = {k:report[k] for k in ('status','physical_attempts','broker_orders','external_model_calls','manifest_hash',
        'publication_time','limitation','docs','dividend_controls_passed','split_control_passed','completed_at','zero_additional_replay_requests')}
    public['runs'] = [{k:r[k] for k in ('status','reason','attempts','pages','throttles','retries','receipts','supported_actions','gaps','symbols')} for r in report['runs']]
    write_once(ROOT/'examples/step-11/corporate-action-qualification.json',public)
    print(json.dumps(public,indent=2))
