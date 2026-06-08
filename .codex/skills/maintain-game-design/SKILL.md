---
name: maintain-game-design
description: Convert human requests, gameplay feedback, and review findings into traceable Unity game-design updates. Use when creating or revising design item IDs, acceptance criteria, verification methods, assumptions, approval gates, or the canonical game design sheet before implementation.
---

# Maintain Game Design

## Canonical documents

Read these files before editing:

1. `docs/unity_harness_engineering.md`
2. `docs/unity_design_sheet.md`
3. `docs/mcp_and_skills_list.md`
4. Repository-level Codex instructions and any notes linked from the affected design section

Treat the game design sheet as the source of truth. Do not silently change gameplay specifications to simplify implementation.

## Workflow

1. Restate the requested outcome and expected player experience.
2. Locate related design items, acceptance criteria, implementation notes, and known review findings.
3. Classify each input as:
   - **確定仕様**: already stated or explicitly approved
   - **実装上の決定**: may be chosen without changing player-facing behavior
   - **仮定**: temporary premise needed to continue
   - **要確認**: requires human judgment or approval
4. Identify contradictions, missing decisions, affected systems, save compatibility, and regression risks.
5. Update the smallest coherent design section.
6. Add or revise design item IDs and acceptance criteria.
7. Separate changes that require approval from changes safe to implement immediately.
8. Report the edited sections, unresolved questions, and the next implementable unit.

## Traceability rules

- Use `<DOMAIN>-<NNN>` for design items.
- Use only domains defined in the design sheet unless no existing domain fits.
- Never change or reuse an issued ID. Mark retired items as `廃止`.
- Split independent behaviors into separate design items.
- Use `<DesignId>-AC<NN>` for acceptance criteria.
- Never renumber or reuse issued AC IDs. Mark obsolete criteria as `廃止`.
- Do not add IDs to explanatory text or examples that do not require implementation or verification.

Use this design-item form:

```markdown
### MECH-001: 行動として判定できる短い名称

**仕様**

プレイヤーから観察できる振る舞い、判断、または制約を書く。

#### 受け入れ条件

| AC ID | 状態 | 検証種別 | 合格条件 | 検証方法 |
|---|---|---|---|---|
| `MECH-001-AC01` | `有効` | `AUTO:EDIT` | 一つの観察可能な結果 | 実行するテストまたは検査 |
| `MECH-001-AC02` | `有効` | `MANUAL:PLAY` | 人間が判断する体験 | Scene、操作、観点 |
```

Use only these verification types: `AUTO:STATIC`, `AUTO:EDIT`, `AUTO:PLAY`, `AUTO:ASSET`, `AUTO:BUILD`, `MANUAL:EDITOR`, `MANUAL:PLAY`.

## Acceptance-criterion quality

- Express one observable result per row.
- Include concrete input, action, value, and result where possible.
- Make pass/fail binary; avoid words such as 「正常」「適切」「いい感じ」.
- Describe externally observable behavior unless structure itself is the requirement.
- Keep execution results out of the design sheet. Record `PASS`, `FAIL`, `BLOCKED`, or `NOT RUN` in validation reports instead.
- Assign subjective judgments to `MANUAL:PLAY` and specify the scene, play path, and review lens.

## Review-to-design conversion

Convert gameplay feedback into:

```text
観察された事実:
期待する体験:
現在の問題:
変更候補:
影響する設計項目:
影響する実装:
検証方法:
人間の判断が必要な点:
```

Do not turn feedback directly into code when it changes rules, player experience, balance policy, content meaning, or acceptance criteria. Update and approve the design first.

## Approval boundary

Require human approval for:

- concept or core-mechanic changes
- major player-experience changes
- deletion of existing specifications
- save-data incompatibility
- major architecture, technology, package, render-pipeline, or platform decisions
- balance changes without an approved metric or rule
- baseline approval or replacement

When approval is pending, preserve useful analysis and draft wording, but label it `要確認` rather than presenting it as settled.
