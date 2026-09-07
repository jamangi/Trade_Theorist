"""Write original recorded pages and a nonsecret policy/query; no network or private state."""
import json
from pathlib import Path
from trade_theorist.request_contracts import policy, validate

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1] / "examples/step-06"
    root.mkdir(exist_ok=True)
    query = validate(dict(schema_version=1, record_type="market_query", provider="alpaca", endpoint="stock_bars",
        sharing_scope="scope:original-fixture", rights_ref="rights:original-fixture", feed="sip", symbols=["AAPL", "MSFT"],
        timeframe="1Day", start="2020-01-02T00:00:00Z", end="2020-01-03T00:00:00Z", adjustment="raw", asof=None,
        revision_policy="revision:original-fixture", freshness_after="2020-01-02T20:00:00Z", information_cutoff="2020-01-04T00:00:00Z",
        expected_sessions=["2020-01-02"], page_limit=1000))
    bar = dict(t="2020-01-02T20:00:00Z", o=100, h=102, l=99, c=101, v=1000)
    pages = [dict(status=200, headers={}, body=dict(bars={symbol: [bar]}, next_page_token=token), received_at="2020-01-03T00:00:00Z")
             for symbol, token in (("AAPL", "second-symbol"), ("MSFT", None))]
    for name, value in (("policy", policy()), ("query", query), ("responses", pages)):
        (root / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Wrote three original Step 06 fixtures; no account data")
