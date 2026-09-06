# Tasks 014–015: vendor adapter and prospective shadow controls

Implemented on 2026-09-06 as a bounded, offline qualification package. Real vendor
selection and the real forward observation window remain blocked rather than being
simulated or backdated.

## TASK-014 result

`trade_theorist.adapters.alpaca_market_data` implements Alpaca bars requests with an
explicit feed and raw adjustment, continuation-token pagination, resumable page
boundaries, deterministic bounded backoff, response-shape checks and fail-closed
entitlement handling. Credentials belong to the injected transport and never enter
adapter state or output. Normalization reuses the existing market validator and
revision book. Duplicate ingestion is idempotent, changed payloads append revisions,
and the quality report lists missing sessions instead of filling them.

[ADR-003](../decisions/records/ADR-003-alpaca-market-data-qualification.md) records
the official evidence and unresolved rights. The checked-in capability file uses
`false` for every unproved capability. The recorded quality report is a mechanics
fixture, not an account-authorized sample; required coverage is therefore blocked.
No subscription, credential, account call or alternate vendor selection occurred.

## TASK-015 result

`trade_theorist.forward` freezes a prospective manifest before its start, includes
exact Character versions, one opportunity-set hash, the feed/retrieval policy, horizon,
tool allowlist and blockers. The forward evidence gate accepts only qualified adapters
and preserves event, publication and ingestion clocks. Generic repository, mail,
retrieval, web, HTTP and broker tools are absent from forward runs. Even qualified
evidence is rejected when its publication or ingestion time is after the decision
cutoff. Recommendations must be committed by that cutoff against the same opportunity
set. Shadow reports always report zero broker orders.

The candidate pilot manifest is intentionally `blocked`: the immutable Character
contracts do not yet contain eligible `ready` versions for the proposed participants,
Alpaca coverage has not been sampled through an authorized account, and required data
rights remain unresolved. Its dashboard-status report is `forward-blocked`, shows zero
completed sessions and zero committed decisions, and retains every blocker. A separate
offline fixture audit demonstrates the leakage controls without claiming an observed
market session or performance.

Real elapsed time is not compressed. No ongoing task, schedule, broker integration,
paper portfolio or dependent TASK-016 work was launched.

## Validation

Focused tests cover pagination and resume, feed pinning, 429 retry, entitlement denial,
token loops, malformed payload quarantine, idempotence, revisions and gaps. Forward
tests cover generic repository/mail/retrieval rejection, late qualified evidence,
timestamp retention, tool construction, identical opportunity sets, pre-cutoff commit,
immature horizons, blocked readiness and zero broker orders. The full suite is the
release gate recorded in the task files. Final validation passed all 143 tests across
18 isolated modules; generated specimens and whitespace checks also passed.
