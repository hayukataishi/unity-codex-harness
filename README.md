# Unity Codex Harness

Unityゲーム開発で、OpenAI Codexが設計・実装・検証・報告を一貫して進めるためのリポジトリ内ハーネスです。

このリポジトリには以下が含まれます。

- `.codex/skills/`: Unity開発向けのCodex Skills
- `docs/unity_harness_engineering.md`: ハーネスの運用・安全・品質ルール
- `docs/unity_design_sheet.md`: ゲーム設計書テンプレート
- `docs/mcp_and_skills_list.md`: Unity MCPとSkillsの責務
- `harness.lock.json`: 外部ツールと検証環境の固定情報
- `AGENTS.md`: Codexが最初に読むリポジトリ指示
- `scripts/install.py`: 既存Unityプロジェクトへの安全な導入スクリプト

## 導入

### 1. リポジトリを取得

```bash
git clone https://github.com/hayukataishi/unity-codex-harness.git
cd unity-codex-harness
```

### 2. Unityプロジェクトへインストール

```bash
python3 scripts/install.py /path/to/YourUnityProject
```

インストーラーはUnityプロジェクトの目印を検証し、次をプロジェクトルートへコピーします。

```text
<UNITY_PROJECT_ROOT>/
├─ .codex/skills/
├─ .gitignore
├─ Assets/UnityCodexHarness/Editor/
├─ docs/
├─ harness.lock.json
├─ ProjectSettings/UnityCodexHarnessAssetValidation.json
└─ AGENTS.md
```

`Assets/UnityCodexHarness/Editor/`はMissing Script、Missing Reference、必須資産をUnity Editor APIで検査するEditor専用Assemblyです。Player Buildには含まれません。既存ファイルは標準では上書きせず、ゲーム固有に編集する資産検査設定JSONは通常の再導入でも保持します。

インストーラーは既存`.gitignore`の末尾へ、管理マーカー付きの`/Artifacts/`ルールを追加します。既存ルールと改行形式は保持し、再実行してもブロックは重複しません。`Artifacts`内にGit追跡済みファイルがある場合は、自動削除せずインストールを停止します。

```bash
# 変更内容だけ確認
python3 scripts/install.py /path/to/YourUnityProject --dry-run

# AGENTS.mdを既存のプロジェクト指示で管理する
python3 scripts/install.py /path/to/YourUnityProject --skip-agents

# 内容を確認したうえで既存ファイルを置換
python3 scripts/install.py /path/to/YourUnityProject --force

# ファイルを変更せずArtifactsのGit除外状態を検査
python3 scripts/install.py /path/to/YourUnityProject --check
```

手動導入する場合は、`.codex/skills/`、`docs/`、`templates/unity/`の内容、`harness.lock.json`、必要に応じて`AGENTS.md`をUnityプロジェクトルートへコピーし、ルートの`.gitignore`へ`/Artifacts/`を追加してください。Skills内の参照パスはこの配置を前提にしています。

## Codexでの使い方

UnityプロジェクトルートをCodexで開き、設計IDと目的を指定します。

```text
$maintain-game-design を使って、敵撃破時の経験値獲得仕様と受け入れ条件を設計書へ追加してください。
```

```text
$implement-unity-feature を使って MECH-001 を実装し、
$validate-unity-change で検証してください。
```

主なSkill:

| Skill | 用途 |
|---|---|
| `maintain-game-design` | 要求やレビューを追跡可能な設計へ変換 |
| `implement-unity-feature` | 承認済み設計を小さく安全に実装 |
| `validate-unity-change` | コンパイル、テスト、参照、証拠を検証 |
| `report-unity-work` | 人間がレビューできる形式で作業を報告 |
| `integrate-2d-assets` | 2D素材を承認済みプロファイルでUnityへ統合 |
| `review-gameplay` | Play Modeやビルドの観察証拠を整理 |

## 外部ツールと互換性マニフェスト

| ツール | 固定参照 | 用途 | ハーネスでの実行状態 |
|---|---|---|---|
| [CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp) | `v9.7.0` / `417cf351a152b483c91e6e2deaf7ae355fa8eff3` | Unity Editor操作 | `NOT RUN` |
| [0x0funky/agent-sprite-forge](https://github.com/0x0funky/agent-sprite-forge) | `fff651a89223b044ccfc0b75ed9f3754c6d739b1` | 2Dアセット生成 | `NOT RUN` |

これらは本リポジトリへ同梱していません。再現可能な導入基準、Python要件、公式参照元、検証状態は`harness.lock.json`へ記録します。固定参照は「この版を導入対象にする」という意味であり、Unity `6000.4.10f1`との実接続・実生成が成功したという意味ではありません。

更新時は公式Release、commit、Package metadataまたはrequirementsを確認して固定値を変更し、対象環境で実行した後にだけ`verification.status`を`PASS`へ変更します。

## 検証

リポジトリ内のSkill構造、ローカル文書リンク、旧Vaultパス、GitHub ActionsのSHA固定、`harness.lock.json`の整合性を検証:

```bash
python3 scripts/validate_repository.py
```

Unityプロジェクトの静的プリフライト:

```bash
python3 .codex/skills/validate-unity-change/scripts/preflight_unity_project.py \
  --project-root /path/to/YourUnityProject
```

Unity Editorのコンパイル、EditMode、PlayMode、Editor API資産検査を一つのValidation Runへ保存:

```bash
python3 .codex/skills/validate-unity-change/scripts/run_unity_validation.py \
  --project-root /path/to/YourUnityProject \
  --design-id MECH-001 \
  --ac-id MECH-001-AC01
```

`--ac-id`には、この実行全体で検証する自動受け入れ条件だけを指定します。
macOSでは`ProjectVersion.txt`と一致するUnity Hub Editorを自動検出します。
他の環境では`--unity-editor`または`UNITY_EDITOR_PATH`を指定します。

資産検査は、`Assets`以下のPrefab、Scene、ScriptableObjectにあるMissing Scriptと壊れたObject参照を走査します。ゲーム固有の必須資産・必須参照は`ProjectSettings/UnityCodexHarnessAssetValidation.json`へ追加します。

```json
{
  "requiredAssets": [
    {
      "path": "Assets/Game/Scenes/Main.unity",
      "type": "SceneAsset"
    }
  ],
  "requiredReferences": [
    {
      "assetPath": "Assets/Game/Prefabs/Player.prefab",
      "objectPath": "Player",
      "componentType": "Game.PlayerView",
      "propertyPath": "healthBar"
    }
  ]
}
```

`propertyPath`にはUnityのSerializedProperty pathを指定します。必須か任意かはゲーム仕様で異なるため、nullの全フィールドを一律エラーにはしません。

ハーネス自身のUnity 6.4 fixtureを検証:

```bash
python3 .codex/skills/validate-unity-change/scripts/run_unity_validation.py \
  --project-root tests/fixtures/UnityValidationFixture \
  --design-id HARNESS-001 \
  --ac-id HARNESS-001-AC01
```

### ハーネス自身のCI

`.github/workflows/validate-harness.yml`は、このハーネスリポジトリを自己検証するためのGitHub Actionsです。

- `Repository`: 文書・Skill構造、Pythonテスト、Python構文、Unity fixtureの静的プリフライト
- `Unity 6.4 Fixture`: GameCIでfixtureのEditMode / PlayModeと資産検査回帰テストを実行し、結果をArtifactへ保存

`tests/fixtures/`と`.github/workflows/`は`install.py`のコピー対象ではないため、導入先ゲームには入りません。導入先ゲームでは、コピーされた`.codex/skills/validate-unity-change/`のローカル検証スクリプトを利用し、ゲーム固有のCIは対象プラットフォームやライセンス方針に合わせて別途定義します。

Unity jobにはGitHub Actions Secretsとして`UNITY_EMAIL`、`UNITY_PASSWORD`、および`UNITY_LICENSE`または`UNITY_SERIAL`が必要です。Secretを取得できないfork由来Pull RequestではUnity jobを実行せず、`Repository` jobだけを実行します。

GameCIが正確な`6000.4.10f1` Docker imageを提供していることも実行条件です。2026-06-08の確認時点では該当imageを確認できていないため、ローカルUnity検証はPASS、GitHub上のUnity jobは未実行です。

## ライセンス

[MIT License](./LICENSE)
