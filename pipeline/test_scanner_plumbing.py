#!/usr/bin/env python3
"""Synthetic scanner I/O and gate tests; never targets the research corpus."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from experiment import frozen_command, outcome_for_stages, stage
from normalize_findings import parse
from scanner_io import (
    CHECKOV_REPORT_FILENAME,
    load_json_report,
    resolve_checkov_report,
    validate_report,
)

ROOT = Path(__file__).resolve().parents[1]


class ScannerReportTests(unittest.TestCase):
    def test_concrete_checkov_report_and_empty_results(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "report-dir"
            output.mkdir()
            report = output / CHECKOV_REPORT_FILENAME
            report.write_text(json.dumps({"check_type": "terraform", "results": {"failed_checks": []}}))
            self.assertEqual(resolve_checkov_report(output), report)
            document = load_json_report(report)
            validate_report("checkov", document)
            self.assertEqual(parse("checkov", document, "S-C5-SYNTH", str(report)), [])

    def test_checkov_report_normalizes_synthetic_record(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "report-dir"
            output.mkdir()
            report = output / CHECKOV_REPORT_FILENAME
            report.write_text(json.dumps({"results": {"failed_checks": [{
                "check_id": "CKV_SYNTHETIC", "check_name": "Synthetic fixture check",
                "severity": "LOW", "file_path": "main.tf", "file_line_range": [1, 1],
            }]}}))
            normalized = parse("checkov", load_json_report(resolve_checkov_report(output)), "S-C5-SYNTH", str(report))
            self.assertEqual(len(normalized), 1)
            self.assertEqual(normalized[0]["classification"], "UNRESOLVED")

    def test_checkov_report_discovery_rejects_missing_multiple_and_unexpected_files(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            with self.assertRaises(ValueError):
                resolve_checkov_report(output)
            (output / CHECKOV_REPORT_FILENAME).write_text('{"results":{"failed_checks":[]}}')
            extra = output / "unexpected.json"
            extra.write_text("{}")
            with self.assertRaises(ValueError):
                resolve_checkov_report(output)
            extra.unlink()
            (output / "second.json").write_text("{}")
            with self.assertRaises(ValueError):
                resolve_checkov_report(output)

    def test_normalizer_rejects_directory_and_malformed_json(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ValueError):
                load_json_report(root)
            malformed = root / "bad.json"
            malformed.write_text("{")
            with self.assertRaises(ValueError):
                load_json_report(malformed)
            result = subprocess.run([
                sys.executable, str(ROOT / "pipeline/normalize_findings.py"),
                "--tool", "checkov", "--input", str(root), "--run-id", "S-C5-SYNTH",
                "--output", str(root / "out.json"),
            ], capture_output=True, text=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            malformed = root / "malformed.json"
            malformed.write_text("{")
            result = subprocess.run([
                sys.executable, str(ROOT / "pipeline/normalize_findings.py"),
                "--tool", "checkov", "--input", str(malformed), "--run-id", "S-C5-SYNTH",
                "--output", str(root / "out.json"),
            ], capture_output=True, text=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)

    def test_checkov_normalizer_rejects_malformed_shape(self):
        with self.assertRaises(ValueError):
            validate_report("checkov", {"results": {"failed_checks": {}}})

    def test_trivy_empty_report_and_invalid_shape(self):
        empty = {"SchemaVersion": 2, "ArtifactType": "container_image"}
        validate_report("trivy", empty)
        validate_report("trivy", {"SchemaVersion": 2, "ArtifactType": "container_image", "Results": []})
        self.assertEqual(parse("trivy", empty, "S-C4-SYNTH", "raw.json"), [])
        with self.assertRaises(ValueError):
            validate_report("trivy", {})


class RuntimeAndGateTests(unittest.TestCase):
    def test_trivy_command_is_offline_vulnerability_only_with_separate_db_mount(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp)
            run_dir.mkdir(exist_ok=True)
            (run_dir / "raw").mkdir()
            (run_dir / "container-image.iid").write_text("sha256:synthetic-image-id")
            runtime = run_dir / "writable-runtime"
            (runtime / "cache").mkdir(parents=True)
            (runtime / "tmp").mkdir()
            command = frozen_command("CONTAINER_SCANNING", run_dir, runtime)
            joined = " ".join(command)
            self.assertIn("--read-only", command)
            self.assertIn("--network", command)
            self.assertIn("none", command)
            self.assertIn("--scanners", command)
            self.assertIn("vuln", command)
            self.assertIn("--skip-db-update", command)
            self.assertIn("--skip-java-db-update", command)
            self.assertIn("dst=/frozen-db,readonly", joined)
            self.assertIn("dst=/tmp", joined)
            self.assertNotIn("misconfig", joined)
            self.assertNotIn("secret", joined)
            self.assertNotIn("--download-db-only", joined)

    def test_completed_findings_are_not_execution_errors(self):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.CompletedProcess([], 1, "", "")
            result.normalized = {"normalized_count": 1}
            record = stage("SCA", lambda: result, Path(temp), finding_exit_codes=(1,))
            self.assertEqual(record["status"], "SCAN_COMPLETED_WITH_FINDINGS")
            self.assertEqual(outcome_for_stages([record])["validity"], "VALID")

    def test_gate_separates_valid_finding_from_normalization_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            finding = {"finding_id": "synthetic-finding", "control": "SAST",
                       "classification": "SEEDED_TRUE_POSITIVE"}
            run = {"execution": [{"stage": "SAST", "status": "SCAN_COMPLETED_WITH_FINDINGS"}]}
            run_path, findings_path, gate_path = root / "run.json", root / "findings.json", root / "gate.json"
            run_path.write_text(json.dumps(run)); findings_path.write_text(json.dumps([finding]))
            command = [sys.executable, str(ROOT / "pipeline/evaluate-gate.py"), "--run", str(run_path),
                       "--findings", str(findings_path), "--output", str(gate_path)]
            self.assertEqual(subprocess.run(command, timeout=15).returncode, 0)
            self.assertEqual(json.loads(gate_path.read_text())["status"], "FAIL")
            run["execution"] = [{"stage": "IAC_SCANNING", "status": "ERROR"}]
            run_path.write_text(json.dumps(run))
            self.assertEqual(subprocess.run(command, timeout=15).returncode, 0)
            self.assertEqual(json.loads(gate_path.read_text())["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()
