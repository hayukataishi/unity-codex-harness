from __future__ import annotations

import importlib.util
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


if __name__ == "__main__":
    unittest.main()
