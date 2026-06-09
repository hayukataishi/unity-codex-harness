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
verify_run = load_module(
    "verify_validation_run",
    SCRIPTS / "verify_validation_run.py",
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

    def test_rejects_non_numeric_nunit_attributes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            result_path = Path(temporary_directory) / "EditMode.xml"
            result_path.write_text(
                '<test-run total="invalid" failed="0" result="Passed" />',
                encoding="utf-8",
            )

            result, notes = runner.parse_nunit_result(result_path, 0)

            self.assertEqual(result, "FAIL")
            self.assertIn("Invalid numeric", notes)


class ValidationRunLifecycleTests(unittest.TestCase):
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

    def create_validation_run(self, project: Path) -> str:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "create_validation_run.py"),
                "--project-root",
                str(project),
                "--design-id",
                "DEBUG-001",
                "--ac-id",
                "DEBUG-001-AC01",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()

    def test_run_completes_once_and_detects_artifact_changes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            run_relative = self.create_validation_run(project)
            run_dir = project / run_relative
            initial = json.loads(
                (run_dir / "RunManifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(initial["schemaVersion"], 2)
            self.assertEqual(initial["state"], "RUNNING")
            self.assertEqual(initial["result"], "NOT RUN")

            results_relative = f"{run_relative}/Logs/ValidationResults.json"
            results_path = project / results_relative
            (run_dir / "Logs" / "static.json").write_text(
                '{"status":"PASS"}\n',
                encoding="utf-8",
            )
            results_path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "commands": [
                            {
                                "name": "Static",
                                "command": "python3 validate.py",
                                "exitCode": 0,
                            }
                        ],
                        "checks": [
                            {
                                "name": "Static",
                                "result": "PASS",
                                "evidence": f"{run_relative}/Logs/static.json",
                            }
                        ],
                        "acceptanceCriteria": [
                            {
                                "id": "DEBUG-001-AC01",
                                "result": "PASS",
                                "evidence": [results_relative],
                            }
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            finalized = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "finalize_validation_run.py"),
                    "--project-root",
                    str(project),
                    "--run-dir",
                    run_relative,
                    "--results",
                    results_relative,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(finalized.returncode, 0, finalized.stderr)

            manifest = json.loads(
                (run_dir / "RunManifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["state"], "COMPLETED")
            self.assertEqual(manifest["result"], "PASS")
            self.assertIn("completedAtUtc", manifest)
            self.assertIn("durationSeconds", manifest)
            self.assertTrue(manifest["artifactFiles"])
            self.assertTrue((run_dir / "RunManifest.sha256").is_file())
            self.assertEqual(verify_run.verify_run(project, run_dir), [])

            repeated = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "finalize_validation_run.py"),
                    "--project-root",
                    str(project),
                    "--run-dir",
                    run_relative,
                    "--results",
                    results_relative,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("already completed", repeated.stderr)

            report_path = run_dir / "Report.md"
            original_report = report_path.read_text(encoding="utf-8")
            with report_path.open("a", encoding="utf-8") as handle:
                handle.write("\nchanged after completion\n")
            errors = verify_run.verify_run(project, run_dir)
            self.assertTrue(
                any("artifact" in error and "mismatch" in error for error in errors),
                errors,
            )
            report_path.write_text(original_report, encoding="utf-8")

            manifest["targetPlatform"] = "Changed"
            (run_dir / "RunManifest.json").write_text(
                json.dumps(manifest, indent=2) + "\n",
                encoding="utf-8",
            )
            errors = verify_run.verify_run(project, run_dir)
            self.assertIn("RunManifest.json SHA-256 mismatch", errors)

    def test_unfinished_run_can_be_closed_as_blocked(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            run_relative = self.create_validation_run(project)
            run_dir = project / run_relative

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "finalize_validation_run.py"),
                    "--project-root",
                    str(project),
                    "--run-dir",
                    run_relative,
                    "--blocked-reason",
                    "Unity Editor was unavailable",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 1)
            manifest = json.loads(
                (run_dir / "RunManifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["state"], "COMPLETED")
            self.assertEqual(manifest["result"], "BLOCKED")
            self.assertEqual(
                manifest["acceptanceCriteria"][0]["result"],
                "BLOCKED",
            )
            self.assertEqual(verify_run.verify_run(project, run_dir), [])


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


class BuildProfileDocumentationTests(unittest.TestCase):
    def test_repository_uses_build_profile_guidance(self):
        self.assertEqual(
            repository_validator.validate_build_profile_documentation(ROOT),
            [],
        )

    def test_rejects_outdated_build_settings_guidance(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator.BUILD_PROFILE_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                text = "\n".join(required_values)
                if relative == "docs/unity_design_sheet.md":
                    text += "\nBuild Settings（登録）"
                path.write_text(text, encoding="utf-8")

            errors = (
                repository_validator.validate_build_profile_documentation(root)
            )

            self.assertTrue(
                any("outdated Build Settings guidance" in error for error in errors),
                errors,
            )


class CrossCuttingDocumentationTests(unittest.TestCase):
    def test_repository_defines_cross_cutting_adoption_gate(self):
        self.assertEqual(
            repository_validator.validate_cross_cutting_documentation(ROOT),
            [],
        )

    def test_rejects_missing_privacy_adoption_row(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator.CROSS_CUTTING_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                values = [
                    value
                    for value in required_values
                    if value != "| Privacy / Consent / Compliance |"
                ]
                path.write_text("\n".join(values), encoding="utf-8")

            errors = (
                repository_validator.validate_cross_cutting_documentation(root)
            )

            self.assertTrue(
                any(
                    "Privacy / Consent / Compliance" in error
                    for error in errors
                ),
                errors,
            )

    def test_rejects_cross_cutting_topics_returning_to_appendix_only(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator.CROSS_CUTTING_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                text = "\n".join(required_values)
                if relative == "docs/unity_design_sheet.md":
                    text += "\n**ネットワーク同期** … マルチプレイなら必須"
                path.write_text(text, encoding="utf-8")

            errors = (
                repository_validator.validate_cross_cutting_documentation(root)
            )

            self.assertTrue(
                any(
                    "cross-cutting topic remains appendix-only" in error
                    for error in errors
                ),
                errors,
            )


class ArchitectureProfileDocumentationTests(unittest.TestCase):
    def test_repository_defines_scale_appropriate_architecture_profiles(self):
        self.assertEqual(
            repository_validator.validate_architecture_profile_documentation(
                ROOT
            ),
            [],
        )

    def test_rejects_missing_large_profile_guidance(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator.ARCHITECTURE_PROFILE_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                values = [
                    value
                    for value in required_values
                    if value != "| `Large` |"
                ]
                path.write_text("\n".join(values), encoding="utf-8")

            errors = (
                repository_validator
                .validate_architecture_profile_documentation(root)
            )

            self.assertTrue(
                any("| `Large` |" in error for error in errors),
                errors,
            )

    def test_rejects_service_locator_as_medium_scale_default(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator.ARCHITECTURE_PROFILE_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                text = "\n".join(required_values)
                if relative == "docs/unity_design_sheet.md":
                    text += "\n| ServiceLocator | ☐ | 中規模向け |"
                path.write_text(text, encoding="utf-8")

            errors = (
                repository_validator
                .validate_architecture_profile_documentation(root)
            )

            self.assertTrue(
                any(
                    "overprescriptive architecture guidance" in error
                    for error in errors
                ),
                errors,
            )


class SaveCompatibilityDocumentationTests(unittest.TestCase):
    def test_repository_defines_save_compatibility_gate(self):
        self.assertEqual(
            repository_validator.validate_save_compatibility_documentation(
                ROOT
            ),
            [],
        )

    def test_rejects_missing_atomic_write_guidance(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator.SAVE_COMPATIBILITY_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                values = [
                    value
                    for value in required_values
                    if value != "| Atomic write |"
                ]
                path.write_text("\n".join(values), encoding="utf-8")

            errors = (
                repository_validator
                .validate_save_compatibility_documentation(root)
            )

            self.assertTrue(
                any("| Atomic write |" in error for error in errors),
                errors,
            )

    def test_rejects_playerprefs_as_primary_save_choice(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator.SAVE_COMPATIBILITY_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                text = "\n".join(required_values)
                if relative == "docs/unity_design_sheet.md":
                    text += (
                        "\n保存方式      : JSON ファイル / PlayerPrefs / "
                        "暗号化  （いずれか）"
                    )
                path.write_text(text, encoding="utf-8")

            errors = (
                repository_validator
                .validate_save_compatibility_documentation(root)
            )

            self.assertTrue(
                any("unsafe minimal save guidance" in error for error in errors),
                errors,
            )


class SourceControlDocumentationTests(unittest.TestCase):
    def test_repository_defines_selectable_source_control_policy(self):
        self.assertEqual(
            repository_validator.validate_source_control_documentation(ROOT),
            [],
        )

    def test_rejects_missing_visible_meta_files_guidance(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator.SOURCE_CONTROL_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                values = [
                    value
                    for value in required_values
                    if value != "Visible Meta Files"
                ]
                path.write_text("\n".join(values), encoding="utf-8")

            errors = (
                repository_validator.validate_source_control_documentation(root)
            )

            self.assertTrue(
                any("Visible Meta Files" in error for error in errors),
                errors,
            )

    def test_rejects_fixed_branch_and_extension_lfs_template(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator.SOURCE_CONTROL_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                text = "\n".join(required_values)
                if relative == "docs/unity_design_sheet.md":
                    text += (
                        "\nGit LFS       : .psd .png .fbx .wav 等を対象"
                        "\nブランチ運用  : main / develop / feature/*"
                    )
                path.write_text(text, encoding="utf-8")

            errors = (
                repository_validator.validate_source_control_documentation(root)
            )

            self.assertTrue(
                any(
                    "overprescriptive source-control guidance" in error
                    for error in errors
                ),
                errors,
            )


class CinemachineDocumentationTests(unittest.TestCase):
    def test_repository_uses_cinemachine_3_guidance(self):
        self.assertEqual(
            repository_validator.validate_cinemachine_documentation(ROOT),
            [],
        )

    def test_rejects_cinemachine_2_camera_example(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator.CINEMACHINE_3_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                text = "\n".join(required_values)
                if relative == "docs/unity_design_sheet.md":
                    text += (
                        "\n| `FollowCamera` | プレイヤー追従 | "
                        "CinemachineVirtualCamera | 10 |"
                    )
                path.write_text(text, encoding="utf-8")

            errors = (
                repository_validator.validate_cinemachine_documentation(root)
            )

            self.assertTrue(
                any(
                    "outdated Cinemachine 2 example" in error
                    for error in errors
                ),
                errors,
            )


class ValidationRunDocumentationTests(unittest.TestCase):
    def test_repository_defines_completed_validation_runs(self):
        self.assertEqual(
            repository_validator.validate_validation_run_lifecycle(ROOT),
            [],
        )

    def test_rejects_missing_validation_run_verifier(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator.VALIDATION_RUN_REQUIRED_TEXT.items()
            ):
                if relative.endswith("verify_validation_run.py"):
                    continue
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    "\n".join(required_values),
                    encoding="utf-8",
                )

            errors = (
                repository_validator.validate_validation_run_lifecycle(root)
            )

            self.assertTrue(
                any(
                    "missing Validation Run lifecycle file" in error
                    and "verify_validation_run.py" in error
                    for error in errors
                ),
                errors,
            )


class TemplateRegressionDocumentationTests(unittest.TestCase):
    def test_repository_defines_template_regression_suite(self):
        self.assertEqual(
            repository_validator.validate_template_regression_suite(ROOT),
            [],
        )

    def test_rejects_missing_installer_regression_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator.TEMPLATE_REGRESSION_REQUIRED_TEXT.items()
            ):
                if relative.endswith("test_installer_cli.py"):
                    continue
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    "\n".join(required_values),
                    encoding="utf-8",
                )

            errors = (
                repository_validator.validate_template_regression_suite(root)
            )

            self.assertTrue(
                any(
                    "missing template regression file" in error
                    and "test_installer_cli.py" in error
                    for error in errors
                ),
                errors,
            )


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
        self.assertIn(
            ".codex/skills/validate-unity-change/scripts/"
            "finalize_validation_run.py",
            relative_paths,
        )
        self.assertIn(
            ".codex/skills/validate-unity-change/scripts/"
            "verify_validation_run.py",
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
