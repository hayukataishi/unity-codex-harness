from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from urllib.error import URLError
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_gameci_image.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gameci = load_module("check_gameci_image", SCRIPT)
repository_validator = load_module(
    "validate_repository",
    ROOT / "scripts" / "validate_repository.py",
)


class GameCiImageTests(unittest.TestCase):
    def load_manifest(self):
        return json.loads(
            (ROOT / "harness.lock.json").read_text(encoding="utf-8")
        )

    def remote_payload(self):
        image = self.load_manifest()["ci"]["gameCI"]["editorImage"]
        return {
            "name": image["tag"],
            "tag_status": "active",
            "digest": image["digest"],
            "images": [
                {
                    "architecture": "amd64",
                    "os": "linux",
                    "status": "active",
                }
            ],
        }

    def test_repository_lock_configuration_is_valid(self):
        self.assertEqual(
            gameci.validate_lock_configuration(self.load_manifest()),
            [],
        )

    def test_repository_workflow_matches_lock(self):
        self.assertEqual(
            repository_validator.validate_gameci_workflow(ROOT),
            [],
        )

    def test_rejects_unity_version_mismatch(self):
        manifest = self.load_manifest()
        manifest["harness"]["unityFixtureVersion"] = "6000.4.11f1"

        errors = gameci.validate_lock_configuration(manifest)

        self.assertTrue(any("tag must match" in error for error in errors))

    def test_rejects_unpinned_digest_reference(self):
        manifest = self.load_manifest()
        manifest["ci"]["gameCI"]["editorImage"][
            "reference"
        ] = "unityci/editor:latest"

        errors = gameci.validate_lock_configuration(manifest)

        self.assertIn(
            "GameCI editor image reference must pin tag and digest",
            errors,
        )

    def test_accepts_active_matching_remote_payload(self):
        manifest = self.load_manifest()
        image = manifest["ci"]["gameCI"]["editorImage"]

        self.assertEqual(
            gameci.validate_remote_payload(
                self.remote_payload(),
                image["tag"],
                image["digest"],
            ),
            [],
        )

    def test_rejects_remote_digest_mismatch(self):
        manifest = self.load_manifest()
        image = manifest["ci"]["gameCI"]["editorImage"]
        payload = self.remote_payload()
        payload["digest"] = "sha256:" + ("0" * 64)

        errors = gameci.validate_remote_payload(
            payload,
            image["tag"],
            image["digest"],
        )

        self.assertTrue(any("digest does not match" in error for error in errors))

    def test_rejects_inactive_or_missing_linux_image(self):
        manifest = self.load_manifest()
        image = manifest["ci"]["gameCI"]["editorImage"]
        payload = deepcopy(self.remote_payload())
        payload["tag_status"] = "inactive"
        payload["images"] = []

        errors = gameci.validate_remote_payload(
            payload,
            image["tag"],
            image["digest"],
        )

        self.assertTrue(any("not active" in error for error in errors))
        self.assertTrue(any("linux/amd64" in error for error in errors))

    def test_rejects_workflow_image_drift(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / "harness.lock.json").write_text(
                (ROOT / "harness.lock.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            workflow = (
                ROOT / ".github" / "workflows" / "validate-harness.yml"
            ).read_text(encoding="utf-8")
            workflow = workflow.replace(
                "ubuntu-6000.4.10f1-linux-il2cpp-3.2.2",
                "ubuntu-6000.4.11f1-linux-il2cpp-3.2.2",
            )
            (
                root / ".github" / "workflows" / "validate-harness.yml"
            ).write_text(workflow, encoding="utf-8")

            errors = repository_validator.validate_gameci_workflow(root)

            self.assertTrue(
                any("does not match harness.lock.json" in error for error in errors),
                errors,
            )

    def test_remote_network_failure_is_blocked(self):
        with patch.object(
            gameci.urllib.request,
            "urlopen",
            side_effect=URLError("offline"),
        ):
            with self.assertRaises(gameci.RemoteVerificationError):
                gameci.fetch_remote_payload(
                    "https://example.invalid/image",
                    timeout=1,
                    attempts=1,
                )

    def test_cli_validates_lock_without_network(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("GameCI image check: PASS", completed.stdout)
        self.assertIn("lock verified", completed.stdout)
