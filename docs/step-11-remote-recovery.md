# Step 11C encrypted remote recovery

The finite transport uses the owner's `crcs-lab` SSH profile and Amazon Lightsail
in `us-east-2` (Ohio). The server stores age-encrypted snapshots and a separate
FIDO-encrypted recovery capsule. The two Security Key C NFC devices each unlock
the same age identity using their own dedicated credential, PIN and touch.
The [acceptance metadata](../examples/step-11/remote-backup-status.json) records
the actual rehearsal; the [local recovery runbook](step-11-private-backups.md)
defines snapshot contents, accounting checks and the single-owner activation gate.

## Storage and access

The immutable receiver is installed at
`/home/ubuntu/.local/lib/trade-theorist-backups/<receiver-sha256>/backup_receiver.py`.
Storage is `/home/ubuntu/.local/share/trade-theorist-backups`, owned by `ubuntu`,
with owner-only directories and files. The existing host operator can access
ciphertext; the host has no FIDO device, PIN, plaintext age identity, market-data
credentials or running research installation. No listener, daemon, firewall rule,
new SSH identity or recurring backup job is installed.

SSH requires the existing pinned host key and key authentication, disables agent
forwarding and bounds transport time. Follow the owner's
[CRCS access guide](https://github.com/jamangi/Codex-Remote-Control-Strategy/blob/main/SERVER_ACCESS_GUIDE.md)
to load/reprovision access. Remove only the designated CRCS operator identity from
the workstation agent when finished. Transient pre-authentication banner timeouts
were observed; inspect and retry the bounded command after connectivity recovers.
Do not replace credentials or accept a different host key to address a timeout.

Private configuration records the actual service/region/path and references the
[AWS agreement](https://aws.amazon.com/agreement/),
[service terms](https://aws.amazon.com/service-terms/), and
[Lightsail security responsibilities](https://docs.aws.amazon.com/lightsail/latest/userguide/security.html).
This carries forward the owner's private-use authorization. It makes no new
legal conclusion or allowance to redistribute market data.

## Key custody

These FIDO-only devices do not provide the PIV interface used by age's YubiKey
plugin. Instead, `hardware_recovery.py` uses Yubico's FIDO2 `hmac-secret`
extension, HKDF-SHA256 and AES-256-GCM to wrap a native age identity separately for
each registered device. Credential protection requires user verification at the
authenticator; registration and assertions require PIN and touch. The signed
assertion, relying-party scope and credential are checked before unwrapping.
The dedicated local relying-party identifier does not contact a website.

The identity is generated in memory, passed to age through standard input during
recovery, and never intentionally written to a plaintext identity file. It does
briefly exist in process memory; Python cannot guarantee erasure, and operating
system paging/crash dumps or a compromised administrator can expose memory.
Removing the key does not revoke plaintext already recovered. Local snapshots
and restored evidence are plaintext under owner-only permissions. This hardware
control protects access to the encryption identity, not all data on the computer.

Enrollment verified fresh recovery with both physical keys and rejected using the
primary credential on the spare. No existing login credential was reset. The
capsule contains encrypted identity bytes plus public credential metadata; keep
it outside Git and ordinary backup bundles. The receiver stores it separately
from the age-encrypted snapshots, avoiding a circular recovery dependency.
Its independent SHA-256 pin is in the public acceptance metadata.

Store the spare securely away from the computer, ideally at a separate physical
location. An additional offline copy of the encrypted capsule and its trusted
hash is useful; a second folder on this workstation is not disaster recovery.
Either enrolled key plus its PIN and the capsule can recover the identity.
If both devices are lost/reset or their PINs become unusable, this scheme has no
password-only bypass. Do not reset a key during troubleshooting. Replacement-key
enrollment must first recover the existing identity with a surviving key; do not
generate a new identity and assume old snapshots will decrypt.

## Local operator files and finite commands

The actual owner-only locations are:

- `C:/Users/madis/Documents/TradeTheoristHardwareRecovery`: encrypted capsule,
  public recipients, enrollment receipt and pinned `remote-config.json`.
- `C:/Users/madis/Documents/TradeTheoristRemoteRecovery`: independent remote
  object pins, operation receipts, downloaded ciphertext and offline rehearsals.
- `C:/Users/madis/Documents/TradeTheoristRecovery`: consistent local snapshots.

The optional operator environment is separate from the frozen scientific runtime.
It installs the repository and [requirements-hardware-recovery.txt](../requirements-hardware-recovery.txt).
The rehearsed snapshot records software revision `ce00e18`; retrieve its optional
dependency file from that trusted repository revision if it is absent from the
snapshot. Subsequent snapshots also include that top-level file directly.
The current environment is `.local/ykman-env`; Windows raw FIDO access requires
an administrator console. Enter PINs only in that local console, never in chat,
configuration, command arguments or logs. `--key primary` and `--key spare` select
different capsule entries: connect the corresponding physical key only.

The official age v1.3.2 Windows archive was checked against its upstream SHA-256
`f48d8f8f9ebe903ab5027ed067652f2cc1db94bc206976430133b905dcd8e8c7`.
The executable itself is pinned in private configuration and public acceptance
metadata. Obtain binaries from the [official releases](https://github.com/FiloSottile/age/releases).
Do not substitute an unverified executable found on PATH.

Create the local snapshot using the local runbook, then run from the checkout:

```powershell
$operator = '.local/ykman-env/Scripts/python.exe'
$hardware = 'C:/Users/madis/Documents/TradeTheoristHardwareRecovery'
$recovery = 'C:/Users/madis/Documents/TradeTheoristRemoteRecovery'
& $operator scripts/run_step_11_remote_backup.py roundtrip --config "$hardware/remote-config.json" --local-root $recovery --identity "$hardware/recovery-capsule.json" --key primary --interactive --bundle <absolute-bundle-path> --manifest-hash <independent-manifest-hash>
& $operator scripts/run_step_11_remote_backup.py prune --config "$hardware/remote-config.json" --local-root $recovery --identity "$hardware/recovery-capsule.json" --key primary --interactive --keep 3
```

Encryption uses public recipients and needs no device; verifying or restoring
requires PIN and touch. Every upload has a unique identity and bounded length.
The receiver hashes it before atomic publication. Failed uploads stay `.partial`;
successful uploads remain unverified until a separate download, authenticated
decryption and offline ledger restore succeeds. Client failures leave the remote
object available for inspection; do not treat an upload receipt as recovery proof.

Retention is explicit. It considers only independently pinned objects belonging
to this installation, freshly downloads/decrypts/restores a survivor before
deletion, and keeps at least one verified backup. Corrupt, partial and unverified
objects are retained for investigation. The receiver independently refuses to
delete its designated survivor. No scheduled cleanup is installed.

## Recovery after loss of the workstation

1. Obtain a trusted copy of this repository, the public acceptance metadata, a
   supported Python installation, the pinned age binary and the optional operator
   dependencies. Preserve the wheelhouse separately if fully offline installation
   is required. This rehearsal did not destroy/rebuild the physical workstation.
2. Reprovision the owner's SSH access according to the CRCS guide and verify the
   host key through a trusted source. The FIDO recovery credential does not log
   into the server. Provider credentials are separately reprovisioned only after
   the activation gate; neither is inside a snapshot or recovery capsule.
3. Create a private bootstrap JSON configuration containing `schema_version: 1`,
   `profile: "crcs-lab"`, `storage_terms_recorded: true`, the reviewed storage
   record, `receiver_sha256`, the receiver path above, and `capsule_sha256` from
   trusted acceptance metadata. Capsule retrieval does not require the age binary,
   a local recipient file or a FIDO key, so no circular prerequisite exists.
4. Run `fetch-capsule` with that config and a new private destination. The command
   verifies the downloaded encrypted capsule against the independent pin.
5. Install/verify age and add `age_executable`, `age_sha256`, `recipients_file`,
   `recipients_sha256`, `identity_mode: "fido2_envelope"` and
   `hardware_key_label: "spare"` to the private configuration. Write the capsule's
   public `recipient` plus a newline to the recipient file and hash its exact
   bytes. Use paths appropriate to the replacement computer.
6. Save `surviving_remote_object` from trusted public acceptance metadata as a
   private `object.json`. Restore with the spare connected, its PIN and touch.

```powershell
& $operator scripts/run_step_11_remote_backup.py fetch-capsule --config <private-config> --local-root <new-private-capsule-directory>
& $operator scripts/run_step_11_remote_backup.py restore --config <private-config> --local-root <new-private-restore-directory> --identity <downloaded-capsule-path> --key spare --interactive --metadata <private-object-json>
```

Downloaded ciphertext must match its pinned length and hash. age authenticates
decryption; any partial plaintext archive is removed on failure. Archive extraction
rejects links, path escapes, duplicate members and oversized content. The local
restore then checks database integrity, chains, references, immutable reports,
frozen learning/runtime inputs, request state and replayed accounting. It produces
`evidence.sqlite3` and an offline-only marker, without any provider/model call.
Follow the local runbook's single-owner reconciliation gate before considering
account activation. Restoring spent quotas does not authorize a second live owner.

## Evidence and limits

Public acceptance metadata records counts/hashes, the surviving remote object,
actual recovery time including human interaction, and observed record/attempt
loss against the unchanged source. Private receipts retain start/end times and
sanitized failure types. Cancelled PIN prompts remain failed operations; they
never become successful receipts merely because a later attempt succeeds.

Software tests cover actual age encryption/authentication, altered capsules,
missing-device and interaction gates, interrupted enrollment resume, server
publication failures, bounded extraction, offline ledger reconciliation and
last-survivor retention. Actual device enrollment and the remote rehearsal are
separate evidence from those tests. Future loss is work since the newest surviving
snapshot; finite rehearsal measurements do not promise a future RTO/RPO.
Step 15 separately authorizes recurrence and monitoring. Step 11's future
observation window and Step 12's paper gate remain unchanged.

September 7 actual result: **466 files, 6 reports, 177 v2 records,
9 spent requests and 30 reconciled performance results**. Spare recovery took
**44.26 seconds**, including user prompts and server access. Observed record/attempt
loss was zero against the unchanged source. Two invalid transfers were rejected;
capture to the first verified remote copy took 453.724 seconds, including attended
setup and the cancelled-PIN retry. This is distinct from the spare recovery time.
one older verified object was removed after fresh survivor recovery, leaving one
verified remote snapshot. All 394 tests across 39 modules passed, plus the clean
offline installation and 1,983 field classifications.
