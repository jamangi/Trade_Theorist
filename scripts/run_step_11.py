"""One authorized finite shadow trial: start, manual observe, or private report.

No broker orders, paid model calls, scheduler, new window or policy tuning.
"""
import argparse
import json
import os
from pathlib import Path
import time

from qualify_step_09 import credentials, operating_policy, save
from trade_theorist.adapters.alpaca_market_data.transport import SingleAttemptTransport
from trade_theorist.contracts import ContractError, digest, utc
from trade_theorist.market_requests import Coordinator
from trade_theorist.learn.reviewed import write_once
from trade_theorist.forward.shared import ForwardRound
from trade_theorist.forward.prospective import FoundationRules, save_audit, read_audit
from trade_theorist.forward.trial import freeze, commit_allocations, TRIAL
from trade_theorist.forward.observe import observe

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['start','observe','report'])
    args=parser.parse_args()
    root=Path(os.environ['LOCALAPPDATA'])/'TradeTheorist/alpaca-market-data'
    directory=root/'step-11-forward'
    wire=SingleAttemptTransport(*credentials())
    with Coordinator(root,operating_policy(),wire) as owner:
        mid='forward:'+TRIAL
        row=owner.store.connection.execute('SELECT body FROM v2_records WHERE id=?',(mid,)).fetchone()
        if row:
            manifest=json.loads(row[0])
        else:
            if args.action!='start': raise ContractError('Start the preregistered trial first')
            qualification=json.loads((root/'step-11-actions/report.json').read_text())
            public=json.loads((ROOT/'examples/step-11/corporate-action-qualification.json').read_text())
            if qualification['manifest_hash']!=public['manifest_hash'] or qualification['status']!=public['status']:
                raise ContractError('Private corporate-action qualification differs')
            receipts=sum([json.loads((root/f'step-11-actions/receipts-{i}.json').read_text()) for i in range(2)],[])
            if len(receipts)!=sum(r['receipts'] for r in public['runs']): raise ContractError('Qualified receipt coverage differs')
            manifest=freeze(owner,ROOT,receipts)
        write_once(directory/'manifest.json',manifest)
        round=ForwardRound(owner,mid,repo_root=ROOT)
        if args.action=='start':
            if time.time()<utc(manifest['start_at']).timestamp(): time.sleep(utc(manifest['start_at']).timestamp()-time.time())
            provider=FoundationRules(ROOT,round)
            while True:
                result=round.execute(provider)
                if result['status']!='deferred': break
                time.sleep(1)
            commit_allocations(round)
        report=observe(round,retrieve=args.action=='observe')
        owner.store.verify_v2()
        path=directory/('report-'+digest(report)+'.json')
        write_once(path,report)
        save(directory/'latest-report.json',dict(path=str(path),report_hash=digest(report)))
        save(directory/'transport-attempts-latest.json',wire.observed_attempts())
    # Explicit operational-metadata allowlist. Never export the private report,
    # market rows, rates, order sizes, holdings or reconstructable performance.
    public={k:report[k] for k in ('status','manifest_id','manifest_hash','as_of','elapsed_sessions','completed_real_sessions',
        'matured_forecasts','immature_forecasts','unscorable_forecasts','broker_orders','external_model_calls','promotion_eligible','evidence_grade','review_at','stop_at','limitations')}
    public.update(round_status=report['round']['status'],round_reason=report['round']['result']['reason'] if report['round']['result'] else None,
        snapshot_hash=report['round']['snapshot_hash'],initial_market_requests=report['round']['account_calls'],
        participant_count=len(manifest['participants']),eligible_foundations=3,private_report_hash=digest(report),
        source_gaps=len(report['gaps']),automatic_continuation=False)
    save(ROOT/'examples/step-11/forward-status.json',public)
    print(json.dumps(public,indent=2))


if __name__=='__main__': main()
