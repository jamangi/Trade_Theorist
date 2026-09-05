"""Public logs are deliberately narrow; free text and exception messages stay private."""

import json
import re

_CODES = {"started", "complete", "blocked", "operation_failed", "contract_invalid", "usage_exhausted", "access_unknown"}


def public_log(code, *, run_id=None, phase=None, **private_fields):
    result = {"code": code if code in _CODES else "operation_failed"}
    # Hash-like run identifiers only: an arbitrary user string could itself be a secret.
    if isinstance(run_id, str) and re.fullmatch(r"run:[a-f0-9]{64}", run_id):
        result["run_id"] = run_id
    if phase in {"prepare", "execute", "export", "learn", "library"}:
        result["phase"] = phase
    return json.dumps(result, sort_keys=True)
