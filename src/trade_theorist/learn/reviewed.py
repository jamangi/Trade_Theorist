"""Import an attributed review transcript without pretending to generate it again.

PDF text and model requests remain in the external private store. Public outputs
are explicitly selected records and original notes, never source page text.
"""

from pathlib import Path
import hashlib
import json
import re

from jsonschema import Draft202012Validator

from ..contracts import ContractError, digest, validate_bundle
from ..schema import S, POS, COMPLETABLE_SCOPES, enum, obj
from .engine import OUTPUT, citation_passage


REVIEW_CLAIM = obj(text=S, page=POS, anchor=S, disposition=enum("accept", "qualify", "reject"))


def pages_from_transcript(path, *, expected_sha256, expected_pages):
    """Load a pinned owner-supplied transcript without running OCR or learning.

    The caller binds this derivative to its PDF through the inventory and verifies
    source identity before reading. Page markers establish indexing, not OCR fidelity.
    """
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ContractError("Transcript differs from its registered fingerprint")
    text = data.decode("utf-8-sig")
    markers = list(re.finditer(r"^===== Page ([0-9]+) =====[ \t]*\r?$", text, re.MULTILINE))
    if type(expected_pages) is not int or expected_pages < 1 or [int(m.group(1)) for m in markers] != list(range(1, expected_pages + 1)):
        raise ContractError("Transcript pages are missing, duplicated or reordered")
    return [" ".join(text[m.end():markers[i + 1].start() if i + 1 < len(markers) else len(text)].split())
            for i, m in enumerate(markers)]


def material_from_pdf(path, review, *, expected_pages, expected_ranges, scope="full_book"):
    """Verify this exact locally reviewed edition before creating private sections.

    A matching file does not prove publisher authenticity or legal ownership.
    Human review of the contents/coverage remains part of the acquisition record.
    """
    from pypdf import PdfReader

    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != review["source_pdf_sha256"]:
        raise ContractError("PDF differs from the reviewed source")
    reader = PdfReader(path)
    if reader.is_encrypted or len(reader.pages) != expected_pages:
        raise ContractError("Unexpected encryption or page coverage")
    pages = [" ".join((page.extract_text() or "").split()) for page in reader.pages]
    return material_from_pages(pages, review, expected_ranges=expected_ranges, scope=scope)


def material_from_pages(pages, review, *, expected_ranges, scope="full_book"):
    if scope not in COMPLETABLE_SCOPES:
        raise ContractError("Unsupported reviewed material scope")
    sections = review["sections"]
    ranges = [(s["pdf_start"], s["pdf_end"]) for s in sections]
    if ranges != list(expected_ranges) or [s["number"] for s in sections] != list(range(1, len(sections) + 1)):
        raise ContractError("Review coverage is missing, duplicated or reordered")
    material = dict(source_id=review["source_id"], scope=scope, completeness_verified=True,
                    coverage_evidence="Exact PDF hash and page count checked against the attributed full-source review; substantive sections follow the reviewed contents map.", sections=[])
    for section in sections:
        start, end = section["pdf_start"], section["pdf_end"]
        if not 1 <= start <= end <= len(pages) or not pages[start - 1].strip():
            raise ContractError("Section is outside the file or has no readable opening")
        if not section["claims"]:
            raise ContractError("A reviewed section must contain grounded claims")
        for claim in section["claims"]:
            if not Draft202012Validator(REVIEW_CLAIM).is_valid(claim):
                raise ContractError("Malformed reviewed claim")
            if not start <= claim["page"] <= end or claim["anchor"] not in pages[claim["page"] - 1] or len(claim["anchor"].split()) > 25:
                raise ContractError("Review claim is not anchored in its cited page")
        material["sections"].append(dict(index=section["number"], locator=f"pdf/{review['source_id']}/section-{section['number']}",
            text="\n".join(f"[PDF PAGE {page}]\n{pages[page - 1]}" for page in range(start, end + 1))))
    return material


class ReviewedTranscriptProvider:
    """Deterministic review import, not an LLM and not an independent replication.

    Zero tokens/cost refer ONLY to local import. Original session generation
    usage and sampling are unavailable and disclosed in the acquisition manifest.
    """

    def __init__(self, review, material, constitution, curriculum):
        self.review = review
        self.material = material
        self.constitution = constitution
        self.curriculum = curriculum
        self.calls = 0

    def __call__(self, request, max_output_tokens):
        frozen, section = request["frozen"], request["section"]
        if frozen["source_hash"] != digest(self.material) or frozen["source_id"] != self.review["source_id"] or frozen["constitution"] != self.constitution or frozen["curriculum"] != self.curriculum:
            raise ContractError("Review import inputs differ from the frozen source and Character")
        number = section["index"]
        if not 1 <= number <= len(self.material["sections"]) or section != self.material["sections"][number - 1]:
            raise ContractError("Review section differs from the available source")
        reviewed = self.review["sections"][number - 1]
        extraction, accepted, rejected = [], [], []
        for index, claim in enumerate(reviewed["claims"], 1):
            claim_id = f"claim:review-{digest(self.review['source_id'])[:12]}-s{number:02d}-{index}"
            locator = section["locator"] + f"#page={claim['page']}"
            if claim["anchor"] not in citation_passage(section, locator):
                raise ContractError("Reviewed anchor does not match citation page")
            extraction.append(dict(claim_id=claim_id, text=claim["text"], locator=locator, quote=claim["anchor"]))
            (rejected if claim["disposition"] == "reject" else accepted).append(claim_id)
        response = dict(extraction=extraction, accepted_claim_ids=accepted, rejected_claim_ids=rejected,
                        assimilation=[reviewed["assimilation"]], adversarial_review=[reviewed["adversarial_review"]],
                        memory_delta=[reviewed["memory_delta"]], theory=reviewed.get("theory"), test=reviewed.get("test"))
        if not Draft202012Validator(OUTPUT).is_valid(response):
            raise ContractError("Malformed reviewed response")
        self.calls += 1
        return dict(response=response, usage=dict(input_tokens=0, output_tokens=0, calls=1, cost_usd="0.00"))


def write_once(path, value):
    """Preserve existing bytes on equivalent JSON; never rewrite prior content."""
    path = Path(path)
    encoded = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if digest(json.loads(path.read_text(encoding="utf-8"))) != digest(value):
            raise ContractError("Export exists with different content; append a new version")
    else:
        with path.open("x", encoding="utf-8", newline="\n") as output:
            output.write(encoded)


def foundation_status(character_dir, expected_source_id):
    """Read the published, hash-checked completion; never infer it from possession."""
    directory = Path(character_dir)
    read = lambda path: json.loads(path.read_text(encoding="utf-8"))
    completion = read(directory / "checkpoints/bogle-2017-completion.json")
    bundle = read(directory / "checkpoints/bogle-2017.bundle.json")
    index = validate_bundle(bundle)
    if completion["bundle_hash"] != digest(bundle) or completion["source_id"] != expected_source_id:
        raise ContractError("Completion does not match the published bundle or curriculum")
    for field, path in (("prior_hash", "checkpoints/bogle-2017-prior.json"), ("review_hash", "checkpoints/bogle-2017-reading-review.json"), ("curriculum_hash", "curriculum.v1.json")):
        if completion[field] != digest(read(directory / path)):
            raise ContractError("Completion provenance changed")
    checkpoint = index.get(completion["final_checkpoint_id"])
    checkpoints = sorted((r for r in bundle if r["record_type"] == "checkpoint"), key=lambda r: r["section_index"])
    review = read(directory / "checkpoints/bogle-2017-reading-review.json")
    if not checkpoint or checkpoint != checkpoints[-1] or checkpoint["reading_status"] != "complete" or checkpoint["material_scope"] != "full_book" or checkpoint["source_ids"] != [expected_source_id] or checkpoint["contamination"] != "hindsight-contaminated":
        raise ContractError("Foundation completion lacks a real full-source checkpoint")
    if len(checkpoints) != len(review["sections"]) or completion["sections_completed"] != len(checkpoints) or [c["section_index"] for c in checkpoints] != list(range(1, len(checkpoints) + 1)):
        raise ContractError("Foundation has incomplete or reordered sections")
    return dict(character="index_steward", status="foundation_complete", sections_completed=len(checkpoints), books_read=1, curriculum_complete=False, unread_positions=[2, 3, 4], source_id=expected_source_id, evaluation_status="not_run", contamination="hindsight-contaminated")
