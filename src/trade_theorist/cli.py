"""Small foundation interface; portfolio heartbeat/demo arrive in later tasks."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from .contracts import ContractError, digest, migrate_v0_theory, validate, validate_bundle
from .fixtures import base_records, CHAR, CONSTITUTION, CURRICULUM, EXP, MATERIAL, SOURCE
from .learn import BoundedModel, Learner, RecordedProvider
from .learn.model import AmbiguousCall, UsageExhausted
from .learn.reviewed import foundation_status
from .library import AccessChecker, validate_catalog
from .inventory import inventory_summary, verify_files
from .logging import public_log
from .storage import Store, now


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
    parser = argparse.ArgumentParser(description="Trade Theorist foundation tools")
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
    learn = commands.add_parser("learn", help="Show real Character readiness; use Python API for permitted source inputs")
    learn.add_argument("--character", choices=["index_steward"], required=True)
    learn.add_argument("--catalog", default="library/catalog/pilot.json")
    learn.add_argument("--character-dir", default="characters/index_steward")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            value = read(args.path)
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
            catalog = read(args.catalog)
            index = validate_catalog(catalog)
            slot = next(s for s in catalog["assignments"] if s["character_id"] == args.character and s["position"] == 1)
            source = index[slot["source_id"]]
            if (Path(args.character_dir) / "checkpoints/bogle-2017-completion.json").exists():
                print(json.dumps(foundation_status(args.character_dir, source["id"]), indent=2))
                return 0
            print(json.dumps({"character": args.character, "status": "not_ready", "source_id": source["id"], "reason": source["blocker"] or "Register permitted source material and a reviewed model adapter through the learning API; no real model provider is configured."}, indent=2))
            return 2
    except (ContractError, ValueError, OSError, AmbiguousCall, UsageExhausted):
        print(public_log("operation_failed"), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
