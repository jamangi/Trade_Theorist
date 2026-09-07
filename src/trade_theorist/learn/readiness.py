"""Reproduce the bounded Step 10 review from saved, independently learned artifacts.

This is a versioned evidence audit, not a runtime forward admission adapter. Never
relabel old checkpoints or transplant them into a new Character/experiment.
"""

import json
from pathlib import Path

from ..contracts import ContractError, digest, utc, validate_bundle
from .reviewed import foundation_status, specialist_status


PARTICIPANTS = ("index_steward", "value_rationalist", "systematic_trend_operator")
POLICY_PATH = "examples/step-10/entry-policy.v1.json"
REGISTER_PATH = "examples/step-10/readiness-register.v1.json"
VERSION_PATH = "characters/index_steward/versions/pilot-foundation-v1.bundle.json"


def require(condition, message):
    if not condition:
        raise ContractError(message)


def audit_readiness(root):
    """Return reproducible register and new Index records without writing anything.

    Hashes use canonical JSON; Markdown is decoded with normalized newlines so
    checkout line endings do not change the Character's constitution identity.
    Missing/corrupt evidence raises rather than manufacturing an unready finding.
    """
    root = Path(root)
    evidence = {}

    def read(relative):
        path = root / relative
        value = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            value = json.loads(value)
        evidence[relative] = digest(value)
        return value

    policy = read(POLICY_PATH)
    require(policy["policy_id"] == "pilot-readiness:vti-daily-v1"
            and policy["opportunity_set"] == ["VTI"]
            and [p["character_id"] for p in policy["participants"]] == list(PARTICIPANTS),
            "Step 10 requires its exact policy, opportunity and all three participants")
    decisions, version_bundle = [], None
    for entry in policy["participants"]:
        name = entry["character_id"]
        prefix = f"characters/{name}"
        stem = "bogle-2017" if name == "index_steward" else "foundation"
        status_name = "completion" if name == "index_steward" else "status"
        saved = read(f"{prefix}/checkpoints/{stem}-{status_name}.json")
        bundle = read(f"{prefix}/checkpoints/{stem}.bundle.json")
        prior = read(f"{prefix}/checkpoints/{stem}-prior.json")
        review = read(f"{prefix}/checkpoints/{stem}-reading-review.json")
        curriculum = read(f"{prefix}/curriculum.v1.json")
        memory = read(f"{prefix}/memory/{stem}-consolidated.json")
        constitution_path = f"{prefix}/constitution" + (".v1.md" if name == "index_steward" else ".md")
        constitution = read(constitution_path)
        index = validate_bundle(bundle)
        if name == "index_steward":
            foundation_status(root / prefix, entry["source_id"])
            acquisition = read("library/catalog/bogle-2017-acquisition.json")
            acquired_hash = acquisition["source_pdf_sha256"]
            expected_ranges = acquisition["coverage"]["substantive_ranges"]
        else:
            specialist_status(root / prefix)
            acquisition = read("library/catalog/specialist-foundations-2026-09-05.json")["characters"][name]
            acquired_hash = acquisition["pdf_sha256"]
            expected_ranges = acquisition["substantive_ranges"]
        characters = [r for r in bundle if r["record_type"] == "character"]
        require(len(characters) == 1, "Learning bundle must identify one independent Character")
        character = characters[0]
        source = index[entry["source_id"]]
        checkpoints = sorted((r for r in bundle if r["record_type"] == "checkpoint"), key=lambda r: r["section_index"])
        require(character["character_id"] == name == prior["character_id"] == saved["character_id"]
                and character["foundation_source_id"] == entry["source_id"] == curriculum[0]["source_id"]
                and character["constitution_hash"] == digest(prior["constitution"])
                and character["curriculum_hash"] == digest(curriculum), "Character/prior/curriculum identity mismatch")
        require(source == acquisition["source"]
                and source["contamination"] == "hindsight-contaminated"
                and utc(source["checked_at"]) <= utc(policy["recorded_at"]) < utc(source["next_check_at"])
                and all(source["rights"][key] == "permitted" for key in ("reading", "machine_ingestion", "private_storage")),
                "Nonfixture authorized learning source required")
        require(prior["source_id"] == review["source_id"] == saved["source_id"] == source["id"]
                and acquired_hash == prior["source_pdf_sha256"] == review["source_pdf_sha256"] == saved["source_pdf_sha256"],
                "Source edition fingerprints disagree")
        sections = review["sections"]
        require([[s["pdf_start"], s["pdf_end"]] for s in sections] == expected_ranges
                and len(checkpoints) == len(sections) == saved["sections_completed"]
                and [s["number"] for s in sections] == list(range(1, len(sections) + 1)),
                "Reviewed coverage differs from saved acquisition or checkpoint count")
        expected_prior = dict(constitution=prior["constitution"], memory=[],
                              predictions=prior["predictions_about_source"],
                              original_prior_hash=digest(prior), original_frozen_at=prior["frozen_at"])
        accepted, rejected = [], []
        for number, (checkpoint, section) in enumerate(zip(checkpoints, sections), 1):
            require(checkpoint["character_version"] == character["id"]
                    and checkpoint["contamination"] == "hindsight-contaminated"
                    and checkpoint["source_ids"] == [source["id"]]
                    and checkpoint["curriculum_position"] == 1 and checkpoint["section_index"] == number
                    and utc(prior["frozen_at"]) < utc(checkpoint["created_at"]) <= utc(policy["recorded_at"])
                    and checkpoint["prior_hash"] == digest(expected_prior)
                    and checkpoint["prior_checkpoint_id"] == (None if number == 1 else expected_prior["id"]),
                    "Learning chain does not descend from the exact independent frozen prior")
            require(checkpoint["source_hash"] == checkpoints[0]["source_hash"]
                    and checkpoint["material_scope"] == checkpoints[0]["material_scope"]
                    and (number == len(checkpoints) or checkpoint["reading_status"] == "partial"),
                    "Learning material changed or completed before reviewed coverage ended")
            claims = checkpoint["accepted_claims"] + checkpoint["rejected_claims"]
            require(len(claims) == len(section["claims"]), "Reviewed claims omitted or invented")
            for offset, claim in enumerate(section["claims"], 1):
                claim_id = f"claim:review-{digest(source['id'])[:12]}-s{number:02d}-{offset}"
                group = checkpoint["rejected_claims"] if claim["disposition"] == "reject" else checkpoint["accepted_claims"]
                matches = [c for c in group if c["claim_id"] == claim_id]
                require(claim["disposition"] in ("accept", "qualify", "reject")
                        and section["pdf_start"] <= claim["page"] <= section["pdf_end"]
                        and len(matches) == 1 and matches[0]["text"] == claim["text"],
                        "Claim disposition, text or page differs from the attributed review")
                citations = matches[0]["citations"]
                require(len(citations) == 1 and citations[0]["source_id"] == source["id"]
                        and citations[0]["locator"] == f"pdf/{source['id']}/section-{number}#page={claim['page']}",
                        "Claim lost its exact source/page citation")
            require(checkpoint["memory_delta"] == [section["memory_delta"]]
                    and checkpoint["adversarial_review"] == [section["adversarial_review"]],
                    "Checkpoint differs from reviewed memory or objections")
            accepted += checkpoint["accepted_claims"]
            rejected += checkpoint["rejected_claims"]
            require(checkpoint["consolidated_memory"] == accepted, "Consolidated learning memory drift")
            expected_prior = checkpoint
        final = checkpoints[-1]
        require(saved["final_checkpoint_id"] == final["id"] == memory["checkpoint_id"]
                and memory["character_version"] == character["id"]
                and memory["claims"] == accepted and memory["rejected_claims"] == rejected,
                "Published memory differs from its final checkpoint")
        theories = [r for r in bundle if r["record_type"] == "theory"]
        registrations = [r for r in bundle if r["record_type"] == "registration"]
        if name == "index_steward":
            deltas = read(f"{prefix}/memory/{stem}-deltas.json")
            require(deltas == memory["deltas"] and len(deltas) == len(checkpoints), "Memory deltas differ")
            for delta, checkpoint, section in zip(deltas, checkpoints, sections):
                require(delta["checkpoint_id"] == checkpoint["id"]
                        and delta["assimilation"] == [section["assimilation"]]
                        and delta["adversarial_review"] == checkpoint["adversarial_review"]
                        and delta["memory_delta"] == checkpoint["memory_delta"], "Assimilation delta mismatch")
                expected_theories = [t["id"] for t in theories if t["checkpoint_id"] == checkpoint["id"]]
                require(expected_theories == ([] if delta["theory_id"] is None else [delta["theory_id"]]),
                        "Memory delta lost its theory link")
            require(read(f"{prefix}/theories/{stem}.json") == [r for r in bundle if r["record_type"] in ("theory", "registration")],
                    "Published theory/test pair differs from learning records")
        else:
            require(memory["memory_delta"] == final["memory_delta"] and not theories and not registrations,
                    "Partial specialist memory/theory status differs")
        for theory in theories:
            section = sections[index[theory["checkpoint_id"]]["section_index"] - 1]
            require(all(theory[k] == v for k, v in section["theory"].items())
                    and all(index[theory["test_registration_id"]][k] == v for k, v in section["test"].items()),
                    "Theory or preregistration differs from authored review")
            checkpoint_citations = [c for claim in index[theory["checkpoint_id"]]["accepted_claims"] for c in claim["citations"]]
            require(theory["evidence_and_citations"] == checkpoint_citations,
                    "Theory citations differ from its source checkpoint")
        eligible = final["reading_status"] == "complete" and final["material_scope"] == entry["required_scope"]
        version = character
        if name == "index_steward":
            require(eligible, "Index reconciliation requires its completed foundation")
            scope = "learning-session:index-steward-pilot-foundation-v1"
            version = dict(character, id="character:index-steward-pilot-foundation-v1",
                           version="pilot-foundation-v1", experiment_id=scope,
                           created_at=policy["recorded_at"], constitution_hash=digest(constitution), readiness="ready")
            session = dict(schema_version=1, record_type="learning_session", id=scope, experiment_id=scope,
                           created_at=policy["recorded_at"], contamination="hindsight-contaminated", mode="learning",
                           character_versions=[version["id"]], source_ids=[source["id"]], authorization=policy["authority"],
                           provenance="Saved-evidence reconciliation only. Original checkpoints remain under " + character["id"]
                           + "; exact ancestry and scoped eligibility are in " + REGISTER_PATH + ". No new learning or performance.")
            version_bundle = [source, session, version]
            validate_bundle(version_bundle)
        decisions.append(dict(
            character_id=name, eligible=eligible, decision="ready" if eligible else "unready",
            character_version=version["id"], version_hash=digest(version),
            learning_character_version=character["id"], learning_character_hash=digest(character),
            knowledge_checkpoint=final["id"], knowledge_hash=digest(final),
            reviewed_constitution=constitution_path, reviewed_constitution_hash=digest(constitution),
            source_id=source["id"], source_pdf_sha256=acquired_hash, edition=source["edition"],
            material_scope=final["material_scope"], sections_reviewed=len(checkpoints),
            reviewed_ranges=expected_ranges, books_completed=int(eligible),
            curriculum_complete=False, unread_positions=[2, 3, 4],
            foundation_remaining=None if eligible else saved["blocker"],
            role=entry["role"], limitations=entry["excluded_claims"],
            contamination="hindsight-contaminated", evaluation_status="not_run",
            theory_ids=[r["id"] for r in theories], registration_ids=[r["id"] for r in registrations],
            blockers=[] if eligible else ["Complete and review the remaining pinned foundation; append a reconciled version and rerun this gate."],
        ))
    register = dict(schema_version=1, policy_id=policy["policy_id"], recorded_at=policy["recorded_at"],
                    scope=policy["scope"], participants=decisions,
                    eligible_character_versions=[d["character_version"] for d in decisions if d["eligible"]],
                    participant_gate="passed" if all(d["eligible"] for d in decisions) else "blocked",
                    step_11_status="blocked", step_11_prerequisites=policy["step_11_prerequisites"],
                    reconciled_bundle_path=VERSION_PATH, reconciled_bundle_hash=digest(version_bundle),
                    evidence_hashes=evidence,
                    verification_limit="Checks saved evidence and original attribution, not a fresh PDF passage verification or independent reading replication.")
    register["content_hash"] = digest(register)
    return register, version_bundle


def check_saved_readiness(root):
    """Reject stale decisions/versions, even if a caller recomputed their hashes."""
    root = Path(root)
    register, bundle = audit_readiness(root)
    for path, expected in ((REGISTER_PATH, register), (VERSION_PATH, bundle)):
        require(json.loads((root / path).read_text(encoding="utf-8")) == expected,
                "Saved readiness artifact differs from its reproducible evidence: " + path)
    return register
