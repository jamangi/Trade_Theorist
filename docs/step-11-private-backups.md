# Step 11C private backup and recovery

Local snapshot/recovery is implemented outside Step 11's frozen runtime. Remote
disaster recovery remains pending: the brief names a private server as “lightrail”
but supplies no hostname, service, storage terms or access profile. Nothing is
uploaded, and no recurring backup job is installed. Step 11 maturity and the
Step 12 paper gate are unchanged.

## What is protected

`scripts/run_step_11_backup.py` resolves the same pinned environment as 11B. It
briefly acquires the observation launcher and existing quota-owner locks, refusing
overlap. SQLite's online backup API includes committed WAL contents. The isolated
snapshot uses rollback journaling so verification does not create WAL sidecars.
Production file capture is quiescent under those cooperating locks; the online
database primitive is also tested while a second connection commits writes.

The bundle includes the complete database (all quota/attempt/page/checkpoint
state), Step 09/11 action/forward evidence, immutable reports, 11A receipts, policy,
original owner binding, and tracked software/configuration/learning/catalog files.
Every file has a byte count and SHA-256 hash; the manifest records capture times,
Git revision, exact working file hashes and a retention policy. Uncommitted
working files can differ from the revision; the captured hashes are authoritative.
No original trial input or runtime is edited.

Original PDFs are outside this scope. Stored ledger replay uses the included
learning checkpoints and source metadata; original books must be recovered
separately from the owner's `Investing-Books/books` library. This local rehearsal
does not prove disaster recovery of the books or offline Python dependencies.
Preserve an offline wheelhouse matching `requirements.lock` and the Python version
for recovery on a clean machine; the existing installed-package check tests that
installation path separately.

Credentials are not read or bundled: `.env` and key containers are rejected, and
only selected tracked repository paths and known private evidence directories are
copied. Keep credentials out of those evidence files. Private destinations must be
outside Git. Windows roots receive an ACL for the current owner and SYSTEM;
ordinary subdirectories inherit it. Local bundles are plaintext under that ACL,
so disk encryption and physical-device recovery remain owner responsibilities.

## Finite commands

Run from the checkout as the normal Windows owner. Choose an absolute private
destination outside the source tree and every Git checkout. The actual rehearsal
location and measurements are recorded in the acceptance section below.

```powershell
.venv/Scripts/python.exe scripts/run_step_11_backup.py backup --destination C:/Users/madis/Documents/TradeTheoristRecovery
```

The printed manifest hash identifies the bundle. The private receipt and
`backup-<id>/verified.json` retain it. Save that hash independently when transporting
the bundle; a hash copied alongside a maliciously replaced payload is not
authentication. The backup command records a keep-three policy but never prunes
automatically. An interrupted snapshot remains `.partial` and is not verified.

```powershell
.venv/Scripts/python.exe scripts/run_step_11_backup.py restore --bundle C:/Users/madis/Documents/TradeTheoristRecovery/backup-<id> --destination C:/Users/madis/Documents/TradeTheoristRestore-<unique-id> --manifest-hash <saved-hash>
.venv/Scripts/python.exe scripts/run_step_11_backup.py prune --destination C:/Users/madis/Documents/TradeTheoristRecovery --keep 3
```

Restore requires a new directory. It verifies bytes, SQLite integrity, v1/v2
hash chains and references, frozen learning/runtime inputs, report hashes and
report-to-database accounting identities. It replays stored performance ledgers
and reconciles cash, reserves, FIFO basis, realized results, income and fees.
Every request-state table hash and spent-attempt count must match the snapshot.
No account coordinator, credentials, provider, broker or model is instantiated.
The original absolute report pointer is retained as evidence and never followed;
reports resolve by content hash inside the restored bundle.

An interrupted copy stays `restored.partial`; only a verified copy becomes
`restored`. Retention re-verifies complete bundles, keeps at least one, and leaves
corrupt/unverified/partial evidence for investigation. Retention is an explicit
local action, not a recurring service or a remote retention policy.

Backup and restore write private `operations/runs/<id>/start.json`, flushed
`start <date>`/`end <date>` logs, and final receipts with action/phase, duration,
exit status, manifest hash or exception type. Raw exceptions, market values and
child output never enter receipts. A start without a receipt is interruption
evidence; it must not be rewritten as a successful run. There is no new alert
service; inspect nonzero command results and private receipts.

## Single-owner activation gate

Restore produces `evidence.sqlite3` and `OFFLINE-ONLY.json`, never a runnable
`research.sqlite3` or installed quota registry. Request budgets are preserved as
evidence; this command has no activation option. Do not point the live launcher at
the restored folder or rename its database to bypass reconciliation.

Before any manual activation, stop/disable all original observation and account
consumers, establish that no second owner survives, and compare the newest
surviving database/registry to the snapshot. Preserve all spent work budgets,
ambiguous attempts, cooldowns, page checkpoints and immutable evidence accrued
since capture. If later usage cannot be reconstructed, keep account access
blocked; waiting for a rolling rate window does not replenish finite work budgets.
Only after an explicit owner reconciliation may a reviewed recovery procedure
rebind the single installation and separately reprovision credentials. That
activation procedure is not implemented or exercised here.

## Remote design and outstanding gate

When the destination is known, record its actual service/hostname, region, private
directory, account, provider storage/access terms and authorized readers in
private configuration. The owner's private-use assumption is carried forward;
this implementation makes no new legal finding or redistribution allowance.

Use recipient-based authenticated encryption (for example, an owner-held age
identity) before transfer. Keep the private decryption identity outside Git and
the backup payload, with a separately recoverable offline copy. The server needs
only ciphertext and a restricted SSH/SFTP account. Pin the SSH host key through a
trusted channel, require key authentication, restrict the remote directory to the
backup account, and give it no application or broker credentials. Do not invent an
endpoint, accept unknown host keys automatically, or place keys in shell arguments.

The future transport should upload a unique `.partial` ciphertext, verify its
length/hash, and atomically rename it. Only a separately downloaded, authenticated,
decrypted and locally restored copy earns remote-verified status. Exercise network
interruption before publication, corruption/authentication failure, loss of the
original machine's key copy, and conservative remote retention that never deletes
the last round-trip-verified backup. Preserve independent manifest hashes/receipts
with the offline recovery material. These remote tests have **not** run; the local
interrupted-copy test is not evidence of interrupted network-transfer recovery.

Measure capture-to-restorable-copy time and recovery-point loss on that actual
round trip. Step 15 separately authorizes any recurring schedule and monitoring.

## Acceptance

The September 7, 13:43 UTC actual rehearsal passed with network connections trapped:
458 files, six immutable reports, 177 v2 records, nine accounted requests and 30
replayed performance results. Backup took 4.772 seconds and restore 6.395 seconds.
Request-state hashes and both record chains matched the unchanged live source
after rehearsal: observed record/attempt loss was zero. This is measured loss for
that rehearsal, not a zero-loss recovery-point guarantee. For later failure, loss
is the evidence accumulated since the latest surviving verified snapshot; no
recurrence is installed to bound that age.

The owner-restricted local root is
`C:/Users/madis/Documents/TradeTheoristRecovery`; its private
`recovery-rehearsal.json` identifies the exact bundle, independent restored folder
and manifest hash. [Public acceptance metadata](../examples/step-11/backup-status.json)
contains counts, timings and hashes only. The bundle remains outside Git.

Twelve focused tests cover WAL/concurrent-write snapshot consistency, bounded
snapshot timeout, read-only ledger replay and quota preservation with network
trapped, byte/manifest/report corruption, interrupted copy publication, abrupt
process death, credential/path rejection, overlap, isolated destination checks,
and retention with corrupt and partial backups. Remote destination,
encryption-key recovery and download/decrypt/restore remain pending.

Final checks passed: 375 tests across 37 modules, all 1,983 schema-field
classifications, and the clean offline installed-package workflow. The existing
11A launcher tests passed, and a read-only Windows inspection reconfirmed both
11B tasks, all three trigger instants, pinned executable/private paths, original
expiration, interactive limited principal and overlap settings. The prior actual
scheduled rehearsal remains the deployment evidence; no extra observation ran.
