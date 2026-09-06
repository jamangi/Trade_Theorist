"""Build the checked-in, non-performance specimens for TASK-014 and TASK-015."""

import json
from pathlib import Path

from trade_theorist.forward import freeze_manifest, shadow_report


ROOT = Path(__file__).resolve().parents[1]


def write(relative, value):
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    quality = {
        "schema_version": 1,
        "report_kind": "market-data-quality",
        "vendor": "Alpaca",
        "feed": "sip",
        "sample_kind": "recorded_fixture",
        "checked_at": "2026-09-06T18:00:00Z",
        "coverage_status": "blocked",
        "observed_sessions": ["2026-09-04"],
        "expected_sessions": ["2026-09-03", "2026-09-04"],
        "missing_sessions": ["2026-09-03"],
        "revision_count": 1,
        "quarantine_count": 0,
        "blockers": [
            "No account-authorized Alpaca sample was supplied; fixture evidence cannot qualify required coverage.",
            "Expected market sessions are missing; no bars were synthesized.",
            "Private storage, internal replay and reporting rights remain unverified."
        ],
        "claims": [
            "This fixture demonstrates adapter mechanics only.",
            "It is not evidence of Alpaca account entitlement, coverage, timeliness or performance."
        ]
    }
    write("examples/ingest/alpaca-quality.blocked.json", quality)

    manifest = freeze_manifest(
        manifest_id="forward:pilot-candidate-2026-09-06",
        frozen_at="2026-09-06T18:00:00Z",
        start_at="2026-09-08T13:30:00Z",
        end_at="2026-12-05T00:00:00Z",
        horizon_sessions=60,
        characters=[
            {"character_id": "index_steward", "readiness": "partial", "version_hash": None},
            {"character_id": "value_rationalist", "readiness": "partial", "version_hash": None},
            {"character_id": "systematic_trend_operator", "readiness": "partial", "version_hash": None}
        ],
        opportunity_set=[
            {"instrument_id": "instrument:vti", "asset_class": "unleveraged_us_etf", "cadence": "daily_session"}
        ],
        data_feed="alpaca:sip:conditional-not-entitled",
        retrieval_policy="Only qualified timestamp-preserving market/public-research adapters; no generic repo, mail, retrieval, web or HTTP access",
        source_blockers=[
            "No account-authorized Alpaca sample demonstrates required coverage.",
            "Private storage, internal replay and derived reporting rights are unresolved.",
            "No paid SIP subscription has been authorized."
        ]
    )
    write("examples/forward-shadow/pilot-candidate.blocked.json", manifest)
    write("examples/forward-shadow/dashboard-status.blocked.json", shadow_report(
        manifest=manifest, decisions=(), completed_session_closes=(), matured_forecasts=0,
        as_of="2026-09-06T18:00:00Z"
    ))
    write("examples/forward-shadow/provenance-audit.fixture.json", {
        "schema_version": 1,
        "report_kind": "forward-provenance-control-audit",
        "evidence_grade": "fixture-control-test",
        "checked_at": "2026-09-06T18:00:00Z",
        "controls": {
            "repository_output_rejected": True,
            "mail_output_rejected": True,
            "generic_retrieval_output_rejected": True,
            "late_qualified_output_rejected": True,
            "publication_and_ingestion_clocks_preserved": True,
            "broker_tool_absent": True,
            "identical_opportunity_set_hash_enforced": True,
            "pre_cutoff_commit_enforced": True
        },
        "real_sessions_observed": 0,
        "performance_claim": None,
        "note": "Offline fixture test of controls only; see blocked pilot manifest for real-run prerequisites."
    })


if __name__ == "__main__":
    main()
