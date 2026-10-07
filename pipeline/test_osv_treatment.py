"""Unit checks for PA-001 invocation wiring; these never execute a scanner."""
from pathlib import Path
import json
import tempfile
import unittest

from experiment import control_environment, frozen_command
from tool_runtime import RUNTIME_ROOT


class OsvTreatmentTest(unittest.TestCase):
    def test_command_keeps_scope_and_strict_offline_flags(self):
        with tempfile.TemporaryDirectory() as temp:
            command = frozen_command("SCA", Path(temp))
        self.assertIn("application/package-lock.json", command)
        self.assertIn("--offline", command)
        self.assertIn("--offline-vulnerabilities", command)
        self.assertNotIn("--local-db-path", command)
        self.assertNotIn("--download-offline-databases", command)
        self.assertEqual(command.count("--lockfile"), 1)

    def test_environment_points_to_controlled_cache_root(self):
        original = {"EXISTING_TEST_ENV": "kept"}
        result = control_environment("SCA", original)
        self.assertEqual(result["OSV_SCANNER_LOCAL_DB_CACHE_DIRECTORY"], str(RUNTIME_ROOT / "cache/osv"))
        self.assertEqual(result["EXISTING_TEST_ENV"], "kept")
        self.assertNotIn("OSV_SCANNER_LOCAL_DB_CACHE_DIRECTORY", original)

    def test_descriptor_preserves_snapshot_identity_and_layout(self):
        descriptor = json.loads(Path("pipeline/security/osv-database-v1.json").read_text())
        self.assertEqual(descriptor["cache_root_environment_variable"], "OSV_SCANNER_LOCAL_DB_CACHE_DIRECTORY")
        self.assertEqual(descriptor["cache_layout"], "osv-scalibr/npm/all.zip")
        self.assertEqual(descriptor["scanner_flags"], ["--offline", "--offline-vulnerabilities"])
        self.assertEqual(descriptor["prohibited_flags"], ["--local-db-path", "--download-offline-databases"])
        self.assertEqual(descriptor["gcs_generation"], "1790875957849873")
        self.assertEqual(descriptor["md5_base64"], "tkWSeWnYUpzWbsr9u+8lXA==")
        self.assertEqual(descriptor["size_bytes"], 217297800)


if __name__ == "__main__":
    unittest.main()
