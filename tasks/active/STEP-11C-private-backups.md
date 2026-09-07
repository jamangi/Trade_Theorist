# Step 11C: Build and prove private backup and restore

- Status: pending; brief only, no backup service or remote transfer installed.
- Recommended model / effort: Sol / high.
- Queue: [ordered roadmap](../README.md); early recovery part of [TASK-020](../TASK-020-medium-Sol.md).
- Starting evidence: existing private SQLite storage, [11A](STEP-11A-run-observability.md) receipts and the owner's available private server (described as “lightrail”; exact hosting/service details remain to be established).

## Purpose and finished state

Protect the accumulated evidence and prove it can be restored before relying on
recurring operation. This can be implemented while Step 11 waits, independently
of scientific maturity. A local restore rehearsal can proceed before remote access
is provided; remote delivery remains pending until its destination is concrete.

## Scope

Create a consistent SQLite online backup or a documented quiescent snapshot;
never copy a live main database alone while its WAL can contain committed data.
Include immutable manifests/reports, request budgets and checkpoints, required
private learning/source dependencies or documented recovery locations, configuration
and software revision. Record content hashes, creation time and retention policy.

Restore into an isolated directory and verify integrity, references, report
hashes and replay without new provider/model calls. Restored quota state must not
create a second live owner or replenish spent request budgets. Require explicit
single-owner reconciliation before any restored installation can access an account.

Design encrypted, authenticated transfer to the owner's private server, restricted
filesystem/service access, retention and an independently recoverable encryption
key. Exclude credentials from Git and ordinary report bundles. Define credential
reprovisioning separately. Test a remote download/decrypt/restore, not just upload
success, before claiming disaster recovery. Log backup failures through 11A's
receipt conventions without placing data in operational metadata.

The owner's stated assumption is that private server backups fit the existing
private-use interpretation when data is not distributed publicly. Record the
actual destination and applicable storage/access terms when configuring transfer;
this brief makes no new legal conclusion or public-distribution allowance. Do not
request credentials in tracked files. No server endpoint or login is configured yet.

## Acceptance and handoff

Demonstrate a snapshot during writes, corruption detection, an interrupted transfer,
retention without deleting the last verified backup, and a zero-request restore
with reconciled accounting. Document recovery time and recovery-point loss actually
measured. Feed evidence into Step 12 and Step 15; backup success cannot substitute
for forward maturity or paper-stage approval. Step 15 reuses this implementation
and separately authorizes any recurring backup schedule.
