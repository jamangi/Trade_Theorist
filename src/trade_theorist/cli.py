"""Offline demo, explicit operating commands and resumable readiness blockers."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import sqlite3

from .contracts import ContractError, digest, migrate_v0_theory, validate, validate_bundle
from .fixtures import base_records, CHAR, CONSTITUTION, CURRICULUM, EXP, MATERIAL, SOURCE
from .learn import BoundedModel, Learner, RecordedProvider
from .learn.model import AmbiguousCall, UsageExhausted
from .learn.reviewed import foundation_status, specialist_status
from .library import AccessChecker, validate_catalog
from .inventory import inventory_summary, verify_files
from .logging import public_log
from .storage import Store, now


def operator_command(args):
    from .operations import doctor, run_demo, seed_demo, fixture_heartbeat, ingest_csv, FINAL_CUTOFF
    from .evaluate import Evaluator
    from .export import export_dashboard
    config = read(args.config) if args.config else {}
    if set(config) - {"schema_version", "data_root", "fixture", "policy_path"} or config.get("schema_version", 1) != 1:
        raise ContractError("Unsupported operating configuration")
    if not isinstance(config.get("fixture", False), bool):
        raise ContractError("Fixture flag must be boolean")
    root = args.data_root or config.get("data_root") or os.environ.get("TRADE_THEORIST_DATA_ROOT")
    fixture = args.fixture or config.get("fixture", False) or args.command == "demo"
    if args.command == "doctor":
        result = doctor(root, synthetic=fixture, policy_path=args.policy or config.get("policy_path"))
        print(json.dumps(result, indent=2))
        return 2 if result["status"] == "real_work_blocked" else 0
    if args.command == "demo":
        if root is None:
            root = str(Path(os.environ.get("LOCALAPPDATA", Path.home())) / "TradeTheorist" / "fixture-demo-v1")
        result = run_demo(root)
        print(json.dumps(result, indent=2), flush=True)
        if args.serve:
            from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
            public = (Path(root) / "public").resolve()
            class ReportHandler(SimpleHTTPRequestHandler):
                def __init__(self, *a, **kw):
                    super().__init__(*a, directory=str(public), **kw)
                def translate_path(self, path):
                    target = Path(super().translate_path(path)).resolve()
                    return str(target if target.is_relative_to(public) else public / "__not_allowed__")
            server = ThreadingHTTPServer(("127.0.0.1", args.port), ReportHandler)
            print(f"Local dashboard: http://127.0.0.1:{server.server_port}/", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
        return 0
    if root is None:
        print("Blocked: choose an absolute private data root with --data-root or TRADE_THEORIST_DATA_ROOT.")
        return 2
    with Store(root, synthetic=fixture) as store:
        if args.command == "heartbeat":
            if not fixture:
                print("Blocked: real heartbeat plans require eligible learning, a qualified source and a recorded paper policy. Run doctor; no live endpoint is available.")
                return 2
            setups = seed_demo(store)
            setup = next((s for s in setups if s["experiment"]["id"] == args.experiment or s["name"] == "demo-" + args.experiment), None)
            if setup is None or setup["role"] != "strategy":
                print("Blocked: select a registered demo strategy (council, index, value, trend or no-mail).")
                return 2
            try:
                output = fixture_heartbeat(store, setup)
            except (ContractError, ValueError, OSError):
                print("Heartbeat incomplete. Resume the same command with the same experiment and data root; committed phases are reused.", file=sys.stderr)
                return 1
            print(json.dumps({"status": "completed", "run_id": output["run_id"], "phases": len(output["phases"]), "next": "Run demo to observe fixture outcomes and export the dashboard"}))
        elif args.command == "ingest":
            if not all((args.csv, args.capability, args.sessions)):
                print("Blocked: provide --csv, --capability and --sessions for the permitted CSV adapter. No vendor endpoint is configured.")
                return 2
            capability = read(args.capability)
            if args.source not in (capability["source_id"], capability["feed"]):
                raise ContractError("Requested source differs from the capability record")
            print(json.dumps(ingest_csv(store, args.experiment, args.csv, capability, read(args.sessions)), indent=2))
        elif args.command == "evaluate":
            evaluator = Evaluator(store)
            trials = [e["payload"] for e in store.iter_events(args.experiment, "evaluation.trial")]
            if not trials:
                print("Blocked: preregister an evaluation trial and its session schedule before evaluating. Run the offline demo for fixture evidence.")
                return 2
            cutoff = args.as_of or (FINAL_CUTOFF if fixture else now())
            reports = [evaluator.evaluate(t["trial_id"], as_of=cutoff) for t in trials]
            print(json.dumps({"status": "evaluated", "reports": [r["report_id"] for r in reports], "next": "Run export with the same experiment and cutoff"}))
        elif args.command == "export":
            cutoff = args.as_of or (FINAL_CUTOFF if fixture else now())
            result = export_dashboard(store, store.root / "public", as_of=cutoff, experiment_id=args.experiment)
            print(json.dumps({"status": "exported", "report": str(result), "visibility": "local only; no publication performed"}))
    return 0


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def foundation_demo(root, outputs):
    provider = RecordedProvider(read(outputs))
    with Store(root, synthetic=True) as store:
        store.put_records(base_records())
        code_root = Path(__file__).parent
        code_hash = digest({p.relative_to(code_root).as_posix(): p.read_text(encoding="utf-8") for p in sorted(code_root.rglob("*.py"))})
        commit = subprocess.run(["git", "-c", f"safe.directory={Path.cwd().as_posix()}", "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip()
        store.append("provenance:" + digest([code_hash, commit]), EXP, "run.provenance", {"code_tree_hash": code_hash, "code_commit": commit or None, "package_version": "0.1.0", "recorded_outputs_hash": digest(provider.outputs), "note": "Base manifest is a contract specimen; this event pins actual executing code."})
        model = BoundedModel(store, EXP, provider, budget_id="budget:fixture-learning", model_id="recorded-fixture-v1", prompt_version="learning-v1", max_calls=2, max_tokens=100000, max_output_tokens=4000)
        learner = Learner(store, model)
        session = learner.freeze(character_version=CHAR, curriculum=CURRICULUM, constitution=CONSTITUTION, material=MATERIAL, source_id=SOURCE, position=1)
        first = learner.step(session, section_index=1)
        second = learner.step(session, section_index=2)
        output = {"status": "fixture_only", "real_character_status": "not_ready", "sections_completed": [first["section_index"], second["section_index"]], "real_books_read": 0, "new_recorded_responses": provider.calls, "memory_claims": len(second["consolidated_memory"]), "checkpoint_ids": [first["id"], second["id"]]}
        store.run_phase("run:foundation-fixture", EXP, "learn_summary", digest([first, second]), lambda _: output | {"new_recorded_responses": 0})
        output["integrity"] = store.verify()
        return output


def main(argv=None):
    parser = argparse.ArgumentParser(description="Trade Theorist offline observatory and operating tools")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("validate", help="Validate a record or a complete reference bundle")
    check.add_argument("path")
    migrate = commands.add_parser("migrate-theory", help="Explicitly migrate documented v0 theory to v1")
    migrate.add_argument("path")
    migrate.add_argument("output")
    demo = commands.add_parser("foundation-demo", help="Offline learning/storage fixture; no portfolio simulation")
    demo.add_argument("--data-root", required=True)
    demo.add_argument("--outputs", default="examples/learning/recorded-outputs.fixture.json")
    library = commands.add_parser("library")
    library.add_argument("action", choices=["report", "check", "verify-files"])
    library.add_argument("--catalog", help="Defaults to current inventory for report/verify-files, historical pilot for HTTP check")
    library.add_argument("--books-root", help="Local PDF directory; defaults to TRADE_THEORIST_BOOKS_ROOT")
    library.add_argument("--data-root")
    library.add_argument("--force", action="store_true")
    learn = commands.add_parser("learn", help="Inspect readiness or resume a permitted reviewed learning plan")
    learn.add_argument("--character", choices=["index_steward", "value_rationalist", "systematic_trend_operator"], required=True)
    learn.add_argument("--catalog", default="library/catalog/pilot.json")
    learn.add_argument("--character-dir")
    learn.add_argument("--plan", help="Reviewed learning plan with permitted records, material and recorded responses")
    learn.add_argument("--data-root")
    learn.add_argument("--fixture", action="store_true")
    for name in ("doctor", "demo", "ingest", "heartbeat", "evaluate", "export"):
        command = commands.add_parser(name)
        command.add_argument("--data-root")
        command.add_argument("--fixture", action="store_true", help="Use explicitly synthetic storage")
        command.add_argument("--config", help="Nonsecret operator configuration JSON")
        if name == "doctor":
            command.add_argument("--policy")
        if name == "demo":
            command.add_argument("--serve", action="store_true", help="Serve only the local public report on loopback")
            command.add_argument("--port", type=int, default=8765)
        if name in {"ingest", "heartbeat"}:
            command.add_argument("--experiment", required=True)
        if name in {"evaluate", "export"}:
            command.add_argument("--experiment")
            command.add_argument("--as-of")
        if name == "ingest":
            command.add_argument("--source", required=True)
            command.add_argument("--csv")
            command.add_argument("--capability")
            command.add_argument("--sessions")
    args = parser.parse_args(argv)
    try:
        if args.command in {"doctor", "demo", "ingest", "heartbeat", "evaluate", "export"}:
            return operator_command(args)
        if args.command == "validate":
            value = read(args.path)
            if isinstance(value, dict) and "redaction_policy" in value:
                from .export import validate_export
                validate_export(value)
                print("Valid allowlisted dashboard export and content hash.")
                return 0
            validate_bundle(value) if isinstance(value, list) else validate(value)
            print("Valid reference bundle." if isinstance(value, list) else "Valid record structure; use a bundle to check references.")
        elif args.command == "migrate-theory":
            migrated = migrate_v0_theory(read(args.path))
            with Path(args.output).open("x", encoding="utf-8") as output:
                output.write(json.dumps(migrated, indent=2) + "\n")
            print("Migrated to a new file; original retained.")
        elif args.command == "foundation-demo":
            print(json.dumps(foundation_demo(args.data_root, args.outputs), indent=2))
        elif args.command == "library":
            catalog = read(args.catalog or ("library/catalog/pilot.json" if args.action == "check" else "library/catalog/characters.json"))
            if catalog.get("catalog_type") == "local_book_inventory":
                if args.action == "report":
                    print(json.dumps(inventory_summary(catalog), indent=2))
                elif args.action == "verify-files":
                    root = args.books_root or os.environ.get("TRADE_THEORIST_BOOKS_ROOT")
                    if not root:
                        print("Set TRADE_THEORIST_BOOKS_ROOT or pass --books-root.", file=sys.stderr)
                        return 2
                    result = verify_files(catalog, root)
                    print(json.dumps(result, indent=2))
                    return 2 if any(f["status"] in ("missing", "changed") for f in result["files"]) else 0
                else:
                    print("Use verify-files for the local inventory; check is for publisher URLs in pilot.json.", file=sys.stderr)
                    return 2
                return 0
            if args.action == "verify-files":
                print("verify-files requires the local inventory catalog.", file=sys.stderr)
                return 2
            validate_catalog(catalog)
            if args.action == "report":
                print(json.dumps({"scope": "pilot_publisher_candidates_and_frozen_bogle_source", "current_inventory": "library/catalog/characters.json", "slots": len(catalog["assignments"]), "sources": len(catalog["sources"]), "review_queue": catalog["review_queue"]}, indent=2))
            else:
                with Store(args.data_root) as store:
                    checker = AccessChecker(store)
                    for source in catalog["sources"]:
                        result = checker.check(source, force=args.force)
                        print(json.dumps({"source_id": source["id"], "checked_at": result["checked_at"], "cached": result["cached"], "status": result["result"]["status"], "review_reasons": result.get("review_reasons", [])}))
                    print(json.dumps({"review_queue": checker.review_queue()}))
        elif args.command == "learn":
            if args.plan:
                from .operations import learn_plan
                print(json.dumps(learn_plan(args.plan, args.data_root, synthetic=args.fixture, expected_character=args.character), indent=2))
                return 0
            character_dir = args.character_dir or f"characters/{args.character}"
            if args.character != "index_steward":
                print(json.dumps(specialist_status(character_dir), indent=2))
                return 2
            catalog = read(args.catalog)
            index = validate_catalog(catalog)
            slot = next(s for s in catalog["assignments"] if s["character_id"] == args.character and s["position"] == 1)
            source = index[slot["source_id"]]
            if (Path(character_dir) / "checkpoints/bogle-2017-completion.json").exists():
                print(json.dumps(foundation_status(character_dir, source["id"]), indent=2))
                return 0
            print(json.dumps({"character": args.character, "status": "not_ready", "source_id": source["id"], "reason": source["blocker"] or "Register permitted source material and a reviewed model adapter through the learning API; no real model provider is configured."}, indent=2))
            return 2
    except (ContractError, ValueError, OSError, sqlite3.Error, AmbiguousCall, UsageExhausted):
        print(public_log("operation_failed"), file=sys.stderr)
        print("Check the named input and prerequisites with doctor, then repeat the same command and data root. Saved successful work is retained.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
