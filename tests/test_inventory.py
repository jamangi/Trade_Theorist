from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import hashlib
from io import StringIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from trade_theorist.cli import main
from trade_theorist.contracts import ContractError
from trade_theorist.inventory import inventory_summary, render_report, validate_inventory, verify_files
from trade_theorist.learn.reviewed import foundation_status


ROOT = Path(__file__).resolve().parents[1]


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT / "library/catalog/characters.json").read_text(encoding="utf-8"))

    def test_acquisition_is_not_complete_coverage_or_learning(self):
        summary = inventory_summary(self.catalog)
        self.assertEqual((summary["characters"], summary["slots"], summary["unique_titles"]), (7, 28, 27))
        self.assertEqual((summary["local_files"], summary["slots_with_files"]), (25, 26))
        self.assertEqual(summary["coverage"], {"unverified": 23, "partial": 1, "verified_in_prior_learning": 1, "missing": 2})
        self.assertEqual(summary["text_status"]["ocr_required"], 2)
        self.assertFalse(summary["grants_learning_readiness"])
        index = validate_inventory(self.catalog)
        shared = [a for a in self.catalog["assignments"] if a["source_id"] == "local:mauboussin-expectations"]
        self.assertEqual({(a["character_id"], a["position"]) for a in shared}, {("value_rationalist", 4), ("event_and_disclosure_detective", 3)})
        harris = index["local:harris-trading-exchanges"]
        self.assertEqual((harris["file"]["page_count"], harris["coverage"]), (113, "partial"))
        bogle = index["local:bogle-common-sense"]
        acquisition = json.loads((ROOT / "library/catalog/bogle-2017-acquisition.json").read_text(encoding="utf-8"))
        self.assertIn(bogle["file"]["sha256"], json.dumps(acquisition))
        status = foundation_status(ROOT / "characters/index_steward", bogle["prior_source_id"])
        self.assertEqual(status["status"], "foundation_complete")

    def test_bad_slots_duplicate_files_and_fabricated_material_rejected(self):
        mutations = [
            lambda c: c["assignments"].pop(),
            lambda c: c["assignments"][1].update(position=1),
            lambda c: c["assignments"][1].update(source_id=c["assignments"][0]["source_id"]),
            lambda c: c["sources"][1].update(file=c["sources"][0]["file"]),
            lambda c: c["sources"][-1].update(coverage="verified_in_prior_learning"),
            lambda c: c["sources"][0].update(coverage="verified_in_prior_learning"),
            lambda c: c["sources"][0]["identity_evidence"].update(pdf_pages=[100000]),
            lambda c: c["sources"][0]["observed_isbns"][0].update(isbn="9781324035443"),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                bad = deepcopy(self.catalog)
                mutate(bad)
                with self.assertRaises(ContractError):
                    validate_inventory(bad)

    def test_changed_and_missing_files_detected_without_promoting_inventory(self):
        with TemporaryDirectory() as directory:
            for source in self.catalog["sources"]:
                file = source["file"]
                if file:
                    body = ("Synthetic file identity test: " + source["id"]).encode()
                    (Path(directory) / file["name"]).write_bytes(body)
                    file.update(size_bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
            original = deepcopy(self.catalog)
            result = verify_files(self.catalog, directory)
            self.assertEqual(sum(f["status"] == "verified" for f in result["files"]), 25)
            self.assertEqual(sum(f["status"] == "not_acquired" for f in result["files"]), 2)
            (Path(directory) / self.catalog["sources"][0]["file"]["name"]).write_bytes(b"changed")
            (Path(directory) / self.catalog["sources"][1]["file"]["name"]).unlink()
            result = verify_files(self.catalog, directory)
            self.assertEqual([f["status"] for f in result["files"][:2]], ["changed", "missing"])
            self.assertFalse(result["grants_learning_readiness"])
            self.assertEqual(self.catalog, original)

    def test_paths_cannot_escape_explicit_books_root(self):
        for name in ("../outside.pdf", "..\\outside.pdf", "C:outside.pdf", "/outside.pdf"):
            with self.subTest(name=name):
                bad = deepcopy(self.catalog)
                bad["sources"][0]["file"]["name"] = name
                with self.assertRaises(ContractError):
                    validate_inventory(bad)
        with TemporaryDirectory() as directory, TemporaryDirectory() as outside:
            link = Path(directory) / self.catalog["sources"][0]["file"]["name"]
            target = Path(outside) / "outside.pdf"
            target.write_bytes(b"outside")
            try:
                link.symlink_to(target)
            except OSError:
                return  # Windows may not grant unprivileged symlink creation.
            with self.assertRaises(ContractError):
                verify_files(self.catalog, directory)

    def test_public_report_is_reproducible_and_cli_uses_current_inventory(self):
        report = (ROOT / "library/catalog/INVENTORY_REPORT.md").read_text(encoding="utf-8")
        self.assertEqual(report, render_report(self.catalog))
        with patch("trade_theorist.cli.read", return_value=self.catalog), redirect_stdout(StringIO()) as out:
            self.assertEqual(main(["library", "report"]), 0)
        self.assertEqual(json.loads(out.getvalue())["slots"], 28)
        with patch("trade_theorist.cli.read", return_value=self.catalog), patch.dict(os.environ, {}, clear=True), redirect_stderr(StringIO()):
            self.assertEqual(main(["library", "verify-files"]), 2)
            self.assertEqual(main(["library", "check"]), 2)
        with patch("trade_theorist.cli.read", return_value=self.catalog), patch("trade_theorist.cli.verify_files", return_value={"files": [{"status": "changed"}]}), redirect_stdout(StringIO()):
            self.assertEqual(main(["library", "verify-files", "--books-root", "example"]), 2)


if __name__ == "__main__":
    unittest.main()
