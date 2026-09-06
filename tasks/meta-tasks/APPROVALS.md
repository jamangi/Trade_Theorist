# Meta-task owner approvals

**Owner decision recorded 2026-09-06:** the repository owner explicitly approved every
recommended choice in this register. Checked items authorize META-001 to adopt these
architecture and policy defaults. They do not authorize live capital, a paid plan,
public market-data display, an Alpaca account call or paper orders.

## UI and publication boundary

- [x] **Local/private primary UI.** Make the comprehensive single-page HTML/JS app a
  locally run interface over private artifacts; browser code receives no Alpaca key.
  - Recommended: approve. A local static build or loopback-only local service may be
    used, provided it cannot expose private data to the network by default.
- [x] **Public deployment.** Retire GitHub Pages from the active Alpaca-backed roadmap
  and preserve public publishing only as a future, separately approved derived-summary
  experiment after field-level rights review or written permission.
  - Recommended: approve. Repository documentation and synthetic demonstrations may
    remain public; real Alpaca observations and reconstructable price series remain
    private.
- [x] **Visible mode names.** Label the two primary tabs **Individual** and
  **Monarchy** while retaining stable internal `character_portfolios` and `council`
  identifiers.
  - Recommended: approve, with a short UI explanation that Monarchy means one selected
    lead makes the final decision after bounded advice and a deterministic risk gate.

## Paper attribution and performance

- [x] **Initial broker-execution scope.** Send only the Monarchy portfolio's approved
  orders to the shared Alpaca paper account; evaluate every Individual Character in a
  separate internal virtual portfolio using the same eligible market snapshot and
  declared fill model.
  - Recommended: approve. This prevents shared cash, buying power and net positions from
    contaminating comparisons. A later experiment may give each strategy a genuinely
    isolated paper account if the provider and owner support that arrangement.
- [x] **Order attribution.** Assign every submitted paper order a unique, nonsecret
  `client_order_id` that maps to experiment, portfolio and internal order records; keep
  the internal append-only ledger canonical.
  - Recommended: approve. Alpaca's ID helps reconciliation but does not create broker
    subaccounts or independent Character equity.
- [x] **Primary performance definition.** Use after-cost time-weighted portfolio return,
  maximum drawdown and return versus frozen cash/market baselines as the primary display;
  show dollar P/L, realized/unrealized components, exposure, turnover, evidence grade and
  sample size alongside it.
  - Recommended: approve. Use money-weighted return only as a secondary owner-capital
    measure when external deposits or withdrawals occur.
- [x] **Lot accounting.** Preserve every fill lot and corporate-action event; use FIFO
  as the default realized-gain convention while treating weighted-average cost as a
  display aid rather than the canonical history.
  - Recommended: approve for consistency and auditability. Tax reporting remains outside
    the paper-stage scope.

## Data rights and retention

- [x] **Conservative rights boundary.** Keep raw Alpaca data and replay caches private,
  outside Git, and out of public exports while seeking written confirmation covering
  private retention, internal replay, post-subscription retention and derived reporting.
  - Recommended: approve. API access alone is not treated as proof of every license
    right, and the current official prohibition on redistribution remains controlling.
