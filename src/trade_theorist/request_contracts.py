"""Versioned, nonsecret Market Data operating contracts, independent of accounting."""
from jsonschema import Draft202012Validator, FormatChecker
from .schema import obj, array, enum, nullable, ID, UTC, N, BOOL, HASH
from .contracts import ContractError, canonical, utc

NUM = {"type": "number", "minimum": 0}
POLICY = obj(schema_version={"const": 1}, record_type={"const": "request_policy"},
    quota_id=ID, provider={"const": "alpaca"}, api={"const": "market_data"},
    hard_limit={"type": "integer", "minimum": 1, "maximum": 200},
    operating_limit={"type": "integer", "minimum": 1, "maximum": 180},
    max_work_attempts={"type": "integer", "minimum": 1, "maximum": 10000},
    max_retries={"type": "integer", "minimum": 0, "maximum": 10},
    max_wait_seconds=NUM, fallback_cap_seconds={"type": "number", "exclusiveMinimum": 0, "maximum": 60},
    entitlement_ref=ID, feed_delays=obj(iex=nullable(NUM), sip=nullable(NUM)),
    sharing_scopes=array(ID, 1), rights_ref=ID, private_storage={"const": True}, internal_replay={"const": True},
    cooperating_callers_only={"const": True}, verified_rate_headers=BOOL)
BAR_QUERY = obj(schema_version={"const": 1}, record_type={"const": "market_query"}, provider={"const": "alpaca"},
    endpoint={"const": "stock_bars"}, sharing_scope=ID, rights_ref=ID, feed=enum("iex", "sip"),
    symbols=array({"type": "string", "pattern": "^[A-Z][A-Z0-9.]{0,15}$"}, 1),
    timeframe={"const": "1Day"}, start=UTC, end=UTC, adjustment=enum("raw", "split", "dividend", "all"),
    asof=nullable({"type": "string", "format": "date", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"}),
    revision_policy=ID, freshness_after=UTC, information_cutoff=UTC,
    expected_sessions=array({"type": "string", "format": "date"}, 1),
    page_limit={"type": "integer", "minimum": 1, "maximum": 10000})
ACTION_QUERY = obj(schema_version={"const": 1}, record_type={"const": "market_query"}, provider={"const": "alpaca"},
    endpoint={"const": "corporate_actions"}, sharing_scope=ID, rights_ref=ID,
    symbols=array({"type": "string", "pattern": "^[A-Z][A-Z0-9.]{0,15}$"}, 1),
    start=UTC, end=UTC, revision_policy=ID, freshness_after=UTC, information_cutoff=UTC,
    data_quality={"const": "all"}, region={"const": "us"},
    page_limit={"type": "integer", "minimum": 1, "maximum": 1000})
QUERY = {"oneOf": [BAR_QUERY, ACTION_QUERY]}
TELEMETRY = obj(schema_version={"const": 1}, record_type={"const": "request_telemetry"}, quota_id=ID,
    work_id=ID, shared_work_id=nullable(ID), query_hash=HASH, status=enum("queued", "fetching", "waiting", "deferred", "complete", "incomplete", "expired", "failed"),
    reason=enum("none", "quota", "cooldown", "recovery", "page_limit", "attempt_budget", "deadline", "entitlement", "retry_limit", "transport", "response", "coverage", "busy"),
    attempts=N, retries=N, throttles=N, pages=N, cache_hits=N, subscribers=N, wait_seconds=NUM, queue_seconds=NUM,
    remaining_attempts=N, coverage_expected=N, coverage_observed=N, not_before=nullable(UTC),
    cooperating_callers_only={"const": True})
SCHEMAS = {"request_policy": POLICY, "market_query": QUERY, "request_telemetry": TELEMETRY}


def validate(value):
    try:
        canonical(value)
        schema = SCHEMAS[value["record_type"]]
        if list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value)):
            raise ContractError("Invalid request contract")
        if value["record_type"] == "request_policy":
            if value["operating_limit"] > value["hard_limit"] or value["feed_delays"]["sip"] is not None and value["feed_delays"]["sip"] < 900:
                raise ContractError("Operating ceiling or Basic SIP delay is invalid")
        if value["record_type"] == "market_query":
            if not utc(value["freshness_after"]) <= utc(value["information_cutoff"]) or not utc(value["start"]) < utc(value["end"]):
                raise ContractError("Invalid query window")
            if any(not value["start"][:10] <= day <= value["end"][:10] for day in value.get("expected_sessions", [])):
                raise ContractError("Expected sessions must belong to query window")
            if value['endpoint'] == 'corporate_actions' and any(utc(value[k]).strftime('%H:%M:%S.%f')!='00:00:00.000000' for k in ('start','end')):
                raise ContractError('Corporate action process-date bounds must be UTC midnight')
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError("Invalid nonsecret request contract") from exc
    return value


def policy(quota_id="quota:original-fixture", **changes):
    value = dict(schema_version=1, record_type="request_policy", quota_id=quota_id, provider="alpaca", api="market_data",
        hard_limit=200, operating_limit=180, max_work_attempts=30, max_retries=3, max_wait_seconds=2,
        fallback_cap_seconds=30, entitlement_ref="review:original-fixture", feed_delays=dict(iex=0, sip=900),
        sharing_scopes=["scope:original-fixture"], rights_ref="rights:original-fixture", private_storage=True,
        internal_replay=True, cooperating_callers_only=True, verified_rate_headers=False)
    return validate(value | changes)
