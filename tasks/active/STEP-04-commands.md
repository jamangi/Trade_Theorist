# Step 04: Connect the private workflow to usable commands

- Status: pending; remaining scope as of 2026-09-06
- Recommended model / effort: Sol / medium
- Historical coverage: [TASK-013](../TASK-013-medium-Sol.md)
- Queue: [ordered remaining work](../README.md)
- Design inputs: [Operations](../../docs/operations.md), [runbook](../../docs/runbook.md)

## Why this position

The private read model now exists; wire reproducible commands before packaging the launch experience.

## Starting evidence

Step 03's read-model contract and Step 02's accounting are available.

## Finished state

Documented commands select versions explicitly, write to appropriate private paths, report actionable prerequisites and reproduce the account-free demo.

## Implementation and acceptance

META-001 adds a follow-up after Step 03's private v2 read model: commands must choose the schema/projection version explicitly, keep the v1 fixture demo working, use a private bundle root outside Git for real inputs, and report missing rights, migrations and reconciliation clearly. Doctor inspects prerequisites without exposing secrets or making account calls. Step 05 owns hardened loopback serving; `--fixture` is not a license or a way to publish a private database. Preserve the prior implementation evidence in the linked historical record.

Retain the existing implemented commands; add only the pending version/private-output integration. Update the Windows quickstart, nonsecret example config and runbook. Reproduce both views from a clean installation without accounts, model calls or external network use. Failed phases give concrete resume actions; doctor reports missing migrations, rights or reconciliation without disclosing secrets.

## Validation and handoff

Use the [focused validation workflow](../../docs/development.md). Record changed files, actual checks, evidence artifacts and remaining blockers here. For code changes, run relevant tests and the full suite once after focused checks pass; for UI changes, verify keyboard and narrow/wide layouts too. Original synthetic acceptance never substitutes for required real-source or elapsed-time evidence.

Stop at this step's finished state. The default next item is [Step 05](STEP-05-local-package.md); do not start it automatically. Follow the queue's blocker rule for independent work. Preserve historical completion claims. No account call, order, paid subscription, public market-data deployment or recurring work is authorized merely by this task brief.
