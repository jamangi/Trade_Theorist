"""Audit completed specialist foundations and append the all-participant gate.

Original Step 10 artifacts remain immutable. This checks saved attribution and
chains; PDF passage verification occurs separately during the private import.
"""

import json
from pathlib import Path

from ..contracts import digest, utc, validate_bundle
from .readiness import check_saved_readiness, require

RANGES = {
    'value_rationalist': [(17,31),(32,56),(57,70),(71,92),(93,115),(116,134),(135,153),(154,182),
        (183,214),(215,240),(241,262),(263,288),(289,305),(306,320),(321,345),(346,371),(372,390),
        (391,411),(412,447),(448,466),(467,483),(484,487),(488,525),(526,550),(599,614),(615,630),(631,646),(647,660)],
    'systematic_trend_operator': [(11,24),(25,32),(33,43),(44,57),(58,69),(70,77),(78,86),(87,103),
        (104,113),(114,119),(120,135),(136,156),(157,177),(178,189),(190,197),(198,204),(205,231)],
}
MATTER = {'value_rationalist': ([1,16], [551,598]), 'systematic_trend_operator': ([1,10], [232,259])}
POLICY = 'examples/step-11/entry-policy.v2.json'
REGISTER = 'examples/step-11/readiness-register.v2.json'


def read(path):
    path = Path(path)
    value = path.read_text(encoding='utf-8')
    return json.loads(value) if path.suffix == '.json' else value


def audit_foundation(root, name, *, as_of):
    root = Path(root)
    directory = root / 'characters' / name
    folder = directory / 'checkpoints/foundation-v2'
    completion = read(folder / 'completion.json')
    bundle = read(folder / 'bundle.json')
    review = read(folder / 'reading-review.json')
    coverage = read(folder / 'coverage-map.json')
    freeze = read(folder / 'prior-freeze.json')
    budget = read(folder / 'import-budget.json')
    prior = read(directory / 'checkpoints/foundation-prior.json')
    opening = read(directory / 'checkpoints/foundation-reading-review.json')
    old_bundle = read(directory / 'checkpoints/foundation.bundle.json')
    curriculum = read(directory / 'curriculum.v1.json')
    memory = read(directory / 'memory/foundation-v2-consolidated.json')
    acquisition = read(root / 'library/catalog/specialist-foundations-2026-09-05.json')['characters'][name]
    index = validate_bundle(bundle)
    for key, value in dict(bundle=bundle, review=review, coverage=coverage, prior=prior, prior_freeze=freeze,
                           budget=budget, curriculum=curriculum, memory=memory).items():
        require(completion[key + '_hash'] == digest(value), 'Continuation fingerprint changed: ' + key)
    require(freeze['original_prior'] == prior and freeze['original_prior_hash'] == digest(prior)
            and freeze['opening_review_hash'] == digest(opening) and freeze['previous_bundle_hash'] == digest(old_bundle)
            and freeze['curriculum_hash'] == digest(curriculum), 'Continuation lost original ancestry')
    require(review['prior_freeze_hash'] == digest(freeze) and review['coverage_hash'] == digest(coverage)
            and budget['review_hash'] == digest(review), 'Review or budget is not frozen')
    require(utc(prior['frozen_at']) < utc(freeze['frozen_at']) <= utc(coverage['completed_at'])
            <= utc(review['reviewed_at']) <= utc(budget['recorded_at']) < utc(completion['completed_at']) <= utc(as_of),
            'Continuation timing is not ordered or is in the future')
    source = index[acquisition['source']['id']]
    require(source == acquisition['source'] and utc(source['checked_at']) <= utc(as_of) < utc(source['next_check_at'])
            and source['contamination'] == 'hindsight-contaminated'
            and all(source['rights'][key] == 'permitted' for key in ('reading','machine_ingestion','private_storage')),
            'Continuation source is not authorized and current')
    require(completion['character_id'] == freeze['character_id'] == prior['character_id'] == name
            and review['source_id'] == completion['source_id'] == freeze['source_id'] == prior['source_id'] == curriculum[0]['source_id'] == source['id']
            and review['source_pdf_sha256'] == completion['source_pdf_sha256'] == freeze['source_pdf_sha256'] == prior['source_pdf_sha256'] == acquisition['pdf_sha256'],
            'Continuation Character or source edition differs')
    sections = review['sections']
    require(review['scope'] == coverage['scope'] == 'full_book' and coverage['reading_status'] == 'read_pending_import'
            and coverage['pdf_pages'] == acquisition['pdf_pages'] == freeze['pdf_pages']
            and (coverage['front_matter'], coverage['back_matter']) == MATTER[name]
            and [(s['pdf_start'],s['pdf_end']) for s in sections] == RANGES[name]
            and coverage['sections'] == [{k:s[k] for k in ('number','pdf_start','pdf_end')} for s in sections]
            and [s['number'] for s in sections] == list(range(1,len(sections)+1)), 'Full-source coverage changed')
    replay_number = 1 if name == 'value_rationalist' else 2
    for section in sections:
        require(section == read(folder / f'section-{section["number"]:02d}.json'), 'Section differs from frozen review')
    replay = sections[replay_number - 1]
    require(all(replay[k] == v for k,v in dict(opening['sections'][0],number=replay_number).items())
            and replay['replay_origin']['review_hash'] == digest(opening)
            and replay['replay_origin']['reviewed_at'] == opening['reviewed_at'], 'Original opening replay was changed')
    chars = [r for r in bundle if r['record_type'] == 'character']
    require(len(chars) == 1, 'Continuation must contain one Character')
    character = chars[0]
    require(character['character_id'] == name and character['id'] == f'character:{name}-foundation-v2'
            and character['constitution_hash'] == digest(prior['constitution'])
            and character['curriculum_hash'] == digest(curriculum), 'Learning Character pin differs')
    checkpoints = sorted((r for r in bundle if r['record_type'] == 'checkpoint'), key=lambda r:r['section_index'])
    require(len(checkpoints) == len(sections) == completion['sections_completed'] == budget['max_calls'], 'Missing checkpoint')
    expected_prior = dict(constitution=prior['constitution'],memory=[],predictions=prior['predictions_about_source'],
                          original_prior_hash=digest(prior),original_frozen_at=prior['frozen_at'])
    accepted, rejected, deltas = [], [], []
    for number,(checkpoint,section) in enumerate(zip(checkpoints,sections),1):
        require(checkpoint['character_version'] == character['id'] and checkpoint['source_ids'] == [source['id']]
                and checkpoint['curriculum_position'] == 1 and checkpoint['section_index'] == number
                and checkpoint['source_hash'] == completion['material_hash'] and checkpoint['material_scope'] == 'full_book'
                and checkpoint['contamination'] == 'hindsight-contaminated'
                and checkpoint['prior_hash'] == digest(expected_prior)
                and checkpoint['prior_checkpoint_id'] == expected_prior.get('id')
                and utc(budget['recorded_at']) < utc(checkpoint['created_at']) <= utc(as_of)
                and checkpoint['reading_status'] == ('complete' if number == len(sections) else 'partial'),
                'Checkpoint chain or completion timing differs')
        require(len(checkpoint['accepted_claims']) + len(checkpoint['rejected_claims']) == len(section['claims']), 'Claim count differs')
        for offset,claim in enumerate(section['claims'],1):
            group = checkpoint['rejected_claims'] if claim['disposition'] == 'reject' else checkpoint['accepted_claims']
            claim_id = f"claim:review-{digest(source['id'])[:12]}-s{number:02d}-{offset}"
            matches = [c for c in group if c['claim_id'] == claim_id]
            require(claim['disposition'] in ('accept','qualify','reject') and len(matches) == 1
                    and matches[0]['text'] == claim['text'] and section['pdf_start'] <= claim['page'] <= section['pdf_end']
                    and 0 < len(claim['anchor'].split()) <= 25, 'Claim disposition, text or locator differs')
            citations = matches[0]['citations']
            require(len(citations) == 1 and citations[0]['source_id'] == source['id']
                    and citations[0]['locator'] == f"pdf/{source['id']}/section-{number}#page={claim['page']}", 'Citation ancestry differs')
        require(checkpoint['memory_delta'] == [section['memory_delta']]
                and checkpoint['adversarial_review'] == [section['adversarial_review']]
                and section.get('theory') is None and section.get('test') is None, 'Review was changed or untested theory added')
        accepted.extend(checkpoint['accepted_claims'])
        rejected.extend(checkpoint['rejected_claims'])
        require(checkpoint['consolidated_memory'] == accepted, 'Consolidation drift')
        deltas.append(dict(checkpoint_id=checkpoint['id'],assimilation=[section['assimilation']],
            adversarial_review=checkpoint['adversarial_review'],memory_delta=checkpoint['memory_delta'],theory_id=None))
        expected_prior = checkpoint
    require(memory == dict(character_version=character['id'],checkpoint_id=checkpoints[-1]['id'],claims=accepted,rejected_claims=rejected,deltas=deltas)
            and completion['final_checkpoint_id'] == checkpoints[-1]['id'] and completion['completed_at'] == checkpoints[-1]['created_at']
            and completion['status'] == 'foundation_complete' and completion['books_read'] == 1
            and completion['curriculum_complete'] is False and completion['unread_positions'] == list(range(2,len(curriculum)+1))
            and completion['contamination'] == 'hindsight-contaminated' and completion['evaluation_status'] == 'not_run',
            'Published completion or memory overstates evidence')
    require(not any(r['record_type'] in ('theory','registration') for r in bundle), 'Unreviewed theory present')
    return dict(character=character,checkpoint=checkpoints[-1],source=source,accepted=len(accepted),rejected=len(rejected),
                sections=len(sections),completion_hash=digest(completion),bundle_hash=digest(bundle))


def audit_readiness_v2(root):
    root = Path(root)
    previous = check_saved_readiness(root)
    policy = read(root / POLICY)
    require(policy['predecessor_hash'] == digest(previous) and policy['policy_id'] == 'pilot-readiness:vti-daily-v2'
            and policy['opportunity_set'] == ['VTI'] and policy['data_controls_only'] == ['QQQ','SPY'], 'Entry policy ancestry differs')
    require(policy['participants'] == read(root / 'examples/step-10/entry-policy.v1.json')['participants'], 'Pilot roles or roster changed')
    participants = [previous['participants'][0]]
    versions = {}
    for entry in policy['participants'][1:]:
        name = entry['character_id']
        evidence = audit_foundation(root,name,as_of=policy['recorded_at'])
        character,checkpoint,source = (evidence[k] for k in ('character','checkpoint','source'))
        constitution_path = f'characters/{name}/constitution.foundation-v2.md'
        constitution = read(root / constitution_path)
        scope = f'learning-session:{name}-pilot-foundation-v2'
        version = dict(character,id=f'character:{name}-pilot-foundation-v2',version='pilot-foundation-v2',
            experiment_id=scope,created_at=policy['recorded_at'],constitution_hash=digest(constitution),readiness='ready')
        session = dict(schema_version=1,record_type='learning_session',id=scope,experiment_id=scope,created_at=policy['recorded_at'],
            contamination='hindsight-contaminated',mode='learning',character_versions=[version['id']],source_ids=[source['id']],
            authorization=policy['authority'],provenance='Completed foundation reconciliation. Exact immutable learning ancestry is pinned in ' + REGISTER)
        path = f'characters/{name}/versions/pilot-foundation-v2.bundle.json'
        versions[path] = [source,session,version]
        validate_bundle(versions[path])
        participants.append(dict(character_id=name,eligible=True,decision='ready',character_version=version['id'],version_hash=digest(version),
            learning_character_version=character['id'],learning_character_hash=digest(character),knowledge_checkpoint=checkpoint['id'],knowledge_hash=digest(checkpoint),
            reviewed_constitution=constitution_path,reviewed_constitution_hash=digest(constitution),source_id=source['id'],
            source_pdf_sha256=read(root / f'characters/{name}/checkpoints/foundation-v2/completion.json')['source_pdf_sha256'],
            material_scope='full_book',sections_reviewed=evidence['sections'],books_completed=1,curriculum_complete=False,unread_positions=[2,3,4],
            role=entry['role'],limitations=entry['excluded_claims'],contamination='hindsight-contaminated',evaluation_status='not_run',
            accepted_claims=evidence['accepted'],rejected_claims=evidence['rejected'],completion_hash=evidence['completion_hash'],learning_bundle_hash=evidence['bundle_hash'],blockers=[]))
    result = dict(schema_version=1,policy_id=policy['policy_id'],policy_hash=digest(policy),recorded_at=policy['recorded_at'],
        predecessor_hash=digest(previous),participants=participants,participant_gate='passed',
        eligible_character_versions=[p['character_version'] for p in participants],
        version_bundles={p:digest(b) for p,b in versions.items()},
        step_11_status='requires_real_integration_and_prospective_evidence',
        verification_limit='Saved chain and attribution audit. Exact PDF anchors separately verified in private imports; no independent authoring replication or performance validation.')
    result['content_hash'] = digest(result)
    return result,versions


def check_saved_readiness_v2(root):
    register,versions = audit_readiness_v2(root)
    require(read(Path(root) / REGISTER) == register, 'Saved v2 readiness changed')
    for path,bundle in versions.items():
        require(read(Path(root) / path) == bundle, 'Saved eligible version changed')
    return register
