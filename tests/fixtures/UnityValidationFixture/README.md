# Unity Validation Fixture

Minimal Unity project used to verify `DEBUG-003` and the harness batch
validation path.

- Unity Editor: `6000.4.10f1`
- Assemblies: Runtime, Editor, EditMode, and PlayMode
- Saved assets: `CounterFixture.prefab`, `FixtureScene.unity`, and
  `FixtureDevelopment.asset`
- EditMode: pure C# behavior, saved asset contract, and dynamically generated
  broken-reference fixtures
- PlayMode: saved Scene loading and `MonoBehaviour` integration
- Asset validation: required assets, required Prefab reference, Missing
  Reference, and missing required reference detection

Generated directories such as `Library`, `Logs`, `Temp`, `Artifacts`, and
`UserSettings` are not version controlled. This fixture is not copied into
game projects by `scripts/install.py`.

Optional Editor review:

1. Open `Assets/Game/Scenes/FixtureScene.unity`.
2. Select `CounterFixture` and confirm it is a Prefab instance.
3. Confirm `CounterBehaviour.target` points to the child `Target`.
4. Open `Assets/Settings/BuildProfiles/FixtureDevelopment.asset` and confirm
   the Scene List override and `UNITY_CODEX_FIXTURE` scripting define.
