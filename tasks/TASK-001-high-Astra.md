# TASK-001: Define validated contracts and experiment policy

- Status: planned
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
