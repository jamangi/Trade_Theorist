"""Immutable council mail with bounded deliberation and generated views.

Message records and store events are authoritative.  Markdown trees are rebuilt
from those sources and never accepted as input.  Reflections are authored text,
not hidden model reasoning, and are visible only in their author's mailbox view.
"""

from dataclasses import asdict, dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from ..contracts import ContractError, canonical, digest, utc, validate


@dataclass(frozen=True)
class Bounds:
    max_words_per_message: int = 500
    max_words_per_reflection: int = 500
    questions_per_character: int = 1
    recipients_per_question: int = 2
    replies_per_recipient: int = 1
    final_revisions_per_character: int = 1
    total_messages: int = 24

    def __post_init__(self):
        values = asdict(self)
        if any(type(value) is not int or value <= 0 for value in values.values()):
            raise ValueError("Council bounds must be positive integers")
        if self.questions_per_character != 1 or self.replies_per_recipient != 1 or self.final_revisions_per_character != 1:
            raise ValueError("This protocol implements exactly one question, reply and final revision")
        if self.recipients_per_question > 2:
            raise ValueError("A question may have at most two recipients")


def _words(value):
    return len(re.findall(r"\S+", value))


def _time(value):
    try:
        return utc(value)
    except (TypeError, ValueError) as exc:
        raise ContractError("Council time must be UTC") from exc


def _safe_label(value, limit=120):
    if not isinstance(value, str):
        raise ContractError("Mail title must be text")
    value = " ".join(value.replace("\x00", " ").split())
    value = re.sub(r"[^\w .,:;?!'()-]+", "", value, flags=re.UNICODE).strip()
    if not value or len(value) > limit:
        raise ContractError("Mail title is empty or too long")
    return value


def _component(value):
    """Map an already validated identity to one harmless path component."""
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip(".-")
    if not value or value in {".", ".."}:
        raise ContractError("Unsafe export identity")
    return value[:160]


def _anchor(event_id):
    return "event-" + digest(event_id)[:16]


def atomic_write_tree(destination, files, *, fail_before_handoff=False):
    """Replace one generated tree only after every bounded relative path is ready."""
    destination = Path(destination)
    if not destination.is_absolute():
        raise ValueError("Export destination must be absolute")
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".mail-stage-", dir=destination.parent))
    backup = destination.parent / (".mail-backup-" + digest(str(destination))[:12])
    moved_old = False
    try:
        for relative, content in files.items():
            relative = Path(relative)
            if relative.is_absolute() or ".." in relative.parts:
                raise ContractError("Generated file escaped the export root")
            target = (stage / relative).resolve()
            if not target.is_relative_to(stage):
                raise ContractError("Generated file escaped the export root")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8", newline="\n")
        if fail_before_handoff:
            raise OSError("injected export failure")
        if backup.exists():
            raise ContractError("Stale export backup requires owner review")
        if destination.exists():
            os.replace(destination, backup)
            moved_old = True
        try:
            os.replace(stage, destination)
        except BaseException:
            if moved_old:
                os.replace(backup, destination)
            raise
        if moved_old:
            shutil.rmtree(backup)
        return destination
    finally:
        if stage.exists():
            shutil.rmtree(stage)


class Council:
    def __init__(self, store, conversation_id, *, bounds=None):
        self.store = store
        self.conversation = store.record(conversation_id, "conversation")
        self.experiment_id = self.conversation["experiment_id"]
        self.experiment = store.record(self.experiment_id, "experiment")
        self.portfolio = store.record(self.conversation["portfolio_id"], "portfolio")
        self.snapshot = store.record(self.conversation["snapshot_id"], "snapshot")
        self.bounds = bounds or Bounds()
        self.participants = tuple(self.conversation["participant_character_versions"])
        if self.experiment["advice"] != "bounded":
            raise ContractError("Conversation requires an experiment with bounded advice")
        if set(self.participants) - set(self.experiment["character_versions"]):
            raise ContractError("Conversation participants are not registered")
        payload = {"conversation_id": conversation_id, "bounds": asdict(self.bounds), "bounds_hash": digest(asdict(self.bounds))}
        self.store.append("mail-open:" + digest(conversation_id), self.experiment_id, "mail.opened", payload,
                          created_at=self.conversation["created_at"])

    def _events(self, kind=None):
        events = self.store.events(self.experiment_id, kind)
        return [event for event in events if event["payload"].get("conversation_id") == self.conversation["id"]]

    def _message(self, message_id):
        message = self.store.record(message_id, "message")
        if message["conversation_id"] != self.conversation["id"] or message["experiment_id"] != self.experiment_id:
            raise ContractError("Message belongs to another conversation")
        return message

    def _initials(self):
        return {event["payload"]["character_version"]: event for event in self._events("mail.initial_committed")}

    def discussion_open(self):
        return set(self._initials()) == set(self.participants)

    def commit_initial(self, recommendation_id, *, at):
        recommendation = self.store.record(recommendation_id, "recommendation")
        character = recommendation["character_version"]
        if (character not in self.participants or recommendation["experiment_id"] != self.experiment_id
                or recommendation["portfolio_id"] != self.portfolio["id"]
                or recommendation["snapshot_id"] != self.snapshot["id"]):
            raise ContractError("Initial opinion has the wrong Character or frozen context")
        if _time(recommendation["created_at"]) > _time(at) or _time(recommendation["expires_at"]) <= _time(at):
            raise ContractError("Initial opinion is not available and live at commitment")
        event_id = "mail-initial:" + digest([self.conversation["id"], character])
        payload = {"conversation_id": self.conversation["id"], "character_version": character,
                   "recommendation_id": recommendation_id, "recommendation_hash": digest(recommendation), "committed_at": at}
        previous = self._initials().get(character)
        if previous and previous["payload"] != payload:
            raise ContractError("Initial opinion is already committed")
        self.store.append(event_id, self.experiment_id, "mail.initial_committed", payload, created_at=at)
        return payload

    def initial_opinions(self, viewer_character):
        if viewer_character not in self.participants:
            raise ContractError("Viewer is outside this experiment")
        initials = self._initials()
        if not self.discussion_open():
            own = initials.get(viewer_character)
            return [] if own is None else [self.store.record(own["payload"]["recommendation_id"], "recommendation")]
        return [self.store.record(initials[character]["payload"]["recommendation_id"], "recommendation")
                for character in self.participants]

    def send(self, message_id, *, sender, recipients, kind, body, title, available_at,
             expires_at, question=None, reply_to=None, evidence_ids=None, related_theory_ids=None,
             created_at=None):
        if not self.discussion_open():
            raise ContractError("Peer mail is hidden until every initial opinion is committed")
        if sender not in self.participants or not recipients or sender in recipients or any(r not in self.participants for r in recipients):
            raise ContractError("Mail sender and recipients must be distinct conversation participants")
        if len(recipients) != len(set(recipients)) or len(recipients) > self.bounds.recipients_per_question:
            raise ContractError("Mail exceeds its recipient cap")
        if not isinstance(body, str) or not body.strip() or _words(body) > self.bounds.max_words_per_message:
            raise ContractError("Mail body exceeds its configured word bound")
        title = _safe_label(title)
        created_at = created_at or available_at
        if _time(expires_at) <= _time(available_at):
            raise ContractError("Mail must expire after it becomes available")
        messages = [record for record in self.store.records()
                    if record["record_type"] == "message" and record["conversation_id"] == self.conversation["id"]]
        if len(messages) >= self.bounds.total_messages and not any(m["id"] == message_id for m in messages):
            raise ContractError("Conversation message cap reached")
        if kind == "question":
            if not question or reply_to is not None:
                raise ContractError("A question needs focused question text and no parent")
            sent = [m for m in messages if m["kind"] == "question" and m["sender_character_version"] == sender]
            if len(sent) >= self.bounds.questions_per_character and not any(m["id"] == message_id for m in sent):
                raise ContractError("Character already asked its one question")
        elif kind == "reply":
            if question is not None or reply_to is None or len(recipients) != 1:
                raise ContractError("A reply needs one recipient, a parent and no new question")
            parent = self._message(reply_to)
            if parent["kind"] != "question" or sender not in parent["recipient_character_ids"] or recipients != [parent["sender_character_version"]]:
                raise ContractError("Reply is not from an addressed adviser to the questioner")
            prior = [m for m in messages if m["kind"] == "reply" and m["reply_to"] == reply_to
                     and m["sender_character_version"] == sender]
            if len(prior) >= self.bounds.replies_per_recipient and not any(m["id"] == message_id for m in prior):
                raise ContractError("Adviser already used its one reply")
        elif reply_to is not None or question is not None:
            raise ContractError("Only focused questions and their replies use question linkage")
        if kind not in {"question", "evidence", "objection", "reply", "decision", "retrospective"}:
            raise ContractError("Unknown mail kind")
        message = {
            "id": message_id, "schema_version": 1, "record_type": "message",
            "experiment_id": self.experiment_id, "created_at": created_at,
            "contamination": self.experiment["contamination"], "conversation_id": self.conversation["id"],
            "sender_character_version": sender, "recipient_character_ids": recipients,
            "portfolio_context": self.portfolio["id"], "snapshot_id": self.snapshot["id"],
            "available_at": available_at, "expires_at": expires_at, "reply_to": reply_to,
            "kind": kind, "question": question, "body": body.strip(),
            "evidence_ids": evidence_ids or [], "related_theory_ids": related_theory_ids or [],
        }
        validate(message)
        self.store.put_records([message])
        event_id = "mail-authored:" + digest(message_id)
        payload = {"conversation_id": self.conversation["id"], "message_id": message_id,
                   "message_hash": digest(message), "title": title}
        self.store.append(event_id, self.experiment_id, "mail.authored", payload, created_at=created_at)
        return message

    def deliver(self, message_id, recipient, *, at):
        message = self._message(message_id)
        if recipient not in message["recipient_character_ids"]:
            raise ContractError("Recipient is not addressed")
        if not self.discussion_open():
            raise ContractError("Peer mail is hidden until initial opinions are committed")
        event_id = "mail-delivery:" + digest([message_id, recipient])
        previous = next((event for event in self._events("mail.delivered") if event["id"] == event_id), None)
        if previous:
            return previous["payload"]
        if _time(at) < _time(message["available_at"]):
            raise ContractError("Message is not yet available")
        if _time(at) >= _time(message["expires_at"]):
            self._expire_one(message, recipient, at)
            return {"conversation_id": self.conversation["id"], "message_id": message_id,
                    "recipient_character": recipient, "status": "expired"}
        payload = {"conversation_id": self.conversation["id"], "message_id": message_id,
                   "recipient_character": recipient, "delivered_at": at,
                   "eligible_for_decision": _time(at) <= _time(self.conversation["deadline"])}
        self.store.append(event_id, self.experiment_id, "mail.delivered", payload, created_at=at)
        return payload

    def read(self, message_id, recipient, *, at):
        message = self._message(message_id)
        delivery = next((event for event in self._events("mail.delivered")
                         if event["payload"]["message_id"] == message_id
                         and event["payload"]["recipient_character"] == recipient), None)
        if delivery is None:
            raise ContractError("Message must be delivered before it is read")
        event_id = "mail-read:" + digest([message_id, recipient])
        previous = next((event for event in self._events("mail.read") if event["id"] == event_id), None)
        if previous:
            return previous["payload"]
        if _time(at) < _time(delivery["payload"]["delivered_at"]):
            raise ContractError("Read time cannot precede delivery")
        if _time(at) >= _time(message["expires_at"]):
            self._expire_one(message, recipient, at)
            raise ContractError("Expired mail cannot be newly read")
        payload = {"conversation_id": self.conversation["id"], "message_id": message_id,
                   "recipient_character": recipient, "read_at": at,
                   "eligible_for_decision": delivery["payload"]["eligible_for_decision"]
                                           and _time(at) <= _time(self.conversation["deadline"])}
        self.store.append(event_id, self.experiment_id, "mail.read", payload, created_at=at)
        return payload

    def _expire_one(self, message, recipient, at):
        event_id = "mail-expiry:" + digest([message["id"], recipient])
        previous = next((event for event in self._events("mail.expired") if event["id"] == event_id), None)
        if previous:
            return previous["payload"]
        payload = {"conversation_id": self.conversation["id"], "message_id": message["id"],
                   "recipient_character": recipient, "expired_at": at}
        self.store.append(event_id, self.experiment_id, "mail.expired", payload, created_at=at)
        return payload

    def expire(self, *, at):
        expired = []
        for message in self._messages():
            if _time(at) >= _time(message["expires_at"]):
                for recipient in message["recipient_character_ids"]:
                    expired.append(self._expire_one(message, recipient, at))
        return expired

    def reflect(self, reflection_id, *, author, subject_character, body, source_message_ids, at):
        if author not in self.participants or subject_character not in self.participants or author == subject_character:
            raise ContractError("Reflection Characters must be distinct participants")
        if not isinstance(body, str) or not body.strip() or _words(body) > self.bounds.max_words_per_reflection:
            raise ContractError("Reflection exceeds its configured word bound")
        for message_id in source_message_ids:
            message = self._message(message_id)
            if author != message["sender_character_version"]:
                if author not in message["recipient_character_ids"] or self.status(message_id, author) == "pending":
                    raise ContractError("Reflection cannot use mail the author has not received")
        payload = {"conversation_id": self.conversation["id"], "reflection_id": reflection_id,
                   "private_to": author, "subject_character": subject_character,
                   "body": body.strip(), "source_message_ids": source_message_ids, "authored_at": at}
        self.store.append("mail-reflection:" + digest([self.conversation["id"], reflection_id]),
                          self.experiment_id, "mail.reflection", payload, created_at=at)
        return payload

    def commit_final(self, recommendation_id, *, at, considered_message_ids=None):
        recommendation = self.store.record(recommendation_id, "recommendation")
        character = recommendation["character_version"]
        if (character not in self.participants or recommendation["experiment_id"] != self.experiment_id
                or recommendation["portfolio_id"] != self.portfolio["id"]
                or recommendation["snapshot_id"] != self.snapshot["id"]):
            raise ContractError("Final recommendation has the wrong frozen context")
        if character not in self._initials():
            raise ContractError("Final revision requires a committed initial opinion")
        if _time(recommendation["created_at"]) > _time(at) or _time(recommendation["expires_at"]) <= _time(at):
            raise ContractError("Final recommendation is not available and live at commitment")
        considered_message_ids = considered_message_ids or []
        reads = {(e["payload"]["message_id"], e["payload"]["recipient_character"]): e for e in self._events("mail.read")}
        for message_id in considered_message_ids:
            self._message(message_id)
            receipt = reads.get((message_id, character))
            if receipt is None or not receipt["payload"]["eligible_for_decision"]:
                raise ContractError("Late or unread mail cannot alter a committed decision")
        event_id = "mail-final:" + digest([self.conversation["id"], character])
        payload = {"conversation_id": self.conversation["id"], "character_version": character,
                   "recommendation_id": recommendation_id, "recommendation_hash": digest(recommendation),
                   "considered_message_ids": considered_message_ids, "committed_at": at}
        prior = [event for event in self._events("mail.final_committed")
                 if event["payload"]["character_version"] == character]
        if len(prior) >= self.bounds.final_revisions_per_character:
            if prior[0]["payload"] == payload:
                return payload
            raise ContractError("Character already committed its one final revision")
        self.store.append(event_id, self.experiment_id, "mail.final_committed", payload, created_at=at)
        return payload

    def close(self, *, at):
        if _time(at) < _time(self.conversation["deadline"]):
            raise ContractError("A timeout closure cannot precede the deadline")
        # Consideration is not resolution.  Preserve every objection unless a later
        # protocol adds an explicit, attributable resolution event.
        objections = [m["id"] for m in self._messages() if m["kind"] == "objection"]
        late = [event["payload"]["message_id"] for event in self._events("mail.delivered")
                if not event["payload"]["eligible_for_decision"]]
        payload = {"conversation_id": self.conversation["id"], "closed_at": at,
                   "reason": "deadline", "outstanding_objection_ids": objections,
                   "late_message_ids": sorted(set(late))}
        self.store.append("mail-close:" + digest(self.conversation["id"]), self.experiment_id,
                          "mail.closed", payload, created_at=at)
        return payload

    def _messages(self):
        return sorted((record for record in self.store.records()
                       if record["record_type"] == "message" and record["conversation_id"] == self.conversation["id"]),
                      key=lambda message: (message["available_at"], message["id"]))

    def status(self, message_id, recipient):
        self._message(message_id)
        for kind, status in (("mail.read", "read"), ("mail.expired", "expired"), ("mail.delivered", "unread")):
            if any(event["payload"]["message_id"] == message_id
                   and event["payload"]["recipient_character"] == recipient for event in self._events(kind)):
                return status
        return "pending"

    def _event_link(self, event):
        return f"[{event['id']}](../../EVENTS.md#{_anchor(event['id'])})"

    def _visible_messages(self, viewer_character):
        delivered = {(event["payload"]["message_id"], event["payload"]["recipient_character"])
                     for event in self._events("mail.delivered")}
        return [message for message in self._messages()
                if message["sender_character_version"] == viewer_character
                or (message["id"], viewer_character) in delivered]

    def _summary(self, viewer_character):
        lines = [f"# Conversation {self.conversation['id']}", "",
                 f"Frozen snapshot: `{self.snapshot['id']}`", f"Portfolio: `{self.portfolio['id']}`", "", "## Opinions", ""]
        for event in self._events("mail.initial_committed"):
            p = event["payload"]
            lines.append(f"- Initial `{p['character_version']}` → `{p['recommendation_id']}` ({self._event_link(event)})")
        for event in self._events("mail.final_committed"):
            p = event["payload"]
            lines.append(f"- Final `{p['character_version']}` → `{p['recommendation_id']}` ({self._event_link(event)})")
        lines.extend(["", "## Messages", ""])
        authored = {e["payload"]["message_id"]: e for e in self._events("mail.authored")}
        visible = self._visible_messages(viewer_character)
        for message in visible:
            event = authored[message["id"]]
            lines.append(f"- **{event['payload']['title']}** — `{message['kind']}` from `{message['sender_character_version']}` ({self._event_link(event)})")
        closures = self._events("mail.closed")
        if closures:
            close = closures[-1]
            lines.extend(["", "## Outstanding at timeout", ""])
            visible_ids = {message["id"] for message in visible}
            outstanding = [message_id for message_id in close["payload"]["outstanding_objection_ids"]
                           if message_id in visible_ids]
            lines.extend([f"- `{message_id}`" for message_id in outstanding] or ["- None"])
            lines.append(f"- Closure source: {self._event_link(close)}")
        return "\n".join(lines).rstrip() + "\n"

    def _responses(self, viewer_character):
        lines = [f"# Responses so far: {self.conversation['id']}", ""]
        for message in self._visible_messages(viewer_character):
            title_event = next(e for e in self._events("mail.authored") if e["payload"]["message_id"] == message["id"])
            lines.extend([f"## {title_event['payload']['title']}", "",
                          f"From `{message['sender_character_version']}`; kind `{message['kind']}`.", "", message["body"], "",
                          f"Source: {self._event_link(title_event)}", ""])
        return "\n".join(lines).rstrip() + "\n"

    def export(self, destination, *, generated_at, fail_before_handoff=False):
        _time(generated_at)
        files = {}
        events = self._events()
        characters = {identifier: self.store.record(identifier, "character") for identifier in self.participants}
        authored = {e["payload"]["message_id"]: e for e in self._events("mail.authored")}
        reflections = self._events("mail.reflection")
        for character_id, character in characters.items():
            root = Path("characters") / _component(character["character_id"]) / "mail"
            visible_ids = {message["id"] for message in self._visible_messages(character_id)}
            visible_events = []
            for event in events:
                p = event["payload"]
                if event["kind"] == "mail.reflection" and p["private_to"] != character_id:
                    continue
                message_id = p.get("message_id")
                if message_id is not None and message_id not in visible_ids:
                    continue
                recipient = p.get("recipient_character")
                if recipient is not None and recipient != character_id:
                    message = self._message(message_id)
                    if message["sender_character_version"] != character_id:
                        continue
                visible_events.append(event)
            event_lines = ["# Mail source events", "", f"Generated at `{generated_at}`.", ""]
            for event in visible_events:
                event_lines.extend([f"<a id=\"{_anchor(event['id'])}\"></a>",
                                    f"- `{event['id']}` — `{event['kind']}` at `{event['created_at']}`", ""])
            files[root / "EVENTS.md"] = "\n".join(event_lines)
            files[root / "conversations" / _component(self.conversation["id"]) / "CONVERSATIONAL_SUMMARY.md"] = self._summary(character_id)
            files[root / "conversations" / _component(self.conversation["id"]) / "RESPONSES_SO_FAR.md"] = self._responses(character_id)
            for message in self._messages():
                if character_id not in message["recipient_character_ids"]:
                    continue
                status = self.status(message["id"], character_id)
                if status == "pending":
                    continue
                sender = characters[message["sender_character_version"]]["character_id"]
                relative = (root / "read_mail" / _component(sender) / (_component(message["id"]) + ".md")
                            if status == "read" else root / "unread_mail" / (_component(message["id"]) + ".md"))
                title_event = authored[message["id"]]
                event_path = "../../EVENTS.md" if status == "read" else "../EVENTS.md"
                files[relative] = "\n".join([
                    f"# {title_event['payload']['title']}", "", f"Status: `{status}`", f"Kind: `{message['kind']}`",
                    f"From: `{message['sender_character_version']}`", f"Available: `{message['available_at']}`",
                    f"Expires: `{message['expires_at']}`", "", message["body"], "",
                    f"Source event: [{title_event['id']}]({event_path}#{_anchor(title_event['id'])})", "",
                ])
            grouped = {}
            for event in reflections:
                if event["payload"]["private_to"] == character_id:
                    grouped.setdefault(event["payload"]["subject_character"], []).append(event)
            for subject, items in grouped.items():
                lines = [f"# Authored reflections on {subject}", "",
                         "These are explicit Character-authored notes, not hidden reasoning.", ""]
                for event in items:
                    lines.extend([event["payload"]["body"], "", f"Source event: `{event['id']}`", ""])
                files[root / "personal_thoughts" / _component(characters[subject]["character_id"]) / "ANALYSIS.md"] = "\n".join(lines)
        manifest = {"generated_at": generated_at, "conversation_id": self.conversation["id"],
                    "source_event_ids": [event["id"] for event in events],
                    "files": sorted(path.as_posix() for path in files)}
        files[Path("manifest.json")] = json.dumps(manifest, indent=2) + "\n"
        atomic_write_tree(destination, files, fail_before_handoff=fail_before_handoff)
        return {"destination": str(Path(destination).resolve()), "manifest_hash": digest(manifest),
                "files": len(files), "source_event_ids": manifest["source_event_ids"]}
