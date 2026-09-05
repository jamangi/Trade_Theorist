"""Provider-neutral bounded adapter; no paid provider or network tools are enabled."""

from jsonschema import Draft202012Validator

from ..contracts import ContractError, canonical, digest
from ..schema import USAGE
from ..storage import now


class UsageExhausted(RuntimeError):
    pass


class AmbiguousCall(RuntimeError):
    pass


class RecordedProvider:
    def __init__(self, outputs):
        self.outputs = outputs
        self.calls = 0

    def __call__(self, request, max_output_tokens):
        key = digest(request)
        if key not in self.outputs:
            raise ContractError("No recorded response for these exact inputs and versions")
        self.calls += 1
        return self.outputs[key]


class BoundedModel:
    def __init__(self, store, experiment_id, provider, *, budget_id, model_id, prompt_version, max_calls, max_tokens, max_output_tokens):
        if any(type(n) is not int or n <= 0 for n in (max_calls, max_tokens, max_output_tokens)):
            raise ValueError("Usage limits must be positive integers")
        self.store, self.experiment_id, self.provider = store, experiment_id, provider
        self.budget_id, self.model_id, self.prompt_version = budget_id, model_id, prompt_version
        self.max_calls, self.max_tokens, self.max_output_tokens = max_calls, max_tokens, max_output_tokens
        self.budget = dict(budget_id=budget_id, model_id=model_id, prompt_version=prompt_version, max_calls=max_calls, max_tokens=max_tokens, max_output_tokens=max_output_tokens)

    def complete(self, request):
        if request["model_id"] != self.model_id or request["prompt_version"] != self.prompt_version:
            raise ContractError("Model or prompt version changed")
        key = digest(request)
        call_id = "call:" + digest([self.experiment_id, self.budget_id, key])
        # UTF-8 byte count is a deliberately conservative input reservation. Provider
        # adapters must enforce max_output_tokens and report actual usage afterward.
        reserve = len(canonical(request).encode("utf-8")) + self.max_output_tokens
        with self.store.transaction():
            self.store.append("budget:" + digest([self.experiment_id, self.budget_id]), self.experiment_id, "model.budget", self.budget)
            events = self.store.events(self.experiment_id)
            done = next((e for e in events if e["id"] == call_id + ":complete"), None)
            if done:
                return done["payload"]["response"], call_id
            if any(e["id"] == call_id + ":started" for e in events):
                raise AmbiguousCall("Unfinished or failed call reserved usage; no automatic retry")
            starts = [e for e in events if e["kind"] == "model.started" and e["payload"]["budget_id"] == self.budget_id]
            if len(starts) >= self.max_calls or sum(e["payload"]["reserved_tokens"] for e in starts) + reserve > self.max_tokens:
                raise UsageExhausted("Model usage ceiling reached")
            self.store.append(call_id + ":started", self.experiment_id, "model.started", {"budget_id": self.budget_id, "input_hash": key, "request": request, "reserved_tokens": reserve, "max_output_tokens": self.max_output_tokens})
        try:
            result = self.provider(request, self.max_output_tokens)
            canonical(result)
            if set(result) != {"response", "usage"} or not Draft202012Validator(USAGE).is_valid(result["usage"]):
                raise ContractError("Provider must return response and explicit usage")
            usage = result["usage"]
            if usage["calls"] != 1 or usage["output_tokens"] > self.max_output_tokens or usage["input_tokens"] + usage["output_tokens"] > reserve:
                raise UsageExhausted("Provider exceeded reserved usage")
            # Keep even malformed semantic output privately; it will fail learning
            # validation on replay without making another call.
            if len(canonical(result["response"]).encode("utf-8")) > self.max_output_tokens * 16:
                raise ContractError("Provider response exceeds storage bound")
            timestamp = now()
            experiment = next(r for r in self.store.records() if r["id"] == self.experiment_id)
            call_record = dict(id=call_id, schema_version=1, record_type="model_call", experiment_id=self.experiment_id, created_at=timestamp, contamination=experiment["contamination"], model_id=self.model_id, prompt_version=self.prompt_version, input_hash=key, response_hash=digest(result["response"]), source_ids=[request["frozen"]["source_id"]], usage=usage)
            with self.store.transaction():
                self.store.put_records([call_record])
                self.store.append(call_id + ":complete", self.experiment_id, "model.complete", {"budget_id": self.budget_id, "input_hash": key, **result}, created_at=timestamp)
            return result["response"], call_id
        except Exception:
            self.store.append(call_id + ":failed", self.experiment_id, "model.failed", {"budget_id": self.budget_id, "failure": "operation_failed", "charge_usd": None})
            raise
