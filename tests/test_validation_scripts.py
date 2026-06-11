from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import tomllib
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

    def test_missing_nunit_from_license_failure_is_blocked(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "EditMode.log"
            log_path.write_text(
                "ResponseStatus: Unsupported protocol version '1.18.1'.\n",
                encoding="utf-8",
            )

            result, notes = runner.parse_nunit_result(
                Path(temporary_directory) / "EditMode.xml",
                1,
                log_path,
            )

            self.assertEqual(result, "BLOCKED")
            self.assertIn("incompatible protocols", notes)

    def test_missing_asset_report_after_timeout_is_blocked(self):
        result, notes = runner.parse_asset_validation_result(
            Path("/not-created/AssetValidation.json"),
            runner.TIMEOUT_EXIT_CODE,
        )

        self.assertEqual(result, "BLOCKED")
        self.assertIn("timed out", notes)

    def test_compile_requires_a_valid_unity_result(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            log_path = root / "EditMode.log"
            log_path.write_text(
                "Unity exited before creating test results.\n",
                encoding="utf-8",
            )

            result, notes = runner.parse_compile_result(
                root / "EditMode.xml",
                log_path,
                1,
            )

            self.assertEqual(result, "FAIL")
            self.assertIn("completion was not proven", notes)

    def test_compile_passes_when_license_warning_recovers_and_xml_exists(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            log_path = root / "EditMode.log"
            result_path = root / "EditMode.xml"
            log_path.write_text(
                "\n".join(
                    [
                        "ResponseStatus: Unsupported protocol version '1.18.1'.",
                        "Successfully connected to LicensingClient.",
                        "Test run completed. Exiting with code 0.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            result_path.write_text(
                '<test-run total="1" failed="0" result="Passed" />\n',
                encoding="utf-8",
            )

            result, notes = runner.parse_compile_result(
                result_path,
                log_path,
                0,
            )

            self.assertEqual(result, "PASS")
            self.assertIn("Valid Unity test result", notes)

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
        (project / "Packages" / "manifest.json").write_text(
            '{"dependencies": {}}\n',
            encoding="utf-8",
        )
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

    def test_runner_finalizes_license_failure_without_missing_evidence(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = self.create_project(root)
            fake_unity = root / "fake_unity.py"
            fake_unity.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env python3",
                        "import pathlib",
                        "import sys",
                        "arguments = sys.argv[1:]",
                        "log_index = arguments.index('-logFile') + 1",
                        "log_path = pathlib.Path(arguments[log_index])",
                        "log_path.parent.mkdir(parents=True, exist_ok=True)",
                        "log_path.write_text(",
                        "    \"ResponseStatus: Unsupported protocol version "
                        "'1.18.1'.\\n\",",
                        "    encoding='utf-8',",
                        ")",
                        "raise SystemExit(1)",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            fake_unity.chmod(0o755)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "run_unity_validation.py"),
                    "--project-root",
                    str(project),
                    "--unity-editor",
                    str(fake_unity),
                    "--design-id",
                    "DEBUG-001",
                    "--ac-id",
                    "DEBUG-001-AC04",
                    "--timeout-seconds",
                    "5",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 1, completed.stderr)
            run_relative = completed.stdout.strip().splitlines()[-1]
            run_dir = project / run_relative
            manifest = json.loads(
                (run_dir / "RunManifest.json").read_text(encoding="utf-8")
            )
            checks = {
                check["name"]: check
                for check in manifest["checks"]
            }

            self.assertEqual(manifest["state"], "COMPLETED")
            self.assertEqual(manifest["result"], "BLOCKED")
            self.assertEqual(checks["Compile"]["result"], "BLOCKED")
            self.assertEqual(checks["EditMode"]["result"], "BLOCKED")
            self.assertEqual(checks["PlayMode"]["result"], "BLOCKED")
            self.assertEqual(
                checks["Asset validation"]["result"],
                "BLOCKED",
            )
            self.assertEqual(
                [command["name"] for command in manifest["commands"]],
                ["Preflight", "EditMode"],
            )
            evidence = verify_run.evidence_values(manifest)
            self.assertFalse(
                any(
                    value.endswith((".xml", "AssetValidation.json"))
                    for value in evidence
                ),
                evidence,
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
                if relative == "docs/unity_harness_requirements.md":
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
                if relative == "docs/unity_harness_requirements.md":
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
                if relative == "docs/unity_harness_requirements.md":
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
                if relative == "docs/unity_harness_requirements.md":
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
                if relative == "docs/unity_harness_requirements.md":
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
                if relative == "docs/unity_harness_requirements.md":
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


class DesignDocumentBoundaryTests(unittest.TestCase):
    def test_repository_separates_standard_and_game_requirements(self):
        self.assertEqual(
            repository_validator.validate_design_document_boundaries(ROOT),
            [],
        )

    def test_rejects_missing_project_owned_marker(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator
                .DESIGN_DOCUMENT_BOUNDARY_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                values = [
                    value
                    for value in required_values
                    if "UNITY_CODEX_PROJECT_OWNED: EDIT" not in value
                ]
                path.write_text("\n".join(values), encoding="utf-8")

            errors = (
                repository_validator
                .validate_design_document_boundaries(root)
            )

            self.assertTrue(
                any(
                    "UNITY_CODEX_PROJECT_OWNED: EDIT" in error
                    for error in errors
                ),
                errors,
            )

    def test_rejects_harness_debug_items_in_game_sheet(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator
                .DESIGN_DOCUMENT_BOUNDARY_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                text = "\n".join(required_values)
                if relative == "docs/unity_design_sheet.md":
                    text += "\n### DEBUG-999: harness regression"
                path.write_text(text, encoding="utf-8")

            errors = (
                repository_validator
                .validate_design_document_boundaries(root)
            )

            self.assertTrue(
                any(
                    "design document boundary violation" in error
                    for error in errors
                ),
                errors,
            )

    def test_rejects_internal_contract_in_standard_requirements(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator
                .DESIGN_DOCUMENT_BOUNDARY_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                text = "\n".join(required_values)
                if relative == "docs/unity_harness_requirements.md":
                    text += "\n### DEBUG-999: internal contract"
                path.write_text(text, encoding="utf-8")

            errors = (
                repository_validator
                .validate_design_document_boundaries(root)
            )

            self.assertTrue(
                any(
                    "design document boundary violation" in error
                    and "DEBUG-" in error
                    for error in errors
                ),
                errors,
            )


class HarnessIntegrityContractTests(unittest.TestCase):
    def test_repository_defines_harness_integrity_gate(self):
        self.assertEqual(
            repository_validator.validate_harness_integrity_contract(ROOT),
            [],
        )

    def test_rejects_missing_skill_integrity_gate(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator.HARNESS_INTEGRITY_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                values = list(required_values)
                if relative == ".codex/skills/implement-unity-feature/SKILL.md":
                    values.remove("verify_harness_integrity.py")
                path.write_text("\n".join(values), encoding="utf-8")

            errors = (
                repository_validator
                .validate_harness_integrity_contract(root)
            )

            self.assertTrue(
                any(
                    "implement-unity-feature/SKILL.md" in error
                    and "verify_harness_integrity.py" in error
                    for error in errors
                ),
                errors,
            )


class InitialDesignDialogueTests(unittest.TestCase):
    def test_repository_defines_initial_design_dialogue(self):
        self.assertEqual(
            repository_validator.validate_initial_design_dialogue(ROOT),
            [],
        )

    def test_rejects_subagent_write_authority(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator
                .INITIAL_DESIGN_DIALOGUE_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                values = list(required_values)
                if relative.endswith("subagent-audit.md"):
                    values.remove("Do not edit files")
                path.write_text("\n".join(values), encoding="utf-8")

            errors = repository_validator.validate_initial_design_dialogue(root)

            self.assertTrue(
                any(
                    "subagent-audit.md" in error
                    and "Do not edit files" in error
                    for error in errors
                ),
                errors,
            )

    def test_rejects_missing_final_phase(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator
                .INITIAL_DESIGN_DIALOGUE_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                values = list(required_values)
                if relative == "docs/unity_design_sheet.md":
                    values.remove("| `PHASE-09` |")
                path.write_text("\n".join(values), encoding="utf-8")

            errors = repository_validator.validate_initial_design_dialogue(root)

            self.assertTrue(
                any(
                    "docs/unity_design_sheet.md" in error
                    and "PHASE-09" in error
                    for error in errors
                ),
                errors,
            )

    def test_rejects_missing_milestone_phase_depth(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator
                .INITIAL_DESIGN_DIALOGUE_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                values = list(required_values)
                if relative.endswith("interview-phases.md"):
                    values.remove("## Phase depth by milestone")
                path.write_text("\n".join(values), encoding="utf-8")

            errors = repository_validator.validate_initial_design_dialogue(root)

            self.assertTrue(
                any(
                    "interview-phases.md" in error
                    and "Phase depth by milestone" in error
                    for error in errors
                ),
                errors,
            )

    def test_rejects_missing_dialogue_evidence(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator
                .INITIAL_DESIGN_DIALOGUE_REQUIRED_TEXT.items()
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                values = list(required_values)
                if relative == "docs/unity_design_sheet.md":
                    values.remove("#### 対話証跡")
                path.write_text("\n".join(values), encoding="utf-8")

            errors = repository_validator.validate_initial_design_dialogue(root)

            self.assertTrue(
                any(
                    "docs/unity_design_sheet.md" in error
                    and "対話証跡" in error
                    for error in errors
                ),
                errors,
            )

    def test_custom_design_auditor_is_read_only(self):
        agent = tomllib.loads(
            (
                ROOT
                / ".codex"
                / "agents"
                / "game-design-auditor.toml"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(agent["name"], "game_design_auditor")
        self.assertEqual(agent["sandbox_mode"], "read-only")
        self.assertIn("STANDARD_RECOMMENDED", agent["developer_instructions"])
        self.assertIn("GAME_SPECIFIC", agent["developer_instructions"])


class DesignReadinessContractTests(unittest.TestCase):
    def test_repository_defines_design_readiness_validator(self):
        self.assertEqual(
            repository_validator.validate_design_readiness_contract(ROOT),
            [],
        )

    def test_rejects_missing_readiness_cli(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for relative, required_values in (
                repository_validator.DESIGN_READINESS_REQUIRED_TEXT.items()
            ):
                if relative == "scripts/validate_design_readiness.py":
                    continue
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("\n".join(required_values), encoding="utf-8")

            errors = repository_validator.validate_design_readiness_contract(
                root
            )

            self.assertIn(
                "missing design readiness file: "
                "scripts/validate_design_readiness.py",
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

    def test_rejects_bundled_external_dependency(self):
        manifest = self.load_manifest()
        manifest["externalDependencies"]["unityMcp"]["distribution"][
            "bundled"
        ] = True

        errors = repository_validator.validate_harness_lock_data(
            manifest,
            "6000.4.10f1",
        )

        self.assertTrue(
            any("unityMcp.distribution.bundled" in error for error in errors),
            errors,
        )

    def test_requires_commit_pinned_unity_mcp_install_url(self):
        manifest = self.load_manifest()
        manifest["externalDependencies"]["unityMcp"]["install"][
            "unityPackageUrl"
        ] = "https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#main"

        errors = repository_validator.validate_harness_lock_data(
            manifest,
            "6000.4.10f1",
        )

        self.assertTrue(
            any("unityMcp.install.unityPackageUrl" in error for error in errors),
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
        self.assertIn(
            ".codex/skills/bootstrap-game-design/SKILL.md",
            relative_paths,
        )
        self.assertIn(
            ".codex/skills/bootstrap-game-design/references/"
            "subagent-audit.md",
            relative_paths,
        )
        self.assertIn(
            ".codex/agents/game-design-auditor.toml",
            relative_paths,
        )
        self.assertIn(
            "docs/unity_harness_agent_contract.md",
            relative_paths,
        )
        self.assertIn("harness.lock.json", relative_paths)
        self.assertIn(
            "scripts/unity_codex_harness/check_external_dependencies.py",
            relative_paths,
        )
        self.assertIn(
            "scripts/unity_codex_harness/validate_design_contract.py",
            relative_paths,
        )
        self.assertIn(
            "scripts/unity_codex_harness/validate_design_readiness.py",
            relative_paths,
        )
        self.assertIn(
            "scripts/unity_codex_harness/verify_harness_integrity.py",
            relative_paths,
        )
        config = next(
            item
            for item in sources
            if item.relative.as_posix()
            == "ProjectSettings/UnityCodexHarnessAssetValidation.json"
        )
        self.assertEqual(config.ownership, installer.OWNERSHIP_PROJECT)
        design = next(
            item
            for item in sources
            if item.relative.as_posix() == "docs/unity_design_sheet.md"
        )
        self.assertEqual(design.ownership, installer.OWNERSHIP_PROJECT)
        requirements = next(
            item
            for item in sources
            if item.relative.as_posix() == "docs/unity_harness_requirements.md"
        )
        self.assertEqual(requirements.ownership, installer.OWNERSHIP_HARNESS)
        agent_contract = next(
            item
            for item in sources
            if item.relative.as_posix()
            == "docs/unity_harness_agent_contract.md"
        )
        self.assertEqual(
            agent_contract.ownership,
            installer.OWNERSHIP_HARNESS,
        )
        integrity_checker = next(
            item
            for item in sources
            if item.relative.as_posix()
            == "scripts/unity_codex_harness/verify_harness_integrity.py"
        )
        self.assertEqual(
            integrity_checker.ownership,
            installer.OWNERSHIP_HARNESS,
        )
        bootstrap_skill = next(
            item
            for item in sources
            if item.relative.as_posix()
            == ".codex/skills/bootstrap-game-design/SKILL.md"
        )
        self.assertEqual(bootstrap_skill.ownership, installer.OWNERSHIP_HARNESS)
        design_auditor = next(
            item
            for item in sources
            if item.relative.as_posix()
            == ".codex/agents/game-design-auditor.toml"
        )
        self.assertEqual(design_auditor.ownership, installer.OWNERSHIP_HARNESS)
        validator = next(
            item
            for item in sources
            if item.relative.as_posix()
            == "Assets/UnityCodexHarness/Editor/AssetValidationBatch.cs"
        )
        self.assertEqual(validator.ownership, installer.OWNERSHIP_HARNESS)

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

    def test_check_rejects_rule_negated_later_in_gitignore(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            subprocess.run(
                ["git", "init", "--quiet", str(project_root)],
                check=True,
            )
            (project_root / ".gitignore").write_text(
                self.installer.GITIGNORE_BLOCK
                + "\n!/.codex/external/\n",
                encoding="utf-8",
            )

            ignored, detail = (
                self.installer.git_ignores_local_only_paths(project_root)
            )

            self.assertFalse(ignored)
            self.assertIn(".codex/external", detail)

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
            self.assertIn(
                "Harness local-path ignore check: PASS",
                check.stdout,
            )
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
