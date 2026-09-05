"""Local book identity audit. File possession never promotes a Character."""

from collections import Counter
import hashlib
from pathlib import Path
import re

from .contracts import ContractError, utc
from .storage import now


CHARACTERS = (
    "index_steward", "value_rationalist", "systematic_trend_operator",
    "mean_reversion_experimentalist", "market_microstructure_mechanic",
    "probabilistic_risk_skeptic", "event_and_disclosure_detective",
)


def _filename(value):
    # Reject Windows drive paths and separators even when running on Linux.
    return (isinstance(value, str) and value.lower().endswith(".pdf")
            and not any(c in value for c in '/\\:') and value not in (".", ".."))


def validate_inventory(catalog):
    """Validate the acquisition inventory independently of frozen learning sources."""
    try:
        if catalog["schema_version"] != 1 or catalog["catalog_type"] != "local_book_inventory":
            raise ContractError("Unsupported local inventory")
        if utc(catalog["checked_at"]).utcoffset() is None:
            raise ContractError("Inventory timestamp needs a timezone")
        index, filenames, hashes = {}, set(), set()
        for source in catalog["sources"]:
            if source["id"] in index or not all(source[k] for k in ("title", "authors", "edition", "notes")):
                raise ContractError("Duplicate or unidentified source")
            index[source["id"]] = source
            if source["availability"] not in ("local_file", "missing"):
                raise ContractError("Invalid acquisition status")
            if source["coverage"] not in ("unverified", "partial", "verified_in_prior_learning", "missing"):
                raise ContractError("Invalid coverage status")
            if source["text_status"] not in ("text_present", "ocr_required", "layout_review_required", "missing"):
                raise ContractError("Invalid text status")
            file = source["file"]
            if source["availability"] == "missing":
                if file is not None or source["coverage"] != "missing" or source["text_status"] != "missing":
                    raise ContractError("Missing title cannot claim material")
                continue
            if (not _filename(file["name"]) or file["name"].casefold() in filenames
                    or not re.fullmatch(r"[0-9a-f]{64}", file["sha256"])
                    or file["sha256"] in hashes):
                raise ContractError("Invalid or duplicate local file identity")
            filenames.add(file["name"].casefold())
            hashes.add(file["sha256"])
            if source["coverage"] == "missing" or source["text_status"] == "missing":
                raise ContractError("Local file cannot use missing-material states")
            if source["coverage"] == "verified_in_prior_learning" and not all(source.get(k) for k in ("prior_source_id", "learning_evidence")):
                raise ContractError("Prior coverage requires linked learning evidence")
            if any(type(file[k]) is not int or file[k] <= 0 for k in ("size_bytes", "page_count")):
                raise ContractError("Invalid file dimensions")
            pages = source["identity_evidence"]["pdf_pages"]
            if not pages or any(type(p) is not int or not 1 <= p <= file["page_count"] for p in pages):
                raise ContractError("Identity evidence needs in-range PDF pages")
            if not source["identity_evidence"]["method"]:
                raise ContractError("Identity evidence needs an inspection method")
            for entry in source["observed_isbns"]:
                isbn = entry["isbn"]
                if not re.fullmatch(r"[0-9]{13}", isbn) or not entry["format"]:
                    raise ContractError("Invalid observed ISBN")
                if sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(isbn)) % 10:
                    raise ContractError("Invalid observed ISBN check digit")
        assignments = catalog["assignments"]
        if {a["character_id"] for a in assignments} != set(CHARACTERS) or len(assignments) != 28:
            raise ContractError("Inventory must cover all twenty-eight curriculum slots")
        for char in CHARACTERS:
            slots = [a for a in assignments if a["character_id"] == char]
            if sorted(a["position"] for a in slots) != [1, 2, 3, 4]:
                raise ContractError("Missing or duplicated curriculum position")
            if len({a["source_id"] for a in slots}) != 4:
                raise ContractError("A Character cannot fill multiple book slots with one file")
            if any(a["source_id"] not in index or not a["intended_lesson"] for a in slots):
                raise ContractError("Assignment lacks source or lesson")
        if {a["source_id"] for a in assignments} != set(index):
            raise ContractError("Unassigned inventory source")
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        if isinstance(exc, ContractError):
            raise
        raise ContractError("Malformed local inventory") from exc
    return index


def inventory_summary(catalog):
    index = validate_inventory(catalog)
    return {
        "scope": "all_seven_characters_local_acquisition_audit",
        "checked_at": catalog["checked_at"],
        "characters": len(CHARACTERS), "slots": len(catalog["assignments"]),
        "unique_titles": len(index),
        "local_files": sum(s["file"] is not None for s in index.values()),
        "slots_with_files": sum(index[a["source_id"]]["file"] is not None for a in catalog["assignments"]),
        "coverage": dict(Counter(s["coverage"] for s in index.values())),
        "text_status": dict(Counter(s["text_status"] for s in index.values())),
        "grants_learning_readiness": False,
        "review_queue": [{"source_id": s["id"], "coverage": s["coverage"],
                          "text_status": s["text_status"], "action": s["notes"]}
                         for s in index.values() if s["coverage"] != "verified_in_prior_learning"],
    }


def verify_files(catalog, books_root):
    """Read only named PDFs under an explicit root; emit no text or absolute paths."""
    index = validate_inventory(catalog)
    root = Path(books_root).resolve(strict=True)
    if not root.is_dir():
        raise ContractError("Books root must be a directory")
    results = []
    for source in index.values():
        file = source["file"]
        if file is None:
            results.append({"source_id": source["id"], "status": "not_acquired"})
            continue
        path = (root / file["name"]).resolve()
        if not path.is_relative_to(root):
            raise ContractError("Local source resolves outside the books root")
        try:
            with path.open("rb") as stream:
                actual_hash = hashlib.file_digest(stream, "sha256").hexdigest()
            status = "verified" if path.stat().st_size == file["size_bytes"] and actual_hash == file["sha256"] else "changed"
        except FileNotFoundError:
            status = "missing"
        results.append({"source_id": source["id"], "status": status})
    return {"checked_at": now(), "grants_learning_readiness": False, "files": results}


def render_report(catalog):
    index = validate_inventory(catalog)
    summary = inventory_summary(catalog)
    coverage_labels = {"unverified": "Coverage not yet checked", "partial": "Incomplete excerpts",
                       "verified_in_prior_learning": "Complete reading verified", "missing": "No file"}
    text_labels = {"text_present": "Text available in checked pages", "ocr_required": "OCR needed",
                   "layout_review_required": "Text/layout review needed", "missing": "Acquisition needed"}
    lines = ["# Current book inventory", "", f"Checked {catalog['checked_at']}. "
             f"{summary['local_files']} local PDFs map to {summary['slots_with_files']} of {summary['slots']} ordered slots across seven Characters. "
             "Expectations Investing is shared. Two titles have no file; the Harris file is only a partial draft.", "",
             "This is an identity/access audit, not Character learning. Only the previously completed Bogle foundation "
             "has full reading evidence. Other files require coverage checks, source registration and ordered reading. "
             "PDF page counts are file pages, not print-edition page counts.", "",
             "| Character / order | Title | Observed edition | PDF pages | Coverage / preparation |",
             "| --- | --- | --- | --- | --- |"]
    for a in catalog["assignments"]:
        s = index[a["source_id"]]
        pages = s["file"]["page_count"] if s["file"] else "—"
        name = a['character_id'].replace('_', ' ').title()
        lines.append(f"| {name} / {a['position']} | {s['title']} | {s['edition']} | {pages} | {coverage_labels[s['coverage']]}; {text_labels[s['text_status']]} |")
    lines += ["", "## Findings and preparation", ""]
    for s in index.values():
        lines.append(f"- **{s['title']}:** {s['notes']}")
    lines += ["", "## Reuse", "",
              "The machine-readable [catalog](characters.json) records filenames, SHA-256 fingerprints, sizes, "
              "observed ISBNs, identity-evidence pages and Character-specific order. ISBNs identify editions/formats "
              "printed inside the source; they do not prove a converted PDF is a native publisher ePDF. "
              "No PDF bodies, page images or extracted book text are published here.", "",
              "Run `trade-theorist library report` for the current inventory. Set `TRADE_THEORIST_BOOKS_ROOT` "
              "to the existing local books directory and run `trade-theorist library verify-files` to recheck all "
              f"{summary['local_files']} fingerprints. A matching hash confirms file identity, not completeness, text quality, permissions "
              "or learning. A changed/missing registered file produces a nonzero exit; the two known unacquired titles "
              "remain explicitly listed. No download or automatic source promotion occurs.", "",
              "The [pilot audit](ACCESS_REPORT.md) and pilot.json retain earlier publisher candidates and the source "
              "used by the completed Bogle run. Their old acquisition blockers are historical; use this report for "
              "current possession. Select and register the actual edition in a new curriculum version before its "
              "first learning run; never rewrite frozen checkpoints.", "",
              "See [training sequence](../../docs/character-training.md) and "
              "[microstructure alternatives](../../docs/microstructure-alternatives.md).", ""]
    return "\n".join(lines)
