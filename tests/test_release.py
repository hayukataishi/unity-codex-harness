from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "scripts" / "build_release.py"


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_release",
        BUILDER_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_builder()


class ReleaseContractTests(unittest.TestCase):
    def test_repository_release_contract_is_valid(self):
        self.assertEqual(builder.validate_release(ROOT), [])

    def test_rejects_tag_mismatch(self):
        errors = builder.validate_release(ROOT, "v9.9.9")

        self.assertTrue(
            any("release tag mismatch" in error for error in errors),
            errors,
        )

    def test_rejects_lock_release_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            release = json.loads(
                (ROOT / "harness.release.json").read_text(encoding="utf-8")
            )
            lock = json.loads(
                (ROOT / "harness.lock.json").read_text(encoding="utf-8")
            )
            lock["harness"]["release"] = "9.9.9"
            (root / "harness.release.json").write_text(
                json.dumps(release),
                encoding="utf-8",
            )
            (root / "harness.lock.json").write_text(
                json.dumps(lock),
                encoding="utf-8",
            )

            errors = builder.validate_release(root)

            self.assertTrue(
                any(
                    "harness.lock.json harness.release" in error
                    for error in errors
                ),
                errors,
            )

    def test_rejects_unsafe_release_notes_path(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            release = json.loads(
                (ROOT / "harness.release.json").read_text(encoding="utf-8")
            )
            lock = json.loads(
                (ROOT / "harness.lock.json").read_text(encoding="utf-8")
            )
            release["releaseNotes"] = "../outside.md"
            (root / "harness.release.json").write_text(
                json.dumps(release),
                encoding="utf-8",
            )
            (root / "harness.lock.json").write_text(
                json.dumps(lock),
                encoding="utf-8",
            )

            errors = builder.validate_release(root)

            self.assertTrue(
                any(
                    "releaseNotes must be a safe" in error
                    for error in errors
                ),
                errors,
            )

    def test_release_archive_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            first = root / "first"
            second = root / "second"

            first_archive, _, _ = builder.build_release(ROOT, first)
            second_archive, _, _ = builder.build_release(ROOT, second)

            self.assertEqual(
                builder.sha256_file(first_archive),
                builder.sha256_file(second_archive),
            )

    def test_release_archive_contains_runtime_and_excludes_source_history(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive_path, manifest_path, checksums_path = (
                builder.build_release(
                    ROOT,
                    Path(temporary_directory),
                )
            )
            prefix = "unity-codex-harness-0.1.0/"

            with zipfile.ZipFile(archive_path) as archive:
                names = set(archive.namelist())

            self.assertIn(prefix + "scripts/install.py", names)
            self.assertIn(prefix + "harness.release.json", names)
            self.assertIn(
                prefix + "docs/unity_harness_release.md",
                names,
            )
            self.assertNotIn(
                prefix
                + "docs/unity_harness_evaluation_2026-06-08.md",
                names,
            )
            self.assertFalse(
                any(name.startswith(prefix + "tests/") for name in names)
            )
            self.assertFalse(
                any(name.startswith(prefix + ".github/") for name in names)
            )
            release_manifest = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )
            self.assertEqual(
                release_manifest["artifact"]["sha256"],
                builder.sha256_file(archive_path),
            )
            checksums = checksums_path.read_text(encoding="utf-8")
            self.assertIn(archive_path.name, checksums)
            self.assertIn(manifest_path.name, checksums)


if __name__ == "__main__":
    unittest.main()
