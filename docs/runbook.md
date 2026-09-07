# Operating commands and recovery

Step 04 adds explicit private v2 commands; use the [versioned command guide](step-04-commands.md)
and [Windows quickstart](quickstart.md) for their exact inputs. The table and source/
learning workflow below preserve the **legacy v1** interface. Pass
`--projection-version 1` to select it explicitly. The compatibility default is v1;
the updated example config explicitly selects v2. V2 doctor/export inspect an
existing database read-only. [Step 05](step-05-local-package.md) implements protected
`serve --projection-version 2 --data-root <path> --output-root <path>` and v2
`demo --serve`. Use a bundle outside Git, open the printed address, stop with Ctrl+C.
Export and restart for new evidence; the running snapshot never reloads disk.

[Step 06](step-06-shared-requests.md) adds the account-free `market-recorded --fixture`
collector and shared quota diagnostics. Configure `quota_root` and `quota_policy_path`,
or pass `doctor --quota-root <path> --quota-policy <path>`. Its `market_requests`
section distinguishes missing policy/state and a stopped owner from private
saved-data readiness. All collectors and heartbeat preparation share one owner;
independent processes fail closed. Preserve the bound quota store and registry.

All commands below run locally. `demo` is the complete no-account recipe. `doctor`
explains readiness; it does not grant it. An exit code of 0 means success, 2 means a
named prerequisite is missing, and 1 means a failed operation with a safe retry
instruction. Commands do not echo exception payloads or credential values.

Use `forward-fixture --output-root <directory>` for Step 07's four original paired
forward scenarios and saved private evidence. The [forward guide](step-07-forward-integration.md)
explains deferred snapshots, uniform abstention, budget reservation and recovery.
This command uses recorded data/opinions and temporary stores; it starts no real trial.

| Command | Available behavior |
| --- | --- |
| `doctor --data-root <absolute path> [--fixture] [--policy <JSON>]` | Runtime, writable storage, schema, optional credential presence and explicit source/policy/real-operation blockers |
| `demo [--data-root <absolute path>] [--serve] [--port 8765]` | Seed, run, resume, evaluate and export the full synthetic observatory; optional loopback preview |
| `library report` | Inspect the checked-in library inventory |
| `library verify-files --books-root <path>` | Check supplied local file fingerprints without extracting books |
| `library check --data-root <private path>` | Refresh bounded publisher availability checks; this explicit command uses network access |
| `learn --character <name>` | Inspect the recorded Index/Value/Trend learning state in the checkout |
| `learn --character <name> --plan <JSON> --data-root <path> [--fixture]` | Resume permitted, ordered learning using explicitly reviewed recorded responses; no live model provider |
| `ingest --experiment <id> --source <id/feed> --csv <path> --capability <JSON> --sessions <JSON> --data-root <path> [--fixture]` | Validate a permitted CSV, append only new revisions, report quarantine counts/reasons; does not fetch a vendor |
| `heartbeat --experiment council --data-root <demo path> --fixture` | Advance/resume the pinned council fixture heartbeat; aliases `index`, `value`, `trend`, `no-mail` and exact demo experiment IDs also work |
| `evaluate --data-root <path> [--experiment <id>] [--as-of <UTC>] [--fixture]` | Replay registered trials and resolve only eligible matured outcomes into immutable evaluation reports |
| `export --data-root <path> [--experiment <id>] [--as-of <UTC>] [--fixture]` | Validate allowlisted reports and atomically update the local read-only dashboard |
| `validate <report.json>` | Check a dashboard export's complete schema, references and content hash; existing contract validation is retained |

Operator commands also accept `--config examples/operator.config.json`. For a real
private store, omit `--fixture`; synthetic storage rejects real records. A requested
real heartbeat stops with the missing learning, qualified source and paper-policy
prerequisites. The generic heartbeat Python API is available for an explicitly
pinned operating plan; the CLI does not invent a real provider or launch future
tasks. Evaluation/export can operate on properly registered nonfixture records,
with restricted evidence kept private and regimes separated through the explicit
v2 private path. The legacy v1 exporter accepts original synthetic fixtures only.

## Source inputs

CSV ingestion requires a persisted experiment and policy, a source capability
record with internal replay/storage permission, a matching pinned feed, and the
explicit session schedule. Columns follow `CSVMarketAdapter.REQUIRED`; see
`examples/ingest/market.synthetic.csv`. Original publications and later revisions
retain their actual clocks. Correct quarantined rows and repeat the same command;
identical observations are deduplicated. The full demo already seeds its own
observations and does not need an additional import. Vendor qualification remains
task 014.

A reviewed learning plan contains exactly `records`, `character_version`,
`constitution`, `curriculum`, `material`, `source_id`, `position`, `outputs`,
`model_id`, `prompt_version`, and `budget_id`. `outputs` is the recorded-response
mapping keyed by complete request hash; the material and curriculum use the existing
Learner contracts. Source permissions, ordered sections and prior checkpoints
remain authoritative. Repeat the same plan to reuse completed checkpoints. A plan
cannot operate on a different Character than the command names. Future book
sections are not exposed in earlier model requests. There is no automatically
configured real model provider.

## Evaluation and review

Preregister each trial with `Evaluator.register_trial` before the declared start.
Pin its independent portfolio, session schedule, family, role and optional index
baseline/counterfactual link. The registry retains partial, failed, completed and withdrawn
trials. A second trial cannot reuse an existing trial's capital. Register price
threshold forecasts before their outcome using `register_forecast`; supply the
probability explicitly for that exact event rather than reinterpreting an unrelated
recommendation confidence. Outcome time, probability, raw-price predicate and feed
are fixed. Evaluation uses
only published and ingested observations available by its cutoff. Missing mature
outcomes are unscorable; immature ones remain pending.

Net returns use starting capital; external funding requires a separately designed
flow-adjusted method and is rejected here. Dividends and fees already enter ledger
equity and are not added/subtracted again. Turnover uses absolute fill notional over
mean daily equity. Hit rate counts fully closed round trips, including their costs;
partial sells do not manufacture closed-position wins. Missing scheduled marks
invalidate path-dependent metrics. Cash-only returns remain valid even without
trades; hit rate and calibration can remain unavailable.

The index baseline is a separate simulation with the same seed, opportunity set,
costs, dates and schedule. Its fixture policy explicitly permits the mechanical
buy-and-hold sizing; normal strategies retain their stricter turnover limits. It
uses the same reservation/next-open and dividend machinery. Counterfactual portfolios
have independent cash, policy, timing and holdings. `local_counterfactual` is only
a labeled raw price move, excludes execution/costs/sizing and must never be added
to strategy return.

`compare_advice` accepts matched frozen trials with opposite advice settings; it
does not infer causal skill from one pair. Fixture, hindsight, historical-qualified
and forward-insufficient evidence remain distinct. Promotion review requires a
complete declared forward window, at least the configured floor (never below 60
sessions/30 matured forecasts), complete marks and no halt, followed by an explicit
recorded owner review via `approve_forward_review`. Passing those gates does not
change council leadership or authorize paper/live trading. Hindsight and historical
replay cannot enter that review. Source/model contamination remains visible.

## Failures, recovery and export privacy

An interrupted heartbeat retains its lock for the same run ID. Repeat the same
command and data root; completed phases are reused. Another run cannot interleave.
Ambiguous external calls are not automatically retried. The CLI's current complete
recipe uses recorded fixture opinions only, so it has no external model charge.

For missing/stale market data, ingest a properly dated new observation, create a
new valid snapshot, and run a newly pinned cycle. Do not replace old snapshots.
For a halt, investigate and use the simulator's recorded owner reset only after
fresh reconciliation. For database recovery, use `Store.backup` and `Store.restore`
into a new private root and verify/reconcile before continuing.

Exports contain a strict allowlist: metrics, dates, identities, short generated
summaries and approved fixture provenance. They exclude raw bars/books, private
reflections, full mail bodies, prompts, account identifiers and credentials.
META-001 restricts this v1 path to original synthetic fixture stores and fixture-only
records/reports; nonfixture export is refused before output creation. A private-inspection
label alone does not make real derived values safe to publish. The browser validates the same schema and SHA-256 content hash before
rendering, uses text nodes for content, and exposes no mutation endpoint.

Assets are content-addressed. A final atomic replacement of `public/index.html`
publishes the completed local build; a validation or pre-handoff failure keeps the
previous entry. The current report exposes up to 20 historical cutoffs, and normal
retention keeps 20 owned asset versions. Inaccessible/unrecognized folders are left
alone. The private event database and all-trial registry are never pruned by export.
Serve only `public`, never the data root. TASK-018's public Pages outcome is retired under
[ADR-004](../decisions/records/ADR-004-local-observatory.md). Private v2 export is
implemented in Steps 03–04 with a separate bundle root. Step 05 adds a manifest,
protected serving and retention of 20 verified compatible versions, preserving
unrelated/changed files. See its guide for the trust boundary and recovery rules.
These commands do not deploy a public website.
