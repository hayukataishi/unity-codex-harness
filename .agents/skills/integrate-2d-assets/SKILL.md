---
name: integrate-2d-assets
description: Integrate generated or supplied 2D art into a Unity project using the approved art profile, naming and placement rules, TextureImporter settings, sprite slicing, pivots, PPU, animation clips, animator controllers, prefabs, atlases, and scene or ScriptableObject connections. Use when moving agent-sprite-forge output or other 2D source assets into Unity.
---

# Integrate 2D Assets

## Integrity gate

Before asset integration in an installed game project, run
`scripts/unity_codex_harness/verify_harness_integrity.py --project-root
"$UNITY_PROJECT_ROOT"`. Stop if it fails. In the harness source repository,
use `python3 scripts/validate_repository.py`.

## Gate the work

1. Read:
   - `docs/unity_harness_capabilities.md`
   - `HREQ-ART-001` in `docs/unity_harness_requirements.md`
   - the selected profile, affected design items, and ACs in
     `docs/unity_design_sheet.md`
   - `docs/unity_harness_engineering.md`
2. Resolve `UNITY_PROJECT_ROOT` and inspect existing 2D asset conventions.
3. Confirm the applicable profile (`Characters`, `Environment`, `Effects`, or `Ui`) is complete and human-approved.
4. Confirm source dimensions, frame layout, intended display size, animation FPS, license, generator, and provenance.

If the profile gate is incomplete, stop before mass generation, final atlas construction, or bulk AnimationClip creation. Produce only the representative samples and comparison evidence needed for human approval.

## Prepare the source asset

- Use agent-sprite-forge for image generation when available and requested; do not duplicate its image-generation workflow in this skill.
- Preserve an original source copy or reproducible generation record outside Unity-imported derivatives.
- Record generator/tool, prompt or source reference, date, license, and manual edits in the project’s approved provenance location.
- Reject secrets, personal data, unclear third-party ownership, and incompatible licenses.
- Verify transparent padding, color mode, dimensions, frame count, ordering, and alpha edges before import.

## Name and place

- Follow the harness requirements' ASCII PascalCase asset naming and any project-specific
  exception recorded in the design sheet.
- Use names such as `PlayerRunSheet`, `PlayerRun`, and `PlayerAnimator`.
- Place custom sprites under `Assets/Game/Art/Sprites/<Feature>` or the approved existing equivalent.
- Place clips under `Assets/Game/Art/Animations/<Feature>`, prefabs under `Assets/Game/Prefabs/...`, and reusable data under `Assets/Game/Data/...`.
- Do not reorganize unrelated existing assets.
- Preserve `.meta` files and GUIDs; move or rename through Unity MCP or Editor APIs.

## Import through Unity

Use Unity MCP or Editor APIs and apply the approved profile exactly:

- Texture Type / Sprite Mode
- frame size and slice order
- Pixels Per Unit
- Pivot and border
- Filter Mode
- Compression and platform overrides
- Mipmap and Wrap Mode
- Mesh Type
- alpha handling
- Sprite Atlas assignment

Do not invent a PPU, pivot, filter, compression, or FPS value when the profile is blank. Treat per-asset exceptions as `要確認` unless the design explicitly permits them.

For sprite sheets:

1. Verify every cell has the approved dimensions.
2. Apply a consistent pivot to all frames.
3. Name frames deterministically.
4. Confirm no frame is missing, duplicated, reordered, or clipped.
5. Set clip FPS and Loop Time from the approved animation specification.

## Connect gameplay assets

1. Create or update AnimationClips and AnimatorController states only as required.
2. Create or update prefabs without breaking existing serialized references.
3. Connect sprites, clips, materials, prefabs, scenes, or ScriptableObjects through Unity-aware tools.
4. Keep presentation assets separate from domain rules and game-balance data.
5. Save assets and refresh the Asset Database.

## Validate

- Compile and inspect Console.
- Check missing sprites, clips, scripts, materials, and serialized references.
- Compare against the approved sample at the reference camera, resolution, and min/max display scale.
- Check blur, pixel shimmer, transparent seams, atlas bleeding, color shift, pivot drift, frame skips, loop timing, sorting, and memory impact.
- Capture before/after or profile-comparison screenshots under the applicable AC evidence folder.
- Test the actual prefab or scene path, not only the Project preview.
- Use `$validate-unity-change` and then `$report-unity-work`.

Do not approve visual quality, style consistency, or animation feel on behalf of the human reviewer. Prepare evidence and a precise review path.
