"""Owner-authorized, bounded private daily SIP qualification. Never prints prices/keys."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time

from trade_theorist.adapters.alpaca_market_data import quality_report
from trade_theorist.adapters.alpaca_market_data.transport import SingleAttemptTransport
from trade_theorist.contracts import digest
from trade_theorist.ingest.market import CSVMarketAdapter, Normalized, RevisionBook, SessionCalendar
from trade_theorist.market_requests import Coordinator, query, stamp
from trade_theorist.request_contracts import policy


REPO = Path(__file__).resolve().parents[1]


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".pending")
    with temporary.open("w", encoding="utf-8") as out:
        json.dump(value, out, indent=2); out.write("\n"); out.flush(); os.fsync(out.fileno())
    temporary.replace(path)


def credentials():
    # Read only the configured names, without executing dotenv text or printing it.
    values = {}
    for line in (REPO / ".env").read_text(encoding="utf-8-sig").splitlines():
        name, separator, value = line.partition("=")
        if separator and name.strip() in {"APCA_API_KEY_ID", "APCA_API_SECRET_KEY", "APCA_API_BASE_URL"}:
            values[name.strip()] = value.strip().strip("\"'")
    if values.get("APCA_API_BASE_URL", "").rstrip("/") != "https://paper-api.alpaca.markets":
        raise ValueError("Expected configured paper credentials")
    return values["APCA_API_KEY_ID"], values["APCA_API_SECRET_KEY"]


def operating_policy():
    return policy(quota_id="quota:alpaca-owner-market-data", max_work_attempts=8, max_retries=1,
        max_wait_seconds=120, entitlement_ref="review:basic-delayed-sip",
        feed_delays=dict(iex=0, sip=1200), sharing_scopes=["scope:owner-private-research"],
        rights_ref="rights:owner-private-local-2026-09-07")


def manifest(plan, now):
    deadline = stamp(now + 600)
    q = dict(schema_version=1, record_type="market_query", provider="alpaca", endpoint="stock_bars",
        sharing_scope="scope:owner-private-research", rights_ref="rights:owner-private-local-2026-09-07",
        symbols=plan["symbols"], feed="sip", timeframe="1Day", adjustment="raw", asof=plan["asof"],
        start=plan["start"], end=plan["end"], expected_sessions=plan["expected_sessions"], page_limit=7,
        revision_policy="revision:retain-receipts", freshness_after=stamp(now), information_cutoff=deadline)
    return dict(started_at=stamp(now), deadline=deadline, plan_hash=digest(plan), queries=[q], budgets=[8, 4])


def measure(owner, wire, plan, capability, state_dir):
    state_path = state_dir / "manifest.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else manifest(plan, time.time())
    if state["plan_hash"] != digest(plan): raise ValueError("Frozen sample plan changed")
    save(state_path, state)
    attempt_path = state_dir / "transport-attempts.json"
    prior_attempts = json.loads(attempt_path.read_text()) if attempt_path.exists() else []
    baseline = state.setdefault("starting_accounted_attempts", owner.usage()["physical_attempts"])
    save(state_path, state)
    observations_file = state_dir / "normalized.json"
    restored = [Normalized(**item) for item in json.loads(observations_file.read_text())] if observations_file.exists() else []
    book = RevisionBook(restored)
    normalizer = CSVMarketAdapter(experiment_id="experiment:step-09-qualification", contamination="historical-qualified",
        universe=[dict(instrument_id="instrument:" + s.lower(), symbol=s, asset_class="unleveraged_us_etf", sector="Broad Market") for s in plan["symbols"]],
        calendar=SessionCalendar("nyse-step-09-ten-sessions", tuple(plan["expected_sessions"])),
        capability=capability, revision_book=book)
    report = dict(report_kind="step-09-account-quality-workload", started_at=state["started_at"],
        status="blocked", runs=[], orders=0, external_model_calls=0, promotion_eligible=False,
        configured_operating_limit=180, configured_hard_limit=200, maximum_sample_attempts=12,
        cooperating_callers_only=True, outside_account_traffic="unknown")
    for index in range(2):
        if index == len(state["queries"]):
            state["queries"].append(state["queries"][0] | dict(page_limit=100, freshness_after=stamp(time.time())))
            save(state_path, state)
        q = state["queries"][index]
        work = owner.submit(q, consumer="step-09-private-qualification", max_attempts=state["budgets"][index], deadline=state["deadline"])
        initial = owner.run(work, max_pages=1)
        checkpoint = owner.resume(work)
        save(state_dir / f"resume-{index + 1}.json", checkpoint)
        usage = owner.run(work, resume=checkpoint, value=q)
        save(attempt_path, prior_attempts + wire.observed_attempts())
        if owner.usage()["physical_attempts"] - baseline > 12: raise ValueError("Sample exceeded combined budget")
        if usage["status"] != "complete":
            report["blocked_reason"] = usage["reason"]
            report["runs"].append(dict(usage=usage)); break
        accepted, bad = owner.normalize(work, normalizer)
        duplicated, bad_repeat = owner.normalize(work, normalizer)
        save(observations_file, [asdict(item) for item in book.records()])
        # Grade this download, not the union with a prior query that could hide a gap.
        separate = CSVMarketAdapter(experiment_id=normalizer.experiment_id, contamination=normalizer.contamination,
            universe=list(normalizer.universe.values()), calendar=normalizer.calendar, capability=capability)
        current, current_bad = owner.normalize(work, separate)
        quality = quality_report(feed="sip", expected_sessions=plan["expected_sessions"],
            expected_instruments=tuple("instrument:" + s.lower() for s in plan["symbols"]),
            normalized=current, quarantine=current_bad, sample_kind="authorized_account")
        before = owner.usage()["physical_attempts"]
        same = owner.submit(q, consumer="step-09-cache-check", max_attempts=state["budgets"][index], deadline=state["deadline"])
        cached = owner.run(same)
        extra = owner.usage()["physical_attempts"] - before
        report["runs"].append(dict(initial_status=initial["status"], usage=usage, quality=quality.as_dict(),
            accepted_normalized=len(accepted), duplicate_normalized=len(duplicated), quarantined=len(bad) + len(bad_repeat),
            exact_query_added_attempts=extra, resume_bound=checkpoint == owner.resume(work), cached_status=cached["status"]))
        if quality.coverage_status != "qualified" or bad or bad_repeat or duplicated or extra:
            report["blocked_reason"] = "quality_or_idempotence"; break
    report["physical_attempts"] = owner.usage()["physical_attempts"] - baseline
    if len(report["runs"]) == 2 and "blocked_reason" not in report:
        # Replay both saved downloads after restoring the persisted revision book.
        restored = RevisionBook([Normalized(**item) for item in json.loads(observations_file.read_text())])
        normalizer.revisions = restored
        replay_added = replay_bad = 0
        for q in state["queries"]:
            work = owner.submit(q, consumer="step-09-restored-replay", max_attempts=8, deadline=state["deadline"])
            items, bad = owner.normalize(work, normalizer); replay_added += len(items); replay_bad += len(bad)
        report["restored_replay_added_observations"] = replay_added
        report["restored_replay_quarantined"] = replay_bad
        # Count changed economic bars independently from receipt/provenance revisions.
        windows = []
        for q in state["queries"]:
            work = "work:" + digest(query(q))
            windows.append({(o["bar"]["symbol"], o["bar"]["t"]): o["bar"] for o in owner.evidence(work)})
        report["changed_bar_pairs"] = sum(windows[0].get(k) != v for k, v in windows[1].items())
        report["status"] = "qualified_scoped_daily_bars" if replay_added == replay_bad == 0 else "blocked"
        if replay_added or replay_bad: report["blocked_reason"] = "restored_replay_not_idempotent"
    report["completed_at"] = stamp(time.time())
    report["normalized_records"] = len(book.records())
    save(state_dir / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, default=Path(os.environ["LOCALAPPDATA"]) / "TradeTheorist" / "alpaca-market-data")
    args = parser.parse_args()
    root = args.private_root.resolve()
    if any((p / ".git").exists() for p in (root, *root.parents)): raise ValueError("Private state must remain outside Git")
    plan = json.loads((REPO / "examples/step-09/sample-plan.json").read_text())
    capability = json.loads((REPO / "examples/step-09/source-capability.alpaca-conditional.json").read_text())
    if not capability["storage_retention"] or not capability["internal_replay"]: raise ValueError("Private-use decision not recorded")
    wire = SingleAttemptTransport(*credentials())
    dispatches = []
    def audit(event, args):
        if event == "http.client.send" and getattr(args[0], "host", None) == "data.alpaca.markets" and args[1].startswith(b"GET /v2/stocks/bars?"):
            dispatches.append(dict(at=time.monotonic(), utc=stamp(time.time())))
    sys.addaudithook(audit)
    dispatch_path = root / "step-09/wire-dispatches.json"
    prior = json.loads(dispatch_path.read_text()) if dispatch_path.exists() else []
    try:
        with Coordinator(root, operating_policy(), wire) as owner:
            save(root / "policy.json", owner.policy)
            result = measure(owner, wire, plan, capability, root / "step-09")
    finally:
        if root.exists(): save(dispatch_path, prior + dispatches)
    print(json.dumps(dict(status=result["status"], physical_attempts=result["physical_attempts"],
        actual_http_dispatches_this_process=len(dispatches), runs=len(result["runs"]), orders=0)))
    return 0 if result["status"] == "qualified_scoped_daily_bars" else 1


if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        # Error messages may contain network configuration; retain only the class.
        print("Qualification stopped: " + type(exc).__name__)
        raise SystemExit(1)
