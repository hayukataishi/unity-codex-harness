from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install.py"


class InstallerCliRegressionTests(unittest.TestCase):
    def compliant_agents(self, prefix: str = "custom agents") -> str:
        return (
            f"{prefix}\n\n"
            "<!-- UNITY_CODEX_HARNESS_AGENT_CONTRACT: REQUIRED -->\n\n"
            "Before Unity work, read and follow "
            "`docs/unity_harness_agent_contract.md`.\n"
        )

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

    def add_legacy_evaluation_manifest_entry(
        self,
        project: Path,
        content: str,
    ) -> Path:
        evaluation = (
            project / "docs" / "unity_harness_evaluation_2026-06-08.md"
        )
        evaluation.parent.mkdir(parents=True, exist_ok=True)
        evaluation.write_text(content, encoding="utf-8")
        manifest_path = (
            project / ".unity-codex-harness" / "install-manifest.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"].append(
            {
                "path": (
                    "docs/unity_harness_evaluation_2026-06-08.md"
                ),
                "ownership": "harness-managed",
                "sourceSha256": hashlib.sha256(
                    content.encode("utf-8")
                ).hexdigest(),
            }
        )
        manifest_text = json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ) + "\n"
        manifest_path.write_text(manifest_text, encoding="utf-8")
        sidecar = (
            project / ".unity-codex-harness" / "install-manifest.sha256"
        )
        sidecar.write_text(
            f"{hashlib.sha256(manifest_text.encode('utf-8')).hexdigest()}  "
            "install-manifest.json\n",
            encoding="utf-8",
        )
        return evaluation

    def convert_install_to_legacy_skill_layout(self, project: Path) -> None:
        manifest_path = (
            project / ".unity-codex-harness" / "install-manifest.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            path = entry["path"]
            if not path.startswith(".agents/skills/"):
                continue
            legacy_path = path.replace(
                ".agents/skills/",
                ".codex/skills/",
                1,
            )
            source = project / path
            destination = project / legacy_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            source.replace(destination)
            entry["path"] = legacy_path
        manifest["exclusiveManagedRoots"] = [
            path.replace(".agents/skills/", ".codex/skills/", 1)
            for path in manifest["exclusiveManagedRoots"]
        ]
        for directory in sorted(
            (project / ".agents").rglob("*"),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            if directory.is_dir():
                directory.rmdir()
        (project / ".agents").rmdir()
        gitignore = project / ".gitignore"
        gitignore.write_text(
            gitignore.read_text(encoding="utf-8").replace(
                "/.agents/skills/",
                "/.codex/skills/",
            ),
            encoding="utf-8",
        )
        manifest_text = json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ) + "\n"
        manifest_path.write_text(manifest_text, encoding="utf-8")
        sidecar = (
            project / ".unity-codex-harness" / "install-manifest.sha256"
        )
        sidecar.write_text(
            f"{hashlib.sha256(manifest_text.encode('utf-8')).hexdigest()}  "
            "install-manifest.json\n",
            encoding="utf-8",
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
            design = (
                project
                / "docs"
                / "game_design"
                / "all"
                / "acceptance.md"
            )
            design.write_text("project-owned acceptance\n", encoding="utf-8")

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
                "project-owned acceptance\n",
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
            self.assertFalse((project / ".agents").exists())
            self.assertFalse((project / "docs").exists())
            self.assertFalse((project / "harness.lock.json").exists())
            self.assertFalse((project / "harness.overrides.json").exists())
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

    def test_existing_agents_without_contract_stops_before_writes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            agents = project / "AGENTS.md"
            agents.write_text("custom project instructions\n", encoding="utf-8")
            original_gitignore = (project / ".gitignore").read_text(
                encoding="utf-8"
            )

            result = self.run_installer(project)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "existing project-owned AGENTS.md does not activate",
                result.stderr,
            )
            self.assertIn("--prepare-migration", result.stderr)
            self.assertEqual(
                agents.read_text(encoding="utf-8"),
                "custom project instructions\n",
            )
            self.assertEqual(
                (project / ".gitignore").read_text(encoding="utf-8"),
                original_gitignore,
            )
            self.assertFalse((project / ".codex").exists())
            self.assertFalse((project / "docs").exists())
            self.assertFalse((project / ".unity-codex-harness").exists())

    def test_prepare_agents_migration_remains_incomplete(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            agents = project / "AGENTS.md"
            agents.write_text("custom project instructions\n", encoding="utf-8")

            result = self.run_installer(project, "--prepare-migration")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("created AGENTS.md migration", result.stdout)
            self.assertIn("Installation remains incomplete", result.stdout)
            self.assertEqual(
                agents.read_text(encoding="utf-8"),
                "custom project instructions\n",
            )
            self.assertFalse((project / ".codex").exists())
            self.assertFalse((project / "docs").exists())
            self.assertIn(
                "/Artifacts/",
                (project / ".gitignore").read_text(encoding="utf-8"),
            )
            migration_root = next(
                (
                    project / "Artifacts" / "HarnessInstallerMigrations"
                ).iterdir()
            )
            self.assertEqual(
                (
                    migration_root / "local" / "AGENTS.md"
                ).read_text(encoding="utf-8"),
                "custom project instructions\n",
            )
            incoming = (
                migration_root / "incoming" / "AGENTS.md"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "<!-- UNITY_CODEX_HARNESS_AGENT_CONTRACT: REQUIRED -->",
                incoming,
            )
            self.assertIn(
                "docs/unity_harness_agent_contract.md",
                incoming,
            )

    def test_existing_agents_with_contract_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            agents = project / "AGENTS.md"
            custom = self.compliant_agents("team-specific instructions")
            agents.write_text(custom, encoding="utf-8")

            result = self.run_installer(project)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(agents.read_text(encoding="utf-8"), custom)
            self.assertIn(
                "Harness integrity verification: PASS",
                result.stdout,
            )

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
                "AGENTS.md": self.compliant_agents(),
                "docs/unity_design_sheet.md": (
                    (ROOT / "docs" / "unity_design_sheet.md").read_text(
                        encoding="utf-8"
                    )
                    + "\ncustom index note\n"
                ),
                "docs/game_design/all/acceptance.md": "custom acceptance\n",
                "docs/mcp_and_skills_list.md": "custom tools\n",
                "harness.overrides.json": (
                    '{"schemaVersion":1,"externalDependencies":{}}\n'
                ),
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

    def test_force_updates_standard_documents_but_preserves_game_sheet(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            first = self.run_installer(project, "--skip-agents")
            self.assertEqual(first.returncode, 0, first.stderr)

            requirements = project / "docs" / "unity_harness_requirements.md"
            capabilities = project / "docs" / "unity_harness_capabilities.md"
            sheet = project / "docs" / "unity_design_sheet.md"
            requirements.write_text(
                "outdated harness requirements\n",
                encoding="utf-8",
            )
            capabilities.write_text(
                "outdated harness capabilities\n",
                encoding="utf-8",
            )
            sheet.write_text(
                (ROOT / "docs" / "unity_design_sheet.md").read_text(
                    encoding="utf-8"
                )
                + "\nproject game decisions\n",
                encoding="utf-8",
            )

            result = self.run_installer(
                project,
                "--skip-agents",
                "--force",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                requirements.read_bytes(),
                (ROOT / "docs" / "unity_harness_requirements.md").read_bytes(),
            )
            self.assertEqual(
                capabilities.read_bytes(),
                (ROOT / "docs" / "unity_harness_capabilities.md").read_bytes(),
            )
            self.assertEqual(
                sheet.read_text(encoding="utf-8"),
                (ROOT / "docs" / "unity_design_sheet.md").read_text(
                    encoding="utf-8"
                )
                + "\nproject game decisions\n",
            )
            backup_root = next(
                (
                    project / "Artifacts" / "HarnessInstallerBackups"
                ).iterdir()
            )
            self.assertEqual(
                (
                    backup_root
                    / "files"
                    / "docs"
                    / "unity_harness_requirements.md"
                ).read_text(encoding="utf-8"),
                "outdated harness requirements\n",
            )
            self.assertEqual(
                (
                    backup_root
                    / "files"
                    / "docs"
                    / "unity_harness_capabilities.md"
                ).read_text(encoding="utf-8"),
                "outdated harness capabilities\n",
            )

    def test_force_file_rejects_project_owned_path_without_writes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            first = self.run_installer(project, "--skip-agents")
            self.assertEqual(first.returncode, 0, first.stderr)
            design = (
                project
                / "docs"
                / "game_design"
                / "all"
                / "acceptance.md"
            )
            design.write_text("custom acceptance\n", encoding="utf-8")

            result = self.run_installer(
                project,
                "--skip-agents",
                "--force-file",
                "docs/game_design/all/acceptance.md",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Project-owned files cannot be replaced", result.stderr)
            self.assertEqual(
                design.read_text(encoding="utf-8"),
                "custom acceptance\n",
            )
            self.assertTrue((project / ".unity-codex-harness").exists())
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
            self.assertEqual(manifest["schemaVersion"], 2)
            release_hash = hashlib.sha256(
                (ROOT / "harness.release.json").read_bytes()
            ).hexdigest()
            self.assertEqual(manifest["harness"]["release"], "0.1.0")
            self.assertEqual(
                manifest["harness"]["releaseTag"],
                "v0.1.0",
            )
            self.assertEqual(
                manifest["harness"]["releaseManifestSha256"],
                release_hash,
            )
            self.assertIn(
                "scripts/unity_codex_harness",
                manifest["exclusiveManagedRoots"],
            )
            self.assertTrue(
                (
                    project
                    / ".unity-codex-harness"
                    / "install-manifest.sha256"
                ).is_file()
            )
            by_path = {
                entry["path"]: entry for entry in manifest["files"]
            }
            self.assertNotIn(
                "docs/unity_harness_evaluation_2026-06-08.md",
                by_path,
            )
            self.assertFalse(
                (
                    project
                    / "docs"
                    / "unity_harness_evaluation_2026-06-08.md"
                ).exists()
            )
            self.assertEqual(
                by_path["docs/unity_design_sheet.md"]["ownership"],
                "project-owned",
            )
            self.assertIn(
                "baselineSha256",
                by_path["docs/unity_design_sheet.md"],
            )
            self.assertEqual(
                by_path["docs/game_design/all/acceptance.md"]["ownership"],
                "project-owned",
            )
            self.assertIn(
                "baselineSha256",
                by_path["docs/game_design/all/acceptance.md"],
            )
            self.assertEqual(
                by_path[
                    "scripts/unity_codex_harness/design_document_set.py"
                ]["ownership"],
                "harness-managed",
            )
            self.assertEqual(
                by_path["docs/unity_harness_requirements.md"]["ownership"],
                "harness-managed",
            )
            self.assertEqual(
                by_path["docs/unity_harness_capabilities.md"]["ownership"],
                "harness-managed",
            )
            self.assertEqual(
                by_path["harness.lock.json"]["ownership"],
                "harness-managed",
            )
            self.assertEqual(
                by_path["harness.release.json"]["ownership"],
                "harness-managed",
            )
            self.assertEqual(
                by_path["docs/unity_harness_release.md"]["ownership"],
                "harness-managed",
            )
            self.assertEqual(
                by_path["harness.overrides.json"]["ownership"],
                "project-owned",
            )
            self.assertIn(
                "baselineSha256",
                by_path["harness.overrides.json"],
            )
            self.assertNotIn(
                "baselineSha256",
                by_path["harness.lock.json"],
            )
            self.assertNotIn(
                "baselineSha256",
                by_path["docs/unity_harness_requirements.md"],
            )
            self.assertEqual(
                by_path[
                    "scripts/unity_codex_harness/"
                    "check_external_dependencies.py"
                ]["ownership"],
                "harness-managed",
            )

    def test_upgrade_retires_unmodified_evaluation_report_with_backup(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            first = self.run_installer(project, "--skip-agents")
            self.assertEqual(first.returncode, 0, first.stderr)
            content = "# Legacy distributed evaluation\n"
            evaluation = self.add_legacy_evaluation_manifest_entry(
                project,
                content,
            )

            result = self.run_installer(project, "--skip-agents")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "retire: docs/unity_harness_evaluation_2026-06-08.md",
                result.stdout,
            )
            self.assertFalse(evaluation.exists())
            backup_root = next(
                (
                    project / "Artifacts" / "HarnessInstallerBackups"
                ).iterdir()
            )
            retired_backup = (
                backup_root
                / "files"
                / "docs"
                / "unity_harness_evaluation_2026-06-08.md"
            )
            self.assertEqual(
                retired_backup.read_text(encoding="utf-8"),
                content,
            )
            backup_manifest = json.loads(
                (backup_root / "BackupManifest.json").read_text(
                    encoding="utf-8"
                )
            )
            retired_entry = next(
                entry
                for entry in backup_manifest["files"]
                if entry["path"]
                == "docs/unity_harness_evaluation_2026-06-08.md"
            )
            self.assertEqual(retired_entry["operation"], "retire")
            self.assertNotIn("replacementSha256", retired_entry)
            manifest = json.loads(
                (
                    project
                    / ".unity-codex-harness"
                    / "install-manifest.json"
                ).read_text(encoding="utf-8")
            )
            self.assertNotIn(
                "docs/unity_harness_evaluation_2026-06-08.md",
                {entry["path"] for entry in manifest["files"]},
            )

    def test_upgrade_moves_unmodified_skills_to_standard_layout(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            first = self.run_installer(project, "--skip-agents")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.convert_install_to_legacy_skill_layout(project)
            legacy_skill = (
                project
                / ".codex"
                / "skills"
                / "bootstrap-game-design"
                / "SKILL.md"
            )
            self.assertTrue(legacy_skill.is_file())

            result = self.run_installer(project, "--skip-agents")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "retire: .codex/skills/bootstrap-game-design/SKILL.md",
                result.stdout,
            )
            self.assertFalse((project / ".codex" / "skills").exists())
            self.assertTrue(
                (
                    project
                    / ".agents"
                    / "skills"
                    / "bootstrap-game-design"
                    / "SKILL.md"
                ).is_file()
            )
            gitignore = (project / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("/.agents/skills/generate2dsprite/", gitignore)
            self.assertNotIn("/.codex/skills/generate2dsprite/", gitignore)
            backup_root = next(
                (
                    project / "Artifacts" / "HarnessInstallerBackups"
                ).iterdir()
            )
            self.assertTrue(
                (
                    backup_root
                    / "files"
                    / ".codex"
                    / "skills"
                    / "bootstrap-game-design"
                    / "SKILL.md"
                ).is_file()
            )
            manifest = json.loads(
                (
                    project
                    / ".unity-codex-harness"
                    / "install-manifest.json"
                ).read_text(encoding="utf-8")
            )
            paths = {entry["path"] for entry in manifest["files"]}
            self.assertTrue(
                any(path.startswith(".agents/skills/") for path in paths)
            )
            self.assertFalse(
                any(path.startswith(".codex/skills/") for path in paths)
            )

    def test_upgrade_stops_for_modified_legacy_skill(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            first = self.run_installer(project, "--skip-agents")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.convert_install_to_legacy_skill_layout(project)
            legacy_skill = (
                project
                / ".codex"
                / "skills"
                / "bootstrap-game-design"
                / "SKILL.md"
            )
            legacy_skill.write_text(
                "# Local legacy skill changes\n",
                encoding="utf-8",
            )

            result = self.run_installer(project, "--skip-agents")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "cannot be retired safely",
                result.stderr,
            )
            self.assertIn(
                ".codex/skills/bootstrap-game-design/SKILL.md differs",
                result.stderr,
            )
            self.assertEqual(
                legacy_skill.read_text(encoding="utf-8"),
                "# Local legacy skill changes\n",
            )
            self.assertFalse((project / ".agents").exists())
            self.assertFalse(
                (
                    project / "Artifacts" / "HarnessInstallerBackups"
                ).exists()
            )

    def test_legacy_skill_without_manifest_stops_before_writes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            legacy_skill = (
                project
                / ".codex"
                / "skills"
                / "bootstrap-game-design"
                / "SKILL.md"
            )
            legacy_skill.parent.mkdir(parents=True)
            legacy_skill.write_text(
                "# Unknown legacy ownership\n",
                encoding="utf-8",
            )
            original_gitignore = (project / ".gitignore").read_text(
                encoding="utf-8"
            )

            result = self.run_installer(project, "--skip-agents")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "without a verified install manifest",
                result.stderr,
            )
            self.assertEqual(
                legacy_skill.read_text(encoding="utf-8"),
                "# Unknown legacy ownership\n",
            )
            self.assertFalse((project / ".agents").exists())
            self.assertFalse((project / "docs").exists())
            self.assertEqual(
                (project / ".gitignore").read_text(encoding="utf-8"),
                original_gitignore,
            )

    def test_legacy_external_skill_requires_manual_migration(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            external_skill = (
                project
                / ".codex"
                / "skills"
                / "generate2dsprite"
                / "SKILL.md"
            )
            external_skill.parent.mkdir(parents=True)
            external_skill.write_text(
                "# Third-party local Skill\n",
                encoding="utf-8",
            )
            original_gitignore = (project / ".gitignore").read_text(
                encoding="utf-8"
            )

            result = self.run_installer(project, "--skip-agents")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "project-owned external Skills still use the legacy",
                result.stderr,
            )
            self.assertIn(".agents/skills", result.stderr)
            self.assertEqual(
                external_skill.read_text(encoding="utf-8"),
                "# Third-party local Skill\n",
            )
            self.assertFalse((project / ".agents").exists())
            self.assertFalse((project / "docs").exists())
            self.assertEqual(
                (project / ".gitignore").read_text(encoding="utf-8"),
                original_gitignore,
            )

    def test_upgrade_preserves_modified_evaluation_report_and_stops(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            first = self.run_installer(project, "--skip-agents")
            self.assertEqual(first.returncode, 0, first.stderr)
            evaluation = self.add_legacy_evaluation_manifest_entry(
                project,
                "# Legacy distributed evaluation\n",
            )
            evaluation.write_text(
                "# Project notes added locally\n",
                encoding="utf-8",
            )

            result = self.run_installer(project, "--skip-agents")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "cannot be retired safely",
                result.stderr,
            )
            self.assertIn(
                "differs from its previously distributed",
                result.stderr,
            )
            self.assertEqual(
                evaluation.read_text(encoding="utf-8"),
                "# Project notes added locally\n",
            )
            self.assertFalse(
                (
                    project / "Artifacts" / "HarnessInstallerBackups"
                ).exists()
            )

    def test_upgrade_rejects_symlinked_evaluation_report(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            first = self.run_installer(project, "--skip-agents")
            self.assertEqual(first.returncode, 0, first.stderr)
            evaluation = self.add_legacy_evaluation_manifest_entry(
                project,
                "# Legacy distributed evaluation\n",
            )
            evaluation.unlink()
            evaluation.symlink_to(project / "missing-evaluation.md")

            result = self.run_installer(project, "--skip-agents")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "cannot be retired safely",
                result.stderr,
            )
            self.assertIn("is not a regular file", result.stderr)
            self.assertTrue(evaluation.is_symlink())
            self.assertFalse(
                (
                    project / "Artifacts" / "HarnessInstallerBackups"
                ).exists()
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

            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn(
                "created game design document migration",
                result.stdout,
            )
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
            self.assertTrue(
                (
                    migration
                    / "incoming"
                    / "docs"
                    / "game_design"
                    / "all"
                    / "acceptance.md"
                ).is_file()
            )
            self.assertIn(
                "projectDocumentStructure",
                migration_manifest,
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

            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn(
                "created game design document migration",
                result.stdout,
            )
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

    def test_modified_legacy_lock_requires_ownership_migration(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            lock_path = project / "harness.lock.json"
            lock = json.loads(
                (ROOT / "harness.lock.json").read_text(encoding="utf-8")
            )
            lock["externalDependencies"]["unityMcp"]["packageVersion"] = "9.8.0"
            lock_path.write_text(
                json.dumps(lock, indent=2) + "\n",
                encoding="utf-8",
            )
            legacy_baseline = (
                project
                / ".unity-codex-harness"
                / "baselines"
                / "harness.lock.json"
            )
            legacy_baseline.parent.mkdir(parents=True)
            legacy_baseline.write_bytes(
                (ROOT / "harness.lock.json").read_bytes()
            )
            original_lock = lock_path.read_text(encoding="utf-8")

            stopped = self.run_installer(project, "--skip-agents")

            self.assertNotEqual(stopped.returncode, 0)
            self.assertIn("harness-managed standard pin set", stopped.stderr)
            self.assertIn("--prepare-migration", stopped.stderr)
            self.assertEqual(
                lock_path.read_text(encoding="utf-8"),
                original_lock,
            )

            migrated = self.run_installer(
                project,
                "--skip-agents",
                "--prepare-migration",
            )

            self.assertNotEqual(migrated.returncode, 0)
            self.assertIn(
                "created harness.lock.json ownership migration",
                migrated.stdout,
            )
            self.assertIn("Installation remains incomplete", migrated.stdout)
            self.assertEqual(
                lock_path.read_text(encoding="utf-8"),
                original_lock,
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
            self.assertEqual(
                manifest["ownershipTransition"]["to"],
                "harness-managed",
            )
            self.assertEqual(
                manifest["ownershipTransition"]["overridePath"],
                "harness.overrides.json",
            )
            self.assertTrue(
                (
                    migration_root
                    / "override-template"
                    / "harness.overrides.json"
                ).is_file()
            )
            self.assertEqual(
                (
                    project
                    / ".unity-codex-harness"
                    / "baselines"
                    / "harness.overrides.json"
                ).read_bytes(),
                (ROOT / "harness.overrides.json").read_bytes(),
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
            self.assertTrue(
                (
                    project
                    / "scripts"
                    / "unity_codex_harness"
                    / "design_document_set.py"
                ).is_file()
            )
            self.assertTrue(
                (
                    project
                    / "scripts"
                    / "unity_codex_harness"
                    / "validate_design_contract.py"
                ).is_file()
            )
            self.assertTrue(
                (
                    project
                    / "scripts"
                    / "unity_codex_harness"
                    / "validate_design_readiness.py"
                ).is_file()
            )
            self.assertTrue(
                (
                    project
                    / "scripts"
                    / "unity_codex_harness"
                    / "verify_harness_integrity.py"
                ).is_file()
            )
            gitignore = (project / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("/.codex/external/", gitignore)
            self.assertIn(
                "/.agents/skills/generate2dsprite/",
                gitignore,
            )
            self.assertIn(
                "/.agents/skills/generate2dmap/",
                gitignore,
            )
            self.assertIn(
                "External dependencies are not bundled",
                result.stdout,
            )
            self.assertIn(
                "Validate inherited HREQ entries",
                result.stdout,
            )
            contract_result = subprocess.run(
                [
                    sys.executable,
                    str(
                        project
                        / "scripts"
                        / "unity_codex_harness"
                        / "validate_design_contract.py"
                    ),
                    "--project-root",
                    str(project),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                contract_result.returncode,
                0,
                contract_result.stdout + contract_result.stderr,
            )
            self.assertIn(
                "Validate milestone design readiness",
                result.stdout,
            )
            self.assertIn(
                "Verify harness-managed files before Codex work",
                result.stdout,
            )

    def test_check_rejects_modified_harness_managed_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            first = self.run_installer(project, "--skip-agents")
            self.assertEqual(first.returncode, 0, first.stderr)
            (
                project / "docs" / "unity_harness_capabilities.md"
            ).write_text("modified\n", encoding="utf-8")

            result = self.run_installer(project, "--check")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Harness integrity verification: FAIL", result.stderr)
            self.assertIn(
                "harness-managed SHA-256 mismatch",
                result.stderr,
            )

    def test_check_rejects_modified_standard_lock(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            first = self.run_installer(project, "--skip-agents")
            self.assertEqual(first.returncode, 0, first.stderr)
            (project / "harness.lock.json").write_text(
                '{"custom":true}\n',
                encoding="utf-8",
            )

            result = self.run_installer(project, "--check")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Harness integrity verification: FAIL", result.stderr)
            self.assertIn(
                "harness-managed SHA-256 mismatch: harness.lock.json",
                result.stderr,
            )

    def test_check_rejects_missing_agents_contract_reference(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            first = self.run_installer(project)
            self.assertEqual(first.returncode, 0, first.stderr)
            (project / "AGENTS.md").write_text(
                "team instructions without harness contract\n",
                encoding="utf-8",
            )

            result = self.run_installer(project, "--check")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Harness integrity verification: FAIL", result.stderr)
            self.assertIn(
                "AGENTS.md is missing required harness contract marker",
                result.stderr,
            )

    def test_check_allows_project_owned_changes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            first = self.run_installer(project, "--skip-agents")
            self.assertEqual(first.returncode, 0, first.stderr)
            (
                project / "docs" / "unity_design_sheet.md"
            ).write_text("project decision\n", encoding="utf-8")
            (project / "harness.overrides.json").write_text(
                (
                    '{"schemaVersion":1,"externalDependencies":'
                    '{"unityMcp":{"reason":"project compatibility",'
                    '"approvedBy":"team","approvedAt":"2026-06-11",'
                    '"values":{"minimumUnity":"2022.3"}}}}\n'
                ),
                encoding="utf-8",
            )

            result = self.run_installer(project, "--check")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "Harness integrity verification: PASS",
                result.stdout,
            )


if __name__ == "__main__":
    unittest.main()
