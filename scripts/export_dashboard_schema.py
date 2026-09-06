"""Export the strict public dashboard schema without reading private data."""
import json
from pathlib import Path
from trade_theorist.export import DASHBOARD_SCHEMA

if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "schemas/dashboard-v1.json"
    target.write_text(json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema", **DASHBOARD_SCHEMA}, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Exported dashboard schema v1")
