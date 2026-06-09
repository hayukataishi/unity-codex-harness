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
5. For cross-cutting changes, compare implementation, installed packages,
   service settings, network behavior, collected data, and user-facing flows
   with the adoption matrix. Treat implementation under `不採用` or `保留` as
   a design mismatch, not a passing validation.
6. Compare asmdefs, package boundaries, dependency direction, composition,
   long-lived objects, and messaging with the selected architecture profile.
   Treat an unapproved DI container, Service Locator, manager fleet, event bus,
   or feature package as a design mismatch.
7. Build an AC matrix before testing:

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

The new manifest starts with schema version 2 and `state: RUNNING`. Every
created run must reach `state: COMPLETED`. Prefer `run_unity_validation.py`,
which finalizes and verifies automatically.

## Execute checks

Run only applicable checks, but explicitly mark omitted checks.

When changing the harness itself, run the full repository suite with
`python3 -m unittest discover -s tests -p 'test_*.py' -v`. Installer,
preflight, Validation Run, repository-policy, and workflow changes require both
their focused regression tests and the complete suite. Run the Unity fixture
separately when Unity-facing behavior can be affected.

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
   - Run the installed `UnityCodexHarness.Validation.Editor.AssetValidationBatch.Run`
     entry point through `run_unity_validation.py`.
   - Check Missing Script and unresolved serialized object references in scenes,
     prefabs, and ScriptableObjects.
   - Read required asset and serialized-reference rules from
     `ProjectSettings/UnityCodexHarnessAssetValidation.json`.
   - Inspect tag, layer, input, and Build Profile Scene List references separately when
     applicable; they are not yet covered by the generic asset validator.
   - Reopen or reload changed assets when needed to catch serialization issues.
   - For Cinemachine changes, record the installed Package version. On 3.x, inspect `CinemachineBrain`, `CinemachineCamera`, Tracking Target, optional Look At Target, Position / Rotation Control components, and Channels. After a 2.x migration, also inspect Scene, Prefab, Timeline, Animation, code references, obsolete warnings, and missing serialized references.
   - For architecture changes, inspect asmdef references for cycles and reverse
     dependencies, verify `No Engine References` assemblies do not use Unity
     APIs, and confirm public APIs, composition roots, and tests match the
     approved profile and migration plan.
6. **Build verification**
   - Run when required by an `AUTO:BUILD` AC or when Build Profile or platform settings changed.
   - On Unity 6, record the saved Build Profile asset path and inspect its target, purpose, Scene List, Scripting Defines, Player Settings overrides, and debugging options.
   - Start batch builds with `-activeBuildProfile <Assets/...Profile.asset>`; do not rely on the Editor's last active profile.
   - Use a separate Unity process for each target platform.
   - When a clean build is required in CI, use a custom build method with `BuildOptions.CleanBuildCache`; direct `-build` is incremental after the first build.
   - Use the approved Profile and write output under `Artifacts/ValidationRuns/<RunId>/Builds/<ProfileName>/`.
   - Do not switch targets, change Release settings, sign, upload, or publish without approval.
7. **Visual evidence**
   - Capture screenshots, videos, and profiler data for relevant ACs.
   - Store AC-specific evidence under `Evidence/<AcceptanceCriterionIdWithoutHyphens>/`.

Prefer Unity MCP for Editor operations and evidence capture. Re-check Editor state, Console, hierarchy, inspector-equivalent data, and saved asset state after MCP changes.

## Finalize and verify

For a manually orchestrated run, write a schema version 1 results JSON with
`commands`, `checks`, and optional per-AC `acceptanceCriteria`, then run:

```bash
python3 .codex/skills/validate-unity-change/scripts/finalize_validation_run.py \
  --project-root "$UNITY_PROJECT_ROOT" \
  --run-dir "Artifacts/ValidationRuns/<RunId>" \
  --results "Artifacts/ValidationRuns/<RunId>/Logs/ValidationResults.json"
```

If the run cannot continue, close it honestly instead of leaving it running:

```bash
python3 .codex/skills/validate-unity-change/scripts/finalize_validation_run.py \
  --project-root "$UNITY_PROJECT_ROOT" \
  --run-dir "Artifacts/ValidationRuns/<RunId>" \
  --blocked-reason "Unity Editor license was unavailable"
```

The finalizer returns a non-zero exit code for `FAIL`, `BLOCKED`, and
`NOT RUN`, even though the run itself has been successfully closed. Verify every
completed run:

```bash
python3 .codex/skills/validate-unity-change/scripts/verify_validation_run.py \
  --project-root "$UNITY_PROJECT_ROOT" \
  --run-dir "Artifacts/ValidationRuns/<RunId>"
```

Do not re-finalize or edit a completed run. Create a new run when evidence or
checks must change.

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
- `Assets/UnityCodexHarness/Editor/AssetValidationBatch.cs`: scan Unity assets through Editor APIs and write `Logs/AssetValidation.json`.
- `scripts/finalize_validation_run.py`: calculate the final result, write the report, and record artifact hashes.
- `scripts/verify_validation_run.py`: verify the completed state, manifest sidecar hash, and all recorded artifacts.

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
