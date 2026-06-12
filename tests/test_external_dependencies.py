from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_external_dependencies.py"


class ExternalDependencyCheckTests(unittest.TestCase):
    def create_project(self, root: Path) -> Path:
        project = root / "UnityProject"
        (project / "Packages").mkdir(parents=True)
        lock = json.loads(
            (ROOT / "harness.lock.json").read_text(encoding="utf-8")
        )
        (project / "harness.lock.json").write_text(
            json.dumps(lock, indent=2) + "\n",
            encoding="utf-8",
        )
        (project / "harness.overrides.json").write_text(
            (ROOT / "harness.overrides.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (project / "Packages" / "manifest.json").write_text(
            json.dumps({"dependencies": {}}, indent=2) + "\n",
            encoding="utf-8",
        )
        return project

    def run_checker(
        self,
        project: Path,
        *arguments: str,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        if env is None:
            env = os.environ.copy()
            env["CODEX_HOME"] = str(project / ".test-codex-home")
            env["HOME"] = str(project / ".test-home")
        return subprocess.run(
            [
                sys.executable,
                str(CHECKER),
                "--project-root",
                str(project),
                *arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    def create_pinned_sprite_install(self, project: Path) -> None:
        checkout = (
            project / ".codex/external/agent-sprite-forge"
        )
        checkout.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "--quiet", str(checkout)],
            check=True,
        )
        (checkout / "README.md").write_text("fixture\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(checkout), "add", "README.md"],
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(checkout),
                "-c",
                "user.name=Unity Harness Test",
                "-c",
                "user.email=unity-harness@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "fixture",
            ],
            check=True,
        )
        commit = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        lock_path = project / "harness.lock.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        sprite = lock["externalDependencies"]["agentSpriteForge"]
        sprite["commit"] = commit
        sprite["ref"] = commit
        lock_path.write_text(
            json.dumps(lock, indent=2) + "\n",
            encoding="utf-8",
        )
        for name in sprite["install"]["skillNames"]:
            skill = project / ".agents/skills" / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                f"# {name}\n",
                encoding="utf-8",
            )

    def install_pinned_unity_mcp_reference(self, project: Path) -> None:
        lock = json.loads(
            (project / "harness.lock.json").read_text(encoding="utf-8")
        )
        unity_mcp = lock["externalDependencies"]["unityMcp"]
        manifest = {
            "dependencies": {
                unity_mcp["packageName"]: unity_mcp["install"][
                    "unityPackageUrl"
                ]
            }
        }
        (project / "Packages" / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_missing_dependencies_report_fixed_install_steps(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            before = {
                path.relative_to(project).as_posix(): path.read_bytes()
                for path in project.rglob("*")
                if path.is_file()
            }

            result = self.run_checker(project)

            after = {
                path.relative_to(project).as_posix(): path.read_bytes()
                for path in project.rglob("*")
                if path.is_file()
            }
            self.assertEqual(result.returncode, 1)
            self.assertEqual(after, before)
            self.assertIn("Unity MCP: MISSING", result.stdout)
            self.assertIn("agent-sprite-forge: MISSING", result.stdout)
            self.assertIn("Add package from git URL", result.stdout)
            self.assertIn(
                "417cf351a152b483c91e6e2deaf7ae355fa8eff3",
                result.stdout,
            )
            self.assertIn("Review each upstream license", result.stdout)

    def test_pinned_project_installation_passes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            self.create_pinned_sprite_install(project)
            self.install_pinned_unity_mcp_reference(project)

            result = self.run_checker(project, "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["result"], "PASS")
            self.assertTrue(
                all(check["status"] == "PASS" for check in report["checks"])
            )
            self.assertEqual(
                report["checks"][0]["connectionStatus"],
                "NOT CHECKED",
            )

    def test_unity_mcp_version_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            manifest = {
                "dependencies": {
                    "com.coplaydev.unity-mcp": (
                        "https://github.com/CoplayDev/"
                        "unity-mcp.git?path=/MCPForUnity#main"
                    )
                }
            }
            (project / "Packages" / "manifest.json").write_text(
                json.dumps(manifest, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self.run_checker(project, "--json")

            self.assertEqual(result.returncode, 1)
            report = json.loads(result.stdout)
            self.assertEqual(
                report["checks"][0]["status"],
                "VERSION_MISMATCH",
            )

    def test_approved_project_override_changes_effective_pin(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            lock = json.loads(
                (project / "harness.lock.json").read_text(encoding="utf-8")
            )
            unity_mcp = lock["externalDependencies"]["unityMcp"]
            override_commit = "a" * 40
            override_url = (
                f"{unity_mcp['repository']}.git"
                f"?path=/{unity_mcp['unityPackagePath']}#{override_commit}"
            )
            overrides = {
                "schemaVersion": 1,
                "externalDependencies": {
                    "unityMcp": {
                        "reason": "Project compatibility requires a tested pin",
                        "approvedBy": "Unity team",
                        "approvedAt": "2026-06-11",
                        "values": {
                            "commit": override_commit,
                            "install": {
                                "unityPackageUrl": override_url,
                            },
                        },
                    }
                },
            }
            (project / "harness.overrides.json").write_text(
                json.dumps(overrides, indent=2) + "\n",
                encoding="utf-8",
            )
            manifest = {
                "dependencies": {
                    unity_mcp["packageName"]: override_url,
                }
            }
            (project / "Packages" / "manifest.json").write_text(
                json.dumps(manifest, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self.run_checker(project, "--json")

            self.assertEqual(result.returncode, 1)
            report = json.loads(result.stdout)
            self.assertEqual(report["checks"][0]["status"], "PASS")
            self.assertEqual(
                report["activeOverrides"][0]["dependency"],
                "unityMcp",
            )
            self.assertEqual(
                report["activeOverrides"][0]["approvedBy"],
                "Unity team",
            )

    def test_override_requires_approval_metadata(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            overrides = {
                "schemaVersion": 1,
                "externalDependencies": {
                    "unityMcp": {
                        "values": {"minimumUnity": "2022.3"},
                    }
                },
            }
            (project / "harness.overrides.json").write_text(
                json.dumps(overrides, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self.run_checker(project, "--json")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unityMcp.reason is required", result.stderr)

    def test_override_rejects_unknown_metadata_fields(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            overrides = {
                "schemaVersion": 1,
                "externalDependencies": {
                    "unityMcp": {
                        "reason": "test",
                        "approvedBy": "team",
                        "approvedAt": "2026-06-11",
                        "value": {"minimumUnity": "2022.3"},
                        "values": {"minimumUnity": "2022.3"},
                    }
                },
            }
            (project / "harness.overrides.json").write_text(
                json.dumps(overrides, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self.run_checker(project, "--json")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "unknown fields for unityMcp: value",
                result.stderr,
            )

    def test_override_rejects_unknown_fields(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            overrides = {
                "schemaVersion": 1,
                "externalDependencies": {
                    "unityMcp": {
                        "reason": "test",
                        "approvedBy": "team",
                        "approvedAt": "2026-06-11",
                        "values": {"typoField": "value"},
                    }
                },
            }
            (project / "harness.overrides.json").write_text(
                json.dumps(overrides, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self.run_checker(project, "--json")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown field unityMcp.typoField", result.stderr)

    def test_override_rejects_inconsistent_effective_pin(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.create_project(Path(temporary_directory))
            overrides = {
                "schemaVersion": 1,
                "externalDependencies": {
                    "unityMcp": {
                        "reason": "test",
                        "approvedBy": "team",
                        "approvedAt": "2026-06-11",
                        "values": {"commit": "a" * 40},
                    }
                },
            }
            (project / "harness.overrides.json").write_text(
                json.dumps(overrides, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self.run_checker(project, "--json")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "unityMcp.install.unityPackageUrl must pin the effective commit",
                result.stderr,
            )

    def test_user_level_skill_installation_is_detected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            project = self.create_project(temporary)
            codex_home = temporary / "codex-home"
            user_home = temporary / "user-home"
            checkout = codex_home / "external/agent-sprite-forge"
            checkout.mkdir(parents=True)
            subprocess.run(
                ["git", "init", "--quiet", str(checkout)],
                check=True,
            )
            (checkout / "README.md").write_text(
                "fixture\n",
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "-C", str(checkout), "add", "README.md"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(checkout),
                    "-c",
                    "user.name=Unity Harness Test",
                    "-c",
                    "user.email=unity-harness@example.invalid",
                    "commit",
                    "--quiet",
                    "-m",
                    "fixture",
                ],
                check=True,
            )
            commit = subprocess.run(
                ["git", "-C", str(checkout), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            lock_path = project / "harness.lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            sprite = lock["externalDependencies"]["agentSpriteForge"]
            sprite["commit"] = commit
            sprite["ref"] = commit
            lock_path.write_text(
                json.dumps(lock, indent=2) + "\n",
                encoding="utf-8",
            )
            for name in sprite["install"]["skillNames"]:
                skill = user_home / ".agents" / "skills" / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(
                    f"# {name}\n",
                    encoding="utf-8",
                )
            self.install_pinned_unity_mcp_reference(project)
            env = os.environ.copy()
            env["CODEX_HOME"] = str(codex_home)
            env["HOME"] = str(user_home)

            result = self.run_checker(project, "--json", env=env)

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
