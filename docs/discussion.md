# Mail, deliberation, and observable Character life

Status: protocol design. Mail is internal Character-to-Character data, not external email or messages to people.

## Message contract

Use `message_id`, `conversation_id`, `experiment_id`, `sender_character_version`, `recipient_character_ids`, `portfolio_context`, `snapshot_id`, `created_at`, `available_at`, `expires_at`, `reply_to`, `kind`, `question`, `body`, `evidence_ids`, and `related_theory_ids`. Kinds: question, evidence, objection, reply, decision, retrospective. IDs are stable opaque identifiers; a human-readable title is metadata, not a filesystem path. Validate all references against experiment access policy.

The event store is authoritative. Append delivery, read, reply, expiry, and closure events; never move the only copy of a message between folders. A recipient's read receipt does not mark it read for everyone. Duplicate sends are deduplicated by idempotency key. Cross-experiment mail is prohibited unless copied into a new explicitly labeled experiment with provenance.

Provide the owner's preferred readable exports:

```text
characters/<character_id>/mail/
  unread_mail/<message_id>.md
  read_mail/<sender_character_id>/<message_id>.md
  personal_thoughts/<other_character_id>/ANALYSIS.md
  conversations/<conversation_id>/CONVERSATIONAL_SUMMARY.md
  conversations/<conversation_id>/RESPONSES_SO_FAR.md
```

These are regenerated views, with generated-at time and source event IDs. Personal thoughts are the Character's explicitly written reflections, not hidden model reasoning. They are private to that Character during experiments; the owner can inspect them. Summaries cite messages and preserve disagreement. Editing a generated file must not mutate history; owner additions enter as labeled new events.

## A bounded decision conversation

1. All eligible Characters receive the same time-frozen evidence, with portfolio-specific holdings. Each commits its initial recommendation before seeing peers' initial opinions.
2. The coordinator opens at most one focused question per Character per heartbeat and routes it to at most two relevant advisers. Material missing evidence takes priority over conversational curiosity.
3. Each recipient may send one reply. Allow one final revision by the decider; no recursive reply chains in the same heartbeat. A later conversation can continue research without altering a committed decision.
4. The decider records which advice changed its recommendation, which it rejected and why, outstanding objections, and expiry. Consensus is unnecessary. The governor checks hard policy independently.
5. On timeout, the decider may proceed only if its required evidence and risk checks are satisfied. Otherwise record an abstention. Late replies are visible for later eligible decisions and cannot rewrite an earlier result.

Suggested initial bounds: 500 words per message, three minutes total discussion time, one round, and a manifest-defined total token ceiling. These are configurable research parameters. Exhausted allowance means defer or abstain, never unlimited automatic retries. Routine no-change sessions need no new conversation. Calendar deadlines and evidence expiry outrank message urgency labels.

Mail pending before the heartbeat can be delivered at its opening; current-heartbeat replies are delivered only in the bounded round. In replay, wall-clock creation and simulated availability are separate. An archived message containing future knowledge is ineligible even if its title describes an old event. All externally retrieved content is treated as evidence, never as instructions to run tools, change policy, or reveal files.

## Make the project feel alive without creating noise

- A **belief timeline** shows what changed after each book and which contradictions survived.
- A **question garden** lists unresolved questions, next useful evidence, and optional next-review dates. Expiry closes the active queue without erasing the question.
- A **decision postcard** says “I waited because…” or “I changed my mind because…”, linked to the actual recommendation and evidence.
- A **relationship view** shows who exchanged useful evidence, disagreement, and opinion changes. No popularity score or rewards for message volume.
- A **weekly lab notebook** summarizes completed outcomes, surprising failures, and what remains unknown. Generate it from saved events only when there is something new.
- An **owner question box** creates a labeled research question. Injecting owner knowledge into a frozen trial starts a separate variant or marks it contaminated.

Use concise, authored rationales and citations. Do not promise access to private internal chain-of-thought. Measure whether these views improve the owner's ability to explain decisions, not whether Characters appear human or sound confident.
