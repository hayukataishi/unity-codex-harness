from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "UnityValidationFixture"


class UnityFixtureContractTests(unittest.TestCase):
    def load_json(self, relative_path: str):
        return json.loads(
            (FIXTURE / relative_path).read_text(encoding="utf-8")
        )

    def test_required_saved_assets_have_meta_files(self):
        required_files = (
            "Assets/Game/Prefabs/CounterFixture.prefab",
            "Assets/Game/Scenes/FixtureScene.unity",
            "Assets/Game/Scripts/Editor/FixtureProjectContract.cs",
            (
                "Assets/Game/Scripts/Editor/"
                "UnityCodexHarness.Fixture.Editor.asmdef"
            ),
            (
                "Assets/Game/Tests/EditMode/"
                "FixtureProjectContractTests.cs"
            ),
            (
                "Assets/Settings/BuildProfiles/"
                "FixtureDevelopment.asset"
            ),
        )

        for relative_path in required_files:
            path = FIXTURE / relative_path
            self.assertTrue(path.is_file(), relative_path)
            self.assertTrue(
                Path(f"{path}.meta").is_file(),
                f"{relative_path}.meta",
            )

    def test_assembly_boundaries_are_explicit(self):
        expected = {
            (
                "Assets/Game/Scripts/Runtime/"
                "UnityCodexHarness.Fixture.Runtime.asmdef"
            ): ("UnityCodexHarness.Fixture.Runtime", []),
            (
                "Assets/Game/Scripts/Editor/"
                "UnityCodexHarness.Fixture.Editor.asmdef"
            ): (
                "UnityCodexHarness.Fixture.Editor",
                ["Editor"],
            ),
            (
                "Assets/Game/Tests/EditMode/"
                "UnityCodexHarness.Fixture.Tests.EditMode.asmdef"
            ): (
                "UnityCodexHarness.Fixture.Tests.EditMode",
                ["Editor"],
            ),
            (
                "Assets/Game/Tests/PlayMode/"
                "UnityCodexHarness.Fixture.Tests.PlayMode.asmdef"
            ): (
                "UnityCodexHarness.Fixture.Tests.PlayMode",
                [],
            ),
        }

        for relative_path, (name, platforms) in expected.items():
            assembly = self.load_json(relative_path)
            self.assertEqual(assembly["name"], name)
            self.assertEqual(assembly["includePlatforms"], platforms)

        manifest = self.load_json("Packages/manifest.json")
        self.assertEqual(
            manifest["dependencies"]["com.unity.test-framework"],
            "1.6.0",
        )
        project_version = (
            FIXTURE / "ProjectSettings" / "ProjectVersion.txt"
        ).read_text(encoding="utf-8")
        self.assertIn("6000.4.10f1", project_version)

    def test_asset_validation_config_covers_saved_assets(self):
        config = self.load_json(
            "ProjectSettings/UnityCodexHarnessAssetValidation.json"
        )
        required_assets = {
            rule["path"] for rule in config["requiredAssets"]
        }
        self.assertTrue(
            {
                "Assets/Game/Prefabs/CounterFixture.prefab",
                "Assets/Game/Scenes/FixtureScene.unity",
                (
                    "Assets/Settings/BuildProfiles/"
                    "FixtureDevelopment.asset"
                ),
            }.issubset(required_assets)
        )

        self.assertIn(
            {
                "assetPath": "Assets/Game/Prefabs/CounterFixture.prefab",
                "objectPath": "CounterFixture",
                "componentType": (
                    "UnityCodexHarness.Fixture.CounterBehaviour"
                ),
                "propertyPath": "target",
            },
            config["requiredReferences"],
        )

    def test_fixture_is_documented_and_connected_to_ci(self):
        fixture_readme = (FIXTURE / "README.md").read_text(encoding="utf-8")
        workflow = (
            ROOT / ".github" / "workflows" / "validate-harness.yml"
        ).read_text(encoding="utf-8")
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("DEBUG-003", fixture_readme)
        self.assertIn("DEBUG-003-AC04", root_readme)
        self.assertIn(
            "tests/fixtures/UnityValidationFixture",
            workflow,
        )
