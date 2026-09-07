"""Original recorded v2 forward round, with explicit offline clocks and transport."""
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from ..adapters.alpaca_market_data import Response
from ..fixtures_accounting_v2 import FixtureV2
from ..market_requests import Coordinator, stamp
from ..request_contracts import policy
from .shared import freeze_round, RecordedDecisions, ForwardRound


class FixtureClock:
    def __init__(self):
        self.epoch = datetime(2099, 1, 1, 21, 1, tzinfo=timezone.utc).timestamp()
        self.elapsed = 0.0

    def wall(self): return self.epoch + self.elapsed
    def monotonic(self): return self.elapsed
    def sleep(self, seconds): self.elapsed += seconds
    def advance_to(self, at): self.elapsed += datetime.fromisoformat(at.replace("Z", "+00:00")).timestamp() - self.wall()


class RecordedPages:
    def __init__(self): self.responses, self.calls = [], []
    def __call__(self, method, url, params):
        self.calls.append(dict(params))
        if not self.responses: raise RuntimeError("Recorded transport exhausted")
        item = self.responses.pop(0)
        if isinstance(item, Exception): raise item
        return item


def setup(root, *, policy_changes=None, request_attempts=10, model_changes=None):
    clock, transport = FixtureClock(), RecordedPages()
    owner = Coordinator(root / "data", policy(**(policy_changes or {})), transport, synthetic=True,
        registry_root=root / "registry", clock=clock, jitter=lambda: .25)
    try:
        baseline = FixtureV2(owner.store, "forward-baseline", role="baseline", extra_instrument=True)
        peers = [FixtureV2(owner.store, name, mode=mode, baseline=baseline.portfolio, extra_instrument=True)
            for name, mode in (("forward-index", "character_portfolio"), ("forward-trend", "character_portfolio"), ("forward-council", "council"))]
        for p in [baseline, *peers]: p.event("funding", 1, amount="1000.00", boundary_mark_ids=[])
        risk = owner.store.v2_record(peers[0].scope["policy_id"])
        symbols = sorted(i["symbol"] for i in risk["universe"])
        value = dict(schema_version=1, record_type="market_query", provider="alpaca", endpoint="stock_bars",
            sharing_scope="scope:original-fixture", rights_ref="rights:original-fixture", feed="sip", symbols=symbols,
            timeframe="1Day", start="2099-01-02T00:00:00Z", end="2099-01-03T00:00:00Z", adjustment="raw", asof=None,
            revision_policy="revision:original-fixture", freshness_after="2099-01-02T21:00:00Z", information_cutoff="2099-01-03T21:05:00Z",
            expected_sessions=["2099-01-02"], page_limit=1)
        manifest = freeze_round(owner, manifest_id="forward:original-paired-round",
            participants=[(p.portfolio, "plan:" + p.name, p.segment) for p in peers], baseline=(baseline.portfolio, "plan:" + baseline.name), value=value,
            start_at="2099-01-02T00:00:00Z", end_at="2099-01-20T00:00:00Z", data_deadline="2099-01-03T21:05:00Z", decision_at="2099-01-03T21:10:00Z",
            max_request_attempts=request_attempts, model_budget=dict(model_ref="model:recorded-fixture", max_calls=3, max_tokens=100, max_output_tokens=20) | (model_changes or {}),
            stopping_rule=dict(horizon_sessions=5, min_completed_sessions=5, min_matured_forecasts=30, stop_at="2099-01-20T00:00:00Z", stop_on_data_failure=True))
        for index, symbol in enumerate(symbols):
            bar = dict(t="2099-01-02T21:00:00Z", o=100, h=102, l=99, c=101, v=1000)
            transport.responses.append(Response(200, {}, dict(bars={symbol: [bar]}, next_page_token="second-symbol" if index == 0 else None), "2099-01-03T21:00:00Z"))
        clock.advance_to("2099-01-03T21:00:00Z")
        provider = RecordedDecisions({p.portfolio: dict(action="hold", rationale="Original fixture opinion on the common complete evidence.", tokens=10) for p in peers})
        return owner, manifest, transport, provider
    except BaseException:
        owner.close()
        raise


def build_evidence(output):
    """Portable original fixtures; temporary durable stores never contain real data."""
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    evidence = dict(step="07", evidence_grade="fixture", account_calls=0, external_model_calls=0,
                    broker_orders=0, promotion_eligible=False, scenarios={})
    for name in ("complete", "budget", "cooldown", "deadline"):
        with TemporaryDirectory(prefix="forward-original-fixture-") as temp:
            owner, manifest, wire, provider = setup(Path(temp), request_attempts=1 if name == "budget" else 10)
            with owner:
                round = ForwardRound(owner, manifest["id"])
                if name in {"cooldown", "deadline"}:
                    delay = 120 if name == "cooldown" else 600
                    wire.responses.insert(0, Response(429, {"Retry-After": str(delay)}, {}, "2099-01-03T21:00:00Z"))
                first = round.execute(provider, max_pages=1)
                if name in {"cooldown", "deadline"}: owner.clock.sleep(delay)
                result = round.execute(provider)
                report = round.report()
                before = len(wire.calls)
                assert round.execute(provider) == result and len(wire.calls) == before
                assert len({o["snapshot_ref"] for o in result["outcomes"]}) == 1
                assert len({o["snapshot_hash"] for o in result["outcomes"]}) == 1
                assert result["status"] == ("decided" if name in {"complete", "cooldown"} else "abstained")
                owner.store.verify_v2()
                evidence["scenarios"][name] = dict(initial_status=first["status"], final_status=result["status"], reason=result["reason"],
                    snapshot_id=result["snapshot_ref"], shared_snapshot_hash=result["snapshot_hash"], consumers=len(result["outcomes"]),
                    physical_recorded_attempts=len(wire.calls), recorded_character_calls=provider.calls,
                    repeat_added_calls=len(wire.calls) - before, actual_usage=report["progress"]["physical_usage"])
                if name == "complete":
                    for filename, value in (("manifest", manifest), ("snapshot", owner.store.v2_record(manifest["snapshot_ref"])), ("private-report", report)):
                        (output / (filename + ".json")).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    (output / "acceptance.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8", newline="\n")
    return dict(status="fixture_only", scenarios=len(evidence["scenarios"]), account_calls=0, external_model_calls=0,
                broker_orders=0, report=str(output / "private-report.json"), evidence=str(output / "acceptance.json"))
