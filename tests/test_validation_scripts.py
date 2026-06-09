from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    ROOT
    / ".codex"
    / "skills"
    / "validate-unity-change"
    / "scripts"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


finalize = load_module(
    "finalize_validation_run",
    SCRIPTS / "finalize_validation_run.py",
)
runner = load_module(
    "run_unity_validation",
    SCRIPTS / "run_unity_validation.py",
)
ci_secrets = load_module(
    "check_unity_ci_secrets",
    ROOT / "scripts" / "check_unity_ci_secrets.py",
)
repository_validator = load_module(
    "validate_repository",
    ROOT / "scripts" / "validate_repository.py",
)


class AggregateResultTests(unittest.TestCase):
    def test_passes_when_all_checks_pass(self):
        self.assertEqual(finalize.aggregate_result(["PASS", "PASS"]), "PASS")

    def test_uses_most_severe_result(self):
        self.assertEqual(
            finalize.aggregate_result(["PASS", "NOT RUN", "BLOCKED", "FAIL"]),
            "FAIL",
        )

    def test_empty_checks_are_not_run(self):
        self.assertEqual(finalize.aggregate_result([]), "NOT RUN")


class UnityVersionTests(unittest.TestCase):
    def test_reads_fixture_unity_version(self):
        fixture = ROOT / "tests" / "fixtures" / "UnityValidationFixture"
        self.assertEqual(runner.unity_version(fixture), "6000.4.10f1")

    def test_display_command_removes_machine_specific_paths(self):
        fixture = ROOT / "tests" / "fixtures" / "UnityValidationFixture"
        editor = Path(
            "/Applications/Unity/Hub/Editor/6000.4.10f1/"
            "Unity.app/Contents/MacOS/Unity"
        )
        command = [
            runner.sys.executable,
            str(SCRIPTS / "preflight_unity_project.py"),
            str(fixture),
            str(editor),
        ]

        rendered = runner.display_command(command, editor, fixture)

        self.assertIn("<PYTHON>", rendered)
        self.assertIn("<HARNESS_SCRIPTS>", rendered)
        self.assertIn("<UNITY_PROJECT_ROOT>", rendered)
        self.assertIn("<UNITY_EDITOR>", rendered)
        self.assertNotIn(str(ROOT), rendered)

    def test_parses_successful_asset_validation_report(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            report_path = Path(temporary_directory) / "AssetValidation.json"
            report_path.write_text(
                '{"status":"PASS","summary":{"errors":0,"warnings":1}}\n',
                encoding="utf-8",
            )

            result, notes = runner.parse_asset_validation_result(report_path, 0)

            self.assertEqual(result, "PASS")
            self.assertEqual(notes, "errors=0, warnings=1")

    def test_rejects_missing_asset_validation_report(self):
        result, notes = runner.parse_asset_validation_result(
            Path("/not-created/AssetValidation.json"),
            1,
        )

        self.assertEqual(result, "FAIL")
        self.assertIn("was not created", notes)


class UnityCiSecretTests(unittest.TestCase):
    def test_accepts_license_file_credentials(self):
        environment = {
            "UNITY_EMAIL": "developer@example.com",
            "UNITY_PASSWORD": "secret",
            "UNITY_LICENSE": "<license />",
        }

        self.assertEqual(ci_secrets.missing_license_values(environment), [])

    def test_accepts_serial_credentials(self):
        environment = {
            "UNITY_EMAIL": "developer@example.com",
            "UNITY_PASSWORD": "secret",
            "UNITY_SERIAL": "XX-XXXX-XXXX-XXXX-XXXX-XXXX",
        }

        self.assertEqual(ci_secrets.missing_license_values(environment), [])

    def test_reports_missing_values_without_secret_contents(self):
        missing = ci_secrets.missing_license_values({})

        self.assertEqual(
            missing,
            [
                "UNITY_EMAIL",
                "UNITY_PASSWORD",
                "UNITY_LICENSE or UNITY_SERIAL",
            ],
        )


class GithubActionsValidationTests(unittest.TestCase):
    def test_accepts_commit_sha_and_local_action(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "validate.yml").write_text(
                "\n".join(
                    [
                        "steps:",
                        "  - uses: actions/checkout@"
                        "34e114876b0b11c390a56381ad16ebd13914f8d5",
                        "  - uses: ./local-action",
                    ]
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                repository_validator.validate_github_actions(root),
                [],
            )

    def test_rejects_mutable_action_tag(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "validate.yml").write_text(
                "steps:\n  - uses: actions/checkout@v4\n",
                encoding="utf-8",
            )

            errors = repository_validator.validate_github_actions(root)

            self.assertEqual(len(errors), 1)
            self.assertIn("actions/checkout@v4", errors[0])


class HarnessLockValidationTests(unittest.TestCase):
    def load_manifest(self):
        return json.loads(
            (ROOT / "harness.lock.json").read_text(encoding="utf-8")
        )

    def test_repository_lock_is_valid(self):
        self.assertEqual(repository_validator.validate_harness_lock(ROOT), [])

    def test_rejects_non_pinned_dependency_commit(self):
        manifest = self.load_manifest()
        manifest["externalDependencies"]["unityMcp"]["commit"] = "main"

        errors = repository_validator.validate_harness_lock_data(
            manifest,
            "6000.4.10f1",
        )

        self.assertTrue(
            any("unityMcp.commit" in error for error in errors),
            errors,
        )

    def test_requires_reason_for_not_run_dependency(self):
        manifest = self.load_manifest()
        manifest["externalDependencies"]["agentSpriteForge"][
            "verification"
        ].pop("reason")

        errors = repository_validator.validate_harness_lock_data(
            manifest,
            "6000.4.10f1",
        )

        self.assertTrue(
            any(
                "agentSpriteForge.verification.reason" in error
                for error in errors
            ),
            errors,
        )

    def test_rejects_fixture_version_mismatch(self):
        manifest = self.load_manifest()

        errors = repository_validator.validate_harness_lock_data(
            manifest,
            "6000.4.11f1",
        )

        self.assertTrue(
            any("fixture version" in error for error in errors),
            errors,
        )

    def test_rejects_missing_sprite_forge_requirement(self):
        manifest = self.load_manifest()
        manifest["externalDependencies"]["agentSpriteForge"][
            "pythonPackages"
        ].pop("Pillow")

        errors = repository_validator.validate_harness_lock_data(
            manifest,
            "6000.4.10f1",
        )

        self.assertTrue(
            any("pythonPackages.Pillow" in error for error in errors),
            errors,
        )


class InstallerSourceTests(unittest.TestCase):
    def test_maps_unity_template_into_project_paths(self):
        installer = load_module(
            "install",
            ROOT / "scripts" / "install.py",
        )

        sources = installer.source_files(ROOT, skip_agents=False)
        relative_paths = {item.relative.as_posix() for item in sources}

        self.assertIn(
            "Assets/UnityCodexHarness/Editor/AssetValidationBatch.cs",
            relative_paths,
        )
        self.assertIn(
            "ProjectSettings/UnityCodexHarnessAssetValidation.json",
            relative_paths,
        )
        self.assertIn("harness.lock.json", relative_paths)
        config = next(
            item
            for item in sources
            if item.relative.as_posix()
            == "ProjectSettings/UnityCodexHarnessAssetValidation.json"
        )
        self.assertTrue(config.preserve_existing)

    def test_fixture_validator_matches_install_template(self):
        template_root = ROOT / "templates" / "unity"
        fixture_root = ROOT / "tests" / "fixtures" / "UnityValidationFixture"
        relative_paths = [
            Path("Assets/UnityCodexHarness.meta"),
            Path("Assets/UnityCodexHarness/Editor.meta"),
            Path(
                "Assets/UnityCodexHarness/Editor/"
                "UnityCodexHarness.Validation.Editor.asmdef"
            ),
            Path(
                "Assets/UnityCodexHarness/Editor/"
                "UnityCodexHarness.Validation.Editor.asmdef.meta"
            ),
            Path("Assets/UnityCodexHarness/Editor/AssetValidationBatch.cs"),
            Path("Assets/UnityCodexHarness/Editor/AssetValidationBatch.cs.meta"),
        ]

        for relative_path in relative_paths:
            self.assertEqual(
                (template_root / relative_path).read_bytes(),
                (fixture_root / relative_path).read_bytes(),
                relative_path.as_posix(),
            )


class InstallerGitignoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.installer = load_module(
            "install_gitignore",
            ROOT / "scripts" / "install.py",
        )

    def test_appends_managed_block_without_replacing_existing_rules(self):
        existing = "Library/\n# Local rule\n/Builds/\n"

        updated = self.installer.managed_gitignore_text(existing)

        self.assertTrue(updated.startswith(existing))
        self.assertIn(self.installer.GITIGNORE_BLOCK, updated)

    def test_managed_block_update_is_idempotent(self):
        initial = self.installer.managed_gitignore_text("Library/\n")

        updated = self.installer.managed_gitignore_text(initial)

        self.assertEqual(updated, initial)
        self.assertEqual(updated.count(self.installer.GITIGNORE_BEGIN), 1)
        self.assertEqual(updated.count(self.installer.GITIGNORE_RULE), 1)

    def test_replaces_only_existing_managed_block(self):
        existing = "\n".join(
            (
                "Library/",
                self.installer.GITIGNORE_BEGIN,
                "/OldArtifacts/",
                self.installer.GITIGNORE_END,
                "/Builds/",
                "",
            )
        )

        updated = self.installer.managed_gitignore_text(existing)

        self.assertIn("Library/", updated)
        self.assertIn("/Builds/", updated)
        self.assertNotIn("/OldArtifacts/", updated)
        self.assertIn(self.installer.GITIGNORE_BLOCK, updated)

    def test_rejects_unmatched_managed_marker(self):
        with self.assertRaises(ValueError):
            self.installer.managed_gitignore_text(
                self.installer.GITIGNORE_BEGIN + "\n/Artifacts/\n"
            )

    def test_preserves_crlf_line_endings(self):
        existing = "Library/\r\n/Builds/\r\n"

        updated = self.installer.managed_gitignore_text(existing)

        self.assertNotIn("\n", updated.replace("\r\n", ""))
        self.assertTrue(
            self.installer.has_managed_gitignore_block(updated)
        )

    def test_plans_create_update_and_unchanged_actions(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)

            action, updated = self.installer.plan_gitignore_update(project_root)
            self.assertEqual(action, "create")

            (project_root / ".gitignore").write_text(
                "Library/\n",
                encoding="utf-8",
            )
            action, updated = self.installer.plan_gitignore_update(project_root)
            self.assertEqual(action, "update")

            (project_root / ".gitignore").write_text(
                updated,
                encoding="utf-8",
            )
            action, _ = self.installer.plan_gitignore_update(project_root)
            self.assertEqual(action, "unchanged")

    def test_check_accepts_managed_rule_without_git_repository(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            (project_root / ".gitignore").write_text(
                self.installer.GITIGNORE_BLOCK + "\n",
                encoding="utf-8",
            )

            ignored, detail = self.installer.git_ignores_artifacts(project_root)

            self.assertTrue(ignored, detail)

    def test_check_rejects_missing_rule_without_git_repository(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            (project_root / ".gitignore").write_text(
                "Library/\n",
                encoding="utf-8",
            )

            ignored, _ = self.installer.git_ignores_artifacts(project_root)

            self.assertFalse(ignored)

    def test_check_rejects_artifacts_already_tracked_by_git(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            artifacts = project_root / "Artifacts"
            artifacts.mkdir()
            evidence = artifacts / "evidence.log"
            evidence.write_text("tracked\n", encoding="utf-8")
            subprocess.run(
                ["git", "init", "--quiet", str(project_root)],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(project_root), "add", "Artifacts/evidence.log"],
                check=True,
            )
            (project_root / ".gitignore").write_text(
                self.installer.GITIGNORE_BLOCK + "\n",
                encoding="utf-8",
            )

            ignored, detail = self.installer.git_ignores_artifacts(project_root)

            self.assertFalse(ignored)
            self.assertIn("already tracked", detail)

    def create_minimal_unity_project(self, project_root: Path) -> None:
        (project_root / "Assets").mkdir()
        (project_root / "Packages").mkdir()
        (project_root / "ProjectSettings").mkdir()
        (project_root / "ProjectSettings" / "ProjectVersion.txt").write_text(
            "m_EditorVersion: 6000.4.10f1\n",
            encoding="utf-8",
        )

    def test_cli_install_updates_and_checks_gitignore(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            self.create_minimal_unity_project(project_root)
            (project_root / ".gitignore").write_text(
                "Library/\n",
                encoding="utf-8",
            )

            install = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "install.py"),
                    str(project_root),
                    "--skip-agents",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            check = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "install.py"),
                    str(project_root),
                    "--check",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(install.returncode, 0, install.stderr)
            self.assertIn("update: .gitignore", install.stdout)
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertIn("Artifacts ignore check: PASS", check.stdout)
            self.assertIn(
                self.installer.GITIGNORE_BLOCK,
                (project_root / ".gitignore").read_text(encoding="utf-8"),
            )

    def test_cli_dry_run_does_not_update_gitignore(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            self.create_minimal_unity_project(project_root)
            original = "Library/\n"
            (project_root / ".gitignore").write_text(
                original,
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "install.py"),
                    str(project_root),
                    "--dry-run",
                    "--skip-agents",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("would update: .gitignore", result.stdout)
            self.assertEqual(
                (project_root / ".gitignore").read_text(encoding="utf-8"),
                original,
            )

    def test_cli_stops_before_changes_when_artifacts_are_tracked(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            self.create_minimal_unity_project(project_root)
            artifacts = project_root / "Artifacts"
            artifacts.mkdir()
            (artifacts / "evidence.log").write_text(
                "tracked\n",
                encoding="utf-8",
            )
            original = "Library/\n"
            (project_root / ".gitignore").write_text(
                original,
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "init", "--quiet", str(project_root)],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(project_root), "add", "Artifacts/evidence.log"],
                check=True,
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "install.py"),
                    str(project_root),
                    "--skip-agents",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("already tracked by Git", result.stderr)
            self.assertFalse((project_root / ".codex").exists())
            self.assertEqual(
                (project_root / ".gitignore").read_text(encoding="utf-8"),
                original,
            )


if __name__ == "__main__":
    unittest.main()
