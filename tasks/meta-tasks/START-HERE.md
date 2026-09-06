# Start here after META-001

Updated 2026-09-06. **Steps 01–03 are implemented and verified; next is [Step 04: private commands](../active/STEP-04-commands.md).** [Step 01](../active/STEP-01-contracts.md) records the contract/storage evidence; [Step 02](../active/STEP-02-accounting.md) records the persistent accounting and offline reconciliation evidence.

The [ordered remaining-work list](../README.md) now runs from Step 01 onward. Use it instead of jumping between historical task IDs. The [crosswalk](../CROSSWALK.md) preserves all original scopes and evidence.

## Why this task first

The new accounting needs versioned identities, typed cash-flow/lot events and durable attribution before calculation or UI integration. Step 01 establishes that contract and a side-by-side synthetic migration; Step 02 implements and proves FIFO, flow-adjusted performance and offline attribution.

Average-cost accounting and no-external-flow endpoint returns retain their original valid scope. FIFO is the approved new lot-relief convention; it does not itself increase equity or profitability. Flow-adjusted TWR prevents deposits and withdrawals from becoming false returns.

The singular serialized name **character_portfolio** is already correct and remains unchanged alongside **council**. This spelling is unrelated to why the repair comes first. Individual/Monarchy are UI labels.

## Boundaries

META-001 is complete; see its [impact record](../../docs/meta-001-impact.md). Reference arithmetic is not a production migration. No new approval blocks Step 01's original-synthetic work. Later rights, trained-version, account-operation, paper-policy and elapsed-time gates are explicit in their own steps.

Step 01 stopped at its contract/storage boundary. Step 02 subsequently proved the production FIFO/TWR path and offline attribution, preserving v1. Step 03 subsequently delivered the private read model and browser views. Its [standalone guide](../../docs/step-03-private-dashboard.md) supplies reproduction commands, interfaces and checks without conversation history. Step 04 remains pending; updating this pointer does not start command integration or account activity.
