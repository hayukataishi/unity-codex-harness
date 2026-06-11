---
name: review-gameplay
description: Observe a Unity Play Mode or build play path, collect screenshots, video, Console logs, profiler evidence, and acceptance-criterion observations, and turn findings into structured gameplay-review input. Use when verifying player-facing behavior, preparing a human playtest, investigating feel or clarity issues, or converting gameplay feedback into traceable design work.
---

# Review Gameplay

## Define the review

1. Read the relevant project-owned design items and active ACs in
   `docs/unity_design_sheet.md`, plus applicable inherited `HREQ-*` standards
   in `docs/unity_harness_requirements.md` and evidence capabilities in
   `docs/unity_harness_capabilities.md`.
2. Specify:
   - Unity scene or build
   - starting state and required test data
   - exact input sequence or play path
   - target platform, resolution, and device assumptions
   - criteria that are mechanically observable
   - criteria that require human judgment
3. Resolve `UNITY_PROJECT_ROOT` and inspect Editor state, active scene, compile state, and Console before entering Play Mode.
4. Create a new validation run with `$validate-unity-change`.

If the play path, expected experience, or success criteria are ambiguous, preserve the ambiguity as `要確認`; do not invent a favorable interpretation.

## Execute and capture

- Prefer Unity MCP for Play, Pause, Stop, input-capable testing, screenshots, video, Console, and profiler capture.
- Start from the documented initial state and record deviations.
- Capture evidence at the moment relevant to each AC.
- Store screenshots, video, notes, and profiler output under `Evidence/<AcceptanceCriterionIdWithoutHyphens>/`.
- Save searchable Console text in addition to images.
- Record scene, build, resolution, play path, timing, and input assumptions in evidence notes.
- Stop Play Mode safely and verify the project returned to a clean Editor state.

Do not modify design or implementation while conducting an observation-only review unless the user explicitly expands the task. Preserve reproducibility before attempting fixes.

## Separate machine and human judgment

Codex may determine:

- whether a scene loaded
- whether an event occurred
- whether a UI value changed
- whether an error appeared
- whether timing, count, position, or state matched a defined threshold
- whether an automated test passed

Codex must not independently approve:

- fun
- responsiveness or “game feel”
- satisfying effects
- acceptable difficulty
- UI clarity without an approved measurable rule
- faithfulness to the intended concept as a final subjective judgment

For subjective criteria, prepare a human review step with the exact scene, inputs, duration, expected experience, comparison target, and questions to answer.

## Record each finding

Use:

```text
観察された事実:
期待する体験:
現在の問題:
変更候補:
影響する設計項目:
影響する実装:
検証方法:
人間の判断が必要な点:
証拠:
```

- Keep observation separate from interpretation.
- Describe reproduction steps before proposing a fix.
- Mark AC results as `PASS`, `FAIL`, `BLOCKED`, or `NOT RUN`.
- Never turn a subjective impression into an automated `PASS`.
- Link evidence with project-relative paths.

## Hand off

- Use `$maintain-game-design` when the review implies a specification, acceptance-criterion, balance-policy, or player-experience change.
- Use `$implement-unity-feature` only after the affected design is approved.
- Use `$report-unity-work` to summarize the play path, evidence, AC results, human questions, and risks.
