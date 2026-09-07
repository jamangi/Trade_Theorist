"""Offline paired orchestration over the durable shared Market Data owner."""
from copy import deepcopy
import json
import math
from threading import RLock

from ..contracts import ContractError, canonical, digest, utc
from ..contracts_v2 import validate_references
from ..market_requests import query, stamp
from .validation import comparison, participant
from ..adapters.alpaca_market_data.transport import SingleAttemptTransport


class DeadlineDuringCommit(ContractError):
    pass


def envelope(manifest, kind, identifier, at, **fields):
    common = {k: manifest[k] for k in ("experiment_id", "contamination", "provenance")}
    return dict(common, schema_version=2, record_type=kind, id=identifier, created_at=at,
        field_class="private_market_provenance" if kind == "forward_snapshot" else "private_strategy", **fields)


def freeze_round(coordinator, *, manifest_id, participants, baseline, value, start_at, end_at,
                 data_deadline, decision_at, max_request_attempts, model_budget, stopping_rule):
    """Freeze original v2 identities and policy before a single paired decision round.

    participants are (portfolio, accounting plan, funded segment) IDs; baseline is
    (portfolio, accounting plan). This engineering path is explicitly fixture-only.
    """
    if not coordinator.synthetic or isinstance(coordinator.transport, SingleAttemptTransport):
        raise ContractError("Real forward operation requires the later qualification and eligibility gates")
    q = query(value)
    with coordinator.db:
        store = coordinator.store
        peers = [participant(store.v2_record, *p) for p in participants]
        if not peers: raise ContractError("Paired portfolios are required")
        scope = store.v2_record(peers[0][0]["portfolio_ref"])
        base, base_plan = (store.v2_record(i) for i in baseline)
        expected = len(q["symbols"]) * len(q["expected_sessions"])
        estimated_pages = max(1, math.ceil(expected / q["page_limit"]))
        manifest = envelope(scope, "forward_manifest", manifest_id, stamp(coordinator.clock.wall()),
            start_at=start_at, end_at=end_at, data_deadline=data_deadline, decision_at=decision_at,
            snapshot_ref="snapshot:forward-" + digest([manifest_id, decision_at, digest(q)]),
            work_ref="work:" + digest(q), query=q, query_hash=digest(q), quota_policy=deepcopy(coordinator.policy),
            quota_policy_hash=digest(coordinator.policy), max_request_attempts=max_request_attempts,
            estimated_pages=estimated_pages, estimated_attempts_with_retries=estimated_pages * (1 + coordinator.policy["max_retries"]),
            estimate_is_bound=False, partial_coverage="require_complete", revision_rule="latest_received_before_cutoff", participants=[p[0] for p in peers],
            baseline_ref=base["id"], baseline_plan_ref=base_plan["id"], baseline_hash=digest(base), baseline_plan_hash=digest(base_plan),
            comparison_hash=digest(comparison(peers[0][1])), model_budget=deepcopy(model_budget), stopping_rule=deepcopy(stopping_rule),
            publication_class="private-owner-v2", broker_orders_allowed=False, evidence_grade="fixture", promotion_eligible=False)
        store.put_v2([manifest])
        return manifest


class RecordedDecisions:
    """Original offline opinions keyed by frozen portfolio ID; no external model."""
    def __init__(self, outputs):
        self.outputs, self.calls, self.snapshots = deepcopy(outputs), 0, []

    def complete(self, peer, snapshot):
        self.calls += 1
        self.snapshots.append(digest(snapshot))
        return deepcopy(self.outputs[peer["portfolio_ref"]])


class ForwardRound:
    def __init__(self, coordinator, manifest_id):
        if not coordinator.synthetic or isinstance(coordinator.transport, SingleAttemptTransport):
            raise ContractError("Step 07 is original-fixture integration only")
        self.owner, self.store = coordinator, coordinator.store
        with coordinator.db:
            self._manifest = self.store.v2_record(manifest_id)
            if self.manifest["record_type"] != "forward_manifest": raise ContractError("Expected forward manifest")
            validate_references(self.manifest, self.store.v2_record)
            if digest(coordinator.policy) != self.manifest["quota_policy_hash"]:
                raise ContractError("Shared owner differs from frozen quota policy")
            if not hasattr(coordinator, "_forward_locks"): coordinator._forward_locks = {}
            self.lock = coordinator._forward_locks.setdefault(manifest_id, RLock())

    @property
    def manifest(self):
        """Return a copy of the validated, frozen participant and budget contract."""
        return deepcopy(self._manifest)

    def _existing(self, identifier):
        with self.owner.db:
            row = self.store.connection.execute("SELECT body FROM v2_records WHERE id=?", (identifier,)).fetchone()
            return json.loads(row[0]) if row else None

    def _record(self, kind, identifier, **fields):
        return envelope(self.manifest, kind, identifier, stamp(self.owner.clock.wall()), manifest_ref=self.manifest["id"], **fields)

    def _put(self, *records):
        with self.owner.db: self.store.put_v2(records)

    def prepare(self, *, max_pages=100, before_commit=None):
        """Fetch before Character execution, then atomically freeze one common result."""
        with self.lock:
            m = self.manifest
            saved = self._existing(m["snapshot_ref"])
            if saved: return saved
            work = self.owner.submit(m["query"], consumer=m["id"], max_attempts=m["max_request_attempts"], deadline=m["data_deadline"])
            usage = self.owner.telemetry(work)
            physical_id = usage["shared_work_id"] or work
            physical = self.owner.telemetry(physical_id)
            budget_conflict = usage["status"] not in {"complete", "incomplete", "failed", "expired"} and physical["attempts"] + physical["remaining_attempts"] > m["max_request_attempts"]
            if not budget_conflict:
                usage = self.owner.run(work, max_pages=max_pages)
                physical = self.owner.telemetry(physical_id)
            expired = self.owner.clock.wall() >= utc(m["data_deadline"]).timestamp()
            reason = "deadline" if expired else "attempt_budget" if budget_conflict else usage["reason"]
            ready = usage["status"] == "complete" and not expired
            evidence = []
            if ready:
                revisions = {}
                for item in self.owner.evidence(work):
                    if item["bar"]["t"][:10] not in m["query"]["expected_sessions"]: continue
                    key = (item["bar"]["symbol"], utc(item["bar"]["t"]))
                    old = revisions.get(key)
                    if old and old["received_at"] == item["received_at"] and old["bar"] != item["bar"]:
                        ready, reason = False, "response"
                        break
                    if old is None or utc(item["received_at"]) > utc(old["received_at"]): revisions[key] = item
                if ready: evidence = [revisions[k] for k in sorted(revisions)]
            terminal = ready or expired or usage["status"] in {"failed", "expired", "incomplete"} or reason == "attempt_budget"
            terminal = terminal or reason == "response"
            state = "ready" if ready else "abstained" if terminal else "deferred"
            progress_fields = dict(snapshot_ref=m["snapshot_ref"], status=state, reason=reason,
                work_usage=usage, physical_usage=physical, physical_work_ref=physical_id,
                estimated_pages=m["estimated_pages"], estimated_attempts_with_retries=m["estimated_attempts_with_retries"],
                incomplete_pages=usage["status"] not in {"complete", "incomplete"}, deadline_missed=expired or usage["status"] == "expired",
                shared_consumers=len(m["participants"]), publication_class="private-owner-v2")
            progress = self._record("forward_progress", "forward-progress:" + digest([m["id"], progress_fields, stamp(self.owner.clock.wall())]), **progress_fields)
            if terminal:
                expected = {(s, d) for s in m["query"]["symbols"] for d in m["query"]["expected_sessions"]}
                observed = {(o["bar"]["symbol"], o["bar"]["t"][:10]) for o in evidence}
                snapshot = self._record("forward_snapshot", m["snapshot_ref"], work_ref=work, query_hash=m["query_hash"],
                    decision_at=m["decision_at"], status=state, reason=reason, observations=evidence,
                    coverage_expected=len(expected), coverage_observed=len(observed & expected), publication_class="private-owner-v2")
                try:
                    with self.owner.db, self.store.transaction():
                        self.store.put_v2([snapshot, progress])
                        if before_commit: before_commit()
                        if ready and self.owner.clock.wall() >= utc(m["data_deadline"]).timestamp(): raise DeadlineDuringCommit()
                except DeadlineDuringCommit:
                    snapshot.update(created_at=stamp(self.owner.clock.wall()), status="abstained", reason="deadline", observations=[], coverage_observed=0)
                    progress_fields.update(status="abstained", reason="deadline", deadline_missed=True)
                    progress = self._record("forward_progress", "forward-progress:" + digest([m["id"], progress_fields, stamp(self.owner.clock.wall())]), **progress_fields)
                    self._put(snapshot, progress)
                return snapshot
            self._put(progress)
            return progress

    def execute(self, provider, *, max_pages=100, after_reserve=None, before_commit=None):
        """Execute all recorded Characters against one snapshot, with atomic publication.

        Reservation precedes callbacks. An interrupted reserved round abstains on
        restart rather than spending again or recreating historical decisions.
        """
        if type(provider) is not RecordedDecisions:
            raise ContractError("Use the explicitly recorded offline Character provider")
        with self.lock:
            m = self.manifest
            result_id = "forward-result:" + digest(m["id"])
            old = self._existing(result_id)
            if old: return old
            snapshot = self.prepare(max_pages=max_pages)
            if snapshot["record_type"] != "forward_snapshot": return snapshot
            budget = m["model_budget"]
            reason = snapshot["reason"]
            calls = tokens = reserved_calls = reserved_tokens = 0
            outputs = []
            reservation_id = "forward-reservation:" + digest(m["id"])
            reservation = self._existing(reservation_id)
            if reservation: calls = tokens = None
            if snapshot["status"] == "ready":
                if self.owner.clock.wall() >= utc(m["decision_at"]).timestamp(): reason = "deadline"
                elif reservation:
                    reason = "execution_ambiguous"; calls = tokens = None
                elif len(m["participants"]) > budget["max_calls"] or len(m["participants"]) * budget["max_output_tokens"] > budget["max_tokens"]: reason = "model_budget"
                else:
                    reserved_calls, reserved_tokens = len(m["participants"]), budget["max_tokens"]
                    reservation = self._record("forward_reservation", reservation_id, snapshot_ref=snapshot["id"],
                        calls_reserved=reserved_calls, tokens_reserved=reserved_tokens)
                    self._put(reservation)
                    if after_reserve: after_reserve()
                    try:
                        for peer in m["participants"]:
                            if self.owner.clock.wall() >= utc(m["decision_at"]).timestamp():
                                reason = "deadline"; break
                            calls += 1
                            output = provider.complete(deepcopy(peer), deepcopy(snapshot))
                            if not isinstance(output, dict) or set(output) != {"action", "rationale", "tokens"} or output["action"] not in {"hold", "buy", "sell", "abstain"} or not isinstance(output["rationale"], str) or not output["rationale"]:
                                raise ContractError("Invalid recorded Character opinion")
                            if type(output["tokens"]) is not int or output["tokens"] < 0 or output["tokens"] > budget["max_output_tokens"] or tokens + output["tokens"] > reserved_tokens:
                                reason = "model_budget"; tokens = None; break
                            tokens += output["tokens"]; outputs.append(output)
                    except Exception:
                        reason = "execution_failed"  # Exception payloads never enter saved reports.
                        tokens = None
                    if self.owner.clock.wall() >= utc(m["decision_at"]).timestamp(): reason = "deadline"
            if reservation:
                reserved_calls, reserved_tokens = reservation["calls_reserved"], reservation["tokens_reserved"]
            outcomes = [dict(portfolio_ref=p["portfolio_ref"], character_ref=p["character_ref"], snapshot_ref=snapshot["id"],
                snapshot_hash=digest(snapshot), action="abstain" if reason != "none" else outputs[i]["action"], reason=reason,
                rationale="Shared round abstained: " + reason if reason != "none" else outputs[i]["rationale"])
                for i, p in enumerate(m["participants"])]
            result = self._record("forward_result", result_id, snapshot_ref=snapshot["id"], snapshot_hash=digest(snapshot),
                status="decided" if reason == "none" else "abstained", reason=reason, outcomes=outcomes,
                model_calls=calls, model_tokens=tokens, calls_reserved=reserved_calls, tokens_reserved=reserved_tokens,
                publication_class="private-owner-v2", evidence_grade="fixture", promotion_eligible=False, broker_orders=0)
            try:
                with self.owner.db, self.store.transaction():
                    self.store.put_v2([result])
                    if before_commit: before_commit()
                    if result["status"] == "decided" and self.owner.clock.wall() >= utc(m["decision_at"]).timestamp(): raise DeadlineDuringCommit()
            except DeadlineDuringCommit:
                result.update(created_at=stamp(self.owner.clock.wall()), status="abstained", reason="deadline")
                for outcome in result["outcomes"]:
                    outcome.update(action="abstain", reason="deadline", rationale="Shared round abstained: deadline")
                self._put(result)
            return result

    def report(self):
        """Read saved private evidence only; no download, Character call or maturation claim."""
        m = self.manifest
        with self.owner.db:
            row = self.store.connection.execute("SELECT body FROM v2_records WHERE record_type='forward_progress' AND json_extract(body,'$.manifest_ref')=? ORDER BY sequence DESC LIMIT 1", (m["id"],)).fetchone()
            progress = json.loads(row[0]) if row else None
            snapshot = self._existing(m["snapshot_ref"])
            result = self._existing("forward-result:" + digest(m["id"]))
            return dict(publication_class="private-owner-v2", evidence_grade="fixture", promotion_eligible=False,
                manifest_id=m["id"], snapshot_id=m["snapshot_ref"], status=result["status"] if result else snapshot["status"] if snapshot else "deferred" if progress else "pending",
                snapshot_hash=digest(snapshot) if snapshot else None, progress=progress, result=result,
                account_calls=0, external_model_calls=0, broker_orders=0, completed_real_sessions=0,
                blockers=["Original offline integration only; independent preflight, source qualification and real eligibility/elapsed evidence remain required."])
