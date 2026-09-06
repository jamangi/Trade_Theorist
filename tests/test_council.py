from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from trade_theorist.contracts import ContractError, digest
from trade_theorist.council import Bounds, Council
from trade_theorist.storage import Store


ROOT = Path(__file__).resolve().parents[1]
AT = "2026-09-05T12:10:00Z"
DEADLINE = "2026-09-06T12:00:00Z"
LATE = "2026-09-06T12:01:00Z"


class CouncilTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name, synthetic=True)
        self.addCleanup(self.store.close)
        records = json.loads((ROOT / "examples/theorize/independent-opinions.bundle.json").read_text(encoding="utf-8"))
        experiment = next(r for r in records if r["id"] == "experiment:foundation-fixture")
        experiment["advice"] = "bounded"
        self.characters = list(experiment["character_versions"])
        self.snapshot = next(r for r in records if r["record_type"] == "snapshot" and r["experiment_id"] == experiment["id"])
        self.portfolio = next(r for r in records if r["record_type"] == "portfolio")
        self.initials = {r["character_version"]: r for r in records
                         if r["record_type"] == "recommendation" and r["id"].startswith("recommendation:")
                         and r["character_version"] in self.characters}
        conversation = dict(id="conversation:task-nine-fixture", schema_version=1, record_type="conversation",
                            experiment_id=experiment["id"], created_at="2026-09-05T12:00:00Z", contamination="fixture",
                            participant_character_versions=self.characters, snapshot_id=self.snapshot["id"],
                            portfolio_id=self.portfolio["id"], deadline=DEADLINE)
        records.append(conversation)
        self.store.put_records(records)
        self.council = Council(self.store, conversation["id"])

    def commit_all(self):
        for character in self.characters:
            self.council.commit_initial(self.initials[character]["id"], at=AT)

    def question(self, message_id="message:task-nine-question", *, sender=None, recipients=None,
                 available_at=AT, expires_at="2026-09-07T12:00:00Z", title="Targeted disagreement"):
        sender = sender or self.characters[0]
        recipients = recipients or self.characters[1:]
        return self.council.send(message_id, sender=sender, recipients=recipients, kind="question",
                                 question="Does the fixture justify activity after costs?", body="Challenge the evidence and sizing.",
                                 title=title, available_at=available_at, expires_at=expires_at,
                                 evidence_ids=[self.snapshot["observation_ids"][0]], related_theory_ids=[])

    def final(self, identifier="recommendation:task-nine-final", *, created_at=AT):
        initial = self.initials[self.characters[0]]
        final = deepcopy(initial)
        final.update(id=identifier, created_at=created_at, action="buy", instrument_id="instrument:fixture-fund",
                     quantity="10", abstention_reason=None, expires_at="2026-09-07T12:00:00Z")
        self.store.put_records([final])
        return final

    def test_visibility_delivery_dedup_and_independent_read_state(self):
        self.council.commit_initial(self.initials[self.characters[0]]["id"], at=AT)
        self.assertEqual(len(self.council.initial_opinions(self.characters[0])), 1)
        with self.assertRaisesRegex(ContractError, "hidden"):
            self.question()
        for character in self.characters[1:]:
            self.council.commit_initial(self.initials[character]["id"], at=AT)
        self.assertEqual(len(self.council.initial_opinions(self.characters[0])), 3)
        message = self.question()
        with self.assertRaises(ContractError):
            self.council.send(message["id"], sender=self.characters[0], recipients=self.characters[1:],
                              kind="question", question="Does the fixture justify activity after costs?",
                              body="A changed immutable body.", title="Targeted disagreement", available_at=AT,
                              expires_at="2026-09-07T12:00:00Z",
                              evidence_ids=[self.snapshot["observation_ids"][0]])
        with self.assertRaises(ContractError):
            self.question(title="Changed immutable title")
        for recipient in self.characters[1:]:
            self.council.deliver(message["id"], recipient, at=AT)
        count = len(self.council._events("mail.delivered"))
        self.council.deliver(message["id"], self.characters[1], at="2026-09-05T12:11:00Z")
        self.assertEqual(len(self.council._events("mail.delivered")), count)
        self.council.read(message["id"], self.characters[1], at=AT)
        self.assertEqual(self.council.status(message["id"], self.characters[1]), "read")
        self.assertEqual(self.council.status(message["id"], self.characters[2]), "unread")

    def test_question_reply_word_and_final_revision_caps(self):
        self.commit_all()
        question = self.question()
        for number, recipient in enumerate(self.characters[1:]):
            reply_id = f"message:task-nine-reply-{number}"
            self.council.send(reply_id, sender=recipient, recipients=[self.characters[0]], kind="reply",
                              body="The evidence is insufficient for that sizing.", title="Bounded objection",
                              available_at=AT, expires_at="2026-09-07T12:00:00Z", reply_to=question["id"])
            self.council.deliver(reply_id, self.characters[0], at=AT)
            self.council.read(reply_id, self.characters[0], at=AT)
        with self.assertRaisesRegex(ContractError, "one reply"):
            self.council.send("message:duplicate-reply", sender=self.characters[1], recipients=[self.characters[0]],
                              kind="reply", body="A second reply.", title="Second", available_at=AT,
                              expires_at="2026-09-07T12:00:00Z", reply_to=question["id"])
        with self.assertRaisesRegex(ContractError, "one question"):
            self.question("message:second-question")
        with self.assertRaisesRegex(ContractError, "word bound"):
            self.council.send("message:too-long", sender=self.characters[1], recipients=[self.characters[0]],
                              kind="objection", body="word " * 501, title="Long", available_at=AT,
                              expires_at="2026-09-07T12:00:00Z")
        final = self.final()
        replies = [m["id"] for m in self.council._messages() if m["kind"] == "reply"]
        self.council.commit_final(final["id"], at="2026-09-05T12:20:00Z", considered_message_ids=replies)
        changed = self.final("recommendation:task-nine-second-final")
        with self.assertRaisesRegex(ContractError, "one final"):
            self.council.commit_final(changed["id"], at="2026-09-05T12:21:00Z")

    def test_late_reply_cannot_influence_committed_recommendation(self):
        self.commit_all()
        question = self.question(available_at=AT)
        late_reply = self.council.send("message:late-reply", sender=self.characters[1], recipients=[self.characters[0]],
                                       kind="reply", body="This arrived after the decision deadline.", title="Late advice",
                                       available_at=LATE, expires_at="2026-09-07T12:00:00Z", reply_to=question["id"])
        self.council.deliver(late_reply["id"], self.characters[0], at=LATE)
        self.council.read(late_reply["id"], self.characters[0], at=LATE)
        final = self.final(created_at=LATE)
        with self.assertRaisesRegex(ContractError, "Late or unread"):
            self.council.commit_final(final["id"], at="2026-09-06T12:02:00Z",
                                      considered_message_ids=[late_reply["id"]])
        self.council.commit_final(final["id"], at="2026-09-06T12:02:00Z")

    def test_timeout_preserves_objection_and_expiry(self):
        self.commit_all()
        objection = self.council.send("message:unresolved-objection", sender=self.characters[1],
                                      recipients=[self.characters[0]], kind="objection",
                                      body="Costs could reverse the apparent signal.", title="Unresolved cost objection",
                                      available_at=AT, expires_at=DEADLINE)
        result = self.council.deliver(objection["id"], self.characters[0], at=DEADLINE)
        self.assertEqual(result["status"], "expired")
        closure = self.council.close(at=LATE)
        self.assertIn(objection["id"], closure["outstanding_objection_ids"])
        self.assertEqual(self.store.record(objection["id"])["body"], objection["body"])

    def test_export_is_atomic_safe_linked_and_reflections_private(self):
        self.commit_all()
        message = self.question(title="../../outside.md\n# unsafe heading")
        for recipient in self.characters[1:]:
            self.council.deliver(message["id"], recipient, at=AT)
        self.council.read(message["id"], self.characters[1], at=AT)
        secret = "Authored private note about the adviser; not hidden chain-of-thought."
        self.council.reflect("reflection:fixture-one", author=self.characters[0], subject_character=self.characters[1],
                             body=secret, source_message_ids=[message["id"]], at=AT)
        self.council.close(at=LATE)
        destination = Path(self.temp.name).resolve() / "mail-export"
        result = self.council.export(destination, generated_at=LATE)
        self.assertGreater(result["files"], 1)
        self.assertFalse((Path(self.temp.name) / "outside.md").exists())
        texts = {p.relative_to(destination).as_posix(): p.read_text(encoding="utf-8")
                 for p in destination.rglob("*") if p.is_file()}
        summaries = [value for key, value in texts.items() if key.endswith("CONVERSATIONAL_SUMMARY.md")]
        self.assertTrue(summaries and all("../../EVENTS.md#event-" in value for value in summaries))
        author_slug = self.store.record(self.characters[0])["character_id"]
        self.assertIn(secret, "\n".join(value for key, value in texts.items() if key.startswith(f"characters/{author_slug}/")))
        for character in self.characters[1:]:
            slug = self.store.record(character)["character_id"]
            self.assertNotIn(secret, "\n".join(value for key, value in texts.items() if key.startswith(f"characters/{slug}/")))
        pending = self.council.send("message:pending-private", sender=self.characters[1], recipients=[self.characters[2]],
                                    kind="evidence", body="Not delivered yet.", title="Pending evidence",
                                    available_at="2026-09-05T13:00:00Z", expires_at="2026-09-07T12:00:00Z")
        self.council.export(destination, generated_at=LATE)
        lead_slug = self.store.record(self.characters[0])["character_id"]
        lead_text = "\n".join(p.read_text(encoding="utf-8") for p in
                              (destination / "characters" / lead_slug).rglob("*.md"))
        self.assertNotIn(pending["body"], lead_text)
        marker = destination / "previous.txt"
        marker.write_text("previous valid export", encoding="utf-8")
        with self.assertRaises(OSError):
            self.council.export(destination, generated_at=LATE, fail_before_handoff=True)
        self.assertEqual(marker.read_text(encoding="utf-8"), "previous valid export")

    def test_experiment_and_bounds_are_pinned(self):
        with self.assertRaises(ContractError):
            Council(self.store, self.council.conversation["id"], bounds=Bounds(max_words_per_message=100))
        self.commit_all()
        foreign = deepcopy(self.initials[self.characters[0]])
        foreign.update(id="recommendation:foreign", experiment_id="experiment:foreign")
        with self.assertRaises(ContractError):
            self.store.put_records([foreign])


if __name__ == "__main__":
    unittest.main()
