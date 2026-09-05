"""Rebuild the public report from reviewed metadata without accessing private PDFs."""

import json
from pathlib import Path

from trade_theorist.inventory import render_report


if __name__ == "__main__":
    directory = Path(__file__).resolve().parents[1] / "library/catalog"
    catalog = json.loads((directory / "characters.json").read_text(encoding="utf-8"))
    (directory / "INVENTORY_REPORT.md").write_text(render_report(catalog), encoding="utf-8", newline="\n")
