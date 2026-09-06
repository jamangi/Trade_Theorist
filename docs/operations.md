# Running and maintaining the future application

Status: operating design with tasks 001–013 available within their recorded scope. Use the [Windows quickstart](quickstart.md) and [operating runbook](runbook.md) for exact implemented commands and recovery steps. The offline demo exercises both portfolio modes, bounded mail, policy rejection, simulation, evaluation, dashboard export and crash recovery without a live endpoint. The design below includes future real-provider operation, which remains gated. See [implementation evidence](task-011-013-implementation.md) and [the task index](../tasks/README.md) for partial real-learning status.

## Intended local interface

| Future action | Purpose / expected result |
| --- | --- |
| `trade-theorist doctor` | Report runtime, writable private storage, schema versions, source access, credentials presence without values, policy completeness, and next actionable blocker |
| `trade-theorist demo` | Run synthetic fixtures with saved/scripted Character outputs; export a visibly labeled demonstration without network or model spend |
| `trade-theorist library check` | Refresh due catalog availability checks; show exact-edition and permission blockers |
| `trade-theorist learn --character <id>` | Resume the next permitted source/checkpoint without overwriting past learning |
| `trade-theorist ingest --source <id>` | Fetch only missing observations and report coverage/quarantine |
| `trade-theorist heartbeat --experiment <id>` | Advance one bounded cycle using pinned config; optional explicit ingest flag |
| `trade-theorist evaluate --experiment <id>` | Resolve mature outcomes and reproduce scorecards from saved records |
| `trade-theorist export --experiment <id>` | Validate and prepare an allowlisted public report |

Provide one documented Windows setup path, pinned dependencies, example nonsecret config, and a private data-root setting. A clean installation must be able to run the synthetic demo before acquiring books or credentials. The first real run requires legal source access, eligible trained Characters, market-data permissions, a complete experiment manifest, and approved numeric paper policy.

## Failure behavior

| Failure | Behavior | Recovery |
| --- | --- | --- |
| Market source unavailable / stale | No new affected recommendations; old report labeled stale | Retry bounded fetch, then resume against a new valid snapshot |
| Model output malformed / timeout | Record failure and bounded retry; otherwise abstain/defer | Keep raw response privately for debugging; do not fabricate a decision |
| Usage ceiling reached | Stop new model work; deterministic reconciliation can finish | Resume only within explicit allocation; no hidden model escalation |
| Duplicate trigger or crash | Acquire lock; continue committed phases only | Same run ID cannot double-charge completed calls or double-fill orders |
| Missing outcome data | Mark forecast pending/unscorable with reason | Backfill as a new data revision and append evaluation revision |
| Risk halt or reconciliation failure | Block new risk and mark report prominently | Owner investigates and explicitly records reset; no automatic restart |
| Public export fails validation | Retain prior valid export | Repair private build, inspect new export, publish validated artifact |

Use structured logs with run/phase IDs and redacted error messages. Back up the database and private source index; verify restore by reconciling a selected run. Append correction events for ledger errors. Never alter past transactions to make balances match.

## Usage policy

Use scripts for mechanical work and deterministic template rendering for ordinary status text. Models receive changed evidence, relevant memory, and bounded recent context; cache results by complete input/version hashes. No agent runs merely because a timer fired when there is no new evidence, due decision, mail, or mature outcome. Record calls, input/output tokens, retries, and charges when available. Unknown charge data is unavailable, not zero.

Development task model recommendations appear in filenames; runtime Character models are an independently pinned experiment setting. Changing a model changes the experiment version. Avoid using different reasoning budgets for competing Characters unless that difference is the preregistered question.

Begin with manual heartbeats. After recovery tests pass, add a private scheduled runner aligned to completed market sessions, with overlap locking and catch-up rules. Notify the owner only on meaningful completion, failure, material health changes, or required action unless periodic updates are requested. This document creates no scheduled automation and spends no recurring usage.

## First useful release

The earliest useful release is an offline demonstration: one fixture market, scripted opinions, both ledger modes, one bounded mailbox exchange, a risk rejection, a mature outcome, and all six explanation panels. It proves mechanics only. The next release uses the trained pilot and permitted historical inputs; then forward shadow observations; then paper execution after gates. A second character's attractive voice or an impressive chart is not evidence that these stages have passed.
