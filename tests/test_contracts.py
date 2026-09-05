from copy import deepcopy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

from trade_theorist.contracts import ContractError, digest, migrate_v0_theory, validate, validate_bundle
from trade_theorist.fixtures import complete_bundle
from trade_theorist.schema import FIELDS, schema


ROOT = Path(__file__).resolve().parents[1]


class ContractsTests(unittest.TestCase):
    def setUp(self):
        self.records = complete_bundle()
        self.by_kind = {r["record_type"]: r for r in self.records}

    def test_all_contracts_have_accepted_examples_and_standard_schema(self):
        self.assertEqual(set(FIELDS), set(self.by_kind))
        Draft202012Validator.check_schema(schema())
        self.assertEqual(schema(), json.loads((ROOT / "schemas/contracts-v1.json").read_text()))
        for record in self.records:
            self.assertTrue(Draft202012Validator(schema()).is_valid(record))
        validate_bundle(self.records)

    def test_every_required_field_rejected_when_missing(self):
        for record in self.records:
            for key in record:
                with self.subTest(record=record["record_type"], missing=key):
                    incomplete = deepcopy(record)
                    del incomplete[key]
                    with self.assertRaises(ContractError):
                        validate(incomplete)

    def test_rejected_fixture_files(self):
        paths = list((ROOT / "schemas/fixtures/rejected").glob("*.json"))
        self.assertGreaterEqual(len(paths), 8)
        for path in paths:
            with self.subTest(path=path.name), self.assertRaises(ContractError):
                value = json.loads(path.read_text())
                validate_bundle(value) if isinstance(value, list) else validate(value)

    def test_migration_is_explicit_and_does_not_mutate_prior(self):
        old = json.loads((ROOT / "schemas/fixtures/migrations/theory-v0.json").read_text())
        before = deepcopy(old)
        with self.assertRaises(ContractError):
            validate(old)
        new = migrate_v0_theory(old)
        self.assertEqual(old, before)
        self.assertEqual(new["schema_version"], 1)
        validate(new)
        with self.assertRaises(ContractError):
            migrate_v0_theory(new)

    def test_unknown_fields_and_nonfinite_confidence(self):
        for value in (float("nan"), float("inf"), -0.1, 1.01, True, "0.5"):
            with self.subTest(value=value), self.assertRaises(ContractError):
                validate(dict(self.by_kind["theory"], confidence=value))
        with self.assertRaises(ContractError):
            validate(dict(self.by_kind["theory"], extra="unknown"))

    def test_cross_experiment_reference_with_target_present(self):
        original = self.by_kind["portfolio"]
        foreign = dict(original, id="portfolio:foreign", experiment_id="experiment:foreign")
        self.records.append(foreign)
        self.by_kind["recommendation"]["portfolio_id"] = foreign["id"]
        with self.assertRaisesRegex(ContractError, "Cross-experiment"):
            validate_bundle(self.records)

    def test_reference_type_and_missing_target(self):
        for target in ("snapshot:does-not-exist", self.by_kind["policy"]["id"]):
            self.by_kind["recommendation"]["snapshot_id"] = target
            with self.assertRaises(ContractError):
                validate_bundle(self.records)

    def test_snapshot_rejects_late_and_quarantined_observations(self):
        for field, value in (("published_at", "2026-09-06T12:00:00Z"), ("ingested_at", "2026-09-06T12:00:00Z"), ("quality", "quarantined")):
            records = complete_bundle()
            observation = next(r for r in records if r["record_type"] == "observation")
            observation[field] = value
            next(r for r in records if r["record_type"] == "snapshot")["content_hash"] = digest([observation])
            with self.subTest(field=field), self.assertRaises(ContractError):
                validate_bundle(records)

    def test_snapshot_cannot_override_clock(self):
        self.by_kind["snapshot"]["clock_policy"] = deepcopy(self.by_kind["snapshot"]["clock_policy"])
        self.by_kind["snapshot"]["clock_policy"]["eligibility"] = "archived_publication"
        with self.assertRaises(ContractError):
            validate_bundle(self.records)

    def test_paper_policy_needs_numeric_limits_and_all_owners(self):
        policy = deepcopy(self.by_kind["policy"])
        policy.update(stage="paper", synthetic=False, contamination="forward-insufficient", approval_ref="test:explicit-policy-approval", approved_at=policy["created_at"], operator="test-owner", kill_switch_owner="test-owner", reconciliation_owner="test-owner", incident_owner="test-owner")
        validate(policy)
        for key in ("approval_ref", "approved_at", "operator", "kill_switch_owner", "reconciliation_owner", "incident_owner"):
            with self.subTest(key=key), self.assertRaises(ContractError):
                validate(dict(policy, **{key: None}))
        for key in policy["limits"]:
            candidate = deepcopy(policy)
            candidate["limits"][key] = None
            with self.subTest(limit=key), self.assertRaises(ContractError):
                validate(candidate)

    def test_preregistration_and_unknown_metrics(self):
        registration = self.by_kind["registration"]
        registration["evaluation_start"] = "2020-01-01T00:00:00Z"
        with self.assertRaises(ContractError):
            validate(registration)
        evaluation = self.by_kind["evaluation"]
        evaluation["metrics"][0]["null_reason"] = None
        with self.assertRaises(ContractError):
            validate(evaluation)

    def test_fixture_cannot_claim_full_reading_or_trained_readiness(self):
        with self.assertRaises(ContractError):
            validate(dict(self.by_kind["checkpoint"], reading_status="complete"))
        with self.assertRaises(ContractError):
            validate(dict(self.by_kind["character"], readiness="ready"))

    def test_abstention_and_active_recommendations(self):
        recommendation = self.by_kind["recommendation"]
        with self.assertRaises(ContractError):
            validate(dict(recommendation, abstention_reason=None))
        with self.assertRaises(ContractError):
            validate(dict(recommendation, action="buy", quantity="1"))
        active = dict(recommendation, action="buy", quantity="1", instrument_id="instrument:fixture-fund")
        validate(active)


if __name__ == "__main__":
    unittest.main()
