"""Ordered, locked and resumable heartbeat execution.

The coordinator grants no trading authority.  Phase callbacks may only connect
already validated domain components; the simulator and governor remain the order
and policy authorities.  External work runs before the phase transaction and must
use an idempotent adapter such as :class:`ModelCallCache`.
"""

from jsonschema import Draft202012Validator

from ..contracts import ContractError, canonical, digest
from ..schema import USAGE


PHASES = (
    "freeze_snapshot",
    "mark_portfolio",
    "deliver_mail",
    "independent_opinions",
    "deliberation",
    "final_decisions",
    "risk_gate",
    "queue_execution",
    "evaluation_handoff",
    "export_handoff",
)


class HeartbeatInterrupted(RuntimeError):
    """Deterministic test/recovery interruption after a durable phase boundary."""


class ModelCallCache:
    """Reserve usage, call outside a phase transaction, and reuse exact completions."""

    def __init__(self, store, experiment_id, provider, *, budget_id, model_id,
                 prompt_version, max_calls, max_tokens, max_output_tokens):
        if any(type(value) is not int or value <= 0 for value in (max_calls, max_tokens, max_output_tokens)):
            raise ValueError("Usage caps must be positive integers")
        self.store, self.experiment_id, self.provider = store, experiment_id, provider
        self.budget_id, self.model_id, self.prompt_version = budget_id, model_id, prompt_version
        self.max_calls, self.max_tokens, self.max_output_tokens = max_calls, max_tokens, max_output_tokens
        self.budget = {"budget_id": budget_id, "model_id": model_id, "prompt_version": prompt_version,
                       "max_calls": max_calls, "max_tokens": max_tokens,
                       "max_output_tokens": max_output_tokens}

    def complete(self, request, *, source_ids, completed_at):
        if (not isinstance(request, dict) or request.get("experiment_id") != self.experiment_id
                or request.get("model_id") != self.model_id
                or request.get("prompt_version") != self.prompt_version
                or request.get("tools") != [] or request.get("source_ids") != source_ids):
            raise ContractError("Model request must pin experiment, model, prompt and no tools")
        if not source_ids:
            raise ContractError("Model call needs frozen source provenance")
        if len(source_ids) != len(set(source_ids)):
            raise ContractError("Model source provenance must be unique")
        for source_id in source_ids:
            source = self.store.record(source_id, "source")
            if source["experiment_id"] not in (None, self.experiment_id):
                raise ContractError("Model source belongs to another experiment")
        request_hash = digest(request)
        call_id = "call:" + digest([self.experiment_id, self.budget_id, request_hash])
        reserve = len(canonical(request).encode("utf-8")) + self.max_output_tokens
        budget_event = "budget:" + digest([self.experiment_id, self.budget_id])
        with self.store.transaction():
            self.store.append(budget_event, self.experiment_id, "model.budget", self.budget)
            events = self.store.events(self.experiment_id)
            completed = next((event for event in events if event["id"] == call_id + ":complete"), None)
            if completed:
                if completed["payload"]["input_hash"] != request_hash:
                    raise ContractError("Cached model call input mismatch")
                return completed["payload"]["response"], call_id, True
            if any(event["id"] == call_id + ":started" for event in events):
                raise ContractError("Ambiguous model call is not automatically retried")
            starts = [event for event in events if event["kind"] == "model.started"
                      and event["payload"]["budget_id"] == self.budget_id]
            if len(starts) >= self.max_calls or sum(e["payload"]["reserved_tokens"] for e in starts) + reserve > self.max_tokens:
                raise ContractError("Model usage ceiling reached before call admission")
            self.store.append(call_id + ":started", self.experiment_id, "model.started",
                              {"budget_id": self.budget_id, "input_hash": request_hash,
                               "request": request, "reserved_tokens": reserve,
                               "max_output_tokens": self.max_output_tokens}, created_at=completed_at)
        try:
            result = self.provider(request, self.max_output_tokens)
            canonical(result)
            if set(result) != {"response", "usage"} or not Draft202012Validator(USAGE).is_valid(result["usage"]):
                raise ContractError("Provider must return response and explicit usage")
            usage = result["usage"]
            if (usage["calls"] != 1 or usage["output_tokens"] > self.max_output_tokens
                    or usage["input_tokens"] + usage["output_tokens"] > reserve):
                raise ContractError("Provider exceeded reserved usage")
            if len(canonical(result["response"]).encode("utf-8")) > self.max_output_tokens * 16:
                raise ContractError("Provider response exceeds storage bound")
            experiment = self.store.record(self.experiment_id, "experiment")
            call = {"id": call_id, "schema_version": 1, "record_type": "model_call",
                    "experiment_id": self.experiment_id, "created_at": completed_at,
                    "contamination": experiment["contamination"], "model_id": self.model_id,
                    "prompt_version": self.prompt_version, "input_hash": request_hash,
                    "response_hash": digest(result["response"]), "source_ids": source_ids,
                    "usage": usage}
            with self.store.transaction():
                self.store.put_records([call])
                self.store.append(call_id + ":complete", self.experiment_id, "model.complete",
                                  {"budget_id": self.budget_id, "input_hash": request_hash, **result},
                                  created_at=completed_at)
            return result["response"], call_id, False
        except Exception:
            self.store.append(call_id + ":failed", self.experiment_id, "model.failed",
                              {"budget_id": self.budget_id, "input_hash": request_hash,
                               "failure": "operation_failed", "charge_usd": None}, created_at=completed_at)
            raise

    def usage(self):
        events = self.store.events(self.experiment_id)
        starts = [event for event in events if event["kind"] == "model.started"
                  and event["payload"]["budget_id"] == self.budget_id]
        completions = [event for event in events if event["kind"] == "model.complete"
                       and event["payload"]["budget_id"] == self.budget_id]
        return {"admitted_calls": len(starts),
                "reserved_tokens": sum(event["payload"]["reserved_tokens"] for event in starts),
                "completed_calls": len(completions),
                "input_tokens": sum(event["payload"]["usage"]["input_tokens"] for event in completions),
                "output_tokens": sum(event["payload"]["usage"]["output_tokens"] for event in completions)}


class Heartbeat:
    """Run one pinned plan through all durable phases exactly once."""

    def __init__(self, store, run_id, *, phase_inputs, operations, external_operations=None):
        self.store = store
        self.manifest = store.record(run_id, "run_manifest")
        self.run_id = run_id
        self.experiment_id = self.manifest["experiment_id"]
        self.experiment = store.record(self.experiment_id, "experiment")
        if set(phase_inputs) != set(PHASES) or set(operations) != set(PHASES):
            raise ValueError("Every ordered heartbeat phase needs pinned input and an operation")
        if set(external_operations or {}) - set(PHASES):
            raise ValueError("External operation names must be heartbeat phases")
        self.phase_inputs = phase_inputs
        self.operations = operations
        self.external_operations = external_operations or {}
        self.plan_hash = digest({"phases": PHASES, "phase_inputs": phase_inputs})
        if self.manifest["input_hash"] != self.plan_hash:
            raise ContractError("Heartbeat plan differs from its immutable run manifest")
        if self.manifest["mode"] != self.experiment["mode"]:
            raise ContractError("Heartbeat mode differs from its experiment")

    def _lock_state(self):
        active = {}
        for event in self.store.events(self.experiment_id):
            if event["kind"] == "heartbeat.locked":
                active[event["payload"]["run_id"]] = event
            elif event["kind"] == "heartbeat.released":
                active.pop(event["payload"]["run_id"], None)
        return active

    def _acquire(self, at):
        with self.store.transaction():
            active = self._lock_state()
            if active and self.run_id not in active:
                raise ContractError("Another heartbeat holds the experiment lock")
            payload = {"run_id": self.run_id, "plan_hash": self.plan_hash, "acquired_at": at}
            previous = next((event for event in self.store.events(self.experiment_id, "heartbeat.locked")
                             if event["payload"]["run_id"] == self.run_id), None)
            if previous:
                if previous["payload"]["plan_hash"] != self.plan_hash:
                    raise ContractError("Resumed heartbeat lock has different inputs")
                return previous["payload"]
            self.store.append("heartbeat-lock:" + digest(self.run_id), self.experiment_id,
                              "heartbeat.locked", payload, created_at=at)
            return payload

    def _release(self, at):
        payload = {"run_id": self.run_id, "plan_hash": self.plan_hash, "released_at": at}
        prior = [event for event in self.store.events(self.experiment_id, "heartbeat.released")
                 if event["payload"]["run_id"] == self.run_id]
        if prior:
            return prior[0]["payload"]
        self.store.append("heartbeat-release:" + digest(self.run_id), self.experiment_id,
                          "heartbeat.released", payload, created_at=at)
        return payload

    def _validate_phase_output(self, phase, output):
        canonical(output)
        if not isinstance(output, dict):
            raise ContractError("Heartbeat phases return structured mappings")
        if phase == "freeze_snapshot":
            snapshot = self.store.record(output.get("snapshot_id"), "snapshot")
            if snapshot["experiment_id"] != self.experiment_id or output.get("snapshot_hash") != digest(snapshot):
                raise ContractError("Heartbeat did not freeze its own exact snapshot")
        if phase == "mark_portfolio":
            portfolio = self.store.record(output.get("portfolio_id"), "portfolio")
            if portfolio["experiment_id"] != self.experiment_id:
                raise ContractError("Heartbeat marked another experiment's portfolio")
        return output

    def run(self, *, at, crash_after=None):
        if crash_after is not None and crash_after not in PHASES:
            raise ValueError("Unknown crash boundary")
        self._acquire(at)
        outputs = {}
        for phase in PHASES:
            context = {"run_id": self.run_id, "experiment_id": self.experiment_id,
                       "phase": phase, "phase_input": self.phase_inputs[phase],
                       "prior_outputs": outputs}
            external = None
            if phase in self.external_operations:
                external = self.external_operations[phase](context)
                canonical(external)
            input_hash = digest({"plan_hash": self.plan_hash, "phase": phase,
                                 "phase_input": self.phase_inputs[phase],
                                 "prior_output_hashes": {key: digest(value) for key, value in outputs.items()},
                                 "external_hash": None if external is None else digest(external)})
            def operation(store, phase=phase, context=context, external=external):
                return self._validate_phase_output(phase, self.operations[phase](store, context, external))
            outputs[phase] = self.store.run_phase(self.run_id, self.experiment_id,
                                                  "heartbeat." + phase, input_hash, operation)
            if crash_after == phase:
                raise HeartbeatInterrupted("Interrupted after durable phase: " + phase)
        self._release(at)
        return {"run_id": self.run_id, "plan_hash": self.plan_hash, "phases": outputs,
                "output_hash": digest(outputs)}
