"""Typed paired references and point-in-time checks for additive forward records."""
from ..contracts import ContractError, digest, utc
from ..market_requests import query
from ..request_contracts import validate as validate_request


def comparison(plan):
    """Economic comparison excludes portfolio/segment identities, not cash flows."""
    return {k: plan[k] for k in ("mark_schedule", "max_mark_age_seconds", "execution_model", "fee_per_share",
        "slippage_bps", "spread_bps", "fractional_shares", "corporate_actions", "baseline_construction")} | {
        "flows": [{k: f[k] for k in ("event_type", "effective_at", "amount")} for f in plan["flows"]]}


def get(lookup, identifier, kind):
    value = lookup(identifier)
    if value["record_type"] != kind:
        raise ContractError("Forward reference has the wrong type")
    return value


def participant(lookup, portfolio_id, plan_id, segment_id):
    p = get(lookup, portfolio_id, "portfolio")
    plan = get(lookup, plan_id, "accounting_plan")
    segment = get(lookup, segment_id, "funded_segment")
    owner = get(lookup, segment["owner_character_version"], "character")
    policy = get(lookup, p["policy_id"], "policy")
    exp = get(lookup, p["experiment_id"], "experiment")
    rights = get(lookup, p["provenance"]["rights_id"], "source_rights")
    fixture = p['contamination'] == 'fixture'
    if p["execution_basis"] != "simulated" or p["initialization"] != "new" or owner["readiness"] != ('fixture_only' if fixture else 'ready'):
        raise ContractError("Forward participant has invalid execution basis or readiness")
    if not fixture and (p['contamination'] != 'forward-insufficient' or exp['regime'] != 'forward_shadow'):
        raise ContractError('Real participant must remain forward-insufficient shadow evidence')
    if rights["origin"] != ('original_synthetic' if fixture else 'licensed') or any(rights[k] != "permitted" for k in ("private_storage", "private_replay", "private_read_model")):
        raise ContractError("Forward rights are unresolved")
    if any(r["experiment_id"] != p["experiment_id"] for r in (plan, segment, owner, policy, rights)) or plan["portfolio_id"] != p["id"] or segment["portfolio_id"] != p["id"] or segment["owner_character_version"] != p["owner_character_version"]:
        raise ContractError("Forward participant has mismatched ownership or accounting scope")
    if owner["id"] not in exp["character_versions"] or any(p[k] != exp[k] for k in ("mode", "execution_basis", "policy_id")):
        raise ContractError("Forward participant differs from its frozen experiment")
    value = dict(portfolio_ref=p["id"], segment_ref=segment["id"], character_ref=owner["id"], plan_ref=plan["id"],
        portfolio_hash=digest(p), segment_hash=digest(segment), character_hash=digest(owner), plan_hash=digest(plan),
        policy_hash=digest(policy), mode=p["mode"], execution_basis=p["execution_basis"])
    return value, plan, exp, policy


def validate_forward(record, lookup):
    if record["contamination"] not in {'fixture','forward-insufficient'}:
        raise ContractError("Forward integration cannot certify reviewed performance")
    kind = record["record_type"]
    if kind == "forward_manifest":
        if record['evidence_grade'] != record['contamination']:
            raise ContractError('Forward evidence grade differs')
        if record['contamination'] == 'fixture' and 'real_context' in record:
            raise ContractError('Fixture cannot carry real eligibility')
        if record['contamination'] != 'fixture':
            from .prospective import validate_real_context
            validate_real_context(record, lookup)
        q = query(record["query"])
        policy = validate_request(record["quota_policy"])
        if q != record["query"] or digest(q) != record["query_hash"] or digest(policy) != record["quota_policy_hash"] or record["work_ref"] != "work:" + digest(q):
            raise ContractError("Frozen forward query or quota policy changed")
        if record["max_request_attempts"] > policy["max_work_attempts"] or q["sharing_scope"] not in policy["sharing_scopes"] or q["rights_ref"] != policy["rights_ref"] or policy["feed_delays"][q["feed"]] is None:
            raise ContractError("Forward request exceeds its reviewed policy")
        if q["adjustment"] != "raw":
            raise ContractError("Forward integration requires raw observation revisions")
        if not utc(record["created_at"]) < utc(record["start_at"]) <= utc(record["data_deadline"]) <= utc(record["decision_at"]) < utc(record["end_at"]):
            raise ContractError("Forward round must be preregistered with ordered deadlines")
        if utc(q["information_cutoff"]) > utc(record["data_deadline"]) or utc(q["end"]) > utc(q["information_cutoff"]):
            raise ContractError("Information cutoff cannot relax the data deadline")
        if record["snapshot_ref"] != "snapshot:forward-" + digest([record["id"], record["decision_at"], digest(q)]):
            raise ContractError("Planned snapshot identity changed")
        stop = record["stopping_rule"]
        if stop["stop_at"] != record["end_at"] or stop["min_completed_sessions"] < stop["horizon_sessions"]:
            raise ContractError("Stopping rule differs from the frozen observation window")
        peers = record["participants"]
        if len({p["portfolio_ref"] for p in peers}) != len(peers):
            raise ContractError("Duplicate paired portfolio")
        if lookup(peers[0]["portfolio_ref"])["experiment_id"] != record["experiment_id"]:
            raise ContractError("Forward manifest must use its first paired experiment's scope")
        signatures, modes = set(), set()
        baseline = get(lookup, record["baseline_ref"], "portfolio")
        baseline_plan = get(lookup, record["baseline_plan_ref"], "accounting_plan")
        if baseline["role"] != "baseline" or baseline["execution_basis"] != "simulated" or baseline_plan["portfolio_id"] != baseline["id"] or digest(baseline) != record["baseline_hash"] or digest(baseline_plan) != record["baseline_plan_hash"]:
            raise ContractError("Baseline identity or construction is invalid")
        if not baseline_plan["flows"]:
            raise ContractError("A funded baseline construction is required")
        participant(lookup, baseline["id"], baseline_plan["id"], baseline_plan["flows"][0]["segment_id"])
        if any(utc(r["created_at"]) > utc(record["created_at"]) for r in (baseline, baseline_plan)):
            raise ContractError("Baseline was not frozen before registration")
        risk_signatures = set()
        for frozen in peers:
            actual, plan, exp, risk = participant(lookup, frozen["portfolio_ref"], frozen["plan_ref"], frozen["segment_ref"])
            if frozen != actual or plan["baseline_portfolio_id"] != baseline["id"]:
                raise ContractError("Frozen Character, portfolio, baseline or plan differs")
            if not utc(exp["start_at"]) <= utc(record["start_at"]) < utc(record["end_at"]) <= utc(exp["end_at"]):
                raise ContractError("Forward round is outside a paired experiment")
            records = [lookup(frozen[k]) for k in ("portfolio_ref", "segment_ref", "character_ref", "plan_ref")]
            records.extend([risk, lookup(records[0]["provenance"]["rights_id"])])
            if any(utc(r["created_at"]) > utc(record["created_at"]) for r in records):
                raise ContractError("Participant was unavailable when preregistered")
            if set(q["symbols"]) != {i["symbol"] for i in risk["universe"]}:
                raise ContractError("Paired opportunities differ from the requested universe")
            signatures.add(digest(comparison(plan))); modes.add(actual["mode"])
            risk_signatures.add(digest({k: risk[k] for k in ("universe", "limits", "clock", "costs", "long_only", "cash_only")}))
        if len(risk_signatures) != 1:
            raise ContractError("Paired consumers must share risk and trading cost conventions")
        if modes != {"character_portfolio", "council"} or signatures != {record["comparison_hash"]} or digest(comparison(baseline_plan)) != record["comparison_hash"]:
            raise ContractError("Paired modes must use identical baseline, costs and cash-flow policies")
        return
    manifest = get(lookup, record["manifest_ref"], "forward_manifest")
    if record["experiment_id"] != manifest["experiment_id"] or utc(record["created_at"]) < utc(manifest["created_at"]):
        raise ContractError("Forward record belongs to another or later manifest")
    snapshot_id = record["id"] if kind == "forward_snapshot" else record["snapshot_ref"]
    if snapshot_id != manifest["snapshot_ref"]:
        raise ContractError("Paired snapshot identity differs")
    if record['contamination'] != manifest['contamination']:
        raise ContractError('Forward evidence regime differs')
    if kind == 'forward_audit':
        import json
        from ..contracts import canonical
        try: payload=json.loads(record['payload_json'])
        except (ValueError,TypeError) as exc: raise ContractError('Invalid private audit payload') from exc
        if canonical(payload)!=record['payload_json'] or digest(payload)!=record['payload_hash']:
            raise ContractError('Private audit payload changed')
        return
    if kind == 'forward_opinion':
        from .prospective import validate_opinion
        validate_opinion(record,manifest,lookup)
        return
    if kind == "forward_snapshot":
        q = manifest["query"]
        if record["work_ref"] != manifest["work_ref"] or record["query_hash"] != manifest["query_hash"] or record["decision_at"] != manifest["decision_at"]:
            raise ContractError("Snapshot query or evidence boundary changed")
        expected = {(s, d) for s in q["symbols"] for d in q["expected_sessions"]}
        observed = set()
        identities, series = set(), set()
        for item in record["observations"]:
            b = item["bar"]
            from ..adapters.alpaca_market_data import AlpacaBarsAdapter, Response
            AlpacaBarsAdapter.parse_page(Response(200, {}, {"bars": {b["symbol"]: [{k: v for k, v in b.items() if k != "symbol"}]}}, item["received_at"]), q["symbols"])
            if item["id"] in identities or (b["symbol"], utc(b["t"])) in series:
                raise ContractError("Snapshot must select one eligible revision per observation")
            identities.add(item["id"]); series.add((b["symbol"], utc(b["t"])))
            if not utc(q["start"]) <= utc(b["t"]) <= utc(q["end"]) or not utc(b["t"]) <= utc(item["received_at"]) <= utc(q["information_cutoff"]) or utc(item["received_at"]) < utc(q["freshness_after"]):
                raise ContractError("Observation is outside frozen information bounds")
            if b["symbol"] not in q["symbols"] or b["t"][:10] not in q["expected_sessions"] or utc(item["received_at"]) > utc(record["created_at"]):
                raise ContractError("Snapshot contains unavailable or unrequested evidence")
            if manifest['contamination'] != 'fixture':
                calendar = {s['session']:s for s in manifest['real_context']['calendar']}
                session = calendar.get(b['t'][:10])
                if session is None or utc(item['received_at']) < utc(session['close_at']):
                    raise ContractError('Daily bar was not observed after its session closed')
            observed.add((b["symbol"], b["t"][:10]))
        if record["coverage_expected"] != len(expected) or record["coverage_observed"] != len(observed & expected):
            raise ContractError("Snapshot coverage counts differ")
        if record["status"] == "ready":
            if record["reason"] != "none" or observed & expected != expected or utc(record["created_at"]) >= utc(manifest["data_deadline"]):
                raise ContractError("Only complete on-time snapshots may be frozen")
        elif record["observations"] or record["reason"] == "none":
            raise ContractError("Abstention cannot expose early-page evidence")
    if kind == "forward_progress":
        for field in ("work_usage", "physical_usage"):
            validate_request(record[field])
            if record[field]["quota_id"] != manifest["quota_policy"]["quota_id"]:
                raise ContractError("Usage belongs to another quota principal")
        usage = record["work_usage"]
        if usage["work_id"] != manifest["work_ref"] or usage["query_hash"] != manifest["query_hash"] or record["physical_work_ref"] != (usage["shared_work_id"] or usage["work_id"]) or record["physical_usage"]["work_id"] != record["physical_work_ref"]:
            raise ContractError("Shared physical usage attributed to the wrong work")
        if record["status"] in {"ready", "abstained"}:
            snapshot = get(lookup, snapshot_id, "forward_snapshot")
            if snapshot["status"] != record["status"] or snapshot["reason"] != record["reason"]:
                raise ContractError("Saved progress differs from its sealed snapshot")
    if kind in {"forward_result", "forward_reservation"}:
        snapshot = get(lookup, snapshot_id, "forward_snapshot")
        if kind == "forward_reservation":
            if snapshot["status"] != "ready" or record["calls_reserved"] != len(manifest["participants"]) or record["calls_reserved"] > manifest["model_budget"]["max_calls"] or record["tokens_reserved"] != manifest["model_budget"]["max_tokens"]:
                raise ContractError("Invalid finite Character reservation")
        else:
            if record['evidence_grade'] != manifest['evidence_grade']:
                raise ContractError('Result evidence grade differs from manifest')
            if record["status"] == "abstained" and record["reason"] == "none":
                raise ContractError("A shared abstention requires an explicit reason")
            if record["snapshot_hash"] != digest(snapshot) or len(record["outcomes"]) != len(manifest["participants"]):
                raise ContractError("Result does not contain every paired consumer")
            for outcome, peer in zip(record["outcomes"], manifest["participants"]):
                if any(outcome[a] != b for a, b in (("portfolio_ref", peer["portfolio_ref"]), ("character_ref", peer["character_ref"]), ("snapshot_ref", snapshot_id), ("snapshot_hash", digest(snapshot)))):
                    raise ContractError("Paired consumers received different frozen evidence")
                if record["status"] == "abstained" and (outcome["action"] != "abstain" or outcome["reason"] != record["reason"]):
                    raise ContractError("Failure must apply equally to all paired consumers")
            if record["status"] == "decided" and (snapshot["status"] != "ready" or record["reason"] != "none" or utc(record["created_at"]) >= utc(manifest["decision_at"])):
                raise ContractError("Decisions were not committed by the frozen deadline")
            if record["model_calls"] is not None and record["model_calls"] > record["calls_reserved"] or record["model_tokens"] is not None and record["model_tokens"] > record["tokens_reserved"]:
                raise ContractError("Recorded Character usage exceeds its reservation")
            if record["status"] == "decided" and (record["model_calls"] is None or record["model_tokens"] is None):
                raise ContractError("Successful recorded decisions require known usage")
