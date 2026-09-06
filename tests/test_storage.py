from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from trade_theorist.contracts import ContractError, digest
from trade_theorist.fixtures import base_records, EXP
from trade_theorist.logging import public_log
from trade_theorist.storage import Store, private_root


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name, synthetic=True)
        self.addCleanup(self.store.close)
        self.store.put_records(base_records())

    def test_replay_dedup_and_backup_restore(self):
        for number, amount in enumerate(("0.10", "0.20", "-0.05")):
            self.store.append(f"event:cash-{number}", EXP, "fixture.cash", {"amount": amount})
        before = self.store.verify()
        self.store.append("event:cash-0", EXP, "fixture.cash", {"amount": "0.10"})
        self.assertEqual(before, self.store.verify())
        reducer = lambda state, event: state + Decimal(event["payload"]["amount"])
        self.assertEqual(self.store.replay(EXP, reducer, Decimal("0")), Decimal("0.25"))
        backup = self.store.backup(Path(self.temp.name) / "backup.sqlite3")
        with Store.restore(backup, Path(self.temp.name) / "restored", synthetic=True) as restored:
            self.assertEqual(before, restored.verify())
            self.assertEqual(restored.replay(EXP, reducer, Decimal("0")), Decimal("0.25"))
        with self.assertRaises(FileExistsError):
            self.store.backup(backup)

    def test_targeted_record_and_streamed_portfolio_reads(self):
        self.assertEqual(self.store.record(EXP, "experiment")["id"], EXP)
        with self.assertRaises(ContractError):
            self.store.record(EXP, "portfolio")
        with self.assertRaises(ContractError):
            self.store.record("record:missing")
        for number, portfolio in enumerate(("portfolio:one", "portfolio:two", "portfolio:one")):
            self.store.append(f"event:stream-{number}", EXP, "simulation", {"portfolio_id": portfolio})
        stream = self.store.iter_events(EXP, "simulation", portfolio_id="portfolio:one")
        self.assertIs(iter(stream), stream)
        self.assertEqual([e["id"] for e in stream], ["event:stream-0", "event:stream-2"])
        self.assertEqual(self.store.events(EXP), list(self.store.iter_events(EXP)))
        self.assertEqual(self.store.verify()["events"], 3)

    def test_records_and_events_cannot_be_changed_or_deleted(self):
        self.store.put_records(base_records())
        self.assertEqual(len(self.store.records()), len(base_records()))
        self.store.append("event:immutable", EXP, "fixture.cash", {"amount": "1.00"})
        for table in ("records", "events"):
            for statement in (f"DELETE FROM {table}", f"UPDATE {table} SET id='new-id'"):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.store.connection.execute(statement)
        with self.assertRaises(ContractError):
            self.store.append("event:immutable", EXP, "fixture.cash", {"amount": "2.00"})
        modified = base_records()
        modified[0]["title"] = "Rewritten history"
        with self.assertRaises(ContractError):
            self.store.put_records(modified)

    def test_transaction_rollback_and_nested_savepoint(self):
        with self.assertRaises(RuntimeError):
            with self.store.transaction():
                self.store.append("event:rolled-back", EXP, "fixture.cash", {"amount": "1.00"})
                raise RuntimeError("Interrupted")
        self.assertEqual(self.store.events(), [])
        with self.store.transaction():
            self.store.append("event:outer", EXP, "fixture.cash", {})
            try:
                with self.store.transaction():
                    self.store.append("event:inner", EXP, "fixture.cash", {})
                    raise RuntimeError("rollback inner")
            except RuntimeError:
                pass
        self.assertEqual([e["id"] for e in self.store.events()], ["event:outer"])

    def test_abrupt_process_exit_does_not_commit_partial_write(self):
        script = """import os, sys
from trade_theorist.storage import Store
from trade_theorist.fixtures import EXP
s = Store(sys.argv[1], synthetic=True)
with s.transaction():
    s.append('event:crash', EXP, 'fixture.cash', {'amount':'5.00'})
    os._exit(9)
"""
        result = subprocess.run([sys.executable, "-c", script, self.temp.name], capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 9, result.stderr)
        self.assertEqual(self.store.events(), [])
        self.store.verify()

    def test_single_writer_concurrent_duplicate_event(self):
        def write(_):
            with Store(self.temp.name, synthetic=True) as store:
                return store.append("event:concurrent", EXP, "fixture.cash", {"amount": "1.00"})
        with ThreadPoolExecutor(max_workers=2) as pool:
            hashes = list(pool.map(write, range(6)))
        self.assertEqual(len(set(hashes)), 1)
        self.assertEqual(len(self.store.events()), 1)

    def test_phase_resume_reuses_committed_output_and_rejects_changed_inputs(self):
        def operation(store):
            store.append("event:phase-effect", EXP, "fixture.cash", {"amount": "1.00"})
            return {"result": "saved"}
        first = self.store.run_phase("run:foundation-fixture", EXP, "prepare", digest("input"), operation)
        second = self.store.run_phase("run:foundation-fixture", EXP, "prepare", digest("input"), lambda _: self.fail("Called twice"))
        self.assertEqual(first, second)
        with self.assertRaises(ContractError):
            self.store.run_phase("run:foundation-fixture", EXP, "prepare", digest("changed"), operation)

    def test_failed_phase_rolls_back_effects_and_can_resume(self):
        def interrupted(store):
            store.append("event:phase-effect", EXP, "fixture.cash", {})
            raise RuntimeError("token=SECRET-TEST-VALUE")
        with self.assertRaises(RuntimeError):
            self.store.run_phase("run:foundation-fixture", EXP, "prepare", digest("input"), interrupted)
        self.assertEqual([e["kind"] for e in self.store.events()], ["phase.failed"])
        self.assertNotIn("SECRET", json.dumps(self.store.events()))
        self.assertEqual(self.store.run_phase("run:foundation-fixture", EXP, "prepare", digest("input"), lambda _: "resumed"), "resumed")

    def test_unknown_database_version_and_changed_migration_rejected(self):
        self.store.connection.execute("INSERT INTO schema_migrations VALUES (99, 'newer')")
        with self.assertRaises(ContractError):
            Store(self.temp.name, synthetic=True)

    def test_public_logs_drop_private_fields_and_bounded_free_text(self):
        secrets = ["sk-test-secret", "Bearer token-value", "password=private", "C:/private/book.pdf"]
        output = public_log(" ".join(secrets), run_id=secrets[0], phase=secrets[1], prompt=secrets[2], path=secrets[3])
        self.assertEqual(json.loads(output), {"code": "operation_failed"})
        self.assertLess(len(output), 100)
        for secret in secrets:
            self.assertNotIn(secret, output)

    def test_private_root_rejects_checkout_and_relative_paths(self):
        with self.assertRaises(ValueError):
            private_root("relative/path")
        with self.assertRaises(ValueError):
            private_root(Path(__file__).resolve().parents[1] / ".local/private-test")


if __name__ == "__main__":
    unittest.main()
