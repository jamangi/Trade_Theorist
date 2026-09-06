# Step 05: Package and protect the local observatory

- Status: implemented and verified 2026-09-06
- Recommended model / effort: Sol / medium
- Historical coverage: [TASK-018](../TASK-018-medium-Sol.md)
- Queue: [ordered remaining work](../README.md)
- Implementation guide: [protected launch, trust boundary and reproduction](../../docs/step-05-local-package.md)
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

## Completion evidence (2026-09-06)

- Added `private_bundle.py`: strict format-1 manifest, exact shipped asset admission,
  report/schema/hash validation, recognizable secret/locator rejection, OS-released
  single-writer lock, atomic files/entry and retention of 20 verified compatible
  versions. Unknown/altered/linked/unrelated files are preserved; no database, book,
  source or backup pruning and no recursive deletion.
- Added `local_server.py`: only literal 127.0.0.1, exact Host/Origin/Fetch-Site and
  GET/HEAD/asset admission, no-store/CSP/same-origin headers, read-only startup
  lineage/replay validation, fixed memory responses and Ctrl+C listener closure.
  No request-time filesystem lookup, account/model transport or browser credential.
  The guide explicitly states other local users/processes can connect.
- Connected `serve --projection-version 2` and v2 `demo --serve`; preserved the v1
  fixture preview. Added the packaged local icon to avoid implicit favicon requests
  and fixed keyboard skip-link focus to avoid asset-base navigation. Updated package
  assets, installed check, quickstart/runbook/rights/development and queue/root handoff.
- Focused checks passed: `test_local_server` (16 new tests), `test_export_v2`,
  `test_operations_v2`. Adversarial cases include binding, Host/Origin duplication,
  encoded/traversal/sibling/unlisted paths, methods, unknown manifest/report fields,
  modified scripts even with rehashed manifests, secret-bearing prose, stale lineage,
  hardlinks, live/dangling Windows junctions, interrupted assets/entry, conservative
  retention, lock overlap/release, and launch/stop. Explicit Alpaca/model and outbound
  socket traps cover the private workflow.
- Clean installed wheel check passed outside the checkout with locked local wheels
  and no downloads. Both versions passed demo/resume/evaluate/export/doctor/validate;
  v2 also served every admitted asset over loopback, refused unsafe binding and
  closed the listener. Evidence: ignored `.local/installed-logs/evidence.json` and
  `v2-serve-stop.log`. There were zero account/model calls.
- Final full suite: **247 tests, 26/26 modules passed in 76.7 seconds** through
  `python scripts/check.py`, after focused checks and the final keyboard fix.
  Complete module output remains in ignored `.local/test-logs/`; no tests were
  suppressed. The installed wheel check was also repeated after that fix.
- Browser walkthrough passed at 1365×1000 and 390×844: Individual/Monarchy,
  historical/restated values, six explanations, evidence dialog Escape/focus return,
  paper versus matched control, horizontal keyboard scrolling, skip-to-results,
  stale/unknown costs and empty/unready views. Each load/refresh requested exactly
  seven allowlisted local files with HTTP 200; interactions made no requests and
  browser error logs were empty. Screenshots/audit: ignored
  `.local/step05-browser-evidence/`, `.local/step05-browser-requests.jsonl` and
  `.local/step05-empty-browser-requests.jsonl`. Test workers/tabs were stopped.
- Protected serving is available for saved, permitted v2 evidence. Original
  synthetic checks do not resolve source rights or qualify a real feed. Routine
  delayed-SIP acquisition and shared admission remain later tasks; Step 06 is next.
