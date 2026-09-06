import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from trade_theorist.contracts import ContractError
from trade_theorist.learn.reviewed import specialist_status


ROOT = Path(__file__).resolve().parents[1]


class SpecialistLearningTests(unittest.TestCase):
    def test_bounded_specialists_are_valid_but_not_ready(self):
        for character in ("value_rationalist", "systematic_trend_operator"):
            with self.subTest(character=character):
                directory = ROOT / "characters" / character
                status = specialist_status(directory)
                self.assertEqual(status["status"], "partial_foundation")
                self.assertFalse(status["real_readiness"])
                self.assertEqual(status["books_read"], 0)
                bundle_text = (directory / "checkpoints/foundation.bundle.json").read_text(encoding="utf-8")
                self.assertNotIn("[PDF PAGE ", bundle_text)
                self.assertNotIn('"request"', bundle_text)
                self.assertNotIn('"quote"', bundle_text)

    def test_changed_status_or_checkpoint_is_detected(self):
        source = ROOT / "characters/value_rationalist"
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in (
                "checkpoints/foundation-status.json", "checkpoints/foundation.bundle.json",
                "checkpoints/foundation-prior.json", "checkpoints/foundation-reading-review.json",
                "curriculum.v1.json",
            ):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((source / relative).read_bytes())
            status_path = root / "checkpoints/foundation-status.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            status["books_read"] = 1
            status_path.write_text(json.dumps(status), encoding="utf-8")
            with self.assertRaises(ContractError):
                specialist_status(root)


if __name__ == "__main__":
    unittest.main()
