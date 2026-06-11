---
name: maintain-game-design
description: Convert human requests, gameplay feedback, and review findings into traceable Unity game-design updates. Use when creating or revising design item IDs, acceptance criteria, verification methods, assumptions, approval gates, or the canonical game design sheet before implementation.
---

# Maintain Game Design

## Integrity gate

Before reading or updating design in an installed game project, run:

```bash
python3 scripts/unity_codex_harness/verify_harness_integrity.py \
  --project-root "$UNITY_PROJECT_ROOT"
```

Stop if it fails. Do not update the manifest or its sidecar to legitimize a
local edit. If the install manifest is missing, require harness installation
or migration first. In the harness source repository, run
`python3 scripts/validate_repository.py` instead.

## Canonical documents

Read these files before editing:

1. `docs/unity_harness_engineering.md`
2. `docs/unity_harness_capabilities.md`
3. `docs/unity_harness_requirements.md`
4. `docs/unity_design_sheet.md`
5. `docs/mcp_and_skills_list.md`
6. Repository-level Codex instructions and any notes linked from the affected design section

Treat the harness requirements as inherited, binding defaults. Treat the game
design sheet as the project-owned source of truth for game-specific
requirements, applicability, and approved exceptions. Do not silently change
either contract to simplify implementation.

## Requirements boundary

- Read `docs/unity_harness_requirements.md` for inherited `HREQ-*`
  requirements, allowed verification types, quality gates, standard choices,
  and examples.
- Read `docs/unity_harness_capabilities.md` only to understand what the
  harness already implements and which capability gaps remain. Do not turn
  capability records into game requirements.
- Write project name, game concept, selected options, design IDs, ACs, and
  approval records only to `docs/unity_design_sheet.md`.
- Maintain the standard-requirement conformance table. Use only `継承`,
  `対象外`, `例外承認`, or `未決定`.
- A game-specific requirement may add detail or become stricter. It may weaken
  an inherited HREQ only through `例外承認` with reason, impact, mitigation,
  approver, and date.
- Never fill blanks or edit examples in the requirements document as a way to
  record a game decision.
- Never copy harness `HCAP-*`, `DEBUG-*`, or harness regression results into
  the game design sheet.
- Change the requirements document only when the user explicitly asks to
  improve the reusable harness contract. Report that as a harness change, not
  a game-design change.
- If an older installation still has rules and game decisions mixed in the
  sheet, preserve it and use the installer migration bundle or a reviewed
  manual migration. Do not delete project decisions while separating them.

## Workflow

1. Restate the requested outcome and expected player experience.
2. Locate related design items, acceptance criteria, implementation notes, and known review findings.
3. Classify each input as:
   - **確定仕様**: already stated or explicitly approved
   - **実装上の決定**: may be chosen without changing player-facing behavior
   - **仮定**: temporary premise needed to continue
   - **要確認**: requires human judgment or approval
4. Identify contradictions, missing decisions, affected systems, save compatibility, and regression risks.
5. Identify every affected `HREQ-*` standard requirement and check its row in
   the standard-requirement conformance table.
6. Run `validate_design_contract.py` for structure and require each HREQ that
   must be resolved before the requested work.
7. Check the cross-cutting adoption matrix for affected services, data, online,
   monetization, accessibility, localization, performance, diagnostics, UGC,
   and XR concerns.
8. Check the active `Small`, `Standard`, or `Large` architecture profile,
   its recorded reason, and migration triggers. Do not infer `Standard` as the
   default or add future-scale abstractions without an observed need.
9. For saved fields, stable IDs, account state, or cloud synchronization, check
   `HREQ-SAVE-001`, supported schemas, fixtures, recovery, downgrade, and conflict
   rules before approving a change.
10. For large assets, scenes, prefabs, project settings, or repository policy,
   check `HREQ-REPO-001`, LFS criteria, serialization, merge, ownership, and
   history-migration decisions.
11. Update the smallest coherent project-owned section in
   `docs/unity_design_sheet.md`.
12. Add or revise game-specific design item IDs and acceptance criteria.
13. Separate changes that require approval from changes safe to implement immediately.
14. Report the affected HREQ IDs, edited sections, unresolved questions, and the next implementable unit.

## Architecture profile gate

- Use the smallest profile that satisfies current team, lifetime, dependency,
  platform, reuse, and ownership constraints.
- Treat asmdef splits, feature packages, DI containers, long-lived managers,
  singletons, and event channels as explicit decisions rather than profile
  decorations.
- Do not recommend Service Locator as a medium-scale pattern. When inherited
  code uses one, record its boundary, replacement plan, and regression tests.
- Reevaluate the profile only when migration triggers are observed. Record the
  dependency, public API, serialized-reference, package, test, and build impact
  before requesting approval for a profile change.

## Cross-cutting adoption gate

- Every matrix row uses `採用`, `不採用`, or `保留`; never infer an empty row
  as not applicable.
- `採用` requires scope, dependency or `なし（自作）`, data and regulatory
  considerations, and linked design and acceptance-criterion IDs.
- `不採用` requires a reason and reevaluation trigger.
- `保留` requires a reason, decision owner, and deadline or milestone. Do not
  approve dependent implementation while it remains pending.
- Require human approval for privacy, consent, accounts, online services,
  analytics, monetization, ads, UGC, moderation, and target-region decisions.
- Do not present legal, store-policy, child-safety, or security assumptions as
  settled facts. Record them as `要確認` and identify the needed reviewer.

## Save compatibility gate

- Separate serialization format, storage, atomic commit, backup, integrity,
  confidentiality, and tamper detection instead of treating them as one choice.
- Require a supported-oldest schema, sequential `N -> N+1` migrations,
  pre-migration backup, rollback, and non-destructive future-schema behavior.
- Require anonymous fixtures for every supported schema and for corruption,
  interrupted writes, storage failures, and cloud conflicts when adopted.
- Link Cloud Save to Account, Privacy, and Security adoption decisions. Record
  unresolved platform, key-management, retention, and conflict rules as
  `要確認`.

## Repository and asset gate

- Choose branch strategy from team size, CI speed, release support, and actual
  integration needs. Do not prescribe `main / develop / feature/*`.
- Choose LFS by path, measured size, churn, mergeability, hosting quota, and
  CI availability. An extension such as `.png` is not sufficient by itself.
- Require `Visible Meta Files` for Git Unity projects. Record whether `Force
  Text`, UnityYAMLMerge, LFS locks, and asset ownership are adopted.
- Treat history rewrites, serialization migrations, and existing LFS-pattern
  changes as approval-required migrations with rollback and team resync plans.

## Traceability rules

- Use `<DOMAIN>-<NNN>` for design items.
- Use only domains defined in the harness requirements unless no existing domain fits.
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
