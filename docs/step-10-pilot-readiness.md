# Step 10: cited participant readiness

Reviewed 2026-09-07 UTC. **The bounded review is complete; the three-participant
learning gate is blocked.** Index Steward has one eligible, reconciled version for
its limited Bogle-grounded VTI research role. Value Rationalist and Systematic
Trend Operator remain unready. Step 11 has not started.

## Policy fixed before prospective outcomes

The [entry policy](../examples/step-10/entry-policy.v1.json) retains all three
owner-approved participants, VTI at delayed daily cadence, and QQQ/SPY as data
controls only. It names each participant's entry criteria, role, cited rationale,
and excluded claims. The [reproducible register](../examples/step-10/readiness-register.v1.json)
contains exact record IDs, canonical hashes, source editions, checkpoint ancestry,
coverage and blockers. Eligibility here is a **participant-learning decision**;
data, decision-policy, integration and elapsed-evidence gates remain separate.

Index's completed introduction and 20 Bogle chapters support broad-fund cost,
diversification and long-horizon reasoning, including explicit abstention. The
[constitution](../characters/index_steward/constitution.v1.md) and the review's
introduction and chapter 15 on ETFs supply the scope rationale. Daily observation
does not require daily trading or an active timing hypothesis.

Value must complete the pinned Graham foundation, whose introduction explicitly
does not cover the later margin-of-safety argument and qualifications. Trend must
complete the pinned Faith foundation beyond chapter 1's market-participant
overview. Each then needs a reviewed constitution/version reconciliation. Their
roles may require abstention: daily ETF bars do not establish a business valuation,
and historical trend anecdotes do not supply a preregistered VTI system. The
readiness criterion is the named foundation and role coverage, not a universal
book count, all seven curricula, or a minimum realized return. Books 2–4 remain
unread and are not added to this gate.

| Participant | Exact reviewed version | Saved foundation | Decision |
| --- | --- | --- | --- |
| Index Steward | `character:index-steward-pilot-foundation-v1` | Bogle 2017 ePDF, ISBN 9781119404521; 21 ordered sections, 43 accepted/qualified and three rejected claims; one complete book | Eligible for its scoped participant-learning role |
| Value Rationalist | `character:value_rationalist-foundation-v1` | Graham revised text with Zweig commentary, ISBN 9780061745171; introduction/commentary at PDF 17–31, one sample checkpoint, zero complete books | Unready: remaining foundation unread |
| Systematic Trend Operator | `character:systematic_trend_operator-foundation-v1` | Faith 2007 ebook, ISBN 9780071509466; chapter 1 at PDF 25–32, one sample checkpoint, zero complete books | Unready: remaining foundation unread |

## Reconciliation and evidence boundaries

The new [Index version bundle](../characters/index_steward/versions/pilot-foundation-v1.bundle.json)
is a validated non-trading learning scope. It pins the reviewed constitution v1
and unchanged curriculum. The original `character:index-steward-bogle-2017-v1`
remains `partial`, because it records the original pre-reading state. Every
original checkpoint, prior, model-call attribution, theory and memory file is
unchanged. The register binds the new version to the old Character and final
checkpoint by both ID and content hash; it does not invent a checkpoint under
the new version or claim a second reading.

All learning retains `hindsight-contaminated` and evaluation `not_run`.
Index's saved theory/test pair concerns a prospective one-year comparison of
S&P 500 index mutual-fund cost groups. It is neither a VTI daily signal nor an
observed result. Its original dates, scope and abstention remain intact; do not
silently reuse it as the pilot's registration. Value and Trend have no saved
theory/test pairs. Absence is explicit, not replaced by fixture opinions.

The audit checks source permissions at the recorded review date and edition
fingerprints against acquisition records; validated bundle references; the exact
independent frozen prior and checkpoint chain; coverage ranges; every claim's
disposition, text and page citation; objections and cumulative memory; and Index's
assimilation deltas, consolidated memory, theory export and preregistration.
Every input artifact is cited by path and hash. Markdown hashes normalize checkout
newlines; JSON hashes use the project's canonical encoding.

This is reproducibility of the **saved attributed review**. No PDF was reread,
no fresh passage hash was computed from private text, and no independent source
assimilation was generated. The earlier acquisition/review verification remains
the basis for source anchoring. Public structural reproducibility needs no PDF,
credential, account call or external model provider.

## Next bounded learning work

The selected Step 10 workload was this saved-evidence review and reconciliation,
with **zero new source sections and zero model/provider calls**. Its finished state
allows documented unready participants. Missing learning is the substantive
blocker; this review does not claim permission is missing for ordinary bounded
private analysis. The [training continuation map](character-training.md) and
[specialist acquisition record](../library/catalog/specialist-foundations-2026-09-05.json)
record the existing owner-supplied-file/private-reading authority. Keep source
PDFs, extracted text, requests and private learning stores outside Git; public
outputs contain original analysis and citation hashes.

| Participant | Next finite coverage target | Pinned material and required output |
| --- | --- | --- |
| Value | Curriculum v1, position 1: chapter 1 plus its associated Zweig commentary, following the reviewed introduction; stop before chapter 2 | The same 660-page supplied Graham PDF, SHA-256 `d1cfe51346ff4796c61d549da3b8837ec68a4ea4a791c5ea01b6be95a6ca3c4f`. Verify exact start/end pages from this edition before freezing. Produce one attributed section review covering that entire chapter/commentary unit, explicit claim dispositions, page anchors, adversarial review, memory delta and checkpoint. Retain partial-foundation status. |
| Trend | Curriculum v1, position 1: chapter 2, following reviewed chapter 1; stop before chapter 3 | The same supplied Faith PDF, SHA-256 `582d494f455b4b8430ccdbdce4e92b824fd488c902dbb5cade98d00136ef66cf`. Verify chapter page boundaries before freezing. Produce one attributed complete-chapter review, claim dispositions, page anchors, adversarial review, memory delta and checkpoint. Retain partial-foundation status. |
| Index | No additional source reading required by this gate | Preserve the completed Bogle edition and curriculum. Optional later learning starts at position 2 only in a separately selected bounded continuation. |

These next sections are **not the remaining foundation as a whole** and cannot
make either specialist ready on their own. Continue the remainder in source order
until the entire declared foundation coverage has been reviewed; only then append
a new readiness decision. Do not skip to Buffett or Clenow.

There is a concrete continuation constraint: the historical specialist sessions
froze one-section `sample` material. `Learner.freeze` pins the entire material
hash, so editing that frozen sample to append chapters is invalid. The current
specialist importer only replays the old opening; rerunning it does not read the
next chapter. For the next run:

1. Verify the exact PDF and create a complete, ordered private material coverage
   map. Preserve the opening unit and its original review attribution. Preparation
   of a complete material map is not a claim that the material has been learned.
2. Register a fresh, explicitly linked continuation version/session with the same
   foundation and curriculum order, preserving its original independent prior.
   Use the existing `Learner`/`BoundedModel` APIs; never overwrite the old bundle.
3. Re-import the already reviewed opening into that new material scope with its
   original attribution, then review only the next unit above. This is one replay
   plus one newly authored section per selected participant, not two new readings.
   Freeze before exposing unread text, keep Characters' formative memories separate,
   and disclose model/context limitations. Stop before the third section.
4. Select and record the run's authoring/model/prompt and hard usage caps before
   any call. For this two-unit replay/continuation shape, use at most two calls
   and the existing importer's ceilings of 250,000 reserved tokens and 6,000 output
   tokens per call; these are ceilings, not permission to start a paid provider or a schedule.
   If the material cannot fit, stop and select a smaller documented section scope.
5. Require validated citations, prior/checkpoint hashes, independent assimilation,
   adversarial review, memory delta and consolidation, plus a preregistered test
   for any promoted theory. Retain the complete material map with partial reading
   status until its last reviewed section. Original import usage does not measure
   the original review's unavailable generation cost.

Implementing those source-specific continuations and reading the remaining
foundations are outstanding learning work. They were not silently launched by
this review, and no new user authorization question is being inserted here.

## Reproduce and continue

```powershell
.\.venv\Scripts\python.exe scripts/review_step_10.py --check
.\.venv\Scripts\python.exe scripts/check.py test_pilot_readiness test_reviewed_learning test_specialist_learning test_forward_shadow
.\.venv\Scripts\python.exe scripts/check.py
```

The review command exits zero when the saved review reproduces, even though it
prints `participant gate: blocked; Step 11: blocked`. It is not a launch command.
Without `--check`, it writes missing artifacts once, preserves equivalent existing
bytes, and rejects changes under an existing version. This is a dated v1 review:
after new learning, append a new register/policy/version and update the auditor's
inputs, rather than overwriting these historical findings.

The next task must retain all three participants. Finish the learning blockers,
then implement Step 11's real-source integration, required dividend/split evidence,
and preregistered future decision policy. The existing v2 shared-forward validator
is intentionally fixture-only. The current recommendation adapter requires
knowledge and Character to share a version and experiment; it cannot directly
consume the new version with the old checkpoint. Step 11 must implement and test
explicit immutable ancestry binding, rather than relabeling old learning records,
removing checks, or copying fixture opinions. Readiness `ready` on a record alone
is insufficient: verify the full roster and the register's hashes and scope.

No real forward manifest is frozen here. Earlier blocked manifests remain dated
historical evidence. Runtime Character models, lead-selection policy, market-data
rights and standing free-account authorization are unchanged. Paper execution and
its live Trading-quota verification remain Step 13 work.

## Validation evidence

Focused checks pass for the actual saved learning and manifest gate. Ten new
readiness tests cover exact versions, partial coverage, preservation of the old
Character, blocked forward admission, omitted participants, forged ready flags,
constitution and standalone-memory drift, rehashed checkpoint/prior/citation
tampering, fixture substitution, sample promotion, changed source editions and
theory exports, and immutable reruns. The full suite passed **321 tests across 32
modules** in 89.3 seconds. The [active Step 10 brief](../tasks/active/STEP-10-pilot-readiness.md)
records the handoff and remaining blockers.
