#!/usr/bin/env python3
"""Synthetic validator namespace tests; no experimental stages are invoked."""
from __future__ import annotations
import csv, importlib.util, json, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validate_experiment", REPO / "pipeline/validate-experiment.py")
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)

class DatasetNamespaceTests(unittest.TestCase):
    def test_same_id_in_smoke_and_final_is_accepted(self):
        seen = set()
        validator.register_run_identity(seen, "smoke", "C0-R001")
        validator.register_run_identity(seen, "final", "C0-R001")
        self.assertEqual(seen, {("smoke", "C0-R001"), ("final", "C0-R001")})

    def test_same_id_in_pilot_and_final_is_accepted(self):
        seen = set()
        validator.register_run_identity(seen, "pilot", "C1-R001")
        validator.register_run_identity(seen, "final", "C1-R001")

    def test_duplicate_id_within_final_is_rejected(self):
        seen = set()
        validator.register_run_identity(seen, "final", "C1-R001")
        with self.assertRaisesRegex(AssertionError, "within classification"):
            validator.register_run_identity(seen, "final", "C1-R001")

    def test_duplicate_id_within_pilot_is_rejected(self):
        seen = set()
        validator.register_run_identity(seen, "pilot", "P-C1-R001")
        with self.assertRaisesRegex(AssertionError, "within classification"):
            validator.register_run_identity(seen, "pilot", "P-C1-R001")

    def test_final_dataset_accepts_cross_class_collision(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for classification in ("pilot", "smoke", "final"):
                (root / "data/raw" / classification).mkdir(parents=True)
            research = root / "research"; research.mkdir()
            (research / "pilot-schedule-v1.csv").write_text(
                "sequence_number,block,ordinal_position,configuration,run_id\n")
            with (research / "final-schedule-pa003.csv").open("w", newline="") as out:
                writer=csv.DictWriter(out, fieldnames=["sequence_number","block","ordinal_position","configuration","run_id"])
                writer.writeheader()
                for block in range(1,21):
                    for position in range(1,8):
                        configuration=f"C{position-1}"
                        writer.writerow({"sequence_number":(block-1)*7+position,"block":block,"ordinal_position":position,"configuration":configuration,"run_id":f"{configuration}-R{block:03d}"})
            for classification in ("smoke", "final"):
                directory=root / "data/raw" / classification / "C0-R001"; directory.mkdir()
                record={"schema_version":"1.0","run_id":"C0-R001","classification":classification,"configuration":"C0","environment":{},"timings":{"total_ms":1},"resources":{},"tools":[],"security":{},"outcome":{"failure_stage":None},"validity":"VALID"}
                (directory / "run.json").write_text(json.dumps(record))
                for name in ("environment.json","timings.json","gate.json","normalized-findings.json"):
                    (directory / name).write_text("{}")
            saved_root, saved_schedule = validator.ROOT, validator.FINAL_SCHEDULE_PATH
            try:
                validator.ROOT=root; validator.FINAL_SCHEDULE_PATH=research / "final-schedule-pa003.csv"
                validator.runs()
            finally:
                validator.ROOT, validator.FINAL_SCHEDULE_PATH=saved_root, saved_schedule

    def _assert_classification_rejected(self, record):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for classification in ("pilot", "smoke", "final"):
                (root / "data/raw" / classification).mkdir(parents=True)
            research = root / "research"; research.mkdir()
            (research / "pilot-schedule-v1.csv").write_text(
                "sequence_number,block,ordinal_position,configuration,run_id\n")
            directory=root / "data/raw/final/C0-R001"; directory.mkdir()
            (directory / "run.json").write_text(json.dumps(record))
            for name in ("environment.json","timings.json","gate.json","normalized-findings.json"):
                (directory / name).write_text("{}")
            saved_root = validator.ROOT
            try:
                validator.ROOT=root
                with self.assertRaises((AssertionError, KeyError)):
                    validator.runs()
            finally:
                validator.ROOT=saved_root

    def test_malformed_classification_is_rejected(self):
        self._assert_classification_rejected({
            "schema_version":"1.0", "run_id":"C0-R001", "classification":"unknown",
            "configuration":"C0", "environment":{}, "timings":{"total_ms":1}, "resources":{},
            "tools":[], "security":{}, "outcome":{"failure_stage":None}, "validity":"VALID"})

    def test_missing_classification_is_rejected(self):
        self._assert_classification_rejected({
            "schema_version":"1.0", "run_id":"C0-R001", "configuration":"C0", "environment":{},
            "timings":{"total_ms":1}, "resources":{}, "tools":[], "security":{},
            "outcome":{"failure_stage":None}, "validity":"VALID"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
