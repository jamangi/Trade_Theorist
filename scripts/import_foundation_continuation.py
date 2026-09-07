"""Import the two completed, attributed foundations into new immutable sessions."""

import argparse
import json
from pathlib import Path
import subprocess

from trade_theorist.contracts import ContractError, digest, validate_bundle
from trade_theorist.learn import BoundedModel, Learner
from trade_theorist.learn.reviewed import ReviewedTranscriptProvider, material_from_pdf, write_once
from trade_theorist.storage import Store

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('value_rationalist', 'systematic_trend_operator')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def import_review(name, pdf, data_root, *, export_dir=None, stop_after=None):
    character_dir = ROOT / 'characters' / name
    inputs_dir = character_dir / 'checkpoints/foundation-v2'
    destination = Path(export_dir) if export_dir else character_dir
    review = read(inputs_dir / 'reading-review.json')
    coverage = read(inputs_dir / 'coverage-map.json')
    freeze = read(inputs_dir / 'prior-freeze.json')
    prior = read(character_dir / 'checkpoints/foundation-prior.json')
    old_review = read(character_dir / 'checkpoints/foundation-reading-review.json')
    old_bundle = read(character_dir / 'checkpoints/foundation.bundle.json')
    curriculum = read(character_dir / 'curriculum.v1.json')
    budget = read(inputs_dir / 'import-budget.json')
    acquired = read(ROOT / 'library/catalog/specialist-foundations-2026-09-05.json')['characters'][name]
    if (freeze['original_prior'] != prior or freeze['original_prior_hash'] != digest(prior)
            or freeze['opening_review_hash'] != digest(old_review) or freeze['previous_bundle_hash'] != digest(old_bundle)
            or freeze['curriculum_hash'] != digest(curriculum) or freeze['character_id'] != name
            or review['prior_freeze_hash'] != digest(freeze) or review['coverage_hash'] != digest(coverage)
            or budget['review_hash'] != digest(review) or budget['max_calls'] != len(review['sections'])
            or review['source_id'] != acquired['source']['id'] or review['source_pdf_sha256'] != acquired['pdf_sha256']
            or coverage['reading_status'] != 'read_pending_import'):
        raise ContractError('Continuation inputs differ from frozen source, prior, coverage or budget')
    opening_number = 1 if name == 'value_rationalist' else 2
    opening = review['sections'][opening_number - 1]
    if any(opening[k] != v for k, v in dict(old_review['sections'][0], number=opening_number).items()):
        raise ContractError('Opening replay differs from original attributed reading')
    material = material_from_pdf(pdf, review, expected_pages=acquired['pdf_pages'],
        expected_ranges=[(s['pdf_start'], s['pdf_end']) for s in coverage['sections']])
    count = len(material['sections'])
    if stop_after is not None and not 1 <= stop_after <= count:
        raise ContractError('Invalid stopping section')
    constitution = prior['constitution']
    scope = f'learning-session:{name}-foundation-v2'
    version = f'character:{name}-foundation-v2'
    source = acquired['source']  # Preserve the original acquisition record, including its historical partial status.
    base = dict(schema_version=1, experiment_id=scope, created_at=review['reviewed_at'], contamination='hindsight-contaminated')
    character = dict(base, id=version, record_type='character', character_id=name, version='foundation-v2',
        constitution_hash=digest(constitution), curriculum_hash=digest(curriculum), readiness='partial', foundation_source_id=source['id'])
    learning = dict(base, id=scope, record_type='learning_session', mode='learning', character_versions=[version],
        source_ids=[source['id']], authorization=freeze['authority'], provenance=review['provenance'])
    inputs = dict(review_hash=digest(review), prior_hash=digest(prior), prior_freeze_hash=digest(freeze),
        material_hash=digest(material), coverage_hash=digest(coverage), curriculum_hash=digest(curriculum), budget_hash=digest(budget))
    provider = ReviewedTranscriptProvider(review, material, constitution, curriculum)
    with Store(data_root) as store:
        store.put_records([source, character, learning])
        store.append('inputs:' + digest(scope), scope, 'learning.review_inputs', inputs)
        provenance_events = store.events(scope, 'run.provenance')
        if not provenance_events:
            commit = subprocess.run(['git', '-c', f'safe.directory={ROOT.as_posix()}', 'rev-parse', 'HEAD'],
                                    cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
            tree = {p.relative_to(ROOT).as_posix(): p.read_text(encoding='utf-8')
                    for p in sorted((ROOT / 'src/trade_theorist').rglob('*.py'))}
            tree['scripts/import_foundation_continuation.py'] = Path(__file__).read_text(encoding='utf-8')
            store.append('provenance:' + digest(scope), scope, 'run.provenance',
                         dict(code_commit=commit, code_tree_hash=digest(tree), **inputs))
        provenance = store.events(scope, 'run.provenance')[0]['payload']
        model = BoundedModel(store, scope, provider, budget_id=f'budget:{name}-foundation-v2',
            **{k: budget[k] for k in ('model_id', 'prompt_version', 'max_calls', 'max_tokens', 'max_output_tokens')})
        learner = Learner(store, model)
        initial = dict(constitution=constitution, memory=[], predictions=prior['predictions_about_source'],
                       original_prior_hash=digest(prior), original_frozen_at=prior['frozen_at'])
        session = learner.freeze(character_version=version, curriculum=curriculum, constitution=constitution,
            material=material, source_id=source['id'], position=1, initial_prior=initial)
        for number in range(1, (stop_after or count) + 1):
            checkpoint = learner.step(session, section_index=number)
        if stop_after is not None and stop_after < count:
            return dict(status='partial', sections=checkpoint['section_index'], new_imports=provider.calls, integrity=store.verify())
        records = [r for r in store.records() if r['experiment_id'] == scope or r['id'] == source['id']]
        checkpoints = sorted((r for r in records if r['record_type'] == 'checkpoint'), key=lambda r: r['section_index'])
        if len(checkpoints) != count or checkpoint['reading_status'] != 'complete':
            raise ContractError('Incomplete continuation cannot export completion')
        run_id = f'run:{name}-foundation-v2'
        if not any(r['id'] == run_id for r in records):
            run = dict(base, id=run_id, record_type='run_manifest', created_at=checkpoint['created_at'], mode='learning',
                code_commit=provenance['code_commit'], policy_version='not_applicable:learning_only',
                source_revisions=[digest(material), acquired['pdf_sha256']], character_versions=[version],
                model_id=budget['model_id'], prompt_version=budget['prompt_version'], sampling=dict(temperature=0, seed=0),
                market_cutoff=review['reviewed_at'], knowledge_cutoff=review['reviewed_at'], input_hash=digest(inputs),
                output_hash=digest(checkpoints), phase_status=dict(prepare='complete', execute='complete', export='pending'),
                usage=dict(input_tokens=0, output_tokens=0, calls=count, cost_usd='0.00'), failure=None, resume_from=None, parent_run_id=None)
            store.put_records([run])
            records.append(run)
        records.sort(key=lambda r: r['id'])
        validate_bundle(records)
        deltas = [{k: e['payload'][k] for k in ('checkpoint_id', 'assimilation', 'adversarial_review', 'memory_delta', 'theory_id')}
                  for e in store.events(scope, 'learning.delta')]
        memory = dict(character_version=version, checkpoint_id=checkpoint['id'], claims=checkpoint['consolidated_memory'],
                      rejected_claims=[c for cp in checkpoints for c in cp['rejected_claims']], deltas=deltas)
        completion = dict(schema_version=1, character_id=name, status='foundation_complete', books_read=1,
            curriculum_complete=False, unread_positions=list(range(2, len(curriculum) + 1)),
            source_id=source['id'], source_pdf_sha256=acquired['pdf_sha256'], sections_completed=count,
            completed_at=checkpoint['created_at'], final_checkpoint_id=checkpoint['id'], bundle_hash=digest(records),
            memory_hash=digest(memory), **inputs, executing_code=provenance,
            contamination='hindsight-contaminated', evaluation_status='not_run', usage_scope=review['authoring_usage'],
            acquisition_note='Original source record retains its historical partial-ingestion state. This new completion records full reading; old records are unchanged.')
        write_once(destination / 'checkpoints/foundation-v2/bundle.json', records)
        write_once(destination / 'memory/foundation-v2-consolidated.json', memory)
        write_once(destination / 'checkpoints/foundation-v2/completion.json', completion)
        store.append('export:' + digest(scope), scope, 'learning.public_export',
                     dict(bundle_hash=digest(records), completion_hash=digest(completion)))
        return dict(status='foundation_complete', sections=count, books_read=1, new_imports=provider.calls, integrity=store.verify())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--character', choices=NAMES, required=True)
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--data-root', required=True)
    parser.add_argument('--export-dir')
    parser.add_argument('--stop-after', type=int)
    args = parser.parse_args()
    try:
        print(json.dumps(import_review(args.character, args.pdf, args.data_root,
            export_dir=args.export_dir, stop_after=args.stop_after), indent=2))
    except (ContractError, ValueError, OSError):
        raise SystemExit('Continuation import failed; check frozen inputs, PDF identity and private store. No source text is printed.')
