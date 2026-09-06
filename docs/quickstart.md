# Run the offline observatory

From the repository root on Windows, use Python 3.14 (3.11 is also checked in CI):

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\trade-theorist.exe demo --serve
```

Open the printed local address, normally `http://127.0.0.1:8765/`. Stop the preview
with Ctrl+C. The demo itself needs no accounts, network access, books, external
model or credentials. Installing dependencies is a separate setup step.

The default fixture directory is `%LOCALAPPDATA%\TradeTheorist\fixture-demo-v1`
(or the home directory on platforms without `LOCALAPPDATA`). To choose it:

```powershell
.\.venv\Scripts\trade-theorist.exe demo --data-root C:\TradeTheorist\fixture-demo --serve
```

Only the generated `public` directory is served, on loopback. SQLite and private
mail stay outside that web root. A demo is fictional engineering evidence: council
and three individual sleeves, a separate index baseline, a no-mail trial, and a
rejected-decision counterfactual. Each has its own capital. A scripted discussion
ends in a council risk rejection; the individual portfolios demonstrate costs,
dividends and matured/pending forecasts. Trend deliberately lacks its final market
session so the report shows stale, unavailable results instead of a made-up mark.

Switch between **Council** and **Character portfolios**. Select a saved historical
report, experiment or advice setting. Use **Explain this result** for the six
questions and **Saved evidence** links for allowlisted provenance. The report
includes charts with exact table alternatives, keyboard tab navigation and narrow
screen layouts. No click starts a model call.

Repeat the same demo command after an interruption. It reuses committed heartbeat
phases, saved opinions, market observations, orders and fills. To start a distinct
experiment with changed recipe inputs, choose a new data root. Never edit the
database or overwrite old trades to restart a losing portfolio.

The nonsecret [example configuration](../examples/operator.config.json) leaves the
data root unset for an explicit local choice. `--data-root` overrides its setting,
then `TRADE_THEORIST_DATA_ROOT` provides the fallback. `fixture: true` is limited
to fixture storage; real storage must be an absolute path outside every Git
checkout. Never put credentials in this JSON or in Git.

For a quick check:

```powershell
.\.venv\Scripts\trade-theorist.exe doctor --config examples/operator.config.json
.\.venv\Scripts\python.exe scripts/check.py
```

Doctor intentionally reports real-work blockers and exits 2 while prerequisites
remain missing. The offline demo can still pass. Test output is one line per module;
complete logs stay in ignored `.local/test-logs/`.

See the [operating runbook](runbook.md) for individual commands, source learning,
CSV ingestion, evaluation, recovery, export boundaries and current limitations.

## META-001 boundary

This demo uses original synthetic fixtures. Its public directory name and current Council/Character portfolios labels belong to v1. The exporter refuses nonfixture sources; private real-data reporting is not yet implemented. [ADR-004](../decisions/records/ADR-004-local-observatory.md) retires public Pages and targets Individual/Monarchy labels through the [024/025 repair sequence](../tasks/meta-tasks/START-HERE.md). Local use does not itself establish source retention or replay rights.
