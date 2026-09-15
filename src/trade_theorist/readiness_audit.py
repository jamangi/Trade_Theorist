"""Offline Step 12 evidence review, outside the immutable Step 11 runtime.

No coordinator or transport is constructed. Public results are explicit counts,
booleans and hashes; exceptions never contain private records or market values.
"""
from decimal import Decimal as D, localcontext
import json

from .contracts import ContractError, digest, utc
from .adapters.trader_user_sim.v2 import SimulatorV2
from .evaluate.portfolio_v2 import number, compare
from .forward.prospective import check_runtime_inputs
from .forward.observe import queries
from .forward.trial import FUTURE
from .adapters.alpaca_market_data.actions import accounting_action
from .market_requests import query
from .contracts_v2 import validate_references
from .observation_job import load_config, read, verified_report
from .private_backup import database_evidence, readonly
from .storage_v2 import V2Store


def require(condition, message):
    if not condition:
        raise ContractError(message)


def replay_performance(store, report):
    """Recompute ledger values; evaluate() can return its cached saved report.

The source reducer is production code; the golden-vector regression supplies
the independent numerical oracle. Do not mistake equality to a cache for replay.
"""
    with localcontext() as context:
        context.prec = 50
        state, sources = SimulatorV2(store, report['portfolio_id']).state(
            effective_cutoff=report['effective_cutoff'], receipt_cutoff=report['receipt_cutoff'])
        require(report['source_chain_hash'] == digest(sources), 'Accounting source hash differs')
        require(report['source_event_ids'] == [r['id'] for r in sources], 'Accounting source list differs')
        scalars = dict(cash=state.cash, reserved=state.reserved, available=state.cash-state.reserved,
            initial_funding=state.initial, net_external_flows=state.external, fifo_basis=state.basis,
            realized=state.realized, income=state.income, fees=state.fees,
            receivables=state.receivable, unallocated_expenses=state.expenses)
        nav, wealth = state.equity(), state.wealth()
        pnl = None if nav is None else nav-state.initial-state.external
        if state.ended:
            pnl = state.realized+state.income-state.expenses
        metrics = dict(equity=nav, unrealized=None if nav is None else nav-state.cash-state.receivable-state.basis,
            strategy_pnl=pnl, twr=None if wealth is None else wealth-1,
            max_drawdown=None if state.schedule_gap else state.max_dd)
        for key, amount in scalars.items():
            require(report[key] == number(amount), 'Ledger scalar mismatch: '+key)
        for key, amount in metrics.items():
            require(report[key]['value'] == number(amount), 'Ledger metric mismatch: '+key)
            require(amount is not None or bool(report[key]['reason']), 'Missing valuation null reason')
        require(report['halted'] == state.halted, 'Stored halt differs')
        history = [dict(at=p['at'], equity=number(p['equity']), wealth=number(p['wealth']),
                        drawdown=number(p['drawdown']), reason=p['reason']) for p in state.history]
        require(report['history'] == history, 'Stored valuation history differs')
        require(report['promotion_eligible'] is False, 'Accounting cannot grant promotion')


def evidence_decision(summary):
    """Floors are necessary, never sufficient; this auditor cannot grant a stage."""
    sessions, forecasts = summary['completed_real_sessions'], summary['matured_forecasts']
    require(type(sessions) is int and sessions >= 0 and type(forecasts) is int and forecasts >= 0,
            'Invalid evidence counts')
    blockers = []
    if not summary['complete']:
        blockers.append('observation_incomplete')
    if sessions < 60:
        blockers.append('forward_sessions_below_60')
    if forecasts < 30:
        blockers.append('matured_forecasts_below_30')
    return dict(promotion_eligible=False,
        stage_decision='hold_forward_shadow' if blockers else 'requires_separate_readiness_review',
        evidence_floors=dict(sessions=60, matured_forecasts=30), evidence_blockers=blockers)


def verify_saved_trial(repo, private):
    config = load_config(repo)
    completion = read(repo / 'examples/step-11/observation-completion.json')
    directory = private / 'step-11-forward'
    manifest = read(directory / 'manifest.json')
    require(digest(manifest) == config['manifest_hash'] == completion['manifest_hash'], 'Trial manifest differs')
    check_runtime_inputs(repo, manifest)
    summary = verified_report(directory, config)
    # Step 12 audits the identified completed trial, not a later pointer alone.
    require(summary == completion['report'], 'Completion report differs from the handoff')
    report = read(directory / ('report-'+summary['report_hash']+'.json'))
    require(report['promotion_eligible'] is False and report['evidence_grade'] == 'forward-insufficient',
            'Unexpected scientific evidence grade')
    before = database_evidence(private / 'research.sqlite3')
    retained = 0
    with readonly(private / 'research.sqlite3') as connection:
        store = V2Store.__new__(V2Store)
        store.connection = connection
        require(store.v2_record(manifest['id']) == manifest, 'Stored manifest differs')
        validate_references(manifest, store.v2_record)
        performances = list(store.iter_v2(kind='performance_result'))
        for performance in performances:
            replay_performance(store, performance)
        for path in sorted(directory.glob('report-*.json')):
            previous = read(path)
            require(path.name == 'report-'+digest(previous)+'.json', 'Retained report hash differs')
            require(previous['manifest_hash'] == digest(manifest) and previous['manifest_id'] == manifest['id'],
                    'Retained report trial differs')
            for performance in previous['performance']:
                require(store.v2_record(performance['id']) == performance, 'Report and stored accounting differ')
            retained += 1
        expected = {p['portfolio_ref'] for p in manifest['participants']} | {manifest['baseline_ref']}
        require(len(report['performance']) == len(expected) and
                {p['portfolio_id'] for p in report['performance']} == expected, 'Incomplete portfolio report')
        baseline = next(p for p in report['performance'] if p['portfolio_id'] == manifest['baseline_ref'])
        comparisons = 0
        for performance in report['performance']:
            require(not performance['gaps'] and not performance['halted'], 'Latest accounting has unresolved gaps or halt')
            require(performance['equity']['value'] is not None, 'Latest valuation unavailable')
            if performance['portfolio_id'] != manifest['baseline_ref']:
                compare(performance, baseline)
                require(performance['baseline_result_hash'] == digest(baseline), 'Matched baseline hash differs')
                require(performance['broad_market_baseline'] == baseline['twr'], 'Matched baseline value differs')
                comparisons += 1
        opinions = [r for r in store.iter_v2(kind='forward_opinion') if r['manifest_ref'] == manifest['id']]
        require(len(opinions) == 4 and len({r['snapshot_hash'] for r in opinions}) == 1, 'Missing or unequal opinions')
        # Store.verify() checks each opinion, request ancestry and ordered council advice.
        require(sum(r['phase'] == 'independent' for r in opinions) == 3, 'Missing independent opinions')
        audits = [r for r in store.iter_v2(kind='forward_audit') if r['manifest_ref'] == manifest['id']]
        settlements = [json.loads(r['payload_json']) for r in audits if r['purpose'] == 'settled']
        require(len(settlements) == 1, 'Missing or duplicate settlement')
        settled = settlements[0]
        require(settled['completed_real_sessions'] == summary['completed_real_sessions'] and not settled['split_crossed'],
                'Settlement maturity differs')
        require(utc(config['review_at']) <= utc(settled['observed_at']) <= utc(report['as_of']) < utc(config['stop_at']),
                'Settlement outside frozen window')
        forecasts = [r for r in opinions if r['forecast_probability'] is not None]
        require(len(forecasts) == summary['matured_forecasts'] and
                all(utc(r['created_at']) < utc(r['forecast_resolves_at']) <= utc(settled['observed_at']) for r in forecasts),
                'Forecast maturity differs')
        works = [manifest['work_ref']] + [u['work_id'] for u in report['observation_usage']]
        require(len(set(works)) == 3, 'Missing decision or outcome workload')
        expected_queries = [manifest['query']] + [query(q) for q in queries(manifest)]
        observations, dispatches = [], []
        for work_id, expected_query in zip(works, expected_queries):
            row = connection.execute('SELECT query,body FROM market_work WHERE id=?', (work_id,)).fetchone()
            require(row is not None and json.loads(row['query']) == expected_query, 'Stored query differs')
            work = json.loads(row['body'])
            require(work['status'] == 'complete' and work['max_attempts'] == 4, 'Incomplete or changed work budget')
            rows = []
            for identifier in work['record_ids']:
                observed = connection.execute('SELECT body FROM market_observations WHERE id=?', (identifier,)).fetchone()
                require(observed is not None, 'Missing underlying observation')
                rows.append(dict(id=identifier, **json.loads(observed['body'])))
            observations.append(rows)
            sends = [r[0] for r in connection.execute('SELECT dispatched FROM market_attempts WHERE work_id=?', (work_id,))]
            # Attempt timestamps use the coordinator's durable logical clock,
            # not UTC; receipt/calendar validation supplies the wall-clock proof.
            require(all(work['queued_logical'] <= t <= work['deadline_logical'] for t in sends),
                    'Dispatch outside original logical workload window')
            dispatches.extend(sends)
        snapshot = store.v2_record(manifest['snapshot_ref'])
        require(snapshot['observations'] == observations[0], 'Sealed snapshot differs from stored download')
        bars, actions = observations[1], [accounting_action(a) for a in observations[2]]
        require(digest(bars) == settled['bars_hash'] and digest(actions) == settled['actions_hash'],
                'Settlement differs from underlying observations')
        require(len(bars) == 5 and {b['bar']['t'][:10] for b in bars} == set(FUTURE), 'Outcome sessions differ')
        require(all(b['bar']['symbol'] == 'VTI' and utc(b['bar']['t'][:10]+'T20:00:00Z') <=
                    utc(b['received_at']) <= utc(settled['observed_at']) for b in bars), 'Outcome receipt time differs')
        last = max(snapshot['observations'], key=lambda b:b['bar']['t'])['bar']['c']
        end = max(bars, key=lambda b:b['bar']['t'])['bar']['c']
        require(len(forecasts) == 1 and report['brier'] == (forecasts[0]['forecast_probability']-int(end > last))**2,
                'Forecast score differs from frozen target and received outcomes')
        attempts = [connection.execute('SELECT COUNT(*) FROM market_attempts WHERE work_id=?', (w,)).fetchone()[0]
                    for w in works]
        require(all(0 < n <= 4 for n in attempts), 'Trial attempt budget differs')
        require(not list(store.iter_v2(kind='submission_mapping')), 'Unexpected broker submissions in shadow store')
    # Account totals include earlier qualification, not only this trial.
    require(database_evidence(private / 'research.sqlite3') == before, 'Evidence changed during audit; retry when quiescent')
    original = read(private / 'step-11-operations/runs' / completion['original_observation']['run_id'] / 'receipt.json')
    require(original['status'] == 'observed' and original['exit_code'] == 0 and original['report'] == summary,
            'Original observation receipt differs')
    require(not original['previous_unfinished_runs'], 'Original observation has unfinished predecessors')
    unfinished = sum(not (p.parent / 'receipt.json').exists() for p in
                     (private / 'step-11-operations/runs').glob('*/start.json'))
    return dict(schema_version=1, scope='saved_step11_trial_readonly',
        manifest_hash=digest(manifest), report=summary, frozen_inputs_verified=True,
        database=before, expanded_ledger_replays=len(performances), retained_reports_verified=retained,
        matched_baseline_comparisons=comparisons, independent_opinions=3, council_opinions=1,
        trial_attempts=sum(attempts), trial_attempt_limit=12,
        underlying_observations_verified=True, forecast_score_reproduced=True,
        peak_trial_dispatches_per_60_logical_seconds=max(sum(t-60 < other <= t for other in dispatches) for t in dispatches),
        original_receipt_hash=digest(original), unfinished_launcher_runs=unfinished,
        provider_calls=0, model_calls=0, broker_orders=0, **evidence_decision(summary))
