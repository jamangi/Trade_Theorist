from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sqlite3
import subprocess
import sys
import unittest

from trade_theorist.contracts import ContractError, digest
from trade_theorist.fixtures import base_records, EXP as V1_EXP
from trade_theorist.fixtures_v2 import bundle, record, event, PORT, SEG, AT
from trade_theorist.migrate_v2 import migrate, identity
from trade_theorist.storage import Store
from trade_theorist.storage_v2 import V2Store
from trade_theorist.adapters.trader_user_sim import State, VERSION


class V2StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = V2Store(self.root / "v2", synthetic=True)
        self.addCleanup(self.store.close)

    def test_explicit_migration_and_unchanged_v1_tables(self):
        path = self.root / "old"
        with Store(path, synthetic=True) as old:
            old.put_records(base_records())
            old.append("event:old", V1_EXP, "fixture.cash", {"amount": "10.00"}, created_at=AT)
            before = old.verify()
            hashes = list(map(tuple, old.connection.execute("SELECT * FROM schema_migrations")))
            self.assertEqual([r[0] for r in hashes], [1, 2])
        with Store(path, synthetic=True) as old:
            self.assertEqual(list(map(tuple, old.connection.execute("SELECT * FROM schema_migrations"))), hashes)
        with V2Store(path, synthetic=True) as new:
            self.assertEqual(new.verify()["v1"], before)
            self.assertEqual(list(map(tuple, new.connection.execute("SELECT * FROM schema_migrations WHERE version<3"))), hashes)
        with V2Store(path, synthetic=True) as reopened:
            self.assertEqual(reopened.connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0], V2Store.schema_ceiling)

    def test_atomic_bundles_hashes_identity_and_immutable_rows(self):
        records = bundle()
        self.store.put_v2(records)
        before = self.store.verify_v2()
        self.store.put_v2(records)
        self.assertEqual(self.store.verify_v2(), before)
        changed = deepcopy(records[-1]); changed["remaining_basis"] = "1"
        with self.assertRaises(ContractError): self.store.put_v2([changed])
        with self.assertRaises(sqlite3.IntegrityError): self.store.connection.execute("DELETE FROM v2_records")
        with self.assertRaises(RuntimeError):
            with self.store.transaction():
                self.store.put_v2([event("event:halt", 6, "halt", reason="fixture")])
                raise RuntimeError("interrupt")
        self.assertEqual(self.store.verify_v2(), before)
        with self.assertRaises(ContractError): self.store.put_records(records)

    def test_process_crash_rolls_back_v2(self):
        self.store.put_v2(bundle())
        before = self.store.verify_v2()
        script = """import os, sys
from trade_theorist.storage_v2 import V2Store
from trade_theorist.fixtures_v2 import event
with V2Store(sys.argv[1], synthetic=True) as s:
    with s.transaction():
        s.put_v2([event('event:crash', 6, 'halt', reason='fixture')])
        os._exit(9)
"""
        result = subprocess.run([sys.executable, "-c", script, str(self.store.root)], capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 9, result.stderr)
        self.assertEqual(self.store.verify_v2(), before)

    def test_mappings_require_monarchy_and_atomic_outbox(self):
        self.store.put_v2(bundle())
        with self.assertRaises(ContractError): self.store.prepare_submission("order:v2-buy", at=AT)
        self.assertEqual(list(self.store.iter_v2(kind="submission_mapping")), [])
        with V2Store(self.root / "paper", synthetic=True) as paper:
            paper.put_v2(bundle(mode="council", basis="paper_broker"))
            mapping = paper.prepare_submission("order:v2-buy", at=AT)
            self.assertRegex(mapping["client_order_id"], r"^[0-9a-f]{32}$")
            before = paper.verify_v2()
            self.assertEqual(paper.prepare_submission("order:v2-buy", at=AT), mapping)
            self.assertEqual(paper.verify_v2(), before)
            for key, value in (("client_order_id", "character:internal-name"), ("client_order_id", "1" * 32)):
                bad = dict(mapping, id="mapping:duplicate"); bad[key] = value
                outbox = list(paper.iter_v2(kind="outbox"))[0]
                outbox.update(id="outbox:duplicate", mapping_id=bad["id"])
                with self.assertRaises(ContractError): paper.put_v2([bad, outbox])
            self.assertEqual(paper.verify_v2(), before)
            outbox = list(paper.iter_v2(kind="outbox"))[0]
            unknown = dict(outbox, id="outbox:unknown", revision=2, previous_outbox_id=outbox["id"], state="unknown")
            paper.put_v2([unknown])
            with self.assertRaises(ContractError):
                paper.put_v2([dict(unknown, id="outbox:retry", revision=3, previous_outbox_id=unknown["id"], state="prepared")])

    def test_broker_updates_quarantine_conflicts_and_keep_partial_fills(self):
        self.store.put_v2(bundle(mode="council", basis="paper_broker"))
        mapping = self.store.prepare_submission("order:v2-buy", at=AT)
        def update(name, quantity, minute, status="partially_filled", broker="opaque-fixture-broker"):
            at = f"2099-01-01T21:{minute:02d}:00Z"
            return dict(record("broker_update", "update:" + name, portfolio_id=PORT, segment_id=SEG,
                mapping_id=mapping["id"], provider_event_id="provider:" + name, broker_order_id=broker,
                effective_at=at, observed_at=at, cumulative_quantity=quantity, cumulative_notional=f"{int(quantity)*100}.00",
                cumulative_fees=f"{quantity}.00", incremental_fill_id="fill:" + name if quantity != "0" else None, status=status), created_at=at)
        later = update("later", "2", 2, "filled")
        earlier = update("earlier", "1", 1)
        self.assertEqual(self.store.record_update(later), "accepted")
        self.assertEqual(self.store.record_update(earlier), "accepted")
        before = self.store.verify_v2()
        self.assertEqual(self.store.record_update(earlier), "accepted")
        self.assertEqual(self.store.verify_v2(), before)
        for bad in (dict(earlier, cumulative_fees="9.00"), update("decreasing", "1", 3), update("excess", "3", 3),
                    update("replacement", "2", 3, broker="unknown-replacement"), dict(update("unknown", "1", 3), mapping_id="mapping:unknown")):
            self.assertEqual(self.store.record_update(bad), "quarantined")
        self.assertEqual(self.store.verify_v2(), before)
        self.assertEqual(self.store.connection.execute("SELECT COUNT(*) FROM v2_quarantine").fetchone()[0], 5)
        cancel = update("cancel", "2", 3, "cancelled"); cancel["incremental_fill_id"] = None
        self.assertEqual(self.store.record_update(cancel), "accepted")
        self.assertEqual(len(list(self.store.iter_v2(kind="broker_update"))), 3)

    def test_duplicate_event_keys_and_sequence_fail(self):
        self.store.put_v2(bundle())
        first = event("event:halt", 6, "halt", reason="fixture")
        self.store.put_v2([first])
        for change in (dict(id="event:duplicate", sequence=7), dict(id="event:duplicate", idempotency_key="event:duplicate")):
            with self.assertRaises(ContractError): self.store.put_v2([dict(first, **change)])

    def test_newer_database_and_modified_installed_migration_refused(self):
        self.store.connection.execute("INSERT INTO schema_migrations VALUES (99,'newer')")
        with self.assertRaises(ContractError): V2Store(self.store.root, synthetic=True)
        self.store.connection.execute("DELETE FROM schema_migrations WHERE version=99")
        self.store.connection.execute("UPDATE schema_migrations SET content_hash='changed' WHERE version=3")
        with self.assertRaises(ContractError): V2Store(self.store.root, synthetic=True)


SOURCE_AT = "2099-01-03T21:00:00Z"


class SyntheticMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = Store(self.root / "source", synthetic=True); self.addCleanup(self.source.close)
        self.source.put_records(base_records())
        self.source.append("event:v1-funding", V1_EXP, "simulation", dict(version=VERSION, portfolio_id="portfolio:fixture-council",
            type="funding", at=SOURCE_AT, amount="10000.00"), created_at=SOURCE_AT)

    def test_dry_run_apply_preserves_hashes_replay_and_duplicate_lineage(self):
        before = self.source.verify()
        old_state = self.source.replay(V1_EXP, lambda state, e: (state.apply(e["payload"]) or state), State())
        target = self.root / "destination"
        preview = migrate(self.source.path, synthetic=True, destination=target)
        self.assertFalse(target.exists())
        self.assertEqual(len(preview["converted_event_ids"]), 1)
        result = migrate(self.source.path, synthetic=True, destination=target, apply=True)
        self.assertEqual(result["action"], "applied")
        self.assertEqual(self.source.verify(), before)
        with V2Store(target, synthetic=True) as converted:
            self.assertEqual(converted.verify()["v1"], before)
            state = State()
            for e in converted.iter_events(V1_EXP): state.apply(e["payload"])
            self.assertEqual(vars(state), vars(old_state))
            self.assertEqual(list(converted.iter_v2(kind="lot")), [])
            self.assertEqual(list(converted.iter_v2(kind="projection")), [])
            initial = converted.verify()
        self.assertEqual(migrate(self.source.path, synthetic=True, destination=target, apply=True)["action"], "already_applied")
        with V2Store(target, synthetic=True) as converted: self.assertEqual(converted.verify(), initial)
        self.source.append("event:new-history", V1_EXP, "fixture.cash", {}, created_at=SOURCE_AT)
        with self.assertRaises(ContractError): migrate(self.source.path, synthetic=True, destination=target, apply=True)

    def test_unconvertible_and_missing_observed_time_produce_gaps(self):
        self.source.append("event:v1-unknown-lots", V1_EXP, "simulation", dict(version=VERSION, portfolio_id="portfolio:fixture-council",
            type="mark", at=SOURCE_AT, instrument_id="instrument:fixture-fund", price="100", session="2099-01-01", phase="close"), created_at=SOURCE_AT)
        result = migrate(self.source.path, synthetic=True, destination=self.root / "gaps", apply=True)
        self.assertEqual(result["converted_event_ids"], [])
        self.assertEqual(len(result["gaps"]), 2)
        with V2Store(self.root / "gaps", synthetic=True) as converted:
            self.assertEqual(list(converted.iter_v2(kind="portfolio"))[0]["initialization"], "conversion_gap")
            self.assertEqual(list(converted.iter_v2(kind="ledger_event")), [])

    def test_average_cost_sale_replay_is_preserved_without_fifo_relabel(self):
        for n, (side, quantity, notional, fee) in enumerate((("buy", "2", "200.00", "2.00"), ("buy", "2", "240.00", "2.00"), ("sell", "1", "130.00", "1.00"))):
            oid = f"order:legacy-{n}"
            common = dict(version=VERSION, portfolio_id="portfolio:fixture-council", at=SOURCE_AT, session="2099-01-01", order_id=oid)
            self.source.append(f"event:order-{n}", V1_EXP, "simulation", dict(common, type="order", order=dict(instrument_id="instrument:fixture-fund", side=side, quantity=quantity, reserved="0")), created_at=SOURCE_AT)
            self.source.append(f"event:fill-{n}", V1_EXP, "simulation", dict(common, type="fill", notional=notional, fee=fee), created_at=SOURCE_AT)
        def replay(s):
            state = State()
            for e in s.iter_events(V1_EXP, "simulation"): state.apply(e["payload"])
            return state
        before = replay(self.source)
        self.assertEqual(str(before.realized), "18.00")  # Average basis 111; FIFO would be 101/realized 28.
        self.assertEqual(str(before.basis["instrument:fixture-fund"]), "333.00")
        report = migrate(self.source.path, synthetic=True, destination=self.root / "traded", apply=True)
        self.assertEqual(report["converted_event_ids"], [])
        with V2Store(self.root / "traded", synthetic=True) as copied:
            self.assertEqual(vars(replay(copied)), vars(before))
            self.assertEqual(list(copied.iter_v2(kind="lot")), [])

    def test_cli_preview_and_schema_export(self):
        from contextlib import redirect_stdout, redirect_stderr
        from io import StringIO
        from trade_theorist.cli import main
        output = StringIO()
        with redirect_stdout(output), redirect_stderr(StringIO()):
            self.assertEqual(main(["migrate-v2", "--source", str(self.source.path), "--synthetic"]), 0)
        self.assertEqual(json.loads(output.getvalue())["action"], "dry_run")
        path = self.root / "schema.json"
        with redirect_stdout(StringIO()): self.assertEqual(main(["export-v2-schema", str(path)]), 0)
        self.assertIn("$defs", json.loads(path.read_text()))

    def test_apply_rollback_and_source_safety(self):
        target = self.root / "destination"
        before = self.source.verify()
        def fail(_): raise RuntimeError("Simulated interrupted migration")
        with self.assertRaises(RuntimeError): migrate(self.source.path, synthetic=True, destination=target, apply=True, before_commit=fail)
        self.assertFalse((target / "research.sqlite3").exists())
        self.assertEqual(self.source.verify(), before)
        migrate(self.source.path, synthetic=True, destination=target, apply=True)
        for options in ({}, {"synthetic": True, "apply": True, "destination": self.source.root}):
            with self.assertRaises(ContractError): migrate(self.source.path, **options)

    def test_unknown_source_version_refused_without_touching_source(self):
        self.source.connection.execute("INSERT INTO schema_migrations VALUES (99,'future')")
        with self.assertRaises(ContractError): migrate(self.source.path, synthetic=True)
        self.assertEqual(self.source.connection.execute("SELECT content_hash FROM schema_migrations WHERE version=99").fetchone()[0], "future")

    def test_untyped_old_funding_without_time_becomes_gap(self):
        with Store(self.root / "missing-time", synthetic=True) as old:
            old.put_records(base_records())
            old.append("event:missing-time", V1_EXP, "simulation", dict(version=VERSION,
                portfolio_id="portfolio:fixture-council", type="funding", amount="10000.00"), created_at=SOURCE_AT)
            report = migrate(old.path, synthetic=True)
            self.assertEqual(report["converted_event_ids"], [])
            self.assertEqual(report["gaps"], [dict(source_id="event:missing-time", code="requires_accounting_replay")])


if __name__ == "__main__": unittest.main()
