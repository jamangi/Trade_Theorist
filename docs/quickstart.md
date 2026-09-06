# Run the offline observatory

From the repository root on Windows, use Python 3.14 (3.11 is also checked in CI):

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\trade-theorist.exe demo --projection-version 1 --serve
```

Open the printed local address, normally `http://127.0.0.1:8765/`. Stop the preview
with Ctrl+C. The demo itself needs no accounts, network access, books, external
model or credentials. Installing dependencies is a separate setup step.

The default fixture directory is `%LOCALAPPDATA%\TradeTheorist\fixture-demo-v1`
(or the home directory on platforms without `LOCALAPPDATA`). To choose it:

```powershell
.\.venv\Scripts\trade-theorist.exe demo --projection-version 1 --data-root C:\TradeTheorist\fixture-demo --serve
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

## Private v2: Individual and Monarchy

Step 04 adds the private command workflow. After installation, use dedicated roots:

```powershell
$tt = (Resolve-Path .\.venv\Scripts\trade-theorist.exe).Path
$v2Data = Join-Path $env:LOCALAPPDATA 'TradeTheorist\fixture-demo-v2'
$v2Bundle = Join-Path $env:LOCALAPPDATA 'TradeTheorist\fixture-bundle-v2'
& $tt demo --projection-version 2 --data-root $v2Data --output-root $v2Bundle
& $tt doctor --projection-version 2 --fixture --data-root $v2Data --output-root $v2Bundle
& $tt evaluate --projection-version 2 --fixture --data-root $v2Data --portfolio portfolio:v2-fixture-individual --as-of 2099-01-11T21:00:00Z --receipt-cutoff 2099-01-13T21:00:00Z
& $tt export --projection-version 2 --fixture --data-root $v2Data --output-root $v2Bundle --as-of 2099-01-13T21:00:00Z
```

The demo prints its bundle's `index.html`, a reusable portfolio ID and cutoff.
These are original synthetic scenarios: cash flows, FIFO lots, as-known/restated
values, separate simulated/paper results, missing marks and an unready Character.
`evaluate` defaults the receipt cutoff to `--as-of`; the explicit later receipt
above reproduces a restatement. Export includes all saved versions created by its
cutoff. It rejects `--experiment` filtering and makes no source or account calls.

**Step 05 owns browser launch and hardened private serving.** V2 `demo --serve`
reports this missing capability before writing. The v1 preview above remains
available. Repeat the same v2 demo command after interruption: a committed seed
and its evaluations are reused; export resumes independently. Use a new dedicated
root for a changed recipe. The demo refuses unrelated existing research records.

V2 doctor is read-only. `ready_with_gaps` allows inspection with explicit limitations.
Missing rights, migration or integrity problems give a concrete resume action.
Viewing permitted saved evidence does not require a trained Character, profitable
record or trading approval. Real inputs require recorded private storage/replay/
read-model permissions and roots outside Git; `--fixture` cannot grant rights.

The nonsecret [example config](../examples/operator.config.json) explicitly chooses
v2 and leaves both roots unset for your local choice. `schema_version: 1` describes
the config format; `projection_version: 2` selects accounting and the read model.
Without a version flag/config, commands retain legacy v1 behavior. CLI paths override
config, then `TRADE_THEORIST_DATA_ROOT` and `TRADE_THEORIST_PRIVATE_BUNDLE_ROOT`
provide fallbacks. Demo alone supplies a default root under
`%LOCALAPPDATA%\TradeTheorist\fixture-demo-v1` or `fixture-demo-v2` (home when
`LOCALAPPDATA` is absent); v2's default bundle is its `private-bundle` child.
Use `fixture: false` for real storage. Never put credentials in config or Git.

For a quick check:

```powershell
& $tt doctor --config examples/operator.config.json --data-root $v2Data --output-root $v2Bundle
.\.venv\Scripts\python.exe scripts/check.py
```

V1 doctor intentionally reports real-work blockers and exits 2 while prerequisites
remain missing; v2 doctor distinguishes inspection readiness from trading readiness.
The offline demos can still pass. Test output is one line per module;
complete logs stay in ignored `.local/test-logs/`.

See the [operating runbook](runbook.md) for individual commands, source learning,
CSV ingestion, evaluation, recovery, export boundaries and current limitations.
The [Step 04 guide](step-04-commands.md) gives the version contract, file/test map
and offline clean-installation check.

## META-001 boundary

Both demos use original synthetic fixtures. The public directory name and Council/
Character portfolios labels belong to v1, whose exporter refuses nonfixture sources.
Steps 03–04 implement permitted private v2 reporting with Individual/Monarchy labels.
Protected serving remains Step 05. [ADR-004](../decisions/records/ADR-004-local-observatory.md)
retires public Pages. Local use does not itself establish source retention or replay rights.
