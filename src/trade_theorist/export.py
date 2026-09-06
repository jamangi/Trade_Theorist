"""Fixture-only v1 dashboard exports; private real-data exports require the v2 path.

Even a report without raw bars can reconstruct prices from holdings value/quantity.
The old public-summary format is therefore restricted to original synthetic stores.
"""

from importlib.resources import files
import json
import os
from pathlib import Path
import tempfile
import re
import shutil

from jsonschema import Draft202012Validator

from .contracts import ContractError, canonical, digest, utc
from .evaluate import Evaluator
from .schema import S, ID, HASH, UTC, N, BOOL, SIGNED, obj, array, nullable, enum

METRIC = obj(value=nullable(SIGNED), reason=nullable(S), unit=S)
EVIDENCE = obj(id=ID, kind=S, label=S, visibility=enum("fixture", "private"), details=array(S))
ANSWER = obj(question=S, answer=S, evidence_ids=array(ID))
CARD = obj(
    report_id=ID, trial_id=ID, experiment_id=ID, portfolio_id=ID, label=S, mode=S, role=S, regime=S,
    evidence_grade=S, owner_version=ID, readiness=S, advice=S, horizon=S, as_of=UTC, window_start=UTC, window_end=UTC,
    equity=nullable(SIGNED), initial_cash=SIGNED, cash=SIGNED, reserved=SIGNED, fees=SIGNED, income=SIGNED, halted=BOOL,
    metrics=obj(net_return=METRIC, max_drawdown=METRIC, turnover=METRIC, hit_rate=METRIC, worst_session=METRIC,
                daily_volatility=METRIC, gross_exposure=METRIC, brier=METRIC), cash_baseline=METRIC, index_baseline=METRIC,
    history=array(obj(session=S, equity=nullable(SIGNED), drawdown=nullable(SIGNED), reason=nullable(S))),
    holdings=array(obj(symbol=S, quantity=SIGNED, value=nullable(SIGNED), sector=S)),
    decisions=array(obj(id=ID, at=UTC, author=S, action=S, quantity=SIGNED, outcome=S)),
    advice_log=array(obj(id=ID, kind=S, status=S)),
    forecasts=obj(matured=N, pending=N, unscorable=N), fills=N, abstentions=N, trial_count=N,
    learning=obj(checkpoints=N, statement=S), answers=array(ANSWER, 6), evidence_ids=array(ID),
    review_blockers=array(S), limitations=array(S), operating_cost=METRIC, heartbeat_status=S,
)
DASHBOARD_SCHEMA = obj(schema_version={"const": 1}, build_id=HASH, content_hash=HASH, generated_at=UTC,
    redaction_policy={"const": "public-summary-v1"}, source_run_ids=array(ID),
    versions=array(obj(id=HASH, as_of=UTC, cards=array(CARD)), 1), evidence=array(EVIDENCE),
    comparisons=array(obj(no_mail=ID, mail=ID, regime=S, difference=METRIC, interpretation=S)),
    roster=array(obj(name=S, status=S, note=S)),
    registry=array(obj(trial_id=ID, experiment_id=ID, role=S, status=S)), notice=S)

QUESTIONS = [
    "What did this Character believe at the time?",
    "Which sources and reasoning steps produced that belief?",
    "What evidence would have changed its mind?",
    "What action or abstention did it recommend using then-available information?",
    "How did the decision perform after costs and against fair baselines?",
    "Is the apparent edge stable out of sample, or explained by luck, leakage or hidden risk?",
]
LABELS = {"trial:demo-council": "Council", "trial:demo-index": "Index Steward", "trial:demo-value": "Value Rationalist",
          "trial:demo-trend": "Systematic Trend Operator", "trial:demo-no-mail": "Council · no mail",
          "trial:demo-baseline": "Broad-market buy and hold", "trial:demo-counterfactual": "Rejected-decision portfolio"}


def validate_export(value):
    errors = list(Draft202012Validator(DASHBOARD_SCHEMA).iter_errors(value))
    if errors:
        raise ContractError("Invalid public export at " + "/".join(map(str, errors[0].path)))
    if any(e["visibility"] != "fixture" for e in value["evidence"]):
        raise ContractError("The v1 export supports synthetic fixtures only; private evidence is denied")
    unhashed = {k: v for k, v in value.items() if k != "content_hash"}
    if digest(unhashed) != value["content_hash"]:
        raise ContractError("Public export hash mismatch")
    evidence_ids = {e["id"] for e in value["evidence"]}
    if len(evidence_ids) != len(value["evidence"]):
        raise ContractError("Duplicate public evidence identity")
    for version in value["versions"]:
        for card in version["cards"]:
            if card["regime"] != "fixture" or card["evidence_grade"] != "fixture":
                raise ContractError("The v1 export supports synthetic fixtures only; real results remain private")
            if len(card["answers"]) != 6 or any(i not in evidence_ids for a in card["answers"] for i in a["evidence_ids"]):
                raise ContractError("Six answers must reference existing allowlisted evidence")
            if card["evidence_grade"] == "forward-reviewed" and card["review_blockers"]:
                raise ContractError("Blocked evidence cannot be forward reviewed")
            for m in [*card["metrics"].values(), card["cash_baseline"], card["index_baseline"], card["operating_cost"]]:
                if (m["value"] is None) == (m["reason"] is None):
                    raise ContractError("Every metric needs a value or an explicit null reason")
    return value


def build_dashboard(store, *, as_of, experiment_id=None):
    if not store.synthetic:
        raise ContractError("The v1 export supports synthetic fixtures only; private export integration is pending")
    # Check persisted provenance too: reopening a real store with --fixture is not
    # permission to publish it. Stream the records instead of loading source books.
    for row in store.connection.execute("SELECT body FROM records"):
        record = json.loads(row[0])
        if record["contamination"] != "fixture":
            raise ContractError("The v1 export rejects stores containing non-fixture records")
        if record["record_type"] == "observation" and record["feed"] != "synthetic-v1":
            raise ContractError("The v1 export rejects non-synthetic observation feeds")
        if record["record_type"] == "experiment" and (record["regime"] != "fixture" or record["data_feeds"] != ["synthetic-v1"]):
            raise ContractError("The v1 export rejects non-synthetic experiments")
    reports = [e["payload"] for e in store.iter_events(kind="evaluation.report")
               if utc(e["created_at"]) <= utc(as_of) and (experiment_id is None or e["experiment_id"] == experiment_id)]
    reports = list({(r["trial_id"], r["as_of"]): r for r in reports}.values())
    if not reports:
        raise ContractError("No saved evaluation reports; run evaluate first")
    evidence, versions = {}, {}
    def add(identifier, kind, label, details, fixture):
        evidence[identifier] = dict(id=identifier, kind=kind, label=label,
                                    visibility="fixture" if fixture else "private", details=details if fixture else ["Restricted provenance. Inspect the saved record in private storage."])
        return identifier
    for report in reports:
        if report["evidence_grade"] != "fixture" or report["regime"] != "fixture":
            raise ContractError("The v1 export rejects non-fixture evaluation reports")
        fixture = report["evidence_grade"] == "fixture"
        cutoff = report["as_of"]
        character = store.record(report["owner_version"], "character")
        exp = store.record(report["experiment_id"], "experiment")
        decisions = [store.record(i, "recommendation") for i in report["decision_ids"]]
        latest = decisions[-1] if decisions else None
        ids = [add(character["id"], "character", "Frozen Character version",
                   ["Version: " + character["version"], "Constitution hash: " + character["constitution_hash"], "Curriculum hash: " + character["curriculum_hash"]], fixture)]
        for rec in decisions:
            ids.append(add(rec["id"], "recommendation", "Saved recommendation",
                       ["Action: " + rec["action"], "Quantity: " + rec["quantity"], "Created: " + rec["created_at"], "Snapshot: " + rec["snapshot_id"]], fixture))
            snapshot = store.record(rec["snapshot_id"], "snapshot")
            ids.append(add(snapshot["id"], "snapshot", "Frozen information cutoff", ["Cutoff: " + snapshot["cutoff"], "Content hash: " + snapshot["content_hash"]], fixture))
            for citation in rec["citations"]:
                source = store.record(citation["source_id"], "source")
                allowed = fixture and source["publication_eligibility"] in {"raw_permitted", "derived_permitted"}
                ids.append(add(source["id"], "source", "Source provenance", ["Original project arithmetic fixture; no book text", "Edition: " + source["edition"]], allowed))
        ids.append(add(report["report_id"], "evaluation", "Saved after-cost evaluation",
                       ["Cutoff: " + cutoff, "Evidence: " + report["evidence_grade"], report["calculation"]], fixture))
        checkpoints = []
        for row in store.connection.execute("SELECT body FROM records WHERE record_type='checkpoint' AND experiment_id=?", (exp["id"],)):
            c = json.loads(row[0])
            if c["character_version"] == character["id"] and utc(c["created_at"]) <= utc(cutoff):
                checkpoints.append(c)
                ids.append(add(c["id"], "checkpoint", "Frozen learning checkpoint", ["Reading status: " + c["reading_status"], "Source IDs: " + ", ".join(c["source_ids"])], fixture))
        mail = [e for e in store.iter_events(exp["id"]) if e["kind"].startswith("mail.") and utc(e["created_at"]) <= utc(cutoff)
                and "reflection" not in e["kind"]]
        # Event identities/statuses are useful provenance; never copy mail or thought bodies.
        for e in mail:
            ids.append(add(e["id"], "mail_event", "Saved deliberation event", ["Event: " + e["kind"], "Recorded: " + e["created_at"]], fixture))
        considered = {i for e in mail if e["kind"] == "mail.final_committed" for i in e["payload"]["considered_message_ids"]}
        advice_log = []
        for e in mail:
            if e["kind"] == "mail.authored":
                message = store.record(e["payload"]["message_id"], "message")
                status = "Considered in final decision" if message["id"] in considered else "Unresolved objection" if message["kind"] == "objection" else "Recorded; not cited in final decision"
                advice_log.append(dict(id=e["id"], kind=message["kind"], status=status))
        statement = "No learned belief is claimed by these scripted fixtures." if fixture else "Belief text is retained privately; inspect the frozen Character and theory versions."
        texts = [
            statement + (" The last saved stance was " + latest["action"] + " at " + latest["created_at"] + "." if latest else " No recommendation was recorded."),
            "Source and checkpoint identities are preserved. " + ("These opinions use original arithmetic fixtures, not source-trained reasoning." if fixture else "Restricted source locators and authored rationale remain in private storage."),
            ("Fixture invalidation: the frozen context changes. Objections remain recorded; adviser mail does not override policy." if fixture else "Preregistered invalidation and objection records remain available for private inspection."),
            (f"Recommended {latest['action']} of {latest['quantity']} units. " if latest else "No action recorded. ") +
                ("Fixture inputs only; not a real investment recommendation." if fixture else "Historical availability restrictions do not remove possible pretrained-model contamination." if exp["regime"] in {"hindsight", "historical_restricted"} else "Decision and snapshot clocks are preserved; outcomes are evaluated only after availability."),
            "Returns include trading costs and distributions once. Compare the separately funded cash and index baselines; missing outcomes remain unavailable. A rejected trade's later price move is not a portfolio return.",
            f"Insufficient evidence of a stable edge: {report['forecasts']['matured']} matured forecasts, {len(report['history'])} sessions, {report['trial_count']} registered trials. " + " ".join(report["review_blockers"]),
        ]
        evidence_groups = [[character["id"]], [i for i in ids if evidence[i]["kind"] in {"source", "checkpoint"}],
                           [latest["id"]] + [a["id"] for a in advice_log if a["kind"] == "objection"] if latest else [],
                           [i for i in ids if evidence[i]["kind"] in {"recommendation", "snapshot"}],
                           [report["report_id"]], [report["report_id"]]]
        answers = [dict(question=q, answer=a, evidence_ids=list(dict.fromkeys(group))) for q, a, group in zip(QUESTIONS, texts, evidence_groups)]
        model_costs = []
        for row in store.connection.execute("SELECT body FROM records WHERE record_type='model_call' AND experiment_id=?", (exp["id"],)):
            c = json.loads(row[0])
            if utc(c["created_at"]) <= utc(cutoff):
                model_costs.append(c["usage"]["cost_usd"])
        from .evaluate import metric
        from decimal import Decimal
        operating_cost = metric(sum((Decimal(c) for c in model_costs), Decimal(0)), unit="USD") if all(c is not None for c in model_costs) else metric(reason="Model charge is unavailable", unit="USD")
        phases = [e for e in store.iter_events(exp["id"], "phase.complete") if utc(e["created_at"]) <= utc(cutoff)]
        failed = [e for e in store.iter_events(exp["id"], "phase.failed") if utc(e["created_at"]) <= utc(cutoff)]
        heartbeat_status = "Completed" if any(e["kind"] == "heartbeat.released" and utc(e["created_at"]) <= utc(cutoff) for e in store.iter_events(exp["id"])) else "Failed or partial; resume saved run" if failed else "Partial" if phases else "No heartbeat; mechanical simulation"
        outcomes, order_decisions = {}, {}
        for e in store.iter_events(exp["id"], "simulation", portfolio_id=report["portfolio_id"]):
            if utc(e["created_at"]) > utc(cutoff):
                continue
            p = e["payload"]
            if p["type"] == "order":
                order_decisions[p["order_id"]] = p["order"]["decision_id"]
                outcomes[p["order"]["decision_id"]] = "Pending next eligible event"
            elif p["type"] == "fill":
                outcomes[order_decisions[p["order_id"]]] = "Filled after independent policy checks"
            elif p["type"] == "cancellation":
                outcomes[order_decisions[p["order_id"]]] = "Cancelled: " + p["reason"]
            elif p["type"] == "rejection" and p.get("decision_id"):
                outcomes[p["decision_id"]] = "Governor rejected: " + ", ".join(p["reasons"])
        for e in phases:
            for check in e["payload"].get("output", {}).get("checks", []):
                if check["status"] == "rejected":
                    outcomes[check["recommendation_id"]] = "Governor rejected: " + ", ".join(check["reasons"])
        card = {k: report[k] for k in ("report_id", "trial_id", "experiment_id", "portfolio_id", "mode", "role", "regime", "evidence_grade", "owner_version", "advice", "as_of", "window_start", "window_end", "equity", "initial_cash", "cash", "reserved", "fees", "income", "halted", "metrics", "cash_baseline", "index_baseline", "fills", "abstentions", "trial_count", "review_blockers", "limitations")}
        card.update(label=LABELS.get(report["trial_id"], character["character_id"].replace("_", " ").title()),
                    readiness=character["readiness"], horizon="One fixture session" if fixture else "See private preregistration",
                    history=[{k: p[k] for k in ("session", "equity", "drawdown", "reason")} for p in report["history"]],
                    holdings=[{k: h[k] for k in ("symbol", "quantity", "value", "sector")} for h in report["holdings"]],
                    decisions=[dict(id=r["id"], at=r["created_at"], author=store.record(r["character_version"], "character")["character_id"].replace("_", " "), action=r["action"], quantity=r["quantity"],
                                    outcome=outcomes.get(r["id"], "Abstained or waited" if r["action"] in {"wait", "abstain"} else "Unexecuted opinion")) for r in decisions], advice_log=advice_log,
                    forecasts={k: report["forecasts"][k] for k in ("matured", "pending", "unscorable")},
                    learning=dict(checkpoints=len(checkpoints), statement="Fixture learning only; zero real books completed here" if fixture else "Learning state is tied to this frozen Character version"),
                    answers=answers, evidence_ids=list(dict.fromkeys(ids)), operating_cost=operating_cost, heartbeat_status=heartbeat_status)
        reviews = [e for e in store.iter_events(exp["id"], "evaluation.owner_review") if e["payload"]["report_id"] == report["report_id"] and utc(e["created_at"]) <= utc(as_of)]
        if reviews and not report["review_blockers"]:
            card["evidence_grade"] = "forward-reviewed"
        versions.setdefault(cutoff, {})[report["trial_id"]] = card
    version_list = [dict(id=digest([cutoff, list(cards.values())]), as_of=cutoff, cards=list(cards.values())) for cutoff, cards in sorted(versions.items())][-20:]
    comparisons = []
    ev = Evaluator(store)
    latest_reports = [r for r in reports if r["as_of"] == version_list[-1]["as_of"] and r["role"] == "strategy"]
    for left in latest_reports:
        for right in latest_reports:
            if left["advice"] == "none" and right["advice"] == "bounded" and left["comparison_hash"] == right["comparison_hash"]:
                comparisons.append(ev.compare_advice(left, right))
    public = dict(schema_version=1, build_id=digest([r["report_id"] for r in reports]), generated_at=as_of,
                  redaction_policy="public-summary-v1", source_run_ids=sorted({i for r in reports for i in r["source_run_ids"]}),
                  versions=version_list, evidence=list(evidence.values()), comparisons=comparisons,
                  roster=[dict(name=name, status="not_ready", note="No portfolio or results seeded for this fixture") for name in
                          ("Mean-Reversion Researcher", "Microstructure Specialist", "Risk Skeptic", "Event Analyst")],
                  registry=ev.registry(as_of=as_of), notice="Scripted engineering fixtures only. No real performance, promotion, live trading or model call occurs in this dashboard." if all(r["evidence_grade"] == "fixture" for r in reports) else "Evidence regimes remain separate. This read-only report does not authorize promotion or trading.")
    public["content_hash"] = digest(public)
    return validate_export(public)


def export_dashboard(store, destination, *, as_of, experiment_id=None, before_publish=None):
    public = build_dashboard(store, as_of=as_of, experiment_id=experiment_id)
    root = Path(destination).resolve()
    root.mkdir(parents=True, exist_ok=True)
    # Content-addressed assets make the final single-file handoff atomic.
    asset_root = files("trade_theorist").joinpath("dashboard")
    assets = {name: asset_root.joinpath(name).read_text(encoding="utf-8") for name in ("index.html", "style.css", "app.js")}
    assets["schema.json"] = json.dumps(DASHBOARD_SCHEMA, ensure_ascii=False)
    version_id = digest([public["content_hash"], assets])
    version = root / "versions" / version_id
    if not version.resolve().is_relative_to(root):
        raise ContractError("Export path escapes the public root")
    version.mkdir(parents=True, exist_ok=True)
    for name, content in {**assets, "report.json": json.dumps(public, ensure_ascii=False, indent=2) + "\n"}.items():
        target = version / name
        if not target.resolve().is_relative_to(root):
            raise ContractError("Export asset escapes the public root")
        if target.exists() and target.read_text(encoding="utf-8") != content:
            raise ContractError("Immutable export version content changed")
        target.write_text(content, encoding="utf-8", newline="\n")
    (version / "export.json").write_text(json.dumps({"owner": "trade-theorist-public-v1", "version": version_id}), encoding="utf-8")
    if before_publish:
        before_publish()
    entry = assets["index.html"].replace("<!--BASE-->", f'<base href="versions/{version_id}/">')
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=root, delete=False, suffix=".tmp") as temp:
        temp.write(entry)
        temporary = Path(temp.name)
    try:
        os.replace(temporary, root / "index.html")
    finally:
        temporary.unlink(missing_ok=True)
    owned = []
    for candidate in (root / "versions").iterdir():
        if not re.fullmatch(r"[a-f0-9]{64}", candidate.name) or candidate.is_symlink() or not candidate.is_dir():
            continue
        marker = candidate / "export.json"
        try:
            if marker.is_file() and not marker.is_symlink() and json.loads(marker.read_text(encoding="utf-8")).get("owner") == "trade-theorist-public-v1":
                owned.append(candidate)
        except (OSError, ValueError):
            continue  # Unrecognized or inaccessible files are never retention targets.
    keep = {version, *sorted((p for p in owned if p != version), key=lambda p: p.stat().st_mtime_ns, reverse=True)[:19]}
    for candidate in owned:
        if candidate not in keep:
            resolved = candidate.resolve()
            if not resolved.is_relative_to((root / "versions").resolve()) or any(p.is_symlink() or p.is_dir() for p in candidate.iterdir()):
                continue
            if {p.name for p in candidate.iterdir()} <= {"index.html", "style.css", "app.js", "schema.json", "report.json", "export.json"}:
                try:
                    shutil.rmtree(resolved)
                except OSError:
                    pass  # A retention failure must not invalidate a published report.
    return root / "index.html"
