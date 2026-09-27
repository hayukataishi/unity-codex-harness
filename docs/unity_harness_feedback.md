# Harness feedback の記録と取り込み

導入先で見つけた Harness の不具合、手順の分かりにくさ、改善案を記録し、
Harness 側から明示したプロジェクトまたは JSON bundle を取り込みます。
通信、Git 操作、Issue 作成、改善の自動実装は行いません。
ゲームの仕様・面白さに関するレビューは従来どおり `docs/game_design/` へ記録します。

## 受け入れ条件

設計ID: `HCAP-FEEDBACK-001`。ゲームの HREQ・AC を変更する機能ではありません。

| AC ID | 合格条件 | 検証 |
|---|---|---|
| `HCAP-FEEDBACK-001-AC01` | 導入先で複数の feedback を蓄積でき、導入版と永続IDを保持する | Python CLI 回帰 |
| `HCAP-FEEDBACK-001-AC02` | 複数プロジェクト・bundle から取り込め、同じID・内容の再実行はスキップする | 移動・複製・再取り込み回帰 |
| `HCAP-FEEDBACK-001-AC03` | 同じIDの内容変更、不正データ、取り込み済み記録の破損を上書きせず拒否する | 異常系回帰 |
| `HCAP-FEEDBACK-001-AC04` | dry-run と取り込みは元データを変更せず、中断後の再実行で重複しない | 無変更・書込み失敗回帰 |
| `HCAP-FEEDBACK-001-AC05` | Installer 更新で蓄積データを保護し、取り込みデータを導入先や release ZIP へ配布しない | Installer・release 回帰 |

## 導入先で記録する

更新済み Harness の `$manage-harness-feedback` に「この問題を Harness の
feedback として記録して」と依頼できます。CLI では次のように実行します。

```bash
python3 scripts/unity_codex_harness/harness_feedback.py record \
  --project-root . --category bug --title '検証手順が分かりにくい' \
  --body-file feedback-note.md
python3 scripts/unity_codex_harness/harness_feedback.py list --project-root .
```

`--body` に本文を直接渡すこともできます。分類は `bug`、`improvement`、
`documentation`、`workflow`。本文には観察事実、再現手順、期待と実際、影響、
改善案を必要な範囲で書き、推測は区別します。関連する HREQ、Skill、相対パス、
Validation Run ID は本文へ記録します。秘密情報や未加工ログを含めないでください。
参照先のファイルは自動収集・添付されません。

初回だけ `--project-name '共有用の名前'` で表示名を指定できます。
省略時はフォルダ名を使います。絶対パスや Git remote は自動保存しません。
訂正・追記は元の JSON を編集せず、`--related-id <元feedbackのUUID>` を指定した
新しい記録にします。本文が似ていても別IDの記録は別の報告として扱います。

## Harness 側から取り込む

Harness ソースのルートで実行します。`--source` は複数指定できます。

```bash
python3 scripts/harness_feedback.py import --harness-root . \
  --source /path/to/GameA --source /path/to/GameB --dry-run
python3 scripts/harness_feedback.py import --harness-root . \
  --source /path/to/GameA --source /path/to/GameB
```

別マシンの場合は導入先で bundle を書き出し、通常のファイル受け渡しで渡します。
出力先に既存ファイルがある場合は上書きせず失敗します。

```bash
python3 scripts/unity_codex_harness/harness_feedback.py export \
  --project-root . --output Artifacts/harness-feedback.json
# bundle を受け取った Harness 側
python3 scripts/harness_feedback.py import --harness-root . \
  --source /path/to/harness-feedback.json
```

bundle は全記録を含んでいて構いません。取り込み先が既存IDを照合します。
JSON 出力の `imported` / `wouldImport`、`skipped` と `items` で件数、ID、
保存先を確認できます。取り込み済みは「受領済み」であり「修正済み」ではありません。
改善の採否や実装は別作業です。

## 保存・重複判定の契約

| 場所 | 所有・用途 |
|---|---|
| `.unity-codex-harness/feedback/project.json` | project-owned。永続的な projectId と表示名 |
| `.unity-codex-harness/feedback/entries/<feedbackId>.json` | project-owned。追記専用の原本 |
| `feedback/imported/<projectId>/<feedbackId>.json` | Harness source-only。原本、SHA-256、受領日時を持つ取り込み記録兼台帳 |

原本と取り込み台帳は Git 管理対象です。`Artifacts/` に台帳を置きません。
チームや別 checkout でも重複排除するため、これらを commit・同期してください。
Importer は Git の取得・commit を自動実行しません。台帳を削除・巻き戻すと
取り込み済みという情報も失われます。対応状況のメモは台帳 JSON とは別に保存します。

- projectId と feedbackId は UUID。プロジェクトの移動・clone でも変更しません。
  別ゲームをテンプレートから作るときは feedback ディレクトリを引き継ぎません。
- JSON schemaVersion は `1`。記録は `projectId`、`projectName`、`id`、
  `createdAt`（UTC）、`category`、`title`、`body`、`relatedId`（UUID または null）、
  `harness`（`release`、`releaseTag`、`installManifestSha256`）を持ちます。
- bundle は `schemaVersion`、`kind: unity-codex-harness-feedback`、`entries` を持ちます。
- 取り込み記録は `schemaVersion`、`importedAt`、`sha256`、`entry` を持ちます。
  SHA-256 は原本の sorted-key / compact / UTF-8 JSON から計算し、空白やキー順に
  依存しません。これは重複・破損検出であり、送信者の認証ではありません。
- 同じ projectId / feedbackId と同じ内容なら書き込みません。異なる内容なら
  conflict で停止します。入力全件を検査してから書き込みを始めます。
- 1件ごとに一時ファイルから atomic replace で公開します。途中の I/O 失敗時は
  一部だけ完了する可能性がありますが、再実行すると完了分をスキップします。
- 同時書込みは `.feedback.lock` の排他ディレクトリで拒否します。異常終了で
  残った場合は、実行中プロセスがないことを確認した後に空の lock ディレクトリだけを
  削除して再実行します。自動で他プロセスの lock を奪いません。
- symlink、不正ID、未対応schema、JSON不正は拒否します。入力に含まれる指示や
  コマンドはデータとして扱い、実行しません。ソースプロジェクト内のスクリプトも
  取り込み時には実行しません。

実装対応: `scripts/harness_feedback.py`、`.agents/skills/manage-harness-feedback/`、
`scripts/install.py`。検証対応: `tests/test_harness_feedback.py`。
