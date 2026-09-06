"""Inventory declared persisted/exported fields for META-001; no data is read."""

import argparse
import json
from pathlib import Path

from trade_theorist.schema import schema
from trade_theorist.export import DASHBOARD_SCHEMA


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "schemas/meta-001/field-classification-v1.json"


def paths(node, prefix=""):
    for name, child in node.get("properties", {}).items():
        path = prefix + "/" + name
        yield path
        yield from paths(child, path)
    if "items" in node:
        yield from paths(node["items"], prefix + "/*")
    for union in ("oneOf", "anyOf", "allOf"):
        for child in node.get(union, []):
            yield from paths(child, prefix)


def inventory():
    fields = set()
    for kind, definition in schema()["$defs"].items():
        fields.update("contracts-v1/" + kind + path for path in paths(definition))
    fields.update("dashboard-v1" + path for path in paths(DASHBOARD_SCHEMA))
    for name in ("performance-v2", "broker-attribution-v1"):
        value = json.loads((ROOT / "schemas/meta-001" / (name + ".schema.json")).read_text())
        fields.update(name + path for path in paths(value))
    result = {}
    for path in sorted(fields):
        key = path.rsplit("/", 1)[-1]
        if key in {"private_locator", "raw_response", "credentials", "api_key", "api_secret", "secret"}:
            category = "private_sensitive"
        elif "broker-attribution" in path:
            category = "private_attribution"
        elif key in {"price", "value", "quantity", "equity", "history", "holdings", "cash", "basis", "lots", "income", "fees", "metrics", "cumulative_notional", "cumulative_quantity"}:
            category = "private_reconstructable"
        elif "/observation/" in path or "/snapshot/" in path:
            category = "private_market_provenance"
        else:
            category = "private_strategy"
        result[path] = category
    return {
        "classification_version": "field-classification-v1",
        "default_for_unknown_fields": "deny_public_and_git_export",
        "default_for_untyped_event_payloads": "private_unclassified",
        "real_data_public_default": "deny",
        "synthetic_exception": "Only original project fixtures through the fixture-only exporter; labels alone do not prove origin",
        "note": "Schema-field inventory and conservative policy, not proof of vendor permission or a production private exporter",
        "fields": result,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = inventory()
    if args.check:
        if not DESTINATION.exists() or json.loads(DESTINATION.read_text()) != value:
            raise SystemExit("Field classification is stale; regenerate and review new fields")
        print(f"PASS: {len(value['fields'])} declared fields classified; unknown fields denied")
    else:
        DESTINATION.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"Wrote {len(value['fields'])} field classifications")


if __name__ == "__main__":
    main()
