from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install.py"


class InstallerCliRegressionTests(unittest.TestCase):
    def create_project(self, root: Path) -> Path:
        project = root / "UnityProject"
        (project / "Assets").mkdir(parents=True)
        (project / "Packages").mkdir()
        (project / "ProjectSettings").mkdir()
        (project / "ProjectSettings" / "ProjectVersion.txt").write_text(
            "m_EditorVersion: 6000.4.10f1\n",
            encoding="utf-8",
        )
        (project / ".gitignore").write_text(
            "Library/\n",
            encoding="utf-8",
        )
        return project

    def run_installer(
        self,
        project: Path,
        *arguments: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(INSTALLER), str(project), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_rejects_non_unity_project_without_writes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory) / "NotUnity"
            project.mkdir()

            result = self.run_installer(project)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Not a Unity project", result.stderr)
            self.assertEqual(list(project.iterdir()), [])

    def test_reinstall_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))

            first = self.run_installer(project, "--skip-agents")
            second = self.run_installer(project, "--skip-agents")

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("Installation complete: 0 changed", second.stdout)

    def test_conflict_stops_before_any_update(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            destination = project / "docs" / "unity_design_sheet.md"
            destination.parent.mkdir(parents=True)
            destination.write_text("project-owned content\n", encoding="utf-8")
            original_gitignore = (project / ".gitignore").read_text(
                encoding="utf-8"
            )

            result = self.run_installer(project, "--skip-agents")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("existing files differ", result.stderr)
            self.assertEqual(
                destination.read_text(encoding="utf-8"),
                "project-owned content\n",
            )
            self.assertEqual(
                (project / ".gitignore").read_text(encoding="utf-8"),
                original_gitignore,
            )
            self.assertFalse((project / ".codex").exists())

    def test_force_replaces_conflicting_harness_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            destination = project / "docs" / "unity_design_sheet.md"
            destination.parent.mkdir(parents=True)
            destination.write_text("outdated\n", encoding="utf-8")

            result = self.run_installer(
                project,
                "--skip-agents",
                "--force",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                destination.read_bytes(),
                (ROOT / "docs" / "unity_design_sheet.md").read_bytes(),
            )

    def test_dry_run_creates_no_harness_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            original_gitignore = (project / ".gitignore").read_text(
                encoding="utf-8"
            )

            result = self.run_installer(
                project,
                "--skip-agents",
                "--dry-run",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Dry run complete", result.stdout)
            self.assertFalse((project / ".codex").exists())
            self.assertFalse((project / "docs").exists())
            self.assertFalse((project / "harness.lock.json").exists())
            self.assertEqual(
                (project / ".gitignore").read_text(encoding="utf-8"),
                original_gitignore,
            )

    def test_skip_agents_controls_agents_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            skipped = self.create_project(temporary / "Skipped")
            included = self.create_project(temporary / "Included")

            skipped_result = self.run_installer(skipped, "--skip-agents")
            included_result = self.run_installer(included)

            self.assertEqual(skipped_result.returncode, 0, skipped_result.stderr)
            self.assertEqual(included_result.returncode, 0, included_result.stderr)
            self.assertFalse((skipped / "AGENTS.md").exists())
            self.assertTrue((included / "AGENTS.md").is_file())

    def test_existing_asset_validation_config_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            config = (
                project
                / "ProjectSettings"
                / "UnityCodexHarnessAssetValidation.json"
            )
            custom = '{"requiredAssets":[{"path":"Assets/Game/Main.unity"}]}\n'
            config.write_text(custom, encoding="utf-8")

            result = self.run_installer(project, "--skip-agents")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(config.read_text(encoding="utf-8"), custom)


if __name__ == "__main__":
    unittest.main()
