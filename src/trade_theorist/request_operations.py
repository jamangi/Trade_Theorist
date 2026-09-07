"""Bounded recorded collector and read-only shared-request diagnostics."""
import json
import os
from pathlib import Path
import sqlite3

from .contracts import ContractError, digest
from .market_requests import Coordinator, owner_lock
from .request_contracts import validate


def status(root=None, policy_path=None, *, fixture=False, registry_root=None):
    result = dict(status="blocked", account_calls=0, cooperating_callers_only=True)
    if not root or not policy_path:
        return result | dict(reason="missing_request_configuration", resume="Set quota_root and quota_policy_path; use one stable principal and private store for every cooperating caller.")
    try:
        policy = validate(json.loads(Path(policy_path).read_text(encoding="utf-8")))
        if policy["record_type"] != "request_policy": raise ContractError("Wrong policy type")
        # Existing read-only migration validation also accepts additive migration 005.
        from .operations_v2 import ReadOnlyV2, absolute_root
        root = absolute_root(root, fixture=fixture, purpose="quota_root")
        with ReadOnlyV2(root, synthetic=fixture) as store:
            if store.connection.execute("SELECT 1 FROM schema_migrations WHERE version=5").fetchone() is None:
                raise ContractError("Shared request migration missing")
            row = store.connection.execute("SELECT policy FROM market_quota WHERE id=1").fetchone()
            if row is None or json.loads(row[0]) != policy:
                raise ContractError("Policy does not match durable state")
            attempts = store.connection.execute("SELECT COUNT(*) FROM market_attempts").fetchone()[0]
            counts = dict(store.connection.execute("SELECT json_extract(body,'$.status'),COUNT(*) FROM market_work GROUP BY 1"))
        registry = Path(registry_root) if fixture and registry_root else Path(os.environ.get("LOCALAPPDATA", Path.home())) / "TradeTheorist" / "quota-owners"
        key = digest(policy["quota_id"])
        if json.loads((registry / (key + ".json")).read_text()) != dict(root=str(Path(root).resolve())):
            raise ContractError("Principal binding differs")
        active = False
        try:
            with owner_lock(registry / (key + ".lock"), create=False):
                pass
        except (PermissionError, BlockingIOError):
            active = True
        return result | dict(status="ready" if active else "blocked", reason="owner_active" if active else "owner_stopped",
            quota_id=policy["quota_id"], physical_attempts=attempts, work_states=counts,
            resume="Submit to the existing owner; a second owner fails closed." if active else "Open the same bound store with the reviewed policy; recovery admission preserves the allowance.",
            qualification="Readiness of local coordination only; feed rights, account qualification and external traffic remain separate.")
    except (ContractError, OSError, ValueError, KeyError, sqlite3.Error):
        return result | dict(reason="request_state_unverified", resume="Check the reviewed policy, shared store, migration integrity and canonical principal binding. Restore missing state; do not start a fresh allowance.")


def recorded_collect(root, policy_path, query_path, responses_path, *, max_attempts, deadline, registry_root=None):
    """Explicit original-fixture path for manual collectors; never opens a socket."""
    from .adapters.alpaca_market_data import Response
    policy = validate(json.loads(Path(policy_path).read_text(encoding="utf-8")))
    query = validate(json.loads(Path(query_path).read_text(encoding="utf-8")))
    responses = json.loads(Path(responses_path).read_text(encoding="utf-8"))
    if not isinstance(responses, list) or len(responses) > 1000:
        raise ContractError("Use at most 1000 recorded pages")
    for response in responses:
        if not isinstance(response, dict) or set(response) != {"status", "headers", "body", "received_at"}:
            raise ContractError("Invalid recorded response envelope")
    def transport(*_):
        if not responses: raise ContractError("Recorded pages exhausted")
        return Response(**responses.pop(0))
    with Coordinator(root, policy, transport, synthetic=True, registry_root=registry_root) as owner:
        work = owner.submit(query, consumer="manual-recorded-collector", max_attempts=max_attempts, deadline=deadline)
        result = owner.run(work)
        return dict(status=result["status"], fixture_only=True, account_calls=0, telemetry=result, resume=owner.resume(work), usage=owner.usage())
