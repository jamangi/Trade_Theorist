"""Run from repository root after installing the package."""
import json
from pathlib import Path
from trade_theorist.schema import schema

Path("schemas").mkdir(exist_ok=True)
Path("schemas/contracts-v1.json").write_text(json.dumps(schema(), indent=2) + "\n", encoding="utf-8", newline="\n")
