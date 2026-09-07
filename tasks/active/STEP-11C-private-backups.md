# Step 11C: Build and prove private backup and restore

- Status: local and encrypted remote backup/restore verified 2026-09-07, including both physical FIDO keys, interrupted/corrupt transfer rejection and conservative remote retention. No recurring backup service installed.
- Recommended model / effort: Sol / high.
- Queue: [ordered roadmap](../README.md); early recovery part of [TASK-020](../TASK-020-medium-Sol.md).
- Starting evidence: existing private SQLite storage, [11A](STEP-11A-run-observability.md) receipts and the owner's available private server (originally described as “lightrail”; now verified as Lightsail below).

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
request credentials in tracked files. The verified destination is the owner's
`crcs-lab` Amazon Lightsail server in `us-east-2`; private configuration records
its directory, operator profile and applicable storage/access terms.

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
This original local evidence is supplemented by the completed remote acceptance
below; its former destination/key-recovery blockers are resolved.
11A/11B remain implemented; Step 12 and recurring Step 15 work retain their gates.

## September 7 remote acceptance

[Remote runbook](../../docs/step-11-remote-recovery.md) and
[actual public metadata](../../examples/step-11/remote-backup-status.json)
record encrypted upload, separate download/decrypt/offline restore, and independent
primary/spare Security Key C NFC recovery with PIN and touch. The separate
encrypted recovery capsule was retrieved from the server for the spare rehearsal;
no plaintext age identity file was written. Files: 466; reports: 6;
v2 records: 177; spent requests: 9; replayed performance results: 30.
Observed record/attempt loss against the unchanged source was zero; provider/model
calls and restored account activations were zero. Spare recovery took
44.26 seconds including human interaction and server access.

Actual interrupted/corrupt uploads were rejected before publication. Retention
freshly recovered the survivor, removed 1 older verified object and retained
1 verified object. Software checks also prove age authentication failure,
capsule tamper rejection, interrupted enrollment resume and missing-device gates.
394 tests across 39 modules, 1,983 field classifications and the clean offline
installed workflow passed. The receiver is an explicit bounded SSH command;
no service or recurrence was added. This is a finite attended recovery rehearsal,
not a guaranteed future RTO/RPO or a physical workstation rebuild.
Step 12 retains scientific gates and Step 15 owns recurring backup/monitoring.
