"""Import one bounded specialist foundation review without exporting book text."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from trade_theorist.contracts import ContractError, digest, validate_bundle
from trade_theorist.learn import BoundedModel, Learner
from trade_theorist.learn.reviewed import ReviewedTranscriptProvider, material_from_pdf, write_once
from trade_theorist.storage import Store


ROOT = Path(__file__).resolve().parents[1]
ACQUISITION = ROOT / "library/catalog/specialist-foundations-2026-09-05.json"
FILES = {
    "value_rationalist": "The_intelligent_investor_-_Benjamin_Graham.pdf",
    "systematic_trend_operator": "Way_of_the_Turtle_-_Curtis_Faith.pdf",
}
MODEL = "recorded-codex-source-review-v1"
PROMPT = "learning-section-only-v2"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def import_foundation(character_id, pdf, data_root, export_dir=None):
    character_dir = Path(export_dir).resolve() if export_dir else ROOT / "characters" / character_id
    acquisition = read(ACQUISITION)
    details = acquisition["characters"][character_id]
    source = details["source"]
    review = read(character_dir / "checkpoints/foundation-reading-review.json")
    prior = read(character_dir / "checkpoints/foundation-prior.json")
    curriculum = read(character_dir / "curriculum.v1.json")
    if prior["source_id"] != source["id"] or prior["source_pdf_sha256"] != details["pdf_sha256"] or review["source_pdf_sha256"] != details["pdf_sha256"]:
        raise ContractError("Source, prior and review fingerprints differ")
    constitution = prior["constitution"]
    material = material_from_pdf(
        pdf, review, expected_pages=details["pdf_pages"],
        expected_ranges=[tuple(value) for value in details["substantive_ranges"]],
        scope=review["scope"],
    )
    scope = f"learning-session:{character_id}-foundation-v1"
    character_version = f"character:{character_id}-foundation-v1"
    base = dict(
        schema_version=1, experiment_id=scope,
        created_at=review["reviewed_at"], contamination="hindsight-contaminated",
    )
    character = dict(
        base, id=character_version, record_type="character",
        character_id=character_id, version="foundation-v1",
        constitution_hash=digest(constitution), curriculum_hash=digest(curriculum),
        readiness="partial", foundation_source_id=source["id"],
    )
    learning_session = dict(
        base, id=scope, record_type="learning_session", mode="learning",
        character_versions=[character_version], source_ids=[source["id"]],
        authorization=acquisition["authorization"], provenance=acquisition["provenance"],
    )
    provider = ReviewedTranscriptProvider(review, material, constitution, curriculum)
    with Store(data_root) as store:
        store.put_records([source, character, learning_session])
        model = BoundedModel(
            store, scope, provider,
            budget_id=f"budget:{character_id}-foundation-review-v1",
            model_id=MODEL, prompt_version=PROMPT, max_calls=len(material["sections"]),
            max_tokens=250000, max_output_tokens=6000,
        )
        learner = Learner(store, model)
        initial_prior = dict(
            constitution=constitution, memory=[], predictions=prior["predictions_about_source"],
            original_prior_hash=digest(prior), original_frozen_at=prior["frozen_at"],
        )
        session = learner.freeze(
            character_version=character_version, curriculum=curriculum,
            constitution=constitution, material=material, source_id=source["id"],
            position=1, initial_prior=initial_prior,
        )
        checkpoint = None
        for number in range(1, len(material["sections"]) + 1):
            checkpoint = learner.step(session, section_index=number)
        if checkpoint is None or checkpoint["reading_status"] != "partial":
            raise ContractError("Bounded specialist review must remain partial")
        records = [record for record in store.records() if record["experiment_id"] == scope or record["id"] == source["id"]]
        commit = subprocess.run(
            ["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        run = dict(
            base, id=f"run:{character_id}-foundation-v1", record_type="run_manifest",
            created_at=checkpoint["created_at"], mode="learning", code_commit=commit,
            policy_version="not_applicable:learning_only",
            source_revisions=[digest(material), details["pdf_sha256"]],
            character_versions=[character_version], model_id=MODEL, prompt_version=PROMPT,
            sampling=dict(temperature=0, seed=0), market_cutoff=review["reviewed_at"],
            knowledge_cutoff=review["reviewed_at"],
            input_hash=digest([material, prior, curriculum, review]),
            output_hash=digest(checkpoint),
            phase_status=dict(prepare="complete", execute="complete", export="pending"),
            # This is the durable import count, not the number of new calls made
            # during a replay that may reuse already-recorded responses.
            usage=dict(input_tokens=0, output_tokens=0, calls=len(material["sections"]), cost_usd="0.00"),
            failure=None, resume_from=None, parent_run_id=None,
        )
        existing_run = next((record for record in records if record["id"] == run["id"]), None)
        if existing_run is None:
            store.put_records([run])
            records.append(run)
        elif existing_run != run:
            raise ContractError("Existing specialist run differs from the reproducible import")
        records.sort(key=lambda value: value["id"])
        validate_bundle(records)
        write_once(character_dir / "checkpoints/foundation.bundle.json", records)
        write_once(character_dir / "memory/foundation-consolidated.json", {
            "character_version": character_version,
            "checkpoint_id": checkpoint["id"],
            "claims": checkpoint["consolidated_memory"],
            "rejected_claims": checkpoint["rejected_claims"],
            "memory_delta": checkpoint["memory_delta"],
        })
        status = {
            "schema_version": 1,
            "character_id": character_id,
            "status": "partial_foundation",
            "real_readiness": False,
            "recommendation_readiness": "fixture_only",
            "curriculum_complete": False,
            "books_read": 0,
            "partial_books": 1,
            "source_id": source["id"],
            "source_pdf_sha256": details["pdf_sha256"],
            "sections_completed": len(material["sections"]),
            "final_checkpoint_id": checkpoint["id"],
            "bundle_hash": digest(records),
            "review_hash": digest(review),
            "prior_hash": digest(prior),
            "curriculum_hash": digest(curriculum),
            "contamination": "hindsight-contaminated",
            "evaluation_status": "not_run",
            "blocker": source["blocker"],
        }
        write_once(character_dir / "checkpoints/foundation-status.json", status)
        store.append(
            "export:" + digest(scope), scope, "learning.public_export",
            {"bundle_hash": digest(records), "status_hash": digest(status)},
        )
        return {"status": status["status"], "new_imports": provider.calls, "checkpoint": checkpoint["id"], "integrity": store.verify()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--character", required=True, choices=sorted(FILES))
    parser.add_argument("--books-root", default=os.environ.get("TRADE_THEORIST_BOOKS_ROOT"))
    parser.add_argument("--pdf")
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--export-dir")
    args = parser.parse_args()
    pdf = args.pdf or (str(Path(args.books_root) / FILES[args.character]) if args.books_root else None)
    if not pdf:
        raise SystemExit("Pass --pdf or set TRADE_THEORIST_BOOKS_ROOT; no file is copied or downloaded.")
    try:
        print(json.dumps(import_foundation(args.character, pdf, args.data_root, args.export_dir), indent=2))
    except (ContractError, ValueError, OSError):
        raise SystemExit("Specialist review import failed. Check source identity, citations and the external private data directory; no private text is printed.")
