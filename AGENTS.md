# Unity Codex Harness Instructions

## Required context

Before Unity design, implementation, validation, or gameplay-review work, read:

1. `docs/unity_harness_engineering.md`
2. `docs/unity_design_sheet.md`
3. `docs/mcp_and_skills_list.md`
4. The applicable Skill under `.codex/skills/`

## Working contract

- Treat `docs/unity_design_sheet.md` as the source of truth for player-facing behavior.
- Resolve the Unity project root by verifying `Assets/`, `Packages/`, and `ProjectSettings/ProjectVersion.txt`; never persist a machine-specific absolute path.
- Update or obtain approval for affected design items and acceptance criteria before changing approved behavior.
- Prefer Unity MCP or Unity Editor APIs for scenes, prefabs, assets, import settings, tags, layers, and serialized references.
- Preserve `.meta` files and GUIDs. Do not directly edit Unity YAML unless no safer supported operation exists.
- Keep changes small, inspect the diff, and avoid unrelated refactors or asset moves.
- Store validation evidence under `Artifacts/ValidationRuns/<RunId>/` and keep `Artifacts/` out of Git.
- Never claim acceptance while an active acceptance criterion is `FAIL`, `BLOCKED`, or `NOT RUN`.
- Leave subjective judgments such as fun, feel, clarity, and acceptable difficulty to a human reviewer.

## Preferred workflow

1. Use `$maintain-game-design` when requirements or acceptance criteria need changes.
2. Use `$implement-unity-feature` for approved implementation work.
3. Use `$integrate-2d-assets` for generated or supplied 2D art.
4. Use `$validate-unity-change` after code, asset, scene, prefab, or settings changes.
5. Use `$review-gameplay` for player-facing observation and evidence collection.
6. Use `$report-unity-work` for the final human-reviewable report.
