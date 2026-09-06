"""Rebuild a compact, original private UI fixture under ignored local output."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from trade_theorist.storage_v2 import V2Store
from trade_theorist.fixtures_dashboard_v2 import seed_dashboard
from trade_theorist.fixtures_accounting_v2 import at
from trade_theorist.export_v2 import export_private, PRIVATE_SCHEMA

root=Path(__file__).resolve().parents[1]
with TemporaryDirectory() as temporary, V2Store(temporary,synthetic=True) as store:
    seed_dashboard(store)
    entry=export_private(store,root/".local/private-v2-demo",as_of=at(13))
(root/"schemas/private-owner-v2.json").write_text(json.dumps(PRIVATE_SCHEMA,indent=2)+"\n",encoding="utf-8",newline="\n")
print("Verified private fixture: both modes, execution bases, historical correction, stale/pending/no-trade/unready states.")
print("Preview entry: .local/private-v2-demo/index.html")
