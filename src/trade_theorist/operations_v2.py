"""Versioned private commands: saved evidence only, no account or serving transport."""
from contextlib import contextmanager
from importlib.resources import files
import json
import os
from pathlib import Path
import sqlite3

from .contracts import ContractError, digest, utc
from .storage_v2 import V2Store
from .export_v2 import build_private, export_private

DEMO_CUTOFF = "2099-01-13T21:00:00Z"
DEMO_RECEIPT = "command:operator-demo-v2-1"
DEMO_RECIPE = digest("private-dashboard-original-fixture-v2-1")


class Prerequisite(ContractError):
    def __init__(self, code, resume):
        super().__init__(code)
        self.code, self.resume = code, resume


def blocked(code, resume):
    return dict(status="blocked", projection_version=2, code=code, resume=resume)


def absolute_root(value, *, fixture, purpose):
    if not isinstance(value, (str, Path)) or not str(value) or not Path(value).expanduser().is_absolute():
        raise Prerequisite("missing_" + purpose, "Choose an absolute --data-root and --output-root (or their config fields).")
    root = Path(value).expanduser().resolve()
    if not fixture and any((p / ".git").exists() for p in (root, *root.parents)):
        raise Prerequisite("private_path_inside_git", "Choose private roots outside every Git checkout, then repeat the same command.")
    return root


def bundle_root(value, data_root, *, fixture):
    root = absolute_root(value, fixture=fixture, purpose="output_root")
    if data_root.is_relative_to(root):
        raise Prerequisite("bundle_contains_database", "Choose an --output-root that cannot contain the data root; use a separate sibling directory.")
    # A failed path check must not create directories. Resolve existing symlinks first.
    if root.exists() and not root.is_dir():
        raise Prerequisite("output_root_not_directory", "Choose a directory for --output-root and repeat export with the same cutoff.")
    return root


class ReadOnlyV2(V2Store):
    """One deferred SQLite snapshot; never initialize migrations or acquire a writer."""
    def __init__(self, root, *, synthetic=False):
        self.root, self.path, self.synthetic = root, root / "research.sqlite3", synthetic
        if not self.path.is_file():
            raise Prerequisite("missing_database", "Select an existing v2 data root. For the account-free example, run demo --projection-version 2 with a new dedicated root.")
        self.connection = sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        try:
            self.connection.execute("PRAGMA query_only=ON")
            self.connection.execute("BEGIN")
            tables = {r[0] for r in self.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "schema_migrations" not in tables:
                raise Prerequisite("missing_migrations", "Select a migrated v2 store. Do not relabel a v1 database; preview migrate-v2 --synthetic for a separate fixture copy.")
            installed = dict(self.connection.execute("SELECT version, content_hash FROM schema_migrations"))
            expected = {int(p.name.split('_')[0]): digest(p.read_text(encoding="utf-8")) for p in files("trade_theorist").joinpath("migrations").iterdir() if p.name.endswith(".sql")}
            if any(v not in expected or expected[v] != checksum for v, checksum in installed.items()):
                raise Prerequisite("migration_integrity", "Use the package version matching this database and review migration checksums before retrying; doctor never repairs or migrates it.")
            if not set(range(1, self.schema_ceiling + 1)) <= set(installed):
                raise Prerequisite("missing_migrations", "Migrations 001–004 are required. Use an explicitly reviewed V2Store initialization for an existing v2 store, or migrate-v2 --synthetic for a separate supported v1 fixture copy; then repeat doctor.")
        except BaseException:
            self.connection.close()
            raise

    @contextmanager
    def transaction(self):
        yield self.connection


def doctor(root, output=None, *, fixture=False, quota_root=None, quota_policy_path=None):
    """Inspect local prerequisites without writes, raw records or credential values."""
    from .request_operations import status as request_status
    requests = request_status(quota_root, quota_policy_path, fixture=fixture)
    try:
        root = absolute_root(root, fixture=fixture, purpose="data_root")
        destination = bundle_root(output, root, fixture=fixture) if output is not None else None
        with ReadOnlyV2(root, synthetic=fixture) as store:
            integrity = store.verify_v2()
            rights = list(store.iter_v2(kind="source_rights"))
            missing_rights = sum(any(r[k] != "permitted" for k in ("private_storage", "private_replay", "private_read_model")) for r in rights)
            reports = list(store.iter_v2(kind="performance_result"))
            latest = {}
            for r in reports:
                key = tuple(utc(r[k]) for k in ("effective_cutoff", "receipt_cutoff", "created_at"))
                if r["portfolio_id"] not in latest or key > latest[r["portfolio_id"]][0]:
                    latest[r["portfolio_id"]] = (key, r)
            paper = list(p for p in store.iter_v2(kind="portfolio") if p["execution_basis"] == "paper_broker")
            unreconciled = 0
            for p in paper:
                checks = list(store.iter_v2(portfolio_id=p["id"], kind="account_reconciliation"))
                last_check = max(checks, key=lambda r: (utc(r["observed_at"]), utc(r["effective_at"])), default=None)
                if last_check is None or last_check["status"] != "matched" or p["id"] not in latest or latest[p["id"]][1]["halted"] or latest[p["id"]][1]["gaps"]:
                    unreconciled += 1
            issues = []
            if not rights or missing_rights:
                issues.append(dict(code="missing_rights", resume="Record reviewed permissions for private storage, replay and read-model use on each source lineage; --fixture cannot grant rights."))
            if destination is None:
                issues.append(dict(code="missing_output_root", resume="Set private_bundle_root in config or pass an absolute --output-root before export."))
            if destination is not None and rights:
                original = all(r["origin"] == "original_synthetic" for r in rights)
                if not original and any((p / ".git").exists() for p in (destination, *destination.parents)):
                    issues.append(dict(code="private_path_inside_git", resume="Move the private bundle root outside Git; --fixture cannot override source provenance."))
            if not reports:
                issues.append(dict(code="missing_evaluation", resume="Register a funded v2 portfolio and accounting plan, then run evaluate --projection-version 2 --portfolio ID --as-of UTC with the same data root."))
            if unreconciled:
                issues.append(dict(code="reconciliation_incomplete", resume="Review saved broker updates, account checks and attribution using the offline reconciler, then evaluate again. Inspection remains available with explicit gaps; this does not authorize submissions."))
            if any(r[1]["gaps"] or r[1]["halted"] for r in latest.values()):
                issues.append(dict(code="accounting_gaps", resume="Inspect saved gap/halt evidence, record eligible marks or reconciliation evidence, and repeat evaluate at explicit cutoffs."))
            # Check the actual read model as well as the prerequisite inventory.
            if reports and not missing_rights and rights:
                try:
                    build_private(store, as_of=max(r["created_at"] for r in reports))
                except ContractError:
                    issues.append(dict(code="read_model_invalid", resume="Review source rights, projection lineage and saved evaluation integrity before repeating export. No raw evidence or exception text is printed."))
            hard = {"missing_rights", "missing_output_root", "private_path_inside_git", "read_model_invalid"}
            return dict(status="blocked" if any(i["code"] in hard for i in issues) else "ready_with_gaps" if issues else "ready",
                        projection_version=2, migrations="001–004 verified", records=integrity["records"], market_requests=requests,
                        rights_records=len(rights), rights_unresolved=missing_rights, saved_evaluations=len(reports), paper_portfolios=len(paper),
                        reconciliation_incomplete=unreconciled, issues=issues, account_calls=0, model_calls=0,
                        serving="Not started; use serve --projection-version 2 with both roots to validate and launch a fixed private snapshot.")
    except Prerequisite as exc:
        return blocked(exc.code, exc.resume) | dict(market_requests=requests)
    except (ContractError, sqlite3.Error, OSError, ValueError):
        return blocked("store_integrity", "Check local database access, migration integrity and the v2 record chain; restore verified evidence before repeating doctor. No database was repaired.") | dict(market_requests=requests)


def run_demo(root, output):
    """Seed atomically once, then export separately; retries reuse a verified receipt."""
    from .fixtures_dashboard_v2 import seed_dashboard
    from .adapters.trader_user_sim.v2 import SimulatorV2
    root = absolute_root(root, fixture=True, purpose="data_root")
    destination = bundle_root(output, root, fixture=True)
    if (root / "research.sqlite3").exists():
        with ReadOnlyV2(root, synthetic=True) as check:
            check.verify_v2()
    with V2Store(root, synthetic=True) as store:
        with store.transaction():
            receipt = next((r for r in store.iter_v2(kind="execution_command") if r["id"] == DEMO_RECEIPT), None)
            if receipt is None:
                if next(store.iter_v2(), None) is not None or store.connection.execute("SELECT 1 FROM records LIMIT 1").fetchone() or store.connection.execute("SELECT 1 FROM events LIMIT 1").fetchone():
                    raise Prerequisite("demo_root_in_use", "Choose a new dedicated fixture root. The demo cannot seed an existing research database.")
                portfolios = seed_dashboard(store)
                ids = list(portfolios.values())
                receipt = SimulatorV2(store, ids[0]).record("execution_command", DEMO_RECEIPT, DEMO_CUTOFF,
                    portfolio_id=ids[0], input_hash=DEMO_RECIPE, record_ids=ids, result_hash=digest(ids))
                store.put_v2([receipt])
            if receipt["input_hash"] != DEMO_RECIPE or digest(receipt["record_ids"]) != receipt["result_hash"]:
                raise Prerequisite("demo_recipe_changed", "Keep this evidence and choose a new dedicated fixture root for the current demo recipe.")
            store.verify_v2()
        report = export_private(store, destination, as_of=DEMO_CUTOFF)
        return dict(status="fixture_only", projection_version=2, report=str(report), portfolio=receipt["portfolio_id"],
                    as_of=DEMO_CUTOFF, account_calls=0, model_calls=0,
                    resume="Repeat demo with the same roots; committed seed and evaluations are reused. Use --serve for the protected loopback view.")


def operator_command(args, root, output, *, fixture):
    """Keep expected failures actionable, bounded and free of source/credential text."""
    phase = args.command
    try:
        if phase in {"ingest", "heartbeat"}:
            raise Prerequisite("v2_command_unavailable", "V2 ingest/heartbeat orchestration is not implemented. Use the documented v1 fixture command or saved v2 records through the production API; do not relabel v1 data.")
        if phase == "demo":
            root = root or str(Path(os.environ.get("LOCALAPPDATA", Path.home())) / "TradeTheorist" / "fixture-demo-v2")
            output = output or str(Path(root) / "private-bundle")
            if args.serve:
                from .private_bundle import checked_path
                from .local_server import validate_binding
                checked_path(output, outside_git=True)
                validate_binding("127.0.0.1", args.port)
            result = run_demo(root, output)
            if args.serve:
                from .local_server import serve
                serve(root, output, fixture=True, port=args.port)
        elif phase == "serve":
            if not root or not output:
                raise Prerequisite("missing_roots", "Pass absolute --data-root and --output-root (or configure both), then repeat serve --projection-version 2.")
            from .local_server import serve
            serve(root, output, fixture=fixture, host=args.host, port=args.port)
            return 0
        elif phase == "doctor":
            result = doctor(root, output, fixture=fixture, quota_root=args.quota_root, quota_policy_path=args.quota_policy)
        else:
            root = absolute_root(root, fixture=fixture, purpose="data_root")
            if not args.as_of:
                raise Prerequisite("missing_cutoff", "Pass --as-of with an explicit UTC timestamp; evaluate accepts --receipt-cutoff for restatement and defaults it to --as-of.")
            utc(args.as_of)
            if phase == "export":
                if args.experiment:
                    raise Prerequisite("unsupported_export_filter", "Omit --experiment: the v2 private bundle includes all permitted saved portfolios and their shared comparison evidence in this data root.")
                destination = bundle_root(output, root, fixture=fixture)
                with ReadOnlyV2(root, synthetic=fixture) as store:
                    report = export_private(store, destination, as_of=args.as_of)
                result = dict(status="exported", projection_version=2, report=str(report), visibility="private owner bundle; no server or publication started")
            elif phase == "evaluate":
                if not args.portfolio:
                    raise Prerequisite("missing_portfolio", "Pass --portfolio with a funded v2 portfolio ID and --as-of UTC. The v2 demo prints a reusable portfolio ID.")
                receipt_cutoff = args.receipt_cutoff or args.as_of
                utc(receipt_cutoff)
                with ReadOnlyV2(root, synthetic=fixture) as check:
                    check.verify_v2()
                    selected = check.v2_record(args.portfolio)
                    if selected["record_type"] != "portfolio" or (args.experiment and selected["experiment_id"] != args.experiment):
                        raise Prerequisite("portfolio_selection", "Select a v2 portfolio belonging to the requested experiment, then repeat evaluate.")
                from .evaluate.portfolio_v2 import evaluate
                with V2Store(root, synthetic=fixture) as store:
                    report = evaluate(store, args.portfolio, effective_cutoff=args.as_of, receipt_cutoff=receipt_cutoff)
                result = dict(status="evaluated", projection_version=2, report_id=report["id"], halted=report["halted"], gaps=len(report["gaps"]),
                              resume="Repeat evaluate with the same portfolio and cutoffs to reuse its result. Export with --as-of at or after the receipt cutoff.")
        print(json.dumps(result, indent=2))
        return 2 if result["status"] == "blocked" else 0
    except Prerequisite as exc:
        print(json.dumps(blocked(exc.code, exc.resume)))
        return 2
    except (ContractError, ValueError, OSError, sqlite3.Error):
        actions = {"demo": "Repeat demo --projection-version 2 with the same roots. Atomic seed work and saved evaluations are reused; fix output access if only export failed.",
                   "evaluate": "Run doctor --projection-version 2, check the selected portfolio, frozen plan, rights and cutoffs, then repeat evaluate with the same arguments.",
                   "export": "Run doctor --projection-version 2 with both roots. Resolve reported rights, migration or integrity blockers, check output access, then repeat export with the same cutoff.",
                   "serve": "Use 127.0.0.1 and an available port, an ordinary bundle directory outside Git, and its matching data root. Run doctor, re-export with the current package, then repeat serve --projection-version 2. No server started if validation failed."}
        print(json.dumps(dict(status="failed", projection_version=2, phase=phase, resume=actions.get(phase, "Repeat doctor --projection-version 2 with the same roots."))))
        return 1
