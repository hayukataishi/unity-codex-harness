---
name: validate-unity-change
description: Validate Unity changes against design IDs and acceptance criteria using project preflight checks, compilation, Console inspection, EditMode and PlayMode tests, asset-reference inspection, screenshots, and optional build verification. Use after Unity code or asset changes, before claiming completion, or when diagnosing a suspected regression.
---

# Validate Unity Change

## Establish the validation scope

1. Read the active design item and AC rows in `docs/unity_design_sheet.md`.
2. Read validation, artifact, and Definition of Done rules in `docs/unity_harness_engineering.md`.
3. Resolve `UNITY_PROJECT_ROOT`; verify the Unity project markers instead of guessing.
4. List changed code, scenes, prefabs, ScriptableObjects, settings, packages, tags, layers, and build configuration.
5. Build an AC matrix before testing:

```markdown
| AC ID | Verification type | Planned check | Evidence target |
|---|---|---|---|
```

## Create a new evidence run

Run:

```bash
python3 .codex/skills/validate-unity-change/scripts/create_validation_run.py \
  --project-root "$UNITY_PROJECT_ROOT" \
  --design-id MECH-001 \
  --ac-id MECH-001-AC01
```

Use the printed directory for this execution. Never reuse or overwrite an earlier run. Store evidence under:

```text
Artifacts/ValidationRuns/<RunId>/
```

Keep paths in reports relative to `UNITY_PROJECT_ROOT`.

## Execute checks

Run only applicable checks, but explicitly mark omitted checks.

1. **Static preflight**
   ```bash
   python3 .codex/skills/validate-unity-change/scripts/preflight_unity_project.py \
     --project-root "$UNITY_PROJECT_ROOT" \
     --output "Artifacts/ValidationRuns/<RunId>/Logs/Preflight.json"
   ```
2. **Compile**
   - Trigger asset refresh and script compilation through Unity MCP or the approved batch command.
   - Wait for compilation and domain reload to finish.
   - Save searchable Editor and Console logs.
3. **EditMode**
   - Run affected tests first, then the broader relevant suite.
   - Save NUnit-compatible XML to `Tests/EditMode.xml`.
4. **PlayMode**
   - Run integration, scene, input, and time-dependent tests.
   - Save NUnit-compatible XML to `Tests/PlayMode.xml`.
5. **Asset validation**
   - Check Missing Script and Missing Reference.
   - Inspect required scene, prefab, ScriptableObject, tag, layer, input, and build-scene references.
   - Reopen or reload changed assets when needed to catch serialization issues.
6. **Build verification**
   - Run when required by an `AUTO:BUILD` AC or when platform/build settings changed.
   - Use the approved target and existing release settings. Do not switch targets or publish without approval.
7. **Visual evidence**
   - Capture screenshots, videos, and profiler data for relevant ACs.
   - Store AC-specific evidence under `Evidence/<AcceptanceCriterionIdWithoutHyphens>/`.

Prefer Unity MCP for Editor operations and evidence capture. Re-check Editor state, Console, hierarchy, inspector-equivalent data, and saved asset state after MCP changes.

## Classify results

Use only:

- `PASS`: the criterion ran and evidence proves the expected result
- `FAIL`: the criterion ran and contradicted the expected result
- `BLOCKED`: the criterion could not run because of a stated blocker
- `NOT RUN`: the criterion was not executed

Do not infer `PASS` from code inspection when the criterion requires execution. Do not assign subjective manual criteria a passing result on behalf of the human reviewer.

Record:

```markdown
| AC ID | Result | Evidence / notes |
|---|---|---|
| `MECH-001-AC01` | `PASS` | `Tests/EditMode.xml`; test name |
| `MECH-001-AC02` | `NOT RUN` | Human gameplay review required |
```

## Definition of Done

Confirm all applicable items:

- approved design exists
- implementation maps to active ACs
- compilation succeeds
- relevant automated tests pass
- no Missing Script or Missing Reference remains
- changed assets are saved and reload cleanly
- applicable build verification succeeds
- evidence and commands are recorded in a new run
- manual review steps are explicit
- unresolved assumptions and risks are explicit
- design, implementation, names, and tests remain consistent

If any active AC is `FAIL`, `BLOCKED`, or `NOT RUN`, do not call the change accepted. If only `MANUAL:*` criteria remain, hand it off as an implementation candidate awaiting human review.

## Scripts

- `scripts/create_validation_run.py`: create the immutable run directory and initial manifest/report.
- `scripts/preflight_unity_project.py`: check required Unity project structure, `.meta` integrity, duplicate GUIDs, and serialized Missing Script markers.
- `scripts/run_unity_validation.py`: resolve the matching Unity Editor, run preflight, EditMode, and PlayMode checks, and finalize one evidence run.
- `scripts/finalize_validation_run.py`: calculate the final result, write the report, and record artifact hashes.

Run the complete local path with automated AC IDs only:

```bash
python3 .codex/skills/validate-unity-change/scripts/run_unity_validation.py \
  --project-root "$UNITY_PROJECT_ROOT" \
  --design-id MECH-001 \
  --ac-id MECH-001-AC01
```

On macOS, the runner resolves the Unity Hub Editor matching
`ProjectSettings/ProjectVersion.txt`. On other platforms, or for a custom
installation, pass `--unity-editor` or set `UNITY_EDITOR_PATH`.
