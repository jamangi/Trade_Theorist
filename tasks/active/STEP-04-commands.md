# Step 04: Connect the private workflow to usable commands

- Status: implemented and verified 2026-09-06
- Recommended model / effort: Sol / medium
- Historical coverage: [TASK-013](../TASK-013-medium-Sol.md)
- Queue: [ordered remaining work](../README.md)
- Implementation guide: [versioned private commands and clean installation](../../docs/step-04-commands.md)
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

## Completion evidence (2026-09-06)

- Added `operations_v2.py` and CLI routing for explicit projection version/config,
  private output roots, receipt/effective cutoffs, per-portfolio evaluation, private
  artifact validation and provenance-aware export. Existing v1 commands/defaults
  remain available. Unsupported v2 ingest/heartbeat and export filtering report
  their boundary before mutation.
- Doctor and export use a read-only SQLite snapshot without store initialization
  or migration. Doctor reports checksum/chain failures, rights, reconciliation and
  valuation gaps without credential/account/source payloads. Inspection of permitted
  saved data is independent of training and trading readiness.
- V2 demo atomically seeds the existing production accounting fixture and saves a
  recipe receipt. Failed seeds roll back; failed exports retain the previous bundle;
  exact retries reuse saved work. New fixtures refuse unrelated research roots.
- Updated Windows quickstart, nonsecret config, runbook, operating design, development
  map and root/queue pointers. The new guide contains reproduction, recovery and
  the file/test map so a fresh task can continue without conversation history.
- Focused checks passed: `test_operations_v2` (14 new tests), `test_operations`,
  `test_export_v2`, `test_storage_v2`. Coverage includes offline execution, unchanged
  read-only stores, v1/missing/changed migration boundaries, rights and private paths,
  missing/newly halted reconciliation, interrupted seed/export, retries and config
  version overrides. Full suite: **231 tests, 25/25 modules passed in 59.0 seconds**
  via `python scripts/check.py`; detailed output stays in `.local/test-logs/`.
- `python scripts/check_installed.py --wheelhouse .local/wheelhouse` passed with a
  freshly built wheel and clean virtual environment outside the checkout, locked
  local dependencies, `--no-index` and a socket trap. Both versions passed demo,
  resume, evaluate, export, doctor and validate with zero model calls. Reproducible
  logs, generated reports and summary remain in ignored `.local/installed-logs/`.
  Dependency acquisition was separate; this validation made no external calls.
- No dashboard assets/schema changed; Step 03's recorded browser evidence remains
  applicable. No real provider, model, order or serving action occurred. Step 05
  still owns protected loopback launch/stop, manifest/asset admission and retention;
  it is the next task, not part of this completion.
