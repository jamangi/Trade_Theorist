"""Reproduce the dated 2026-09-05 publisher metadata audit, without network claims."""
import json
from pathlib import Path

from trade_theorist.library import validate_catalog

CHECKED = "2026-09-05T20:29:13Z"
NEXT = "2026-09-12T20:29:13Z"
# Title, authors, edition/format, ISBN, publisher, primary evidence URL, access, finding.
BOOKS = [
    ("The Little Book of Common Sense Investing", ["John C. Bogle"], "2nd edition, 2017, hardcover", "9781119404507", "Wiley", "https://www.wiley-vch.de/en?isbn=9781119404507&option=com_eshop&view=product", "purchase_required", "Publisher lists this hardcover and a separate sample-chapter link. No full text acquired or machine-use grant established."),
    ("A Random Walk Down Wall Street", ["Burton G. Malkiel"], "13th edition, 2024 paperback", "9781324035435", "W. W. Norton", "https://wwnorton.co.uk/books/9781324035435-a-random-walk-down-wall-street-04e7966c-6f5e-469f-a62e-69352a44ab82/formats", "purchase_required", "Publisher lists paperback and separately identified ebook for purchase. Territorial distribution rights are not machine-use rights."),
    ("The Four Pillars of Investing", ["William J. Bernstein"], "2nd edition, 2023, print", "9781264715916", "McGraw Hill", "https://www.mheducation.com/highered/mhp/product/four-pillars-investing-second-edition-lessons-building-winning-portfolio.html", "purchase_required", "Publisher identifies print and ebook separately; sample requests are restricted to validated instructors."),
    ("The Psychology of Money", ["Morgan Housel"], "2020 paperback", "9780857197689", "Harriman House", "https://www.harriman-house.com/authors/morgan-housel/the-psychology-of-money/9780857197689", "purchase_required", "Publisher identifies the paperback and purchase route; former harriman.house book URL redirects here. Rights enquiry is separate."),
    ("The Intelligent Investor", ["Benjamin Graham", "Jason Zweig (commentary)"], "Unresolved: revised edition product page does not render format ISBN", None, "HarperCollins", "https://www.harpercollins.com/products/the-intelligent-investor-rev-ed-benjamin-graham", "unknown", "Official revised-edition page exists, but rendered ISBN fields are unresolved placeholders and stock varies by format. Confirm exact edition and format before acquisition."),
    ("The Essays of Warren Buffett", ["Warren E. Buffett", "Lawrence A. Cunningham (arranger)"], "5th edition, 2019, paperback", "9781531017507", "Carolina Academic Press", "https://cap-press.com/books/isbn/9781531017507/The-Essays-of-Warren-Buffett-Fifth-Edition", "unavailable", "Publisher identifies the fifth edition but marks this title no longer available. A contents/preview link is not the book; another lawful seller or library holding remains unverified."),
    ("Common Stocks and Uncommon Profits and Other Writings", ["Philip A. Fisher", "Kenneth L. Fisher (introduction)"], "2nd edition, 2003, softcover", "9780471445500", "Wiley", "https://www.wiley-vch.de/en/areas-interest/finance-economics-law/common-stocks-and-uncommon-profits-and-other-writings-978-0-471-44550-0", "purchase_required", "Publisher lists the expanded volume for purchase and a sample link. The approved title is Part One; additional writings require explicit coverage labels."),
    ("Expectations Investing", ["Michael J. Mauboussin", "Alfred Rappaport"], "Revised and updated, 2021, ebook", "9780231554848", "Columbia University Press", "https://cup.columbia.edu/book/expectations-investing/9780231554848/", "purchase_required", "Publisher identifies this ebook and EPUB/PDF purchase routes through its app. No ingestion or redistribution permission is inferred."),
    ("Way of the Turtle", ["Curtis Faith"], "1st edition, 2007, print", "9780071486644", "McGraw Hill", "https://www.mheducation.com/highered/mhp/product/way-turtle-secret-methods-turned-ordinary-people-into-legendary-traders.html", "purchase_required", "Publisher identifies print and separate ebook. The instructor sample request is not general full-text availability."),
    ("Following the Trend", ["Andreas F. Clenow"], "2nd edition, 2023, hardcover", "9781119908982", "Wiley", "https://www.wiley-vch.de/de?isbn=978-1-119-90898-2&option=com_eshop&view=product", "purchase_required", "Publisher identifies the English-language book on a German catalog page and links purchase/sample options. Futures coverage does not expand the approved tradable universe."),
    ("Trading Systems and Methods", ["Perry J. Kaufman"], "6th edition, 2019, hardcover", "9781119605355", "Wiley", "https://www.wiley-vch.de/en/areas-interest/finance-economics-law/finance-investments-13fi/trading-13fi4/trading-systems-and-methods-978-1-119-60535-5", "purchase_required", "Publisher identifies sixth edition hardcover, purchase and sample options. No source file acquired."),
    ("Evidence-Based Technical Analysis", ["David Aronson"], "1st edition, 2006, hardcover", "9780470008744", "Wiley", "https://www.wiley-vch.de/en/?isbn=978-0-470-00874-4&option=com_eshop&view=product", "purchase_required", "Publisher identifies first edition hardcover and purchase/library-platform links. Institutional entitlement remains unverified."),
]
LESSONS = [
    "Form low-cost diversification, long horizons and humility.", "Challenge forecasts with efficient-market skepticism.", "Connect theory, history, psychology and investment business.", "Include behavior and endurance in risk capacity.",
    "Form margin-of-safety and investor-versus-speculator discipline.", "Add business quality, management and capital allocation.", "Challenge asset-value instincts with qualitative growth and durability.", "Test future expectations embedded in price.",
    "Form explicit entry, sizing and exit discipline.", "Turn trend intuition into testable portfolio rules.", "Expand implementation choices and recognize parameter risk.", "Challenge the formed trend believer with statistical and data-mining tests.",
]


def build():
    catalog = {"schema_version": 1, "audit_checked_at": CHECKED, "sources": [], "assignments": [], "evidence": [], "review_queue": []}
    for i, (title, authors, edition, isbn, publisher, url, access, summary) in enumerate(BOOKS):
        identifier = "book:" + (isbn or "intelligent-investor-unresolved")
        blocker = "No permitted full-text file has been acquired; verify exact format, reading, machine ingestion, private storage and redistribution separately."
        if isbn is None:
            blocker = "Resolve exact edition/ISBN. " + blocker
        source = dict(id=identifier, schema_version=1, record_type="source", experiment_id=None, created_at=CHECKED, contamination="forward-insufficient", title=title, authors=authors, edition=edition, isbn=isbn, publisher=publisher, locator=url, retrieved_at=CHECKED, checked_at=CHECKED, next_check_at=NEXT, access=access, rights=dict(reading="unknown", machine_ingestion="unknown", private_storage="unknown", redistribution="unknown", evidence=[url, "Publisher metadata/availability reviewed only; no title-specific content-use grant established."]), publication_eligibility="metadata_only", private_locator=None, ingestion_status="blocked", blocker=blocker)
        catalog["sources"].append(source)
        character = ["index_steward", "value_rationalist", "systematic_trend_operator"][i // 4]
        catalog["assignments"].append(dict(character_id=character, position=i % 4 + 1, source_id=identifier, intended_lesson=LESSONS[i], edition_selection="catalog candidate; confirm against acquired copy before learning"))
        catalog["evidence"].append(dict(source_id=identifier, url=url, checked_at=CHECKED, method="publisher page inspected via web tool; upstream cache may apply", summary=summary))
        catalog["review_queue"].append(dict(source_id=identifier, reason="edition_unresolved" if isbn is None else "access_and_permissions_needed", action=blocker))
    catalog["review_queue"].extend([
        dict(source_id="book:9780857197689", reason="publisher_url_changed", action="Confirm the new canonical URL and recheck permissions before ingestion; redirect observed from https://harriman.house/books/the-psychology-of-money/."),
        dict(source_id="book:9781531017507", reason="edition_unavailable_from_publisher", action="Ask a library/bookseller about this exact ISBN, or record a deliberate edition update; do not replace the compiled essays with shareholder letters."),
    ])
    acquisition_path = Path(__file__).resolve().parents[1] / "library/catalog/bogle-2017-acquisition.json"
    if acquisition_path.exists():
        acquisition = json.loads(acquisition_path.read_text(encoding="utf-8"))
        source = acquisition["source"]
        catalog["sources"].append(source)
        catalog["evidence"].append(dict(source_id=source["id"], url=source["locator"], checked_at=source["checked_at"], method="Owner-supplied local PDF identity and full-text review; URL is related publisher metadata, not the evidence of permission", summary="Supplied 2017 ePDF ISBN verified on PDF page 10; complete source coverage and owner authorization are recorded in bogle-2017-acquisition.json. Raw file remains local and ignored."))
        catalog["assignments"][0].update(source_id=source["id"], edition_selection="Acquired ePDF format of the same approved 2017 foundation; hardcover candidate retained for audit")
        catalog["review_queue"] = [item for item in catalog["review_queue"] if item["source_id"] != "book:9781119404507"]
        catalog["audit_checked_at"] = source["checked_at"]
    validate_catalog(catalog)
    return catalog


if __name__ == "__main__":
    directory = Path("library/catalog")
    directory.mkdir(parents=True, exist_ok=True)
    catalog = build()
    (directory / "pilot.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    lines = ["# Pilot book-access audit", "", "Updated 2026-09-05: the owner supplied Bogle's 2017 ePDF, ISBN 9781119404521. Identity, all 20 chapters and the introduction were reviewed. See [acquisition and scope](bogle-2017-acquisition.json) and [completed learning](../../docs/index-steward-foundation.md). The PDF stays local; public artifacts contain original analysis and citations. This bounded authorization is not a publisher redistribution grant.", "", "The original publisher metadata audit and hardcover candidate are retained. Thirteen source records cover twelve curriculum slots; all other book-access blockers remain. No additional book was bought or read.", "", "| Character / order | Edition candidate | Access finding and evidence |", "| --- | --- | --- |"]
    for assignment in catalog["assignments"]:
        source = next(s for s in catalog["sources"] if s["id"] == assignment["source_id"])
        evidence = next(e for e in catalog["evidence"] if e["source_id"] == source["id"])
        lines.append(f"| {assignment['character_id']} / {assignment['position']} | {source['title']} — {source['edition']}; ISBN {source['isbn'] or 'unresolved'} | {evidence['summary']} [Publisher]({evidence['url']}) |")
    lines += ["", "Publisher purchase links establish neither acquisition nor content-use permission. Owner-supplied analysis is recorded separately from publisher licensing. HTTP checks cannot renew the local authorization or validate the local PDF; verify its hash against the acquisition record before reuse.", "", "Index Steward has completed its first source; the remaining three curriculum books are unread. The earlier fixture remains a separate synthetic software demonstration. No portfolio experiment or prospective performance has been established.", "", "The Intelligent Investor format/ISBN needs resolution. The fifth Buffett edition is unavailable from its publisher. The changed Harriman URL remains in the review queue. See pilot.json for individual blockers and evidence.", "", "`trade-theorist library check --catalog library/catalog/pilot.json --data-root <private-directory>` performs bounded HEAD requests and caches metadata for seven days. It never downloads book bodies or changes source rights or learning status. These are manual checks; no schedule was added.", ""]
    (directory / "ACCESS_REPORT.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
