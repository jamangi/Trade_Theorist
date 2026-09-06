# TASK-001: Define validated contracts and experiment policy

- Status: complete (2026-09-05)
- Recommended model: GPT-6 Astra (gpt-6-astra)
- Recommended effort: high
- Dependencies: none
- Design: [architecture.md](../docs/architecture.md)

## Scope

Implement versioned schemas for sources, checkpoints, theories, observations, snapshots, messages, recommendations, policies, ledger events, evaluations, and run manifests. Define stable IDs, decimal money, UTC clocks, enums, reference validation, and explicit contamination status. Add preregistration and paper-policy templates; carry approved defaults without inventing approval for new limits.

## Deliverables

schemas/ with accepted/rejected fixtures; policy and experiment examples; deterministic theory-card validator.

## Acceptance

Reject missing publication eligibility, invalid confidence, cross-experiment references, unsupported assets, and incomplete paper policy. Demonstrate schema migration/version rejection. Fixture policy is labeled synthetic.

## Usage rationale

Contract ambiguity propagates into every later result; use Astra to resolve the hard boundaries before routine implementation.

Record validation evidence and remaining blockers here when implemented. Complete the bounded task; do not implicitly launch its dependents or spend on ongoing runs.

## Implementation evidence

Delivered seventeen versioned JSON Schema record contracts (the minimum set plus referenced experiment, Character, portfolio, test, conversation and model-call entities), deterministic structural/reference validation, accepted/rejected fixtures, synthetic policy/preregistration examples and deliberately incomplete paper templates. IDs, fixed decimal strings, UTC clocks, unknown enums/versions, contamination, publication eligibility, experiment scope and paper prerequisites are validated. Explicit v0 theory migration preserves the old input and rejects unsupported migrations.

`python -m unittest discover -s tests -v` and `trade-theorist validate schemas/fixtures/accepted/bundle.json` pass. Contract tests remove every required field and exercise the requested rejection cases, timing, snapshots, paper owners/limits, and fixture readiness labels. See [schema semantics](../schemas/README.md) and [setup/evidence](../docs/foundation-implementation.md). No new paper limits were approved; template completion and owner authorization remain future paper-stage gates.

## META-001 follow-up (2026-09-06)

The completed v1 contracts remain valid. TASK-024 adds separately versioned operational portfolio, typed event, execution-basis and publication contracts, preserving stored mode strings and v1 hashes.

See [the impact record](../docs/meta-001-impact.md) and [next task](meta-tasks/START-HERE.md).
