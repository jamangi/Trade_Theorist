"""Export the nonsecret shared-request contracts without opening a database."""
import json
from pathlib import Path
from trade_theorist.request_contracts import SCHEMAS

if __name__ == "__main__":
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$defs": SCHEMAS,
              "oneOf": [{"$ref": "#/$defs/" + name} for name in SCHEMAS]}
    path = Path(__file__).resolve().parents[1] / "schemas/market-requests-v1.json"
    path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Wrote shared-request contracts")
