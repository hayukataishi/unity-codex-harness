---
name: report-unity-work
description: Produce a concise human-reviewable report of Unity design and implementation work, including design IDs, changed files and assets, acceptance-criterion results, validation evidence, manual Editor or play checks, assumptions, rollback notes, and remaining risks. Use at the end of Unity design, implementation, validation, or gameplay-review tasks.
---

# Report Unity Work

## Collect facts

Before writing:

1. Read the relevant design items and active ACs.
2. Inspect the actual diff and Unity asset changes.
3. Read test XML, Console logs, screenshots, videos, build logs, and `RunManifest.json`.
4. Confirm that the run is `COMPLETED` and passes `verify_validation_run.py`; do not cite a `RUNNING` or integrity-failed run as accepted evidence.
5. Distinguish executed evidence from inference.
6. List manual criteria that still require human judgment.
7. Check for high-impact operations, rollback considerations, temporary assumptions, and unrelated changes.

Do not state that a test, build, scene, or play path passed unless it ran and has evidence. Use project-relative paths such as `Artifacts/ValidationRuns/<RunId>/...`; omit machine-specific absolute paths from shared reports.

## Required report

```markdown
## 実施内容

- 目的と変更範囲
- 対象設計ID・AC ID

## 更新した設計

- 更新箇所、確定事項、要確認事項
- 変更なしの場合は「変更なし」と理由

## 更新した実装

- コード、Scene、Prefab、ScriptableObject、設定、テスト
- 重要な設計判断と依存関係

## 実行した検証と結果

| AC ID | 結果 | 証拠・備考 |
|---|---|---|

- コンパイル、EditMode、PlayMode、アセット検査、ビルドの実行範囲
- 未実行項目と理由

## 検証成果物

- `Artifacts/ValidationRuns/<RunId>/...`

## Unity Editorで確認してほしいこと

- Scene、操作手順、期待結果、見るべき感覚・表示

## 設計との整合性

- 設計、実装、テストの対応
- 意図的な差異または差異なし

## 残課題・仮定・リスク

- `仮定`、`要確認`、回帰リスク、ロールバック方法
```

## Reporting rules

- Prefer exact filenames, asset names, test names, design IDs, and AC IDs.
- Report the Validation Run state, final result, Run ID, and integrity-verification result.
- For harness changes, report the Python test count, affected regression-test files, and whether the Unity fixture ran.
- For cross-cutting changes, report the matrix row, adoption state, linked
  design and AC IDs, dependencies or services, data handling, required human
  approval, and reevaluation trigger.
- For architecture work, report the selected profile, selection reason,
  affected assembly or package boundaries, dependency direction, migration trigger,
  approval state, and whether the change is incremental.
- For save work, report current and supported-oldest schema, changed fields,
  migration and downgrade behavior, atomic-write and backup results, fixture
  coverage, recovery results, platform scope, Cloud conflict policy, and
  whether evidence was checked for personal data or secrets.
- For repository and large-asset work, report branch and merge policy, affected
  LFS paths and size rule, `.meta` pairing, serialization mode, merge driver,
  asset owner or lock, LFS verification, and any history-migration impact.
- For build work, report the exact Build Profile asset path, output path, clean or incremental mode, and target platform.
- For Cinemachine work, report the exact Package version, major-version API used, affected cameras and procedural components, and whether a 2.x migration was performed.
- Summarize large diffs; do not paste generated logs.
- Separate warnings from blockers.
- Label subjective criteria as human review, not automated success.
- State `実装完了候補・人間レビュー待ち` when only manual criteria remain.
- State that acceptance is incomplete when any active AC is `FAIL`, `BLOCKED`, or `NOT RUN`.
- Mention package, platform, build, serialized data, GUID, or baseline changes prominently.
- Report no-op investigations honestly when no files changed.
