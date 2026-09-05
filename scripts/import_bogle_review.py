"""Verify the owner's PDF and import the attributed, ordered Codex review locally.

Run from the repository root. Requires the optional `learning` dependency.
The public export contains original analysis and citation hashes, not book text.
"""

import argparse
import json
from pathlib import Path
import subprocess

from trade_theorist.contracts import ContractError, digest, validate_bundle
from trade_theorist.learn import BoundedModel, Learner
from trade_theorist.learn.reviewed import ReviewedTranscriptProvider, material_from_pdf, write_once
from trade_theorist.storage import Store


ROOT = Path(__file__).resolve().parents[1]
CHAR_DIR = ROOT / "characters/index_steward"
SCOPE = "learning-session:index-steward-bogle-2017-v1"
CHAR = "character:index-steward-bogle-2017-v1"
MODEL = "recorded-codex-source-review-v1"
PROMPT = "learning-section-only-v2"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def import_review(pdf, data_root, *, stop_after=None, export_dir=None):
    destination = Path(export_dir).resolve() if export_dir else CHAR_DIR
    acquisition = read(ROOT / "library/catalog/bogle-2017-acquisition.json")
    review = read(CHAR_DIR / "checkpoints/bogle-2017-reading-review.json")
    prior = read(CHAR_DIR / "checkpoints/bogle-2017-prior.json")
    curriculum = read(CHAR_DIR / "curriculum.v1.json")
    if digest(review) != acquisition["review_hash"] or digest(prior) != acquisition["prior_hash"]:
        raise ContractError("Attributed review or original prior changed")
    constitution = prior["constitution"]
    if digest(constitution) != prior["constitution_hash"] or prior["source_pdf_sha256"] != review["source_pdf_sha256"]:
        raise ContractError("Prior does not match the reviewed source and constitution")
    coverage = acquisition["coverage"]
    material = material_from_pdf(pdf, review, expected_pages=coverage["pdf_pages"], expected_ranges=[tuple(r) for r in coverage["substantive_ranges"]])
    provider = ReviewedTranscriptProvider(review, material, constitution, curriculum)
    source = acquisition["source"]
    base = dict(schema_version=1, experiment_id=SCOPE, created_at=acquisition["review_completed_at"], contamination="hindsight-contaminated")
    character = dict(base, id=CHAR, record_type="character", character_id="index_steward", version="bogle-2017-v1", constitution_hash=digest(constitution), curriculum_hash=digest(curriculum), readiness="partial", foundation_source_id=source["id"])
    session_record = dict(base, id=SCOPE, record_type="learning_session", mode="learning", character_versions=[CHAR], source_ids=[source["id"]], authorization=acquisition["authorization"], provenance=acquisition["provenance"])
    with Store(data_root) as store:
        store.put_records([source, character, session_record])
        inputs = dict(material_hash=digest(material), review_hash=digest(review), prior_hash=digest(prior), curriculum_hash=digest(curriculum))
        store.append("inputs:" + digest(SCOPE), SCOPE, "learning.review_inputs", inputs)
        code = ROOT / "src/trade_theorist"
        tree = {p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8") for p in sorted(code.rglob("*.py"))}
        tree["scripts/import_bogle_review.py"] = Path(__file__).read_text(encoding="utf-8")
        commit = subprocess.run(["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        provenance = dict(code_commit=commit, code_tree_hash=digest(tree), **inputs)
        store.append("provenance:" + digest(provenance), SCOPE, "run.provenance", provenance)
        original_provenance = store.events(SCOPE, "run.provenance")[0]["payload"]
        model = BoundedModel(store, SCOPE, provider, budget_id="budget:bogle-2017-review-import-v1", model_id=MODEL, prompt_version=PROMPT, max_calls=21, max_tokens=2000000, max_output_tokens=6000)
        learner = Learner(store, model)
        initial_prior = dict(constitution=constitution, memory=[], predictions=prior["predictions_about_source"], original_prior_hash=digest(prior), original_frozen_at=prior["frozen_at"])
        session = learner.freeze(character_version=CHAR, curriculum=curriculum, constitution=constitution, material=material, source_id=source["id"], position=1, initial_prior=initial_prior)
        count = len(material["sections"])
        if stop_after is not None and not 1 <= stop_after <= count:
            raise ContractError("Invalid stopping section")
        for number in range(1, (stop_after or count) + 1):
            checkpoint = learner.step(session, section_index=number)
        integrity = store.verify()
        if stop_after is not None and stop_after < count:
            return dict(status="partial", sections=checkpoint["section_index"], new_imports=provider.calls, integrity=integrity)
        records = [r for r in store.records() if r["experiment_id"] == SCOPE or r["id"] == source["id"]]
        checkpoints = sorted((r for r in records if r["record_type"] == "checkpoint"), key=lambda r: r["section_index"])
        if len(checkpoints) != count or checkpoints[-1]["reading_status"] != "complete":
            raise ContractError("Cannot export incomplete foundation as complete")
        final = checkpoints[-1]
        run_id = "run:index-steward-bogle-2017-v1"
        if not any(r["id"] == run_id for r in records):
            # Usage describes local transcript import only. Original inference usage
            # and sampling were not exposed by the Codex session (see acquisition).
            run = dict(base, id=run_id, record_type="run_manifest", created_at=final["created_at"], mode="learning", code_commit=original_provenance["code_commit"], policy_version="not_applicable:learning_only", source_revisions=[digest(material), review["source_pdf_sha256"]], character_versions=[CHAR], model_id=MODEL, prompt_version=PROMPT, sampling=dict(temperature=0, seed=0), market_cutoff=acquisition["review_completed_at"], knowledge_cutoff=acquisition["review_completed_at"], input_hash=digest(inputs), output_hash=digest(checkpoints), phase_status=dict(prepare="complete", execute="complete", export="pending"), usage=dict(input_tokens=0, output_tokens=0, calls=count, cost_usd="0.00"), failure=None, resume_from=None, parent_run_id=None)
            store.put_records([run])
            records.append(run)
        records.sort(key=lambda r: r["id"])
        validate_bundle(records)
        # No event/request/private material export. Source.private_locator is only
        # the repository-relative ignored filename, never a user's absolute path.
        write_once(destination / "checkpoints/bogle-2017-prior.json", prior)
        write_once(destination / "checkpoints/bogle-2017-reading-review.json", review)
        write_once(destination / "curriculum.v1.json", curriculum)
        bundle_path = destination / "checkpoints/bogle-2017.bundle.json"
        write_once(bundle_path, records)
        deltas = [e["payload"] for e in store.events(SCOPE, "learning.delta")]
        public_deltas = [{k: d[k] for k in ("checkpoint_id", "assimilation", "adversarial_review", "memory_delta", "theory_id")} for d in deltas]
        write_once(destination / "memory/bogle-2017-deltas.json", public_deltas)
        write_once(destination / "memory/bogle-2017-consolidated.json", dict(character_version=CHAR, checkpoint_id=final["id"], claims=final["consolidated_memory"], rejected_claims=[c for r in checkpoints for c in r["rejected_claims"]], deltas=public_deltas))
        write_once(destination / "theories/bogle-2017.json", [r for r in records if r["record_type"] in ("theory", "registration")])
        completion = dict(schema_version=1, character_id="index_steward", status="foundation_complete", readiness="ready_for_foundation_research", curriculum_complete=False, books_read=1, unread_positions=[2, 3, 4], source_id=source["id"], source_pdf_sha256=review["source_pdf_sha256"], sections_completed=count, final_checkpoint_id=final["id"], completed_at=final["created_at"], bundle_hash=digest(records), review_hash=digest(review), prior_hash=digest(prior), curriculum_hash=digest(curriculum), executing_code=original_provenance, contamination="hindsight-contaminated", evaluation_status="not_run", usage_scope="Local import only; original Codex generation tokens, cost, exact snapshot and sampling unavailable.")
        write_once(destination / "checkpoints/bogle-2017-completion.json", completion)
        store.append("export:" + digest(SCOPE), SCOPE, "learning.public_export", {"bundle_hash": digest(records), "completion_hash": digest(completion)})
        return dict(status=completion["status"], books_read=1, sections=count, new_imports=provider.calls, integrity=store.verify())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", default=str(ROOT / "library/sources/private/bogle-2017-common-sense-investing.pdf"))
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--stop-after", type=int, help="Import through this section; resume using the same private directory")
    parser.add_argument("--export-dir", help="New public-artifact directory when replaying into a new private database")
    args = parser.parse_args()
    try:
        print(json.dumps(import_review(args.pdf, args.data_root, stop_after=args.stop_after, export_dir=args.export_dir), indent=2))
    except (ContractError, ValueError, OSError):
        raise SystemExit("Review import failed. Check the source hash, review version, citations and external private data directory; no private text is printed.")
