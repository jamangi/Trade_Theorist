# Step 05: protected local observatory

Implemented 2026-09-06. Start with the [Windows quickstart](quickstart.md), then this
bounded guide. [Step 06](../tasks/active/STEP-06-shared-requests.md) is next; no account
traffic, model calls, orders or scheduling were added here.

## Launch, refresh and stop

After the quickstart's evaluate/export commands:

```powershell
& $tt serve --projection-version 2 --fixture --data-root $v2Data --output-root $v2Bundle
```

Open the printed `http://127.0.0.1:<port>/` address. Stop with **Ctrl+C in that
terminal**; the listener closes. Default port is 8765; `--port 0` chooses a free
port. Only literal `127.0.0.1` is accepted. No background service or browser
auto-open is installed. V2 `demo --serve` seeds/resumes, exports and starts the same
protected server. V1 `demo --projection-version 1 --serve` remains a separate fixture preview.

Both roots must be explicit or configured. The **bundle must be outside every Git
checkout even for fixtures** and cannot contain the database root. For permitted
real evidence, omit `--fixture` and set config `fixture: false`. Saved-data inspection
requires recorded permissions, not trained Characters or trading approval.

Each launch verifies the bundle against its database, then serves a fixed snapshot
from memory. Filters, evidence and historical selection make no requests. Browser
refresh rereads the same snapshot. To show new evidence: **stop, evaluate/export,
then launch again**. Exporting or changing disk files does not alter a running page.

## Admission and trust

Before binding, the launcher verifies the strict manifest, report schema/hash,
exact shipped HTML/JS/CSS/icon, source lineage, permissions and saved arithmetic
through a read-only database snapshot. Old bundles without this manifest must be
re-exported with the current package; no database migration is implied.

Only GET/HEAD and exact allowlisted targets are admitted. Host must be exactly
`127.0.0.1:<port>`; Origin must be absent or exactly that HTTP origin. Fetch-Site must
be absent, same-origin or none. Duplicated security headers, foreign origins,
alternate path encodings, traversal, queries, directory listings and other methods
are refused. Requests never resolve filesystem paths or touch the database.
Symlinks, Windows junctions (including dangling ones), reparse points and hardlinked
assets are rejected. The manifest is local metadata, not a browser route.

Responses use no-store, restrictive CSP, nosniff, no-referrer, frame denial and
same-origin resource/opener policies. There is no CORS opt-in, cookie, browser
credential, external asset, telemetry or service worker. Diagnostics omit raw
request/exception values. The browser loads only HTML, CSS, two scripts, report,
schema and a local icon.

**Loopback is a same-computer boundary, not user authentication.** Other local
processes/users may connect. A malicious process with the owner's filesystem access
can read/modify private data or the application. These controls do not protect
against that actor, browser extensions, screenshots or deliberate copying, and do
not grant vendor storage/replay/retention rights.

Typed field selection excludes raw credentials/account payloads and unrestricted
locators. An extra guard rejects recognizable credential assignments, common
key/bearer/private-key patterns and absolute filesystem locators even in allowed
prose. It is not a universal secret detector: never author secrets into analysis.
Unknown report and manifest fields are refused.

## Manifest, atomic publication and retention

`versions/<hash>/manifest.json` has exactly `bundle_format: 1`,
`publication_class: private-owner-v2`, `version_id`, `generated_at`, `report_hash`
and `assets`. Each of seven exact assets has its byte count and SHA-256 hash.
Version identity includes the template and asset contents. Recomputing a manifest
cannot authorize altered scripts or a different schema.

An OS-released writer lock prevents overlapping publishers without stale locks
after process death. Flushed temporary files become immutable assets. Only a
complete validated version can atomically replace root `index.html`. Failure leaves
the prior entry usable; repeat export at the same cutoff to reuse completed files.
Changed existing immutable files require investigation, never automatic overwrite.

Default retention is **20 verified compatible versions including the current one**.
Cleanup runs only after successful publication and removes only exact known ordinary
files in a validated version directory, with no recursive deletion. Extra notes,
altered/legacy versions, links and unrelated directories are preserved. Interrupted
temporary files are not blanket-deleted. Database, books, evidence and backups are
never pruned. Cleanup failure does not undo successful publication.

## Verification and continuation

```text
python scripts/check.py test_local_server test_export_v2 test_operations_v2
python scripts/check_installed.py --wheelhouse .local/wheelhouse
python scripts/check.py
```

The installed check uses a fresh wheel/environment outside the checkout, locked
local dependencies and no downloads. Both versions run offline; v2 additionally
starts the real server, requests every asset, rejects an unsafe bind and closes its
listener. Its socket guard permits only test loopback traffic. Logs remain in
ignored `.local/installed-logs/` and `.local/test-logs/`.

Browser acceptance used 1365×1000 and 390×844: both modes, historical/restated views,
paper/control separation, six explanation panels, skip-link focus without navigation, evidence Escape/focus return,
horizontal keyboard scrolling, stale/unknown values and empty/unready states.
Outbound sockets, Alpaca requests and model completion were trapped. Load and
refresh each requested exactly seven local files; interactions made no requests.
Screenshots/request audits are in ignored `.local/step05-browser-evidence/` and
`.local/step05-browser-requests.jsonl`. Actual counts are in the [Step 05 brief](../tasks/active/STEP-05-local-package.md).

| Responsibility | Implementation / tests |
| --- | --- |
| Manifest, assets, text guard, atomic publication, retention | `src/trade_theorist/private_bundle.py`; `tests/test_local_server.py` |
| Fixed snapshot, request admission, launch/stop | `src/trade_theorist/local_server.py`; `tests/test_local_server.py` |
| Rights/replay export and command integration | `export_v2.py`, `operations_v2.py`, `cli.py`; `test_export_v2`, `test_operations_v2` |
| Local icon and installed package | `dashboard/private.html`, `dashboard/favicon.svg`, `pyproject.toml`, `scripts/check_installed.py` |

Protected serving now works for already saved, permitted v2 evidence. Routine
delayed-SIP acquisition still depends on the separately scoped shared/qualified
data workflow. No live account was used as acceptance evidence.
