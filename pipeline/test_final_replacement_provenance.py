#!/usr/bin/env python3
"""Synthetic PA-003 final-attempt provenance tests; no pipeline stages are invoked."""
from __future__ import annotations
import csv, importlib.util, json, sys, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipeline"))
import experiment

spec = importlib.util.spec_from_file_location("validate_experiment", REPO / "pipeline/validate-experiment.py")
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)

REASON = "unexpected_functional_test_failure"

class FinalReplacementProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "research").mkdir()
        (self.root / "research/pilot-schedule-v1.csv").write_text("sequence_number,block,ordinal_position,configuration,run_id\n")
        for classification in ("pilot", "smoke", "final"):
            (self.root / "data/raw" / classification).mkdir(parents=True)
        self.schedule = self.root / "research/final-schedule-pa003.csv"
        with self.schedule.open("w", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=["sequence_number", "block", "ordinal_position", "configuration", "run_id"])
            writer.writeheader()
            for block in range(1, 21):
                for position in range(1, 8):
                    config = f"C{position-1}"
                    writer.writerow({"sequence_number": (block-1)*7+position, "block": block,
                                     "ordinal_position": position, "configuration": config,
                                     "run_id": f"{config}-R{block:03d}"})
        self.saved = (experiment.ROOT, experiment.FINAL_SCHEDULE_PATH, validator.ROOT, validator.FINAL_SCHEDULE_PATH)
        experiment.ROOT = self.root
        experiment.FINAL_SCHEDULE_PATH = self.schedule
        validator.ROOT = self.root
        validator.FINAL_SCHEDULE_PATH = self.schedule

    def tearDown(self):
        experiment.ROOT, experiment.FINAL_SCHEDULE_PATH, validator.ROOT, validator.FINAL_SCHEDULE_PATH = self.saved
        self.temp.cleanup()

    def args(self, run_id, config="C1", **overrides):
        values = dict(config=config, run_id=run_id, classification="final", original_slot_id=None,
                      scheduled_order=None, attempt_number=None, predecessor_attempt_id=None,
                      replacement_reason=None)
        values.update(overrides)
        return SimpleNamespace(**values)

    def write(self, run_id, validity, provenance=None, config="C1"):
        directory = self.root / "data/raw/final" / run_id
        directory.mkdir()
        record = {"schema_version":"1.0", "run_id":run_id, "classification":"final", "configuration":config,
                  "environment":{}, "timings":{"total_ms":1}, "resources":{}, "tools":[], "security":{},
                  "outcome":{"failure_stage":None}, "validity":validity}
        if provenance: record["replacement_provenance"] = provenance
        (directory / "run.json").write_text(json.dumps(record))
        for name in ("environment.json", "timings.json", "gate.json", "normalized-findings.json"):
            (directory / name).write_text("{}")

    def replacement(self, run_id, order=9, config="C1", **values):
        defaults = dict(original_slot_id="C1-R002", scheduled_order=order,
                        attempt_number=int(run_id[-2:]),
                        predecessor_attempt_id="C1-R002" if run_id.endswith("A02") else "C1-R002-A02",
                        replacement_reason=REASON)
        defaults.update(values)
        return experiment.replacement_provenance(self.args(run_id, config=config, **defaults))

    def test_valid_original_final_attempt(self):
        self.assertIsNone(experiment.replacement_provenance(self.args("C1-R002")))

    def test_invalid_original_then_valid_a02(self):
        self.write("C1-R002", "INVALID_RETRYABLE")
        provenance = self.replacement("C1-R002-A02")
        self.assertEqual(provenance["protocol_amendment"], "PA-003")
        self.assertEqual(provenance["evidence_directory"], "data/raw/final/C1-R002-A02")

    def test_invalid_original_and_a02_then_valid_a03(self):
        self.write("C1-R002", "INVALID_RETRYABLE")
        a02 = self.replacement("C1-R002-A02")
        self.write("C1-R002-A02", "INVALID_RETRYABLE", a02)
        self.assertEqual(self.replacement("C1-R002-A03")["attempt_number"], 3)

    def test_a04_and_unknown_slot_are_rejected(self):
        with self.assertRaises(ValueError): experiment.replacement_provenance(self.args("C1-R002-A04"))
        with self.assertRaises(ValueError): experiment.replacement_provenance(self.args("C1-R999"))

    def test_replacement_requires_invalid_predecessor_and_reason(self):
        with self.assertRaises(ValueError): self.replacement("C1-R002-A02")
        self.write("C1-R002", "VALID")
        with self.assertRaises(ValueError): self.replacement("C1-R002-A02")
        with self.assertRaises(ValueError): self.replacement("C1-R002-A02", replacement_reason=None)

    def test_nonretryable_predecessor_is_rejected(self):
        self.write("C1-R002", "INVALID_NONRETRYABLE")
        with self.assertRaises(ValueError): self.replacement("C1-R002-A02")

    def test_rejects_bad_link_configuration_and_order(self):
        self.write("C1-R002", "INVALID_RETRYABLE")
        with self.assertRaises(ValueError): self.replacement("C1-R002-A02", order=3)
        with self.assertRaises(ValueError): self.replacement("C1-R002-A02", config="C0")
        with self.assertRaises(ValueError): self.replacement("C1-R002-A03", predecessor_attempt_id="C1-R002")

    def test_rejects_replacement_after_valid_and_duplicate_valid_slot(self):
        self.write("C1-R002", "VALID")
        with self.assertRaises(ValueError): self.replacement("C1-R002-A02")
        with self.assertRaises(AssertionError):
            validator.assert_final_slot_limits({"C1-R002": [{"validity":"VALID"}, {"validity":"VALID"}]})
        with self.assertRaises(AssertionError):
            validator.assert_final_slot_limits({"C1-R002": [{"validity":"INVALID_RETRYABLE"} for _ in range(4)]})

    def test_historical_pa002_behavior_is_unchanged(self):
        original_root, original_final = experiment.ROOT, experiment.FINAL_SCHEDULE_PATH
        try:
            experiment.ROOT = REPO
            experiment.FINAL_SCHEDULE_PATH = REPO / "research/final-schedule-pa003.csv"
            args = SimpleNamespace(config="C1", run_id="P-C1-R002-A02", classification="pilot",
                original_slot_id="P-C1-R002", scheduled_order=8, attempt_number=2,
                predecessor_attempt_id="P-C1-R002", replacement_reason=REASON)
            self.assertEqual(experiment.replacement_provenance(args)["protocol_amendment"], "PA-002")
        finally:
            experiment.ROOT, experiment.FINAL_SCHEDULE_PATH = original_root, original_final

if __name__ == "__main__":
    unittest.main(verbosity=2)
