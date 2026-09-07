# Step 11C: Build and prove private backup and restore

- Status: local backup/restore implemented and rehearsed 2026-09-07; remote disaster recovery blocked on destination/access and encrypted round-trip verification. No recurring backup service installed.
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

## September 7 implementation evidence

[Implementation and recovery runbook](../../docs/step-11-private-backups.md),
[backup module](../../src/trade_theorist/private_backup.py),
[finite commands](../../scripts/run_step_11_backup.py), and
[tests](../../tests/test_private_backup.py) deliver the local scope outside the
frozen runtime. [Actual acceptance metadata](../../examples/step-11/backup-status.json)
records a 4.772-second backup and 6.395-second network-blocked restore: 458 files,
six reports, 177 v2 records, nine spent requests and 30 reconciled performance
records. No observed record/attempt loss; no provider/model calls or activation.

Validation passed: twelve focused recovery tests and 375 tests across 37 modules,
1,983 field classifications, and the clean offline installation. Read-only native
Windows inspection reconfirmed both installed 11B jobs and their finite settings.
Local copy interruption and retention are
tested; remote transfer interruption, independent key recovery and an actual
download/decrypt/restore remain pending. The private server hostname/service,
destination, access profile and storage/access terms were requested but are not
configured. This is a partial Step 11C completion, not disaster-recovery acceptance.
11A/11B remain implemented; Step 12 and recurring Step 15 work retain their gates.
