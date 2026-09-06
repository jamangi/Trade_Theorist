# Step 05: Package and protect the local observatory

- Status: pending; remaining scope as of 2026-09-06
- Recommended model / effort: Sol / medium
- Historical coverage: [TASK-018](../TASK-018-medium-Sol.md)
- Queue: [ordered remaining work](../README.md)
- Design inputs: [ADR-004](../../decisions/records/ADR-004-local-observatory.md), [rights](../../docs/data-rights-matrix.md)

## Why this position

Constrain what the local server exposes before it can show permitted real data.

## Starting evidence

Steps 03 and 04 provide a private UI and command interface. Synthetic acceptance needs no account.

## Finished state

A tested Windows loopback launch/stop path serves only validated private bundle assets, with atomic handoff and preserved fixture-demo access.

## Scope

Package the approved read-only Individual/Monarchy single-page app over a generated private v2 bundle and a loopback-only local service. Reuse existing assets/interactions and content-addressed atomic handoff. Serve only validated bundle assets from an explicit private directory outside Git; never serve the database, books, .env, private filesystem paths or unrestricted directories. Browser interactions read saved records only.

Provide one Windows launch/stop path with a printed local address. Refuse non-loopback binding, unexpected Host/Origin and non-allowlisted methods/assets; reject traversal, symlink/junction escape and wildcard CORS. No external CDN/assets, telemetry, service worker, public deployment workflow or browser credentials. State the same-OS-user trust boundary honestly. Keep the older synthetic demo available and visibly separate from permitted private data.

## Deliverables

Local launcher/server, versioned private bundle manifest, access/path tests, offline browser walkthrough and updated quickstart/runbook. Generate bundles atomically, retain the previous valid version on failure and apply a declared retention policy without deleting unrelated private files. Source rights must cover the intended real use; local-only is not automatic permission for storage/replay. Synthetic acceptance has no dependency on an account, full Step 12 completion or public hosting.

## Acceptance

Verify Individual/Monarchy, all six evidence answers, schema/lineage validation, execution-basis selection, stale/unready/empty cases and keyboard/mobile layout. Test rejected network binding/Host/Origin, encoded traversal, sibling-directory and junction access, secret-bearing input rejection, unknown field denial and rollback after interrupted export. A provider-call trap proves launch, refresh, filters and historical selection make zero Alpaca/model calls. Confirm browser requests are confined to the local allowlisted bundle.

## Validation and handoff

Use the [focused validation workflow](../../docs/development.md). Record changed files, actual checks, evidence artifacts and remaining blockers here. For code changes, run relevant tests and the full suite once after focused checks pass; for UI changes, verify keyboard and narrow/wide layouts too. Original synthetic acceptance never substitutes for required real-source or elapsed-time evidence.

Stop at this step's finished state. The default next item is [Step 06](STEP-06-shared-requests.md); do not start it automatically. Follow the queue's blocker rule for independent work. Preserve historical completion claims. No account call, order, paid subscription, public market-data deployment or recurring work is authorized merely by this task brief.
