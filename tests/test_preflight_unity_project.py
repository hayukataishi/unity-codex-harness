from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = (
    ROOT
    / ".agents"
    / "skills"
    / "validate-unity-change"
    / "scripts"
    / "preflight_unity_project.py"
)


class PreflightRegressionTests(unittest.TestCase):
    def create_project(self, root: Path) -> Path:
        project = root / "UnityProject"
        (project / "Assets").mkdir(parents=True)
        (project / "Packages").mkdir()
        (project / "Packages" / "manifest.json").write_text(
            '{"dependencies":{}}\n',
            encoding="utf-8",
        )
        (project / "ProjectSettings").mkdir()
        (project / "ProjectSettings" / "ProjectVersion.txt").write_text(
            "m_EditorVersion: 6000.4.10f1\n",
            encoding="utf-8",
        )
        return project

    def write_meta(self, target: Path, guid: str) -> None:
        Path(str(target) + ".meta").write_text(
            f"fileFormatVersion: 2\nguid: {guid}\n",
            encoding="utf-8",
        )

    def run_preflight(
        self,
        project: Path,
    ) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = subprocess.run(
            [
                sys.executable,
                str(PREFLIGHT),
                "--project-root",
                str(project),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        return result, json.loads(result.stdout)

    def error_codes(self, report: dict) -> set[str]:
        return {error["code"] for error in report["errors"]}

    def test_accepts_valid_assets_and_meta_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            folder = project / "Assets" / "Game"
            folder.mkdir()
            self.write_meta(folder, "11111111111111111111111111111111")
            asset = folder / "Data.asset"
            asset.write_text("%YAML 1.1\n", encoding="utf-8")
            self.write_meta(asset, "22222222222222222222222222222222")

            result, report = self.run_preflight(project)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["unityVersion"], "6000.4.10f1")

    def test_detects_missing_and_orphan_meta(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            asset = project / "Assets" / "NoMeta.asset"
            asset.write_text("%YAML 1.1\n", encoding="utf-8")
            orphan = project / "Assets" / "Gone.asset.meta"
            orphan.write_text(
                "fileFormatVersion: 2\n"
                "guid: 33333333333333333333333333333333\n",
                encoding="utf-8",
            )

            result, report = self.run_preflight(project)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("MISSING_META", self.error_codes(report))
            self.assertIn("ORPHAN_META", self.error_codes(report))

    def test_detects_invalid_and_duplicate_guid(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            first = project / "Assets" / "First.asset"
            second = project / "Assets" / "Second.asset"
            invalid = project / "Assets" / "Invalid.asset"
            for path in (first, second, invalid):
                path.write_text("%YAML 1.1\n", encoding="utf-8")
            duplicate = "44444444444444444444444444444444"
            self.write_meta(first, duplicate)
            self.write_meta(second, duplicate)
            Path(str(invalid) + ".meta").write_text(
                "fileFormatVersion: 2\nguid: invalid\n",
                encoding="utf-8",
            )

            result, report = self.run_preflight(project)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("DUPLICATE_GUID", self.error_codes(report))
            self.assertIn("MISSING_OR_INVALID_GUID", self.error_codes(report))

    def test_detects_missing_script_marker(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            prefab = project / "Assets" / "Broken.prefab"
            prefab.write_text(
                "--- !u!114 &1\n"
                "MonoBehaviour:\n"
                "  m_Script: {fileID: 0}\n",
                encoding="utf-8",
            )
            self.write_meta(prefab, "55555555555555555555555555555555")

            result, report = self.run_preflight(project)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("MISSING_SCRIPT_MARKER", self.error_codes(report))

    def test_reports_missing_required_project_paths(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory) / "Incomplete"
            (project / "Assets").mkdir(parents=True)

            result, report = self.run_preflight(project)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("MISSING_REQUIRED_PATH", self.error_codes(report))

    def test_ignores_hidden_asset_directories(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            hidden = project / "Assets" / ".generated"
            hidden.mkdir()
            (hidden / "NoMeta.asset").write_text(
                "%YAML 1.1\n",
                encoding="utf-8",
            )

            result, report = self.run_preflight(project)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(report["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
