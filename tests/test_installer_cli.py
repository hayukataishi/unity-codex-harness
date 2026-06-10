from __future__ import annotations

import json
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
            destination = project / "docs" / "unity_harness_engineering.md"
            destination.parent.mkdir(parents=True)
            destination.write_text("managed conflict\n", encoding="utf-8")
            original_gitignore = (project / ".gitignore").read_text(
                encoding="utf-8"
            )

            result = self.run_installer(project, "--skip-agents")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("harness-managed files differ", result.stderr)
            self.assertEqual(
                destination.read_text(encoding="utf-8"),
                "managed conflict\n",
            )
            self.assertEqual(
                (project / ".gitignore").read_text(encoding="utf-8"),
                original_gitignore,
            )
            self.assertFalse((project / ".codex").exists())

    def test_force_file_replaces_only_managed_file_with_backup(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            first = self.run_installer(project, "--skip-agents")
            self.assertEqual(first.returncode, 0, first.stderr)
            destination = project / "docs" / "unity_harness_engineering.md"
            destination.write_text("outdated managed file\n", encoding="utf-8")
            design = project / "docs" / "unity_design_sheet.md"
            design.write_text("project-owned design\n", encoding="utf-8")

            result = self.run_installer(
                project,
                "--skip-agents",
                "--force-file",
                "docs/unity_harness_engineering.md",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                destination.read_bytes(),
                (ROOT / "docs" / "unity_harness_engineering.md").read_bytes(),
            )
            self.assertEqual(
                design.read_text(encoding="utf-8"),
                "project-owned design\n",
            )
            backup_roots = list(
                (
                    project / "Artifacts" / "HarnessInstallerBackups"
                ).iterdir()
            )
            self.assertEqual(len(backup_roots), 1)
            self.assertEqual(
                (
                    backup_roots[0]
                    / "files"
                    / "docs"
                    / "unity_harness_engineering.md"
                ).read_text(encoding="utf-8"),
                "outdated managed file\n",
            )
            backup_manifest = json.loads(
                (backup_roots[0] / "BackupManifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                backup_manifest["files"][0]["path"],
                "docs/unity_harness_engineering.md",
            )
            self.assertEqual(
                len(backup_manifest["files"][0]["originalSha256"]),
                64,
            )
            self.assertEqual(
                len(backup_manifest["files"][0]["replacementSha256"]),
                64,
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
            self.assertFalse((project / "scripts").exists())
            self.assertFalse((project / ".unity-codex-harness").exists())
            self.assertFalse((project / "Artifacts").exists())
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

    def test_force_never_replaces_project_owned_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            first = self.run_installer(project)
            self.assertEqual(first.returncode, 0, first.stderr)
            project_owned = {
                "AGENTS.md": "custom agents\n",
                "docs/unity_design_sheet.md": "custom design\n",
                "docs/mcp_and_skills_list.md": "custom tools\n",
                "harness.lock.json": '{"custom":true}\n',
                (
                    "ProjectSettings/"
                    "UnityCodexHarnessAssetValidation.json"
                ): '{"custom":true}\n',
            }
            for relative, content in project_owned.items():
                (project / relative).write_text(content, encoding="utf-8")

            result = self.run_installer(project, "--force")

            self.assertEqual(result.returncode, 0, result.stderr)
            for relative, content in project_owned.items():
                self.assertEqual(
                    (project / relative).read_text(encoding="utf-8"),
                    content,
                    relative,
                )

    def test_force_file_rejects_project_owned_path_without_writes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            design = project / "docs" / "unity_design_sheet.md"
            design.parent.mkdir(parents=True)
            design.write_text("custom design\n", encoding="utf-8")

            result = self.run_installer(
                project,
                "--skip-agents",
                "--force-file",
                "docs/unity_design_sheet.md",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Project-owned files cannot be replaced", result.stderr)
            self.assertEqual(
                design.read_text(encoding="utf-8"),
                "custom design\n",
            )
            self.assertFalse((project / ".unity-codex-harness").exists())
            self.assertFalse((project / "Artifacts").exists())

    def test_install_manifest_records_ownership_and_hashes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))

            result = self.run_installer(project, "--skip-agents")

            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads(
                (
                    project
                    / ".unity-codex-harness"
                    / "install-manifest.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["schemaVersion"], 1)
            by_path = {
                entry["path"]: entry for entry in manifest["files"]
            }
            self.assertEqual(
                by_path["docs/unity_design_sheet.md"]["ownership"],
                "project-owned",
            )
            self.assertIn(
                "baselineSha256",
                by_path["docs/unity_design_sheet.md"],
            )
            self.assertEqual(
                by_path[
                    "scripts/unity_codex_harness/"
                    "check_external_dependencies.py"
                ]["ownership"],
                "harness-managed",
            )

    def test_prepare_migration_creates_three_way_bundle(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            first = self.run_installer(project, "--skip-agents")
            self.assertEqual(first.returncode, 0, first.stderr)
            design = project / "docs" / "unity_design_sheet.md"
            design.write_text("project local design\n", encoding="utf-8")
            baseline = (
                project
                / ".unity-codex-harness"
                / "baselines"
                / "docs"
                / "unity_design_sheet.md"
            )
            baseline.write_text("previous upstream design\n", encoding="utf-8")

            result = self.run_installer(
                project,
                "--skip-agents",
                "--prepare-migration",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                design.read_text(encoding="utf-8"),
                "project local design\n",
            )
            migration_roots = list(
                (
                    project / "Artifacts" / "HarnessInstallerMigrations"
                ).iterdir()
            )
            self.assertEqual(len(migration_roots), 1)
            migration = migration_roots[0]
            for directory in ("base", "local", "incoming"):
                self.assertTrue(
                    (
                        migration
                        / directory
                        / "docs"
                        / "unity_design_sheet.md"
                    ).is_file()
                )
            self.assertTrue(
                (
                    migration
                    / "diff"
                    / "docs"
                    / "unity_design_sheet.md.local.patch"
                ).is_file()
            )
            self.assertTrue(
                (
                    migration
                    / "diff"
                    / "docs"
                    / "unity_design_sheet.md.incoming.patch"
                ).is_file()
            )
            migration_manifest = json.loads(
                (migration / "MigrationManifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                len(migration_manifest["files"][0]["baseSha256"]),
                64,
            )
            self.assertEqual(
                baseline.read_bytes(),
                (ROOT / "docs" / "unity_design_sheet.md").read_bytes(),
            )

    def test_prepare_migration_supports_legacy_install_without_baseline(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            design = project / "docs" / "unity_design_sheet.md"
            design.parent.mkdir(parents=True)
            design.write_text("legacy project design\n", encoding="utf-8")

            result = self.run_installer(
                project,
                "--skip-agents",
                "--prepare-migration",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                design.read_text(encoding="utf-8"),
                "legacy project design\n",
            )
            migration_root = next(
                (
                    project / "Artifacts" / "HarnessInstallerMigrations"
                ).iterdir()
            )
            manifest = json.loads(
                (migration_root / "MigrationManifest.json").read_text(
                    encoding="utf-8"
                )
            )
            design_entry = next(
                entry
                for entry in manifest["files"]
                if entry["path"] == "docs/unity_design_sheet.md"
            )
            self.assertEqual(
                design_entry["baseKind"],
                "legacy-local-snapshot",
            )
            self.assertEqual(
                (
                    migration_root
                    / "base"
                    / "docs"
                    / "unity_design_sheet.md"
                ).read_text(encoding="utf-8"),
                "legacy project design\n",
            )

    def test_installs_external_dependency_checker_and_ignore_rules(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))

            result = self.run_installer(project, "--skip-agents")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(
                (
                    project
                    / "scripts"
                    / "unity_codex_harness"
                    / "check_external_dependencies.py"
                ).is_file()
            )
            gitignore = (project / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("/.codex/external/", gitignore)
            self.assertIn(
                "/.codex/skills/generate2dsprite/",
                gitignore,
            )
            self.assertIn(
                "/.codex/skills/generate2dmap/",
                gitignore,
            )
            self.assertIn(
                "External dependencies are not bundled",
                result.stdout,
            )


if __name__ == "__main__":
    unittest.main()
