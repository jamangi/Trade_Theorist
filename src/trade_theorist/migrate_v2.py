"""Read-only synthetic preview and explicit, side-by-side v1 preservation."""

from contextlib import contextmanager, closing
from importlib.resources import files
from pathlib import Path
import json
import os
import sqlite3
import tempfile

from .contracts import ContractError, digest, utc
from .contracts_v2 import CLASSES
from .storage import Store
from .storage_v2 import V2Store
from .adapters.trader_user_sim import VERSION

CONVERSION = "v1-to-v2-boundary-1"
LIMITATIONS = ["V1 records, hashes and average-cost replay remain authoritative in their original tables.",
              "Only an isolated initial funding event can be converted without accounting replay.",
              "Trading, flows and corporate actions require reviewed Step 02 replay; no lots or TWR are fabricated.",
              "Synthetic opt-in is not a source license or permission to migrate owner data."]


def identity(old):
    return "v2:" + digest([CONVERSION, old])


def envelope(kind, identifier, experiment, at, rights, source_ids=(), source_hash=None, **fields):
    return dict(id=identifier, schema_version=2, record_type=kind, experiment_id=experiment,
                created_at=at, contamination="fixture", field_class=CLASSES[kind],
                provenance=dict(rights_id=rights, source_event_ids=list(source_ids), source_hash=source_hash or digest(list(source_ids))), **fields)


def safe_funding(history, portfolio, experiment):
    if len(history) != 1:
        return False
    event, payload = history[0], history[0]["payload"]
    if set(payload) != {"version", "portfolio_id", "type", "at", "amount"}:
        return False
    try:
        return (payload["type"] == "funding" and payload["amount"] == portfolio["initial_cash"]
                and utc(event["created_at"]) >= utc(payload["at"])
                and utc(experiment["start_at"]) <= utc(payload["at"]) < utc(experiment["end_at"]))
    except (ValueError, TypeError, AttributeError):
        return False  # Untyped v1 history may lack a usable effective timestamp.


@contextmanager
def source_reader(path):
    path = Path(path).expanduser()
    if not path.is_absolute() or not path.is_file():
        raise ContractError("Select an absolute existing synthetic database file")
    source = Store.__new__(Store)
    source.root, source.path, source.synthetic, source._depth = path.parent, path, True, 0
    source.connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    source.connection.row_factory = sqlite3.Row
    try:
        source.connection.execute("BEGIN")
        installed = dict(source.connection.execute("SELECT version,content_hash FROM schema_migrations"))
        known = {int(p.name.split("_")[0]): digest(p.read_text(encoding="utf-8")) for p in files("trade_theorist").joinpath("migrations").iterdir() if p.name.endswith(".sql")}
        if set(installed) - {1, 2} or any(known.get(v) != h for v, h in installed.items()):
            raise ContractError("Migration source must have unchanged supported v1 migrations")
        source.verify()
        records = source.records()
        if not records or any(r["schema_version"] != 1 or r["contamination"] != "fixture" for r in records):
            raise ContractError("Migration accepts original synthetic v1 records only")
        if any(r["record_type"] == "observation" and "synthetic" not in r["feed"].lower() for r in records):
            raise ContractError("Non-synthetic observation feed in migration source")
        yield source
    finally:
        source.close()


def plan(source):
    records = source.records()
    by_id = {r["id"]: r for r in records}
    preserved = source.verify()
    migrations = [list(r) for r in source.connection.execute("SELECT version,content_hash FROM schema_migrations ORDER BY version")]
    records_hash = digest([[r["id"], digest(r)] for r in records])
    lineage = digest([CONVERSION, preserved["tip"], records_hash, migrations])
    versions, gaps, converted, output = set(), [], [], []
    latest_observed = max((r["created_at"] for r in records), key=utc)
    for r in records:
        if r["record_type"] == "ledger_event":
            versions.add(r["simulation_model_version"])
            gaps.append(dict(source_id=r["id"], code="legacy_record_requires_accounting_replay"))
    simulations = {}
    for e in source.iter_events():
        latest_observed = max(latest_observed, e["created_at"], key=utc)
        version = e["payload"].get("version", "unversioned-v1-event") if isinstance(e["payload"], dict) else "unversioned-v1-event"
        versions.add(str(version))
        if e["kind"] == "simulation":
            if version != VERSION:
                raise ContractError("Unsupported simulation event version")
            simulations.setdefault(e["payload"].get("portfolio_id"), []).append(e)
        else:
            gaps.append(dict(source_id=e["id"], code="preserved_v1_only"))
    for exp in (r for r in records if r["record_type"] == "experiment"):
        eid, at, rid = identity(exp["id"]), exp["created_at"], identity(exp["id"] + ":rights")
        def make(kind, old_id, **fields):
            return envelope(kind, identity(old_id), eid, at, rid, [old_id], digest(by_id.get(old_id, old_id)), **fields)
        output.append(envelope("source_rights", rid, eid, at, rid, source_id="source:original-synthetic-v2",
            origin="original_synthetic", private_storage="permitted", private_replay="permitted",
            private_read_model="permitted", public_output="denied", evidence=["Explicit original synthetic migration fixture"], reviewed_at=at))
        for cid in exp["character_versions"]:
            c = by_id[cid]
            output.append(make("character", cid, **{k: c[k] for k in ("character_id", "version", "constitution_hash", "curriculum_hash", "readiness")}))
        policy = by_id[exp["policy_id"]]
        output.append(make("policy", policy["id"], **{k: v for k, v in policy.items() if k not in {"id", "schema_version", "record_type", "experiment_id", "created_at", "contamination"}}))
        output.append(make("experiment", exp["id"], mode=exp["mode"], execution_basis="simulated",
                           character_versions=[identity(c) for c in exp["character_versions"]], policy_id=identity(policy["id"]),
                           instrument_ids=[i["instrument_id"] for i in exp["universe"]], start_at=exp["start_at"], end_at=exp["end_at"], regime="fixture"))
        for p in (r for r in records if r["record_type"] == "portfolio" and r["experiment_id"] == exp["id"]):
            history = simulations.get(p["id"], [])
            safe = (safe_funding(history, p, exp)
                    and not any(r["record_type"] == "ledger_event" and r["portfolio_id"] == p["id"] for r in records))
            # No balances migrate for a history requiring lot reconstruction, even if its first funding is known.
            output.append(make("portfolio", p["id"], mode=exp["mode"], execution_basis="simulated",
                owner_character_version=identity(p["owner_character_version"]), policy_id=identity(policy["id"]), currency=p["currency"],
                role="baseline" if p["mode"] == "baseline" else "strategy", accounting_method="fifo-v2", return_method="exact-twr-v2",
                initialization="new" if safe else "conversion_gap", legacy_portfolio_id=p["id"]))
            if safe:
                e, pid, sid = history[0], identity(p["id"]), identity(p["id"] + ":segment-1")
                effective = e["payload"]["at"]
                output.append(envelope("funded_segment", sid, eid, effective, rid, portfolio_id=pid,
                    owner_character_version=identity(p["owner_character_version"]), ordinal=1, previous_segment_id=None,
                    start_at=effective, reason="initial"))
                output.append(envelope("ledger_event", identity(e["id"]), eid, e["created_at"], rid,
                    [e["id"]], e["content_hash"], portfolio_id=pid, segment_id=sid, idempotency_key=identity(e["id"]),
                    sequence=1, effective_at=effective, observed_at=e["created_at"], event_type="funding",
                    payload=dict(amount=p["initial_cash"], boundary_mark_ids=[])))
                converted.append(identity(e["id"]))
            else:
                gaps.extend(dict(source_id=e["id"], code="requires_accounting_replay") for e in history)
                if not history:
                    gaps.append(dict(source_id=p["id"], code="no_canonical_funding_history"))
    if not output:
        raise ContractError("No synthetic portfolio experiment available to migrate")
    gaps.sort(key=lambda r: (r["source_id"], r["code"]))
    for exp in (r for r in list(output) if r["record_type"] == "experiment"):
        output.append(envelope("migration_lineage", "lineage:" + digest([lineage, exp["id"]]), exp["id"], latest_observed,
            exp["provenance"]["rights_id"], conversion_version=CONVERSION, source_chain_hash=preserved["tip"],
            source_records_hash=records_hash, source_migrations_hash=digest(migrations), destination_identity=lineage,
            source_event_versions=sorted(versions), limitations=LIMITATIONS, converted_event_ids=converted, gaps=gaps))
    from .contracts_v2 import validate_bundle
    validate_bundle(output)
    report = dict(conversion_version=CONVERSION, destination_identity=lineage, source_chain_hash=preserved["tip"],
        source_records_hash=records_hash, source_migrations_hash=digest(migrations), source_event_versions=sorted(versions),
        preserved_v1=preserved, planned_v2_records=len(output), converted_event_ids=converted, gaps=gaps, limitations=LIMITATIONS)
    return report, output


def migrate(source_path, *, synthetic=False, destination=None, apply=False, before_commit=None):
    if not synthetic:
        raise ContractError("Explicit --synthetic required; owner migration is unsupported")
    with source_reader(source_path) as source:
        report, records = plan(source)
        if not apply:
            return dict(report, action="dry_run", destination_written=False)
        if destination is None or not Path(destination).is_absolute():
            raise ContractError("Apply requires an absolute side-by-side destination directory")
        root = Path(destination).resolve()
        if root == source.root.resolve() or root.is_relative_to(source.root.resolve()) or source.root.resolve().is_relative_to(root):
            raise ContractError("Destination must be separate from the source directory")
        target = root / "research.sqlite3"
        if target.exists():
            # Inspect without triggering even a schema migration on unrelated data.
            with closing(sqlite3.connect(target.as_uri() + "?mode=ro", uri=True)) as conn:
                try:
                    old = [json.loads(r[0]) for r in conn.execute("SELECT body FROM v2_records WHERE record_type='migration_lineage'")]
                except sqlite3.Error as exc:
                    raise ContractError("Destination already exists without migration lineage") from exc
                if not old or any(r["destination_identity"] != report["destination_identity"] for r in old):
                    raise ContractError("Destination lineage conflicts with source")
            with V2Store(root, synthetic=True) as existing:
                existing.verify()
                existing.put_v2(records)
            return dict(report, action="already_applied", destination_written=False)
        if root.exists() and any(root.iterdir()):
            raise ContractError("Destination must be empty")
        root.mkdir(parents=True, exist_ok=True)
        # The staging directory is ours, inside the explicitly selected destination.
        with tempfile.TemporaryDirectory(prefix=".v2-stage-", dir=root) as stage:
            copied = sqlite3.connect(Path(stage) / "research.sqlite3")
            try:
                source.connection.backup(copied)
            finally:
                copied.close()
            with V2Store(stage, synthetic=True) as result:
                with result.transaction():
                    result.put_v2(records)
                    if before_commit:
                        before_commit(result)
                checked = result.verify()
                if checked["v1"] != report["preserved_v1"]:
                    raise ContractError("V1 preservation check failed")
                result.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            if target.exists():
                raise ContractError("Destination appeared during conversion")
            # Hard-link publication is atomic and fails if another writer won the identity.
            os.link(Path(stage) / "research.sqlite3", target)
        return dict(report, action="applied", destination_written=True)
