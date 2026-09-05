"""Metadata-only cached availability checks. HTTP success never grants source rights."""

from datetime import timedelta
import json
import urllib.error
import urllib.parse
import urllib.request

from .contracts import ContractError, canonical, digest, utc, validate
from .storage import now


def validate_catalog(catalog):
    if catalog.get("schema_version") != 1:
        raise ContractError("Unsupported catalog version")
    index, isbns = {}, set()
    for source in catalog["sources"]:
        validate(source)
        if source["id"] in index or (source["isbn"] and source["isbn"] in isbns):
            raise ContractError("Duplicate exact edition")
        if source["isbn"]:
            digits = [int(d) for d in source["isbn"]]
            if sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits)) % 10:
                raise ContractError("Invalid ISBN check digit")
            isbns.add(source["isbn"])
        elif not source["edition"].lower().startswith("unresolved"):
            raise ContractError("Missing ISBN needs an explicit unresolved edition")
        index[source["id"]] = source
    assignments = catalog["assignments"]
    characters = {a["character_id"] for a in assignments}
    if characters != {"index_steward", "value_rationalist", "systematic_trend_operator"} or len(assignments) != 12:
        raise ContractError("Catalog must cover the twelve pilot slots")
    for character in characters:
        slots = [a for a in assignments if a["character_id"] == character]
        if sorted(a["position"] for a in slots) != [1, 2, 3, 4]:
            raise ContractError("Missing or duplicated curriculum position")
        if any(a["source_id"] not in index or not a["intended_lesson"] for a in slots):
            raise ContractError("Assignment lacks source or intended lesson")
    for source in index.values():
        evidence = [e for e in catalog["evidence"] if e["source_id"] == source["id"]]
        if not evidence or any(not e["summary"] or not e["url"].startswith("https://") or utc(e["checked_at"]) > utc(source["checked_at"]) for e in evidence):
            raise ContractError("Availability claim needs dated evidence")
    return index


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def head_check(url, previous):
    """No bodies, credentials or automatic redirects; ambiguous responses need review."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.username or parsed.password or not parsed.hostname:
        raise ContractError("Only known public HTTPS catalog URLs may be checked")
    headers = {"User-Agent": "TradeTheoristCatalog/0.1 (metadata HEAD check)"}
    if previous and previous.get("etag"):
        headers["If-None-Match"] = previous["etag"]
    request = urllib.request.Request(url, headers=headers, method="HEAD")
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        response = opener.open(request, timeout=10)
    except urllib.error.HTTPError as exc:
        response = exc
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"status": None, "final_url": url, "etag": None, "last_modified": None, "content_length": None, "content_type": None, "error": "network_unavailable"}
    with response:
        return {"status": response.status, "final_url": response.headers.get("Location", response.geturl()), "etag": response.headers.get("ETag"), "last_modified": response.headers.get("Last-Modified"), "content_length": response.headers.get("Content-Length"), "content_type": response.headers.get("Content-Type"), "error": None}


class AccessChecker:
    def __init__(self, store, fetch=head_check, ttl_days=7):
        if ttl_days <= 0:
            raise ValueError("Cache TTL must be positive")
        self.store, self.fetch, self.ttl = store, fetch, timedelta(days=ttl_days)

    def check(self, source, *, checked_at=None, force=False):
        validate(source)
        checked_at = checked_at or now()
        previous = self.store.connection.execute("SELECT * FROM library_checks WHERE source_id=? ORDER BY sequence DESC LIMIT 1", (source["id"],)).fetchone()
        old = json.loads(previous["result"]) if previous else None
        changed_url = previous is not None and previous["requested_url"] != source["locator"]
        if previous and not force and not changed_url and utc(previous["checked_at"]) <= utc(checked_at) < utc(previous["checked_at"]) + self.ttl:
            return {"cached": True, "checked_at": previous["checked_at"], "result": old}
        result = self.fetch(source["locator"], None if changed_url else old)
        required = {"status", "final_url", "etag", "last_modified", "content_length", "content_type", "error"}
        if set(result) != required:
            raise ContractError("Invalid URL check result")
        reasons = []
        if result["status"] == 304:
            if not old or changed_url:
                reasons.append("304_without_cached_representation")
            else:
                result = {**old, "status": 304}
        if changed_url:
            reasons.append("catalog_url_changed")
        if result["final_url"] != source["locator"]:
            reasons.append("redirect_requires_review")
        if result["status"] not in (200, 304):
            reasons.append("availability_unverified")
        if not result["etag"] and not result["last_modified"]:
            reasons.append("no_change_validator")
        if old and any(old[k] != result[k] for k in ("final_url", "etag", "last_modified", "content_length", "content_type")):
            reasons.append("remote_metadata_changed")
        with self.store.transaction():
            self.store.connection.execute("INSERT INTO library_checks(source_id,requested_url,checked_at,result) VALUES (?,?,?,?)", (source["id"], source["locator"], checked_at, canonical(result)))
            for reason in reasons:
                self.store.connection.execute("INSERT OR IGNORE INTO library_reviews VALUES (?,?,?,?)", (digest([source["id"], source["locator"], checked_at, reason]), source["id"], checked_at, reason))
        # Deliberately never write source.access, rights, or ingestion_status here.
        return {"cached": False, "checked_at": checked_at, "result": result, "review_reasons": reasons}

    def review_queue(self):
        return [dict(row) for row in self.store.connection.execute("SELECT * FROM library_reviews ORDER BY checked_at,id")]
