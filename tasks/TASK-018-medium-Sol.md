# TASK-018: Package the private local observatory

- Status: planned replacement outcome; prior unimplemented GitHub Pages scope retired by META-001
- Recommended model: GPT-5.6 Sol (gpt-5.6-sol)
- Recommended effort: medium
- Dependencies: TASK-012, TASK-013, TASK-024, TASK-025
- Design: [dashboard](../docs/dashboard.md), [rights matrix](../docs/data-rights-matrix.md), [ADR-004](../decisions/records/ADR-004-local-observatory.md)

## Scope

Package the approved read-only Individual/Monarchy single-page app over a generated private v2 bundle and a loopback-only local service. Reuse existing assets/interactions and content-addressed atomic handoff. Serve only validated bundle assets from an explicit private directory outside Git; never serve the database, books, .env, private filesystem paths or unrestricted directories. Browser interactions read saved records only.

Provide one Windows launch/stop path with a printed local address. Refuse non-loopback binding, unexpected Host/Origin and non-allowlisted methods/assets; reject traversal, symlink/junction escape and wildcard CORS. No external CDN/assets, telemetry, service worker, public deployment workflow or browser credentials. State the same-OS-user trust boundary honestly. Keep the older synthetic demo available and visibly separate from permitted private data.

## Deliverables

Local launcher/server, versioned private bundle manifest, access/path tests, offline browser walkthrough and updated quickstart/runbook. Generate bundles atomically, retain the previous valid version on failure and apply a declared retention policy without deleting unrelated private files. Source rights must cover the intended real use; local-only is not automatic permission for storage/replay. Synthetic acceptance has no dependency on an account, full TASK-016 completion or public hosting.

## Acceptance

Verify Individual/Monarchy, all six evidence answers, schema/lineage validation, execution-basis selection, stale/unready/empty cases and keyboard/mobile layout. Test rejected network binding/Host/Origin, encoded traversal, sibling-directory and junction access, secret-bearing input rejection, unknown field denial and rollback after interrupted export. A provider-call trap proves launch, refresh, filters and historical selection make zero Alpaca/model calls. Confirm browser requests are confined to the local allowlisted bundle.

## Historical scope and later publication

The original task planned GitHub Pages and was never implemented. Its stable ID is reused for this approved replacement; no previous success is rewritten. Original synthetic demonstrations and source documents remain repository-safe. A real-data public or derived-summary website requires a new, separately approved task and field-level rights/reconstruction review. This task neither deploys one nor leaves a dormant real-data public-publishing toggle.

## Usage rationale

The private read model and calculations are already defined in upstream work. Use Sol medium for focused packaging and tests, increasing effort only for an unresolved security or accessibility issue. Do not expand into remote control, a database service or broker execution.
