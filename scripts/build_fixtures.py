"""Rebuild deterministic accepted/rejected contract and recorded learning fixtures."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from trade_theorist.contracts import digest
from trade_theorist.fixtures import *
from trade_theorist.learn import BoundedModel, Learner
from trade_theorist.storage import Store


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


bundle = complete_bundle()
write("schemas/fixtures/accepted/bundle.json", bundle)
for kind in ("policy", "experiment"):
    write(f"examples/{kind}.synthetic.json", next(r for r in bundle if r["record_type"] == kind))
paper = deepcopy(next(r for r in bundle if r["record_type"] == "policy"))
paper.update(id="policy:paper-template", experiment_id="experiment:paper-template", stage="paper", synthetic=False, contamination="forward-insufficient")
paper["limits"] = {key: None for key in paper["limits"]}
paper["universe"] = []
write("examples/paper-policy.template.json", paper)
experiment = deepcopy(next(r for r in bundle if r["record_type"] == "experiment"))
experiment.update(id="experiment:paper-template", experiment_id="experiment:paper-template", policy_id="policy:paper-template", regime="forward_paper", contamination="forward-insufficient", approval_ref=None)
experiment["universe"] = []
write("examples/preregistration.template.json", experiment)

cases = [
    ("missing-publication-eligibility", "observation", lambda r: r.pop("publication_eligibility")),
    ("invalid-confidence", "theory", lambda r: r.update(confidence=1.1)),
    ("unsupported-assets", "observation", lambda r: r.update(asset_class="crypto")),
    ("unknown-version", "theory", lambda r: r.update(schema_version=99)),
    ("incomplete-paper-policy", "policy", lambda r: r.update(stage="paper", synthetic=False, contamination="forward-insufficient")),
    ("float-money", "policy", lambda r: r["limits"].update(initial_cash=10000.0)),
    ("non-utc-clock", "observation", lambda r: r.update(published_at="2026-09-05T12:00:00-05:00")),
]
for name, kind, change in cases:
    candidate = deepcopy(next(r for r in bundle if r["record_type"] == kind))
    change(candidate)
    write(f"schemas/fixtures/rejected/{name}.json", candidate)
cross = deepcopy(bundle)
next(r for r in cross if r["record_type"] == "recommendation")["experiment_id"] = "experiment:foreign"
write("schemas/fixtures/rejected/cross-experiment.bundle.json", cross)
old = deepcopy(next(r for r in bundle if r["record_type"] == "theory"))
old["schema_version"] = 0
old["logic_chain"] = old.pop("minimal_logic_chain")
write("schemas/fixtures/migrations/theory-v0.json", old)
write("examples/learning/material.fixture.json", MATERIAL)

outputs = {}
def record_output(request, maximum):
    result = {"response": fixture_response(request["section"]), "usage": {"input_tokens": 0, "output_tokens": 0, "calls": 1, "cost_usd": "0.00"}}
    outputs[digest(request)] = result
    return result

with TemporaryDirectory() as root, patch("trade_theorist.storage.now", return_value="2026-09-05T20:00:00Z"), patch("trade_theorist.learn.model.now", return_value="2026-09-05T20:00:00Z"):
    with Store(root, synthetic=True) as store:
        store.put_records(base_records())
        model = BoundedModel(store, EXP, record_output, budget_id="budget:fixture-learning", model_id="recorded-fixture-v1", prompt_version="learning-v1", max_calls=2, max_tokens=100000, max_output_tokens=4000)
        learner = Learner(store, model)
        session = learner.freeze(character_version=CHAR, curriculum=CURRICULUM, constitution=CONSTITUTION, material=MATERIAL, source_id=SOURCE, position=1)
        learner.step(session)
        learner.step(session)
        write("examples/learning/checkpoints.fixture.json", [r for r in store.records() if r["record_type"] in ("checkpoint", "registration", "theory")])
write("examples/learning/recorded-outputs.fixture.json", outputs)
