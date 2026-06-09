from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CREATE_RUN = (
    ROOT
    / ".codex"
    / "skills"
    / "validate-unity-change"
    / "scripts"
    / "create_validation_run.py"
)


def load_create_module():
    spec = importlib.util.spec_from_file_location(
        "create_validation_run_regression",
        CREATE_RUN,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ValidationRunCreationRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.create_run = load_create_module()

    def create_project(self, root: Path) -> Path:
        project = root / "UnityProject"
        (project / "Assets").mkdir(parents=True)
        (project / "Packages").mkdir()
        (project / "ProjectSettings").mkdir()
        (project / "ProjectSettings" / "ProjectVersion.txt").write_text(
            "m_EditorVersion: 6000.4.10f1\n",
            encoding="utf-8",
        )
        return project

    def test_run_id_collision_uses_two_digit_suffix(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            timestamp = datetime(2026, 6, 9, 1, 2, 3, tzinfo=timezone.utc)
            (base / "20260609T010203Z").mkdir()

            run_id, run_dir = self.create_run.unique_run_dir(base, timestamp)

            self.assertEqual(run_id, "20260609T010203Z-01")
            self.assertTrue(run_dir.is_dir())

    def test_run_id_collision_limit_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            timestamp = datetime(2026, 6, 9, 1, 2, 3, tzinfo=timezone.utc)
            for index in range(100):
                suffix = "" if index == 0 else f"-{index:02d}"
                (base / f"20260609T010203Z{suffix}").mkdir()

            with self.assertRaisesRegex(
                RuntimeError,
                "Could not allocate",
            ):
                self.create_run.unique_run_dir(base, timestamp)

    def test_cli_rejects_invalid_unity_project_without_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory) / "Invalid"
            project.mkdir()

            result = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_RUN),
                    "--project-root",
                    str(project),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Not a Unity project", result.stderr)
            self.assertFalse((project / "Artifacts").exists())

    def test_cli_records_design_ac_platform_and_unity_version(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))

            result = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_RUN),
                    "--project-root",
                    str(project),
                    "--design-id",
                    "DEBUG-002",
                    "--ac-id",
                    "DEBUG-002-AC03",
                    "--platform",
                    "Editor",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = (
                project / result.stdout.strip() / "RunManifest.json"
            ).read_text(encoding="utf-8")
            self.assertIn('"schemaVersion": 2', manifest)
            self.assertIn('"state": "RUNNING"', manifest)
            self.assertIn('"unityVersion": "6000.4.10f1"', manifest)
            self.assertIn('"targetPlatform": "Editor"', manifest)
            self.assertIn('"DEBUG-002"', manifest)
            self.assertIn('"DEBUG-002-AC03"', manifest)


if __name__ == "__main__":
    unittest.main()
