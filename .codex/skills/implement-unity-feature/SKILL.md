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
4. Check the cross-cutting adoption matrix before work involving packages,
   external services, networking, accounts, collected data, analytics,
   monetization, ads, UGC, moderation, accessibility, localization,
   performance budgets, diagnostics, or XR. Stop if the affected row is
   `保留` or contradicts the requested implementation.
5. Read the selected architecture profile and its reason. If it is empty, keep
   the existing architecture for a narrow change and use
   `$maintain-game-design` before introducing new boundaries or global patterns.
6. Before changing saved fields, stable IDs, storage, schema, or cloud state,
   read `SAVE-001`, supported-version fixtures, migration, recovery, downgrade,
   platform, privacy, and conflict rules.
7. Before adding or changing large assets, scenes, prefabs, project settings,
   Git attributes, or LFS tracking, read `PROJECT-002` and inspect repository
   size rules, serialization mode, merge driver, ownership, and locks.
8. Inspect related code, asmdefs, scenes, prefabs, ScriptableObjects, settings, and tests before editing.
9. Record current Unity version, target platform, package state, active Editor instance, active scene, play/edit state, and compile state.

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
- Follow the selected `Small`, `Standard`, or `Large` profile. Do not create
  four layers or four assemblies merely because the template documents them.
- In `Small`, prefer direct ownership, serialized references, manual
  composition, and local events while dependencies remain clear.
- In `Standard` or `Large`, preserve the approved dependency direction and use
  Pure C# assemblies, feature boundaries, or packages only where the design
  records their value.
- Prefer pure C# for rules and calculations when it reduces Unity lifecycle
  coupling; keep MonoBehaviours focused on Unity integration.
- Do not introduce a DI container, Service Locator, singleton, manager fleet,
  or event bus without an approved problem statement, lifetime, and test plan.
- Use one public type per C# file and match the filename to the type.
- Do not add packages, change Unity versions, change the selected architecture
  profile, or alter approved assembly and dependency boundaries without approval.

### Save data

- Never overwrite a valid primary save in place. Implement the approved temp
  write, flush, validation, atomic replace or platform fallback, and backup flow.
- Keep serialization, integrity, encryption, and key management as separate
  responsibilities. Do not use `PlayerPrefs` as the source of truth for
  progression, entitlement, credentials, or tamper-sensitive values.
- Implement schema changes as tested sequential migrations. Preserve the
  original before migration and never destructively rewrite an unknown future schema.
- Serialize writes to the same slot and handle quit, suspend, cancellation,
  full storage, denied access, and serialization failure without losing the
  last known-good data.
- Do not log or commit real user saves, tokens, keys, account identifiers, or
  personal data. Use anonymous synthetic fixtures.
- Do not change supported-oldest schema, downgrade behavior, cloud conflict
  resolution, backup retention, or key management without approval.

### Unity assets

- Keep each asset and its `.meta` file together. Do not put `.meta` files in
  LFS or regenerate them to resolve a merge conflict.
- Follow the approved LFS path and size policy. Do not LFS-track all files of
  an extension merely because some files of that type are large.
- Coordinate ownership before editing a high-contention scene, prefab,
  ProjectSettings file, or non-mergeable binary. Keep the editing window small.
- Use UnityYAMLMerge only for supported text-serialized Unity YAML. After a
  merge, open the asset in Unity and validate references, overrides, Console,
  and relevant tests.
- Prefer Unity MCP or Editor APIs for scenes, prefabs, components, ScriptableObjects, import settings, tags, and layers.
- For Unity 6 build work, use saved Build Profile assets under the approved project path. Do not edit Build Profile YAML directly or rely on the Editor's last active profile.
- Before Cinemachine work, inspect `Packages/manifest.json` and `packages-lock.json` and record the exact installed major version.
- For Cinemachine 3.x, use the `Unity.Cinemachine` namespace, `CinemachineCamera`, Tracking Target, and standard Position / Rotation Control components on the same GameObject. Do not introduce Cinemachine 2.x component names into new Unity 6 examples.
- Treat a Cinemachine 2.x to 3.x upgrade as an approved migration. Back up first, use the Cinemachine Upgrader, and inspect scripts, scenes, prefabs, Timeline, animation bindings, channels, and serialized references instead of editing Unity YAML or performing a blind rename.
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
- For save changes, add fixtures for every supported schema plus interrupted
  writes, corruption, backup recovery, future schemas, and storage failures.
  Add cloud-conflict and account-switch tests when Cloud Save is adopted.
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
