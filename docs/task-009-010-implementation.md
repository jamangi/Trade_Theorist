# Tasks 009–010: bounded council mail and resumable heartbeat

Implemented 2026-09-06. These components exercise original synthetic fixtures
only. They send no external mail, call no network service, schedule no recurring
work, and expose no live-trading endpoint.

## Event-backed council mail

`trade_theorist.council.Council` binds one conversation to its immutable
experiment, snapshot, portfolio, participants and configured `Bounds`. The first
event pins those bounds. Every participant must commit an initial recommendation
before the API reveals peer opinions or permits peer mail. The implemented
protocol allows one focused question per Character, at most two recipients, one
reply from each addressed recipient, and one final revision per Character. Word
and total-message ceilings are explicit. A changed bound, reused message ID with
different content, recursive reply or cross-experiment reference fails closed.

Message records remain immutable. Delivery, per-recipient read, expiry, authored
reflection, initial/final commitment and closure are hash-chained events. A second
delivery has no effect. One recipient reading a message does not change another
recipient's state. Replies delivered or read after the conversation deadline are
retained, but cannot be listed as evidence that influenced the committed final
recommendation. Deadline closure retains unresolved objection IDs instead of
discarding them.

Reflections are concise, explicitly authored notes—not hidden model reasoning.
Only the author's generated mailbox contains their reflection body. The store
remains owner-inspectable. A reflection cannot cite conversation mail the author
did not send or receive.

`Council.export()` deterministically builds readable Markdown inboxes, read-mail
folders, personal-thought files, conversation summaries, response transcripts and
an event index. Summaries link the exact source-event entries. Message titles are
display labels only; filenames derive from validated opaque identities, and every
generated path is checked beneath the export root. The entire tree is staged and
renamed as one handoff. An injected pre-handoff failure leaves the previous valid
tree unchanged. Generated folders are views and are never read back as authority.

## Ordered heartbeat

`trade_theorist.heartbeat.Heartbeat` executes ten pinned phases in order:

1. freeze the exact snapshot;
2. mark the experiment's portfolio;
3. deliver eligible prior mail;
4. commit independent opinions;
5. run one bounded deliberation round;
6. commit portfolio-aware final decisions;
7. apply the independent policy gate;
8. queue approved simulation orders;
9. append an evaluation handoff;
10. atomically hand off the readable export.

The run manifest hashes every phase input and version. An experiment-scoped lock
prevents another heartbeat from interleaving. A crash leaves that lock available
to the same run ID for resumption; a different run is refused. Each local phase
uses the store's transactional phase checkpoint. Repeating a completed phase
returns its saved output and cannot duplicate mail, evaluation handoffs, orders or
fills.

`ModelCallCache` hashes the complete request, including experiment, Character,
snapshot, portfolio state, knowledge/source revisions, model, prompt, sampling,
output version and empty tool list. It reserves the bounded call and token budget
before invoking the provider outside the phase transaction. A completed exact
request is reused; changed inputs produce a distinct call and must pass the
remaining budget. An ambiguous started call is not retried automatically.

The orchestrator connects existing components without replacing their authority:
snapshot records remain the market-data boundary, `Council` owns deliberation
semantics, `Governor` owns policy, and `Simulator` alone queues executable fixture
orders. Event queries and portfolio reconstruction remain scoped by experiment
and portfolio ID, so council holdings and private reflection evidence never enter
an individual sleeve.

## Fixtures and validation

Run `python scripts/build_task_009_010_fixtures.py` to rebuild
`examples/heartbeat/`. The fixture contains:

- three independent council opinions, including abstain and wait;
- one question to two advisers, two bounded replies, an unresolved objection and
  one private authored reflection;
- a final council buy proposal rejected by the deterministic turnover limit;
- a separate individual-portfolio heartbeat that queues one simulated order;
- generated mailbox views whose summaries link their source events; and
- a fixture-only report with separate experiment and portfolio identities.

Local validation on Windows/Python 3.14 ran 109 tests successfully. Targeted tests
interrupt and resume a fresh heartbeat after each of all ten durable phases. Every
case finishes with exactly ten phase completions, three completed council model
calls, five deliveries and one accepted-order event—without duplicates. Tests
also cover lock exclusion, changed-plan rejection, usage admission, exact-input
reuse, independent read state, reply/question/final caps, timeout and late-reply
behavior, title/path attacks, atomic export failure, private-reflection visibility,
cross-mode references and complete fixture reproduction.

There is no blocker for the bounded fixture scope. Task 011 still owns outcome
evaluation and evidence grades; Tasks 012–013 own the dashboard and one-command
operator interface. Real operation remains blocked by incomplete specialist
learning, vendor/calendar qualification, an owner-approved numeric paper policy,
and later readiness review. No real recommendation, paid model call, scheduled
heartbeat, broker connection or performance claim was created here.
