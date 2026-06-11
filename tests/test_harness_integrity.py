from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install.py"
VERIFIER = ROOT / "scripts" / "verify_harness_integrity.py"


def load_verifier():
    spec = importlib.util.spec_from_file_location(
        "verify_harness_integrity",
        VERIFIER,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


integrity = load_verifier()


class HarnessIntegrityTests(unittest.TestCase):
    def create_project(self, root: Path) -> Path:
        project = root / "UnityProject"
        (project / "Assets").mkdir(parents=True)
        (project / "Packages").mkdir()
        (project / "ProjectSettings").mkdir()
        (project / "ProjectSettings" / "ProjectVersion.txt").write_text(
            "m_EditorVersion: 6000.4.10f1\n",
            encoding="utf-8",
        )
        (project / ".gitignore").write_text("Library/\n", encoding="utf-8")
        subprocess.run(
            ["git", "init", "-q"],
            cwd=project,
            check=True,
            capture_output=True,
            text=True,
        )
        result = subprocess.run(
            [
                sys.executable,
                str(INSTALLER),
                str(project),
                "--skip-agents",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return project

    def rewrite_manifest_sidecar(self, project: Path) -> None:
        manifest = project / integrity.MANIFEST_PATH
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        (project / integrity.MANIFEST_HASH_PATH).write_text(
            f"{digest}  {integrity.MANIFEST_PATH.name}\n",
            encoding="utf-8",
        )

    def test_installed_project_passes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))

            self.assertEqual(integrity.validate_integrity(project), [])

    def test_modified_harness_managed_file_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            managed = project / "docs" / "unity_harness_capabilities.md"
            managed.write_text("modified\n", encoding="utf-8")

            errors = integrity.validate_integrity(project)

            self.assertTrue(
                any(
                    "harness-managed SHA-256 mismatch" in error
                    and "unity_harness_capabilities.md" in error
                    for error in errors
                ),
                errors,
            )

    def test_missing_harness_managed_file_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            managed = (
                project
                / "scripts"
                / "unity_codex_harness"
                / "validate_design_contract.py"
            )
            managed.unlink()

            errors = integrity.validate_integrity(project)

            self.assertIn(
                "missing harness-managed file: "
                "scripts/unity_codex_harness/validate_design_contract.py",
                errors,
            )

    def test_missing_design_readiness_validator_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            managed = (
                project
                / "scripts"
                / "unity_codex_harness"
                / "validate_design_readiness.py"
            )
            managed.unlink()

            errors = integrity.validate_integrity(project)

            self.assertIn(
                "missing harness-managed file: "
                "scripts/unity_codex_harness/validate_design_readiness.py",
                errors,
            )

    def test_project_owned_file_may_change(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            design = project / "docs" / "unity_design_sheet.md"
            design.write_text("project decision\n", encoding="utf-8")

            self.assertEqual(integrity.validate_integrity(project), [])

    def test_modified_standard_lock_fails_but_override_may_change(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            overrides = project / "harness.overrides.json"
            overrides.write_text(
                '{"schemaVersion":1,"externalDependencies":{}}\n',
                encoding="utf-8",
            )

            self.assertEqual(integrity.validate_integrity(project), [])

            lock_path = project / "harness.lock.json"
            lock_path.write_text('{"custom":true}\n', encoding="utf-8")
            errors = integrity.validate_integrity(project)

            self.assertTrue(
                any(
                    "harness-managed SHA-256 mismatch: harness.lock.json"
                    in error
                    for error in errors
                ),
                errors,
            )

    def test_modified_manifest_without_sidecar_update_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            manifest = project / integrity.MANIFEST_PATH
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["harness"]["release"] = "tampered"
            manifest.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            errors = integrity.validate_integrity(project)

            self.assertEqual(len(errors), 1)
            self.assertIn("install manifest SHA-256 mismatch", errors[0])

    def test_unsafe_manifest_path_fails_even_with_updated_sidecar(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            manifest = project / integrity.MANIFEST_PATH
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["files"][0]["path"] = "../outside.txt"
            manifest.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self.rewrite_manifest_sidecar(project)

            errors = integrity.validate_integrity(project)

            self.assertTrue(
                any("unsafe install manifest path" in error for error in errors),
                errors,
            )

    def test_windows_drive_manifest_path_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            manifest = project / integrity.MANIFEST_PATH
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["files"][0]["path"] = "C:/outside.txt"
            manifest.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            self.rewrite_manifest_sidecar(project)

            errors = integrity.validate_integrity(project)

            self.assertTrue(
                any("unsafe install manifest path" in error for error in errors),
                errors,
            )

    def test_unexpected_file_in_exclusive_root_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            unexpected = (
                project
                / ".codex"
                / "skills"
                / "maintain-game-design"
                / "LOCAL_OVERRIDE.md"
            )
            unexpected.write_text("override\n", encoding="utf-8")

            errors = integrity.validate_integrity(project)

            self.assertIn(
                "unexpected file in exclusive managed root: "
                ".codex/skills/maintain-game-design/LOCAL_OVERRIDE.md",
                errors,
            )


if __name__ == "__main__":
    unittest.main()
