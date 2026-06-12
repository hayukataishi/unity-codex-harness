# Unity Codex Harness Instructions

<!-- UNITY_CODEX_HARNESS_AGENT_CONTRACT: REQUIRED -->

Before Unity work, read and follow
`docs/unity_harness_agent_contract.md`.

## Required context

Before Unity design, implementation, validation, or gameplay-review work, read:

1. `docs/unity_harness_engineering.md`
2. `docs/unity_harness_capabilities.md`
3. `docs/unity_harness_requirements.md`
4. `docs/unity_design_sheet.md`
5. `docs/mcp_and_skills_list.md`
6. The applicable Skill under `.agents/skills/`

## Working contract

- Before Unity design, implementation, validation, asset integration,
  gameplay review, or reporting in an installed game project, run
  `python3 scripts/unity_codex_harness/verify_harness_integrity.py
  --project-root .`. Stop if it fails.
- If `.unity-codex-harness/install-manifest.json` is missing from a game
  project that claims to use the harness, stop and reinstall or migrate the
  harness. In the harness source repository itself, use
  `python3 scripts/validate_repository.py` instead.
- Treat `docs/unity_harness_capabilities.md` as the `harness-managed`
  inventory of implemented harness capabilities. Do not record game decisions
  there.
- Treat `docs/unity_harness_requirements.md` as the inherited, binding
  mandatory standards and dialogue-driven recommended requirements.
- Treat `docs/unity_design_sheet.md` as the `project-owned` source of truth for
  game-specific requirements, HREQ applicability, and approved exceptions.
- A game-specific requirement may not silently weaken an HREQ. Require an
  `例外承認` record with reason, impact, mitigation, approver, and date.
- Before implementation or acceptance, run
  `scripts/unity_codex_harness/validate_design_contract.py` for affected HREQs.
- Before claiming a Concept, Prototype, Vertical Slice, Alpha, Beta, or Release
  design complete, run `scripts/unity_codex_harness/validate_design_readiness.py`
  for that milestone and require `PASS`.
- During ordinary game work, update only `docs/unity_design_sheet.md`. Change
  the standard requirements only for an explicitly requested harness change.
- Resolve the Unity project root by verifying `Assets/`, `Packages/`, and `ProjectSettings/ProjectVersion.txt`; never persist a machine-specific absolute path.
- Update or obtain approval for affected design items and acceptance criteria before changing approved behavior.
- Prefer Unity MCP or Unity Editor APIs for scenes, prefabs, assets, import settings, tags, layers, and serialized references.
- Preserve `.meta` files and GUIDs. Do not directly edit Unity YAML unless no safer supported operation exists.
- Keep changes small, inspect the diff, and avoid unrelated refactors or asset moves.
- Store validation evidence under `Artifacts/ValidationRuns/<RunId>/` and keep `Artifacts/` out of Git.
- Never claim acceptance while an active acceptance criterion is `FAIL`, `BLOCKED`, or `NOT RUN`.
- Leave subjective judgments such as fun, feel, clarity, and acceptable difficulty to a human reviewer.

## Preferred workflow

1. Use `$bootstrap-game-design` for a new game or incomplete initial design.
2. Use `$maintain-game-design` for later requirement and AC changes.
3. Use `$implement-unity-feature` for approved implementation work.
4. Use `$integrate-2d-assets` for generated or supplied 2D art.
5. Use `$validate-unity-change` after code, asset, scene, prefab, or settings changes.
6. Use `$review-gameplay` for player-facing observation and evidence collection.
7. Use `$report-unity-work` for the final human-reviewable report.

## Initial-design orchestration

- Keep standard-recommended `HREQ-*` decisions and game-specific design in one
  traceable conversation, but label every question as `[標準推奨]`,
  `[ゲーム個別]`, or `[両方]`.
- The main agent is the only user-facing interviewer and design-sheet writer.
- When the user explicitly authorizes subagents, spawn the project custom agent
  `game_design_auditor` after each initial-design phase and before final
  approval. It is read-only and may report findings only.
- `.agents/skills/*/agents/openai.yaml` is Skill UI and dependency metadata. It
  is not a Subagent definition.
