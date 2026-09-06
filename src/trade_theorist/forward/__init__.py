"""Prospective shadow-run manifests and point-in-time evidence admission."""

from dataclasses import dataclass

from ..contracts import ContractError, canonical, digest, utc
from ..ingest.tool_policy import enforce_tool_access


class FutureInformationError(ContractError):
    pass


UNQUALIFIED_SOURCES = frozenset({"repository", "mail", "retrieval"})
QUALIFIED_SOURCES = frozenset({"qualified_market", "qualified_public_research"})


def freeze_manifest(*, manifest_id, frozen_at, start_at, end_at, horizon_sessions,
                    characters, opportunity_set, data_feed, retrieval_policy,
                    source_blockers=()):
    """Freeze a candidate run and retain blockers instead of inventing readiness."""
    if not manifest_id or horizon_sessions < 1 or not opportunity_set:
        raise ContractError("Forward manifest needs identity, horizon and opportunities")
    frozen, start, end = map(utc, (frozen_at, start_at, end_at))
    if not frozen < start < end:
        raise ContractError("Forward manifest must be frozen before its real window")
    blockers = list(source_blockers)
    eligible = []
    for character in characters:
        if character.get("readiness") == "ready" and character.get("version_hash"):
            eligible.append(character)
        else:
            blockers.append(f"Character {character.get('character_id', 'unknown')} has no eligible ready version.")
    opportunity_hash = digest(sorted(opportunity_set, key=canonical))
    manifest = {
        "schema_version": 1, "manifest_id": manifest_id,
        "mode": "forward_shadow", "status": "blocked" if blockers else "frozen",
        "frozen_at": frozen_at, "start_at": start_at, "end_at": end_at,
        "horizon_sessions": horizon_sessions,
        "characters": characters, "eligible_character_versions": eligible,
        "opportunity_set": opportunity_set,
        "opportunity_set_hash": opportunity_hash,
        "data_feed": data_feed, "retrieval_policy": retrieval_policy,
        "allowed_tools": ["calculator", "market_data_qualified", "public_research_qualified"],
        "broker_orders_allowed": False, "blockers": blockers,
    }
    manifest["content_hash"] = digest(manifest)
    return manifest


class ForwardEvidenceGate:
    """Admit only qualified, timestamped evidence available by a decision cutoff."""

    REQUIRED = frozenset({
        "source_kind", "source_id", "event_at", "published_at", "ingested_at",
        "availability_evidence", "payload_hash",
    })

    def __init__(self, *, manifest, decision_cutoff, provided_tools=()):
        expected_hash = digest({k: v for k, v in manifest.items() if k != "content_hash"})
        if manifest.get("content_hash") != expected_hash:
            raise ContractError("Forward manifest hash mismatch")
        if manifest["status"] != "frozen":
            raise ContractError("A blocked forward manifest cannot start")
        self.manifest = manifest
        self.cutoff = utc(decision_cutoff)
        if not utc(manifest["start_at"]) <= self.cutoff < utc(manifest["end_at"]):
            raise ContractError("Decision cutoff is outside the frozen run")
        enforce_tool_access("forward_shadow", provided_tools)
        self._evidence = {}

    def admit(self, item):
        if set(item) != self.REQUIRED:
            raise FutureInformationError("Evidence envelope has missing or unknown fields")
        if item["source_kind"] in UNQUALIFIED_SOURCES:
            raise FutureInformationError(
                "Generic repository, mail, and retrieval output is not admissible forward evidence"
            )
        if item["source_kind"] not in QUALIFIED_SOURCES:
            raise FutureInformationError("Evidence source is not a qualified adapter")
        event, published, ingested = map(
            utc, (item["event_at"], item["published_at"], item["ingested_at"])
        )
        if event > published or published > ingested:
            raise FutureInformationError("Evidence clocks are inconsistent")
        if published > self.cutoff or ingested > self.cutoff:
            raise FutureInformationError("Evidence became available after the decision cutoff")
        if not item["availability_evidence"].strip():
            raise FutureInformationError("Evidence needs availability proof")
        evidence_id = "forward-evidence:" + digest(item)
        prior = self._evidence.get(evidence_id)
        if prior is not None and canonical(prior) != canonical(item):
            raise FutureInformationError("Evidence identity changed")
        self._evidence[evidence_id] = dict(item)
        return evidence_id

    def snapshot(self):
        evidence = [{"id": key, **value} for key, value in sorted(self._evidence.items())]
        return {
            "manifest_id": self.manifest["manifest_id"],
            "decision_cutoff": self.cutoff.isoformat().replace("+00:00", "Z"),
            "opportunity_set_hash": self.manifest["opportunity_set_hash"],
            "evidence": evidence, "evidence_hash": digest(evidence),
        }


@dataclass(frozen=True)
class ShadowDecision:
    decision_id: str
    character_version: str
    created_at: str
    action: str
    opportunity_set_hash: str
    evidence_hash: str


def commit_shadow_decision(*, manifest, evidence_snapshot, character_version,
                           created_at, action):
    if manifest["status"] != "frozen" or character_version not in {
        value["version_hash"] for value in manifest["eligible_character_versions"]
    }:
        raise ContractError("Decision needs an eligible version in a frozen run")
    if not utc(manifest["start_at"]) <= utc(created_at) <= utc(evidence_snapshot["decision_cutoff"]):
        raise ContractError("Recommendation was not committed by its decision cutoff")
    if evidence_snapshot["opportunity_set_hash"] != manifest["opportunity_set_hash"]:
        raise ContractError("Character opportunity sets differ")
    core = [manifest["manifest_id"], character_version, created_at, action,
            evidence_snapshot["evidence_hash"]]
    return ShadowDecision("shadow-decision:" + digest(core), character_version,
                          created_at, action, manifest["opportunity_set_hash"],
                          evidence_snapshot["evidence_hash"])


def shadow_report(*, manifest, decisions=(), completed_session_closes=(),
                  matured_forecasts=0, model_usage=None, as_of):
    """A truthful dashboard-ready status summary; it never infers elapsed evidence."""
    as_of_time = utc(as_of)
    decisions = tuple(decisions)
    closes = tuple(sorted(set(completed_session_closes)))
    if any(utc(value) > as_of_time or not utc(manifest["start_at"]) <= utc(value) < utc(manifest["end_at"])
           for value in closes):
        raise ContractError("Completed sessions must be distinct elapsed closes inside the window")
    completed_sessions = len(closes)
    blockers = list(manifest["blockers"])
    if completed_sessions < manifest["horizon_sessions"]:
        blockers.append(
            f"Only {completed_sessions} real sessions elapsed; {manifest['horizon_sessions']} required."
        )
    if not decisions:
        blockers.append("No pre-outcome shadow recommendation has been committed.")
    if as_of_time < utc(manifest["end_at"]):
        blockers.append("The preregistered real-time observation window has not elapsed.")
    if matured_forecasts < 1:
        blockers.append("No forecast horizon has matured with an eligible outcome.")
    return {
        "schema_version": 1, "report_kind": "forward-shadow-status",
        "manifest_id": manifest["manifest_id"], "as_of": as_of,
        "status": "blocked" if manifest["status"] == "blocked" else "immature" if blockers else "matured",
        "evidence_grade": "forward-blocked" if manifest["status"] == "blocked" else "forward-immature" if blockers else "forward-observed",
        "completed_sessions": completed_sessions,
        "completed_session_closes": list(closes),
        "required_horizon_sessions": manifest["horizon_sessions"],
        "committed_decisions": len(decisions), "matured_forecasts": matured_forecasts,
        "broker_orders": 0, "model_usage": model_usage or {"calls": 0, "tokens": 0, "cost_usd": None},
        "opportunity_set_hash": manifest["opportunity_set_hash"],
        "blockers": blockers,
    }


__all__ = ["ForwardEvidenceGate", "FutureInformationError", "ShadowDecision",
           "commit_shadow_decision", "freeze_manifest", "shadow_report"]
