---
name: implement-unity-feature
description: Implement an approved Unity design item with minimal, architecture-consistent changes to C# code, scenes, prefabs, ScriptableObjects, settings, and tests. Use when a design ID and acceptance criteria are ready for implementation or when extending an existing Unity feature without changing its approved specification.
---

# Implement Unity Feature

## Prepare

1. Read:
   - `docs/unity_harness_engineering.md`
   - `docs/unity_design_sheet.md`
   - `docs/mcp_and_skills_list.md`
   - repository-level instructions
2. Resolve `UNITY_PROJECT_ROOT` from user context or Unity MCP. Verify `Assets/`, `Packages/`, and `ProjectSettings/ProjectVersion.txt`. Never store a machine-specific path in shared files.
3. Read the exact design item and all active AC IDs. If the requested behavior is not approved, use `$maintain-game-design` before implementation.
4. Inspect related code, asmdefs, scenes, prefabs, ScriptableObjects, settings, and tests before editing.
5. Record current Unity version, target platform, package state, active Editor instance, active scene, play/edit state, and compile state.

## Plan the smallest change

- Map each AC ID to an implementation location and verification method.
- Reuse existing project patterns before introducing abstractions.
- Identify serialized-field, GUID, save-data, input, scene-flow, and platform risks.
- Limit one work unit to one clear purpose.
- Add a regression test or explicit check when changing existing behavior.
- Avoid opportunistic renaming, folder migration, cleanup, or unrelated refactoring.

## Implement

### Code and architecture

- Follow the naming, folder, and asmdef rules in the design sheet.
- Place custom assets under `Assets/Game` unless the existing project has an approved structure.
- Keep runtime code independent from `UnityEditor` and test assemblies.
- Preserve layer direction: Presentation → Application → Domain, with Infrastructure serving I/O concerns.
- Prefer pure C# for rules and calculations; keep MonoBehaviours focused on Unity lifecycle and presentation integration.
- Use one public type per C# file and match the filename to the type.
- Do not add packages, change Unity versions, split assemblies beyond the approved minimum, or change architecture without approval.

### Unity assets

- Prefer Unity MCP or Editor APIs for scenes, prefabs, components, ScriptableObjects, import settings, tags, and layers.
- For Unity 6 build work, use saved Build Profile assets under the approved project path. Do not edit Build Profile YAML directly or rely on the Editor's last active profile.
- Inspect an existing asset before modifying it.
- Preserve `.meta` files and GUIDs. Move or rename assets through Unity-aware tools.
- Avoid direct YAML edits to scenes and prefabs unless no supported Editor operation exists and the impact is understood.
- Save dirty scenes and assets intentionally.
- Specify ambiguous objects by full hierarchy path or instance ID, not name alone.

### Tool safety

- Check Editor state and available Unity MCP tool groups at the start; do not assume a fixed beta tool list.
- Use dedicated Unity MCP operations instead of arbitrary C# execution.
- Keep safety checks enabled for arbitrary code.
- Prefer update over overwrite, disable over delete, and reversible operations over destructive ones.
- Stop and request approval before high-impact operations listed in the harness, unless the user explicitly requested them.

## Test while implementing

- Add EditMode tests for pure logic and deterministic data transformations.
- Add PlayMode tests for component integration, scene transitions, input, and time-dependent behavior.
- Add Editor validation for required assets, serialized references, Build Profile scene lists, tags, layers, or naming constraints.
- Name tests so the behavior is searchable, and associate relevant tests or reports with design and AC IDs.

## Finish

1. Refresh assets and compile.
2. Check Console errors and warnings caused by the change.
3. Save modified scenes and assets.
4. Inspect the diff for unrelated changes, broken `.meta` files, generated files, and secrets.
5. Invoke `$validate-unity-change` for the applicable static, EditMode, PlayMode, asset, and build checks.
6. Invoke `$report-unity-work` to summarize implementation, evidence, manual review, assumptions, and risks.

Do not claim completion while any active AC is `FAIL`, `BLOCKED`, or `NOT RUN`. If only manual criteria remain, describe the result as an implementation candidate awaiting human review.
