"""Generate the operational v2 contract; does not read private data."""
import json
from pathlib import Path
from trade_theorist.schema_v2 import schema

if __name__ == "__main__":
    path = Path(__file__).resolve().parents[1] / "schemas/contracts-v2.json"
    path.write_text(json.dumps(schema(), indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Wrote operational v2 contract schema")
