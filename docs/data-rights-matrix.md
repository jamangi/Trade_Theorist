# Data rights, local visibility and publication classification

Checked: 2026-09-06. Architecture policy: [ADR-004](../decisions/records/ADR-004-local-observatory.md). No account or credential was accessed in this review. Source review is evidence for engineering restrictions, not a legal opinion or an amendment to a provider agreement.

## Primary evidence and confidence

| Evidence/version observed | What it establishes | What remains unknown |
| --- | --- | --- |
| [Alpaca Terms and Conditions](https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf), four-page PDF, sections Personal and Non-Commercial Usage and Content, retrieved 2026-09-06; no revision date was established | Describes personal/non-commercial use and restrictions on publication/distribution/commercial reuse without written consent; references additional applicable agreements | Exact private replay, storage duration, model-processing permission, post-subscription retention and this owner's applicable agreement set |
| [Redistribution support article](https://alpaca.markets/support/redistribute-alpaca-api), dated November 2022, retrieved 2026-09-06 | States Alpaca API data cannot be redistributed | Any separately negotiated exception; applicability to specific irreversible derived aggregates |
| [Market Data plans](https://docs.alpaca.markets/us/docs/about-market-data-api), current table retrieved 2026-09-06 | Basic historical 200/min and different real-time/history entitlements | Actual account-wide traffic and complete usage rights; a plan table is not a retention license |
| [Order documentation](https://docs.alpaca.markets/us/docs/working-with-orders), retrieved 2026-09-06, page says updated 19 days ago | Client IDs support order tracking; order timeout requires reconciliation rather than blind resubmission | An ID does not establish isolated account capital or independent strategy returns |
| [Paper-trading limitations](https://docs.alpaca.markets/us/docs/paper-trading), retrieved 2026-09-06 | Paper is simulated and omits several execution/economic effects, including dividends | Whether an apparent paper edge survives actual execution |

The support page's full article was visible in the official search result, while one full-page extraction returned navigation instead. Its restrictive statement is consistent with the retrieved Terms; no broader permission was inferred. Future rights review must save source URL, retrieval time, displayed version/date when available, content hash if permitted, exact intended use and the owner's applicable agreement or provider response. Do not contact Alpaca or accept terms during this meta-task.

## Field-level policy

[field-classification-v1.json](../schemas/meta-001/field-classification-v1.json) enumerates the exact declared fields from persisted v1 records, the current dashboard format, synthetic performance/attribution contracts and Steps 01–02's operational v2 records/storage columns, including private accounting results and reconciliation evidence. Step 02 checks source permissions for replay and result construction; browser exposure remains a later step. Regenerate with `python scripts/export_field_classification.py`; `--check` detects drift. Nested arrays retain wildcard field paths. Unknown fields and open-ended event payloads are private/unclassified and denied public/Git export, so an undeclared payload key cannot inherit permission from its container.

| Fields / examples | Local raw/private storage | Private owner read model | Git/public default |
| --- | --- | --- | --- |
| Credentials, secrets, private source paths (`source.private_locator`) | Secret/config store only; outside Git | Never send credentials or unrestricted paths to browser | Deny; do not emit even in diagnostic failures |
| Observation payloads, bars, quotes, trades, marks, feed/revision/time metadata | Quarantine/private only under the applicable rights policy; retention/replay confirmation remains open | Supply only necessary permitted fields after rights verification | Deny real data and reconstructable series |
| Holdings quantity/value, lot basis, fills, dividend values, cash/equity time series | Private canonical ledger; source rights/provenance retained | Necessary for inspection, subject to private-use rights | Deny: combinations can reconstruct prices even without raw bars |
| Returns, drawdown, benchmark differences, forecasts, confidence, operating cost | Private derived state | Display definitions, evidence status, timestamps and null reasons | Deny real-data summaries until separately approved field/use-specific evidence exists |
| Broker client/order IDs, account state, mappings, updates, reconciliation differences | Private attribution store | Show only necessary opaque local references and aggregate status; never credentials | Deny identifiers and account-derived values |
| Character constitution/memory/notes/messages and free-text explanations | Private unless independently reviewed for source rights and personal details | Owner-visible permitted authored analysis; no hidden chain-of-thought claim | Original analysis/metadata only through a separate reviewed document path; never automatically whitelist free text |
| Schema definitions, source code, original arithmetic fixtures, authored architecture documents | Repository-safe when they contain no private values | Allowed | Allowed as project-authored artifacts; labels do not turn vendor observations into synthetic data |
| Unknown keys, dynamic event payloads, unreviewed new summary fields | Private/unclassified | Omit from browser until typed and reviewed | Deny |

“Keep private” is a conservative location decision, not a claim that perpetual retention or replay is permitted. Existing source permission gates remain active. Do not copy existing raw samples into this repository to fill the matrix. Open rights questions block the corresponding real-source storage/replay/reporting use; original synthetic development can continue.

## Enforced now versus pending

**Enforced in this review:** the legacy v1 exporter only accepts original synthetic fixture stores and fixture outputs; non-fixture reports, private evidence and persisted real observation feeds fail before any output directory is created. Tests cover non-fixture input, a misleading fixture flag and output-class contamination. Exact field inventory is checked. This is a protective boundary, not a general licensed-data scrubber.

**Pending TASK-012/018 implementation:** a distinct versioned `private-owner-v2` read model, complete lineage checks, field-specific local rights checks, private bundle paths outside Git, loopback-only serving, browser/path/origin restrictions and no automatic public publishing. Source rights, publication class and information-regime contamination are separate dimensions. Do not overload `contamination=fixture` as a license grant.

The future server must reject non-loopback binding, unexpected Host/Origin, directory traversal, symlink/junction escape and requests outside the exact bundle allowlist; use no wildcard CORS, external assets, service worker or telemetry. `Cache-Control: no-store` and origin checks reduce unintended exposure but do not protect against a malicious process running as the same OS user. No blanket raw-data deletion or backup removal is authorized; retention decisions must preserve necessary lawful auditability and respect the actual agreement.

Possible later public summaries need a separate field-level reconstruction review and written permission where required. Redacting tickers or keys is insufficient if quantities, values or sequences reconstruct licensed data. No such public real-data export is enabled by this review.
