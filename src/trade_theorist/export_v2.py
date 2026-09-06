"""Allowlisted private owner read model. Reads saved evidence; never runs an agent."""
from copy import deepcopy
from decimal import Decimal as D
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from .contracts import ContractError, digest, utc
from .contracts_v2 import REFS
from .export import ANSWER, EVIDENCE, QUESTIONS
from .schema import S, ID, HASH, UTC, N, BOOL, SIGNED, obj, array, nullable, enum
from .schema_v2 import FIELDS, VALUE, PRECISE
from .evaluate.portfolio_v2 import number
from .adapters.trader_user_sim.v2 import SimulatorV2

# Performance values are copied by name, never by serializing an operational record.
PERFORMANCE_FIELDS = tuple(k for k in FIELDS["performance_result"] if k not in {
    "source_event_ids", "source_chain_hash", "accounting_plan_id", "publication_class", "baseline_result_hash", "operating_expense_ids"})
PERFORMANCE = obj(**{k: FIELDS["performance_result"][k] for k in PERFORMANCE_FIELDS})
CONTEXT_FIELDS = tuple(k for k in FIELDS["inspection_context"] if k not in {"portfolio_id", "segment_id", "character_version", "as_of"})
CONTEXT = obj(**{k: FIELDS["inspection_context"][k] for k in CONTEXT_FIELDS})
LOT = obj(id=ID, instrument_id=ID, acquired_at=UTC, quantity=SIGNED, basis=PRECISE, average_basis=nullable(SIGNED))
RELIEF = obj(id=ID, lot_id=ID, sale_id=ID, quantity=SIGNED, basis=PRECISE, proceeds=PRECISE, fees=PRECISE)
FLOW = obj(id=ID, at=UTC, kind=S, amount=SIGNED)
MARK = obj(id=ID, instrument_id=ID, event_at=UTC, received_at=UTC, feed=S, adjustment=S, revision=N, status=S, reason=nullable(S))
CARD = obj(report_id=ID, label=S, regime=S, role=S, character_id=ID, readiness=S, window_start=UTC, window_end=UTC,
    performance=PERFORMANCE, context=CONTEXT, lots=array(LOT), reliefs=array(RELIEF), flows=array(FLOW), marks=array(MARK),
    decisions=array(obj(id=ID, at=UTC, action=S, instrument_id=ID, quantity=SIGNED, outcome=S)),
    reconciliation=obj(status=S, differences=array(S)), answers=array(ANSWER, 6), evidence_ids=array(ID),
    source_hash=HASH, exposure=VALUE, matched_control_ids=array(ID))
PRIVATE_SCHEMA = obj(schema_version={"const": 2}, publication_class={"const": "private-owner-v2"},
    build_id=HASH, content_hash=HASH, generated_at=UTC, source_record_ids=array(ID), notice=S,
    versions=array(obj(id=HASH, as_of=UTC, receipt_cutoff=UTC, cards=array(CARD))), evidence=array(EVIDENCE),
    roster=array(obj(id=ID, name=S, version=S, readiness=S, note=S)))


def validate_private(report):
    errors = list(Draft202012Validator(PRIVATE_SCHEMA, format_checker=FormatChecker()).iter_errors(report))
    if errors: raise ContractError("Invalid private read model at " + "/".join(map(str, errors[0].path)))
    from .private_bundle import reject_private_text
    reject_private_text(report)
    if digest({k: v for k, v in report.items() if k != "content_hash"}) != report["content_hash"]:
        raise ContractError("Private report hash mismatch")
    evidence = {e["id"] for e in report["evidence"]}
    if len(evidence) != len(report["evidence"]): raise ContractError("Duplicate private evidence")
    for version in report["versions"]:
        for card in version["cards"]:
            p = card["performance"]
            if p["effective_cutoff"] != version["as_of"] or p["receipt_cutoff"] != version["receipt_cutoff"]:
                raise ContractError("Historical cutoffs differ")
            if len(card["answers"]) != 6 or any(i not in evidence for a in card["answers"] for i in a["evidence_ids"]):
                raise ContractError("Six answers require included evidence")
            if not set(card["evidence_ids"]) <= evidence: raise ContractError("Missing card evidence")
            for metric in [card["exposure"], card["context"]["forecasts"]["brier"], *p.values()]:
                if isinstance(metric, dict) and set(metric) == {"value", "reason", "unit"} and (metric["value"] is None) != (metric["reason"] is not None):
                    raise ContractError("Metric needs a value or explicit reason")
    return report


def missing_context(character):
    return dict(label=character["character_id"].replace("character:", "").replace("_", " "), horizon="Not registered",
        advice="none", belief=None, rationale=None, invalidation=None,
        learning_statement="No saved learning summary for this frozen version; readiness is not inferred from returns",
        learning_completed=0, learning_total=0, source_citations=[], advice_log=[],
        forecasts=dict(matured=0, pending=0, unscorable=0, brier=dict(value=None, reason="No saved forecast review", unit="ratio")),
        abstentions=0, heartbeat_status="no_data", last_successful_heartbeat=None)


def build_private(store, *, as_of):
    """Validate lineage, then select browser fields. No writes, model or broker calls."""
    with store.transaction():
        store.verify_v2()
        evidence, used, checked = {}, {}, set()
        def read(identifier):
            record = store.v2_record(identifier)
            if identifier in checked: return record
            checked.add(identifier)
            rights = store.v2_record(record["provenance"]["rights_id"])
            if any(rights[k] != "permitted" for k in ("private_storage", "private_replay", "private_read_model")):
                raise ContractError("Source rights do not permit this private read model")
            used[identifier] = digest(record); used[rights["id"]] = digest(rights)
            # Walk known typed references and source lineage, retaining only IDs/hashes.
            def walk(value):
                if isinstance(value, dict):
                    for key, item in value.items():
                        if key in REFS and item is not None:
                            for ref in item if isinstance(item, list) else [item]: read(ref)
                        elif key == "source_event_ids":
                            for ref in item: read(ref)
                        elif key != "provenance": walk(item)
                elif isinstance(value, list):
                    for item in value: walk(item)
            walk(record)
            for ref in record["provenance"]["source_event_ids"]: read(ref)
            return record
        def add(record, label, details, *, key=None):
            read(record["id"])
            key = key or record["id"]
            evidence[key] = dict(id=key, kind=record["record_type"], label=label,
                visibility="fixture" if record["contamination"] == "fixture" else "private", details=list(dict.fromkeys(details)))
            return key
        versions, control_keys = {}, {}
        saved = [r for r in store.iter_v2(kind="performance_result") if utc(r["created_at"]) <= utc(as_of)]
        for report in saved:
            report = read(report["id"])
            pid, sid = report["portfolio_id"], report["segment_id"]
            portfolio = read(pid); character = read(portfolio["owner_character_version"])
            exp = read(portfolio["experiment_id"])
            # A saved gap projection has no result hash: independently check its
            # monetary values against read-only replay as well as the source hash.
            state, _ = SimulatorV2(store, pid).state(effective_cutoff=report["effective_cutoff"], receipt_cutoff=report["receipt_cutoff"])
            if any(report[k] != number(v) for k,v in (("cash",state.cash),("fifo_basis",state.basis),("reserved",state.reserved),("realized",state.realized),("income",state.income))) or report["equity"]["value"] != number(state.equity()):
                raise ContractError("Saved private values differ from replay")
            projections = [p for p in store.iter_v2(portfolio_id=pid, kind="projection") if p["segment_id"] == sid and p["revision"] == report["projection_revision"]]
            if len(projections) != 1: raise ContractError("Private result needs one matching projection")
            projection = read(projections[0]["id"])
            events = [read(i) for i in report["source_event_ids"]]
            if digest(events) != report["source_chain_hash"] or projection["source_chain_hash"] != report["source_chain_hash"] or projection["effective_cutoff"] != report["effective_cutoff"] or projection["receipt_cutoff"] != report["receipt_cutoff"]:
                raise ContractError("Private projection lineage mismatch")
            if projection["result_hash"] is not None and projection["result_hash"] != digest(report):
                raise ContractError("Private result differs from its projection")
            contexts = [r for r in store.iter_v2(portfolio_id=pid, kind="inspection_context") if r["segment_id"] == sid and utc(r["as_of"]) <= utc(report["effective_cutoff"]) and utc(r["created_at"]) <= utc(report["receipt_cutoff"])]
            context = max(contexts, key=lambda r: (utc(r["as_of"]), utc(r["created_at"]))) if contexts else None
            info = {k: deepcopy(read(context["id"])[k]) for k in CONTEXT_FIELDS} if context else missing_context(character)
            ids = [add(character, "Frozen Character version", ["Version: " + character["version"], "Constitution hash: " + character["constitution_hash"], "Curriculum hash: " + character["curriculum_hash"], "Readiness: " + character["readiness"]]),
                add(report, "Saved accounting result", ["Effective: " + report["effective_cutoff"], "As known: " + report["receipt_cutoff"], "Source hash: " + report["source_chain_hash"], *report["definitions"]])]
            if context:
                ids.append(add(context, "Saved authored research context", ["Saved: " + context["created_at"], info["learning_statement"], *[f'{c["title"]} · {c["edition"]} · {c["locator"]}' for c in info["source_citations"]]]))
            # Lot revisions are tied to a report's ID by the production projector.
            lots, reliefs = [], []
            for lot in store.iter_v2(portfolio_id=pid, kind="lot"):
                if lot["id"] != "lot-revision:" + digest([lot["lot_id"], report["id"]]): continue
                read(lot["id"])
                lots.append(dict(id=lot["id"], instrument_id=lot["instrument_id"], acquired_at=lot["acquired_at"], quantity=lot["remaining_quantity"], basis=lot["remaining_basis"], average_basis=number(D(lot["remaining_basis"]) / D(lot["remaining_quantity"])) if D(lot["remaining_quantity"]) else None))
            lot_ids = {l["id"] for l in lots}
            for relief in store.iter_v2(portfolio_id=pid, kind="lot_relief"):
                if relief["lot_revision_id"] not in lot_ids: continue
                read(relief["id"])
                reliefs.append(dict(id=relief["id"], lot_id=relief["lot_revision_id"], sale_id=relief["sale_fill_id"], quantity=relief["quantity"], basis=relief["allocated_basis"], proceeds=relief["proceeds"], fees=relief["disposal_fees"]))
            # Display effective events after correction chains, preserving receipt selection.
            replaced = {e["payload"]["corrects_id"]: e["payload"]["replacement_id"] for e in events if e["event_type"] == "correction"}
            active = [e for e in events if e["id"] not in replaced and e["event_type"] != "correction" and e["segment_id"] == sid]
            flows, marks, decisions = [], {}, []
            outcomes = {o["order_id"]: o for o in report["order_outcomes"]}
            for event in sorted(active, key=lambda e: (utc(e["effective_at"]), e["sequence"])):
                p, kind = event["payload"], event["event_type"]
                if kind in {"funding", "contribution", "withdrawal"}:
                    flows.append(dict(id=event["id"], at=event["effective_at"], kind=kind, amount=p["amount"]))
                elif kind == "mark":
                    marks[p["instrument_id"]] = dict(id=event["id"], instrument_id=p["instrument_id"], event_at=p["event_at"], received_at=p["received_at"], feed=p["feed"], adjustment=p["adjustment"], revision=p["observation_revision"], status=p["status"], reason=p["reason"])
                elif kind == "order":
                    order = read(p["order_id"]); decision = read(order["final_recommendation_id"])
                    outcome = outcomes.get(order["id"])
                    text = "Pending execution" if not outcome else f'{outcome["status"]}: filled {outcome["filled_quantity"]}; remaining {outcome["remaining_quantity"]}'
                    decisions.append(dict(id=decision["id"], at=decision["created_at"], action=decision["side"], instrument_id=decision["instrument_id"], quantity=decision["quantity"], outcome=text))
                    ids.append(add(decision, "Then-available decision", ["Created: " + decision["created_at"], "Snapshot hash: " + decision["snapshot_hash"], "Action: " + decision["side"], text]))
            plan = read(report["accounting_plan_id"])
            if plan["baseline_portfolio_id"]:
                read(plan["baseline_portfolio_id"])
                for source in store.iter_v2(portfolio_id=plan["baseline_portfolio_id"]):
                    if source["record_type"] == "accounting_plan" or (source["record_type"] in {"ledger_event", "operating_expense"} and utc(source["effective_at"]) <= utc(report["effective_cutoff"]) and utc(source["created_at"]) <= utc(report["receipt_cutoff"])):
                        read(source["id"])
            control_keys[report["id"]] = digest([exp["instrument_ids"],
                {k: plan[k] for k in ("mark_schedule", "max_mark_age_seconds", "execution_model", "fee_per_share", "slippage_bps", "spread_bps", "fractional_shares", "corporate_actions")},
                read(portfolio["policy_id"])["limits"], character["character_id"], character["version"], character["constitution_hash"], character["curriculum_hash"],
                [{k: read(d["id"])[k] for k in ("created_at", "snapshot_hash", "instrument_id", "side", "quantity")} for d in decisions]])
            # The reducer resolves withdrawn marks and multiple correction chains.
            marks = {key: dict(id=state.mark_ids[key], instrument_id=key, event_at=p["event_at"], received_at=p["received_at"], feed=p["feed"], adjustment=p["adjustment"], revision=p["observation_revision"], status=p["status"], reason=p["reason"]) for key,p in state.marks.items()}
            for mark in marks.values():
                if (utc(report["effective_cutoff"]) - utc(mark["event_at"])).total_seconds() > plan["max_mark_age_seconds"]:
                    mark.update(status="stale", reason="Older than the frozen mark policy permits")
                mark["id"] = add(read(mark["id"]), "Mark provenance", ["Market time: " + mark["event_at"], "Received: " + mark["received_at"], "Status at report cutoff: " + report["effective_cutoff"], mark["feed"], mark["status"], mark["reason"] or "Eligible under the frozen mark policy"], key="mark-evidence:" + digest([report["id"], mark["id"]]))
                ids.append(mark["id"])
            reconciliation = dict(status="Offline simulated ledger" if portfolio["execution_basis"] == "simulated" else "No aggregate account check saved", differences=list(report["gaps"]))
            checks = [r for r in store.iter_v2(portfolio_id=pid, kind="account_reconciliation") if utc(r["effective_at"]) <= utc(report["effective_cutoff"]) and utc(r["observed_at"]) <= utc(report["receipt_cutoff"])]
            if checks:
                check = read(max(checks, key=lambda r: utc(r["observed_at"]))["id"])
                reconciliation = dict(status=check["status"], differences=list(dict.fromkeys(check["differences"] + report["gaps"])))
                ids.append(add(check, "Account reconciliation status", [check["status"], *check["differences"]]))
            answers = [info["belief"] or "Not yet known: no saved dated belief is attached to this frozen version.",
                info["rationale"] or "Not yet known: source-linked authored rationale has not been saved.",
                info["invalidation"] or "Not yet known: no preregistered invalidation is attached.",
                (f'{decisions[-1]["action"]} {decisions[-1]["quantity"]} units; {decisions[-1]["outcome"]}.' if decisions else "No trade recommendation recorded; this is not evidence of an authored abstention.") + " Historical availability does not rule out model contamination. Horizon: " + info["horizon"],
                "Trading TWR includes execution fees; operating costs are separate. Inspect cash, lots, flows and matched baselines below. " + report["benchmark_status"],
                "Insufficient evidence of a stable edge. " + "; ".join(report["review_blockers"])]
            nav = report["equity"]["value"]
            exposure = dict(value=number((D(nav)-D(report["cash"])-D(report["receivables"])) / D(nav)) if nav is not None and D(nav)>0 else None, reason=None if nav is not None and D(nav)>0 else "No positive eligible equity", unit="ratio")
            card = dict(report_id=report["id"], label=info["label"], regime=exp["regime"], role=portfolio["role"], character_id=character["character_id"], readiness=character["readiness"],
                window_start=exp["start_at"], window_end=exp["end_at"], performance={k: deepcopy(report[k]) for k in PERFORMANCE_FIELDS}, context=info,
                lots=lots, reliefs=reliefs, flows=flows, marks=list(marks.values()), decisions=decisions, reconciliation=reconciliation,
                answers=[dict(question=q, answer=a, evidence_ids=ids[:3] if i<3 else ids) for i,(q,a) in enumerate(zip(QUESTIONS,answers))], evidence_ids=ids,
                source_hash=report["source_chain_hash"], exposure=exposure, matched_control_ids=[])
            versions.setdefault((report["effective_cutoff"], report["receipt_cutoff"]), []).append(card)
        version_list = []
        for (effective, receipt), cards in sorted(versions.items()):
            for card in cards:
                p = card["performance"]
                # This is an identified control, never a cross-basis return ranking.
                card["matched_control_ids"] = [c["performance"]["portfolio_id"] for c in cards if c["role"] == "matched_control" and control_keys[c["report_id"]] == control_keys[card["report_id"]] and c["performance"]["mode"] == p["mode"] and c["regime"] == card["regime"] and c["window_start"] == card["window_start"] and c["window_end"] == card["window_end"] and c["performance"]["flow_signature"] == p["flow_signature"] and c["performance"]["execution_basis"] == "simulated"] if p["execution_basis"] == "paper_broker" else []
            version_list.append(dict(id=digest([effective,receipt,[c["report_id"] for c in cards]]), as_of=effective, receipt_cutoff=receipt, cards=cards))
        roster = []
        for character in store.iter_v2(kind="character"):
            if utc(character["created_at"]) > utc(as_of): continue
            read(character["id"])
            roster.append(dict(id=character["id"], name=character["character_id"], version=character["version"], readiness=character["readiness"], note="Frozen readiness; a missing portfolio is not a zero return"))
        report = dict(schema_version=2, publication_class="private-owner-v2", generated_at=as_of,
            build_id=digest(used), source_record_ids=sorted(used), versions=version_list, evidence=list(evidence.values()), roster=roster,
            notice="Private owner inspection · saved evidence only. Execution bases and information regimes remain separate; no promotion or account action.")
        report["content_hash"] = digest(report)
        return validate_private(report)


def export_private(store, destination, *, as_of, before_publish=None, retain=20):
    report = build_private(store, as_of=as_of)
    root = Path(destination).resolve()
    # Source origin, never the caller's fixture flag, controls repository output.
    original = all(store.v2_record(i)["contamination"] == "fixture" and store.v2_record(store.v2_record(i)["provenance"]["rights_id"])["origin"] == "original_synthetic" for i in report["source_record_ids"])
    if not original and any((p / ".git").exists() for p in (root, *root.parents)):
        raise ContractError("Real private bundles must be outside Git")
    from .private_bundle import publish
    return publish(report, destination, before_publish=before_publish, keep=retain)
