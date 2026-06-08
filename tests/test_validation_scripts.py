from __future__ import annotations

import importlib.util
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


if __name__ == "__main__":
    unittest.main()
