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

## Unityプロジェクトへの導入

### 最短手順

次の`/path/to/YourUnityProject`を、対象ゲームのUnityプロジェクトルートへ置き換えて実行します。パスに空白がある場合に備えて、引用符で囲むことを推奨します。

```bash
git clone https://github.com/hayukataishi/unity-codex-harness.git
cd unity-codex-harness

# 変更予定を確認
python3 scripts/install.py "/path/to/YourUnityProject" --dry-run

# ハーネスを導入
python3 scripts/install.py "/path/to/YourUnityProject"

# ArtifactsがGit管理外になっていることを確認
python3 scripts/install.py "/path/to/YourUnityProject" --check
```

Windowsで`python3`が見つからない場合は、`python`または`py -3`へ読み替えてください。

### 事前条件

- Python 3.11以上を利用できる
- Unityプロジェクトを作成済みである
- 初回導入前にUnity Editorを閉じている
- 可能なら対象プロジェクトの変更をcommitまたはbackupしている

インストーラーへ渡すのは`Assets`フォルダではなく、その一つ上の**Unityプロジェクトルート**です。次の3つが存在するディレクトリを指定します。

```text
<UNITY_PROJECT_ROOT>/
├─ Assets/
├─ Packages/
└─ ProjectSettings/
   └─ ProjectVersion.txt
```

例:

```text
macOS:   /Users/your-name/UnityProjects/MyGame
Windows: C:\Users\your-name\UnityProjects\MyGame
```

### 手順1: ハーネスを取得する

Unityプロジェクトとは別の場所へ、このリポジトリをcloneします。

```bash
git clone https://github.com/hayukataishi/unity-codex-harness.git
cd unity-codex-harness
```

すでに取得済みの場合は、`unity-codex-harness`ディレクトリへ移動するだけで構いません。

### 手順2: 導入予定を確認する

最初に`--dry-run`を使います。このコマンドはファイルを変更せず、作成・更新予定だけを表示します。

```bash
python3 scripts/install.py "/path/to/YourUnityProject" --dry-run
```

出力の`would create`は新規作成、`would update`は既存ファイルへの追記・更新を表します。

### 手順3: Unityプロジェクトへ導入する

dry-runの内容に問題がなければ、通常実行します。

```bash
python3 scripts/install.py "/path/to/YourUnityProject"
```

導入後の主な構成:

```text
<UNITY_PROJECT_ROOT>/
├─ .codex/skills/                              Codex用Unity開発Skill
├─ .gitignore                                  /Artifacts/ルールを安全に追記
├─ Assets/UnityCodexHarness/Editor/            Unity Editor資産検査
├─ docs/                                       設計・運用ドキュメント
├─ harness.lock.json                           外部ツールの固定情報
├─ ProjectSettings/
│  └─ UnityCodexHarnessAssetValidation.json    ゲーム固有の資産検査設定
└─ AGENTS.md                                   Codex向けリポジトリ指示
```

`Assets/UnityCodexHarness/Editor/`はEditor専用Assemblyで、Missing Script、Missing Reference、必須資産を検査します。Player Buildには含まれません。

インストーラーは既存ファイルを標準では上書きしません。`.gitignore`には管理マーカー付きの`/Artifacts/`ルールだけを追加し、既存ルールや改行形式を保持します。

次のものはゲームプロジェクトへ自動導入されません。

- Unity Editor本体とBuild Support
- Unity MCP
- agent-sprite-forge
- ハーネス自身のGitHub ActionsとUnity fixture
- ゲーム固有のCI、Build Profile、Package

Unity 6のゲームでは、導入後に[BUILD-001](docs/unity_design_sheet.md#build-001)へ従ってDevelopment / QA / ReleaseのBuild Profileをゲーム側で作成します。Build Profileは対象Platform、Scene、配布要件がプロジェクトごとに異なるため、インストーラーは自動生成しません。

Cinemachineを採用する場合もPackageは自動導入されません。[GRAPHICS-001](docs/unity_design_sheet.md#graphics-001)に従い、Unity 6の新規案件はCinemachine 3.xを基準として、ゲーム側の`Packages/manifest.json`と`packages-lock.json`へ記録された正確なバージョンを使用します。

### 手順4: 導入結果を確認する

まず、検証成果物を保存する`Artifacts/`がGit管理外になっていることを確認します。

```bash
python3 scripts/install.py "/path/to/YourUnityProject" --check
```

成功時は次のように表示されます。

```text
Artifacts ignore check: PASS
```

続いてUnityプロジェクトへ移動し、静的プリフライトを実行します。

```bash
cd "/path/to/YourUnityProject"
python3 .codex/skills/validate-unity-change/scripts/preflight_unity_project.py \
  --project-root .
```

`"status": "PASS"`になったことを確認してからUnity Editorを開き、Consoleにコンパイルエラーがないことを確認します。

### 既存の`AGENTS.md`がある場合

通常実行は既存`AGENTS.md`を勝手に上書きせず、競合として停止します。その場合は`--skip-agents`で導入し、このリポジトリの`AGENTS.md`にある必須ルールを既存ファイルへ手動で統合してください。

```bash
python3 scripts/install.py "/path/to/YourUnityProject" --skip-agents
```

### `Artifacts/`がすでにGit追跡されている場合

インストーラーは追跡済みファイルを自動削除せず停止します。対象を確認してからGitのindexだけを外し、再実行します。ローカルファイル自体は削除されません。

```bash
git -C "/path/to/YourUnityProject" ls-files Artifacts
git -C "/path/to/YourUnityProject" rm -r --cached Artifacts
python3 scripts/install.py "/path/to/YourUnityProject"
```

### ハーネスを更新する

ハーネス側を更新した後、最初にdry-runで差分を確認します。

```bash
cd "/path/to/unity-codex-harness"
git pull
python3 scripts/install.py "/path/to/YourUnityProject" --dry-run
```

導入済みファイルと新しいハーネスの内容が異なる場合、通常実行は安全のため停止します。差分を確認し、ハーネス管理ファイルを新しい版へ置き換えてよい場合だけ`--force`を使用します。

```bash
python3 scripts/install.py "/path/to/YourUnityProject" --force
```

`--force`はゲーム固有に編集した`ProjectSettings/UnityCodexHarnessAssetValidation.json`も置換します。必要な設定を退避してから実行してください。

### オプション一覧

| オプション | 用途 |
|---|---|
| `--dry-run` | ファイルを変更せず、導入予定を表示する |
| `--check` | ファイルを変更せず、`Artifacts/`のGit除外状態を検査する |
| `--skip-agents` | `AGENTS.md`を導入対象から外す |
| `--force` | 内容が異なる既存ファイルを置換する |

### 手動導入

自動インストーラーを利用できない場合は、`.codex/skills/`、`docs/`、`templates/unity/`の内容、`harness.lock.json`、必要に応じて`AGENTS.md`をUnityプロジェクトルートへコピーします。ルートの`.gitignore`へ`/Artifacts/`も追加してください。Skills内の参照パスはこの配置を前提にしています。

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

### 横断機能を先に採否判断する

ネットワーク、ローカライズ、アクセシビリティ、分析、Privacy、課金、広告、LiveOps、UGC、XRなどは、使用しない場合も含めて設計書Section 20のマトリクスへ`採用`、`不採用`、`保留`を記録します。

- `採用`: 対象範囲、Package / Service、データ考慮、設計ID・AC IDを記録
- `不採用`: 理由と再評価条件を記録
- `保留`: 理由、決定責任者、期限を記録し、依存実装を開始しない

Packageや外部Service、通信、データ収集、課金・広告・UGCを追加する前に該当行を確認してください。

### 規模に合うアーキテクチャを選ぶ

実装開始前に[ARCH-001](docs/unity_design_sheet.md#architecture-profile-gate)で、現在の制約を満たす最小のProfileを選びます。

| Profile | 目安 | 基本方針 |
|---|---|---|
| `Small` | Game Jam、試作、小規模・少人数 | Unity既定Assemblyまたは単一Runtime asmdef、直接参照、手動Composition、局所イベント |
| `Standard` | 継続開発、複数Feature・複数人 | 必要なRuntime / Editor / Tests分離、Feature境界、明示的な依存方向 |
| `Large` | 複数チーム、長期運用、Module再利用 | Feature Package、Pure C# Assembly、公開API、所有者、Architecture Test |

4層、4 Assembly、DI Container、Manager群、ScriptableObject Event Channelは必須セットではありません。選択理由、採用しない仕組み、次Profileへの移行条件を設計書へ記録し、観測可能な問題が生じた時だけ人間の承認を得て段階的に移行します。Service Locatorは規模別の推奨方式として新規採用しません。

### セーブの破損・Version差を先に設計する

進行データを保存するゲームは、実装前に[SAVE-001](docs/unity_design_sheet.md#save-001)を埋めます。

- Primaryを直接上書きせず、Temp書込み、flush、検証、置換、Backupを定義する
- `schemaVersion`、対応可能な最古Version、段階Migration、downgradeを決める
- 旧Version、破損、書込み中断、未来Version、容量・権限失敗の匿名fixtureを用意する
- Cloud Save採用時はRevision、競合候補保持、Merge禁止Field、Offline再送、Account切替を決める
- 暗号化、Integrity、鍵管理、個人データ、Platform制約を別々に確認する

`PlayerPrefs`は音量など消失しても進行を失わない設定へ限定します。暗号化しただけ、JSONへ保存しただけ、versionフィールドを追加しただけでは、破損復旧や互換性を保証したことにはなりません。

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

ハーネステンプレート自身のInstaller、preflight、Validation Run、文書規約を回帰検証:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

テストは一時Unityプロジェクトを使い、新規・再導入、競合、`--force`、`--dry-run`、`.meta`・GUID・Missing Script異常系、Run ID衝突を検証します。Unity APIを必要とするCompile、EditMode、PlayMode、資産検査は後述のUnity fixtureで別に実行します。

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
このコマンドはRunを`RUNNING`で作成し、検証後に`COMPLETED`へfinalizeして、Manifestと成果物のSHA-256を自動検証します。

手動で開始したRunが継続不能になった場合は、開始状態のまま放置せず、理由付き`BLOCKED`で閉じます。

```bash
python3 .codex/skills/validate-unity-change/scripts/finalize_validation_run.py \
  --project-root /path/to/YourUnityProject \
  --run-dir "Artifacts/ValidationRuns/<RunId>" \
  --blocked-reason "Unity Editor license was unavailable"
```

完了済みRunのManifest sidecar hashと全成果物を再検査:

```bash
python3 .codex/skills/validate-unity-change/scripts/verify_validation_run.py \
  --project-root /path/to/YourUnityProject \
  --run-dir "Artifacts/ValidationRuns/<RunId>"
```

`COMPLETED` Runは再finalize・編集しません。証拠を追加または修正する場合は新しいRunを作成します。

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
  --design-id DEBUG-003 \
  --ac-id DEBUG-003-AC01 \
  --ac-id DEBUG-003-AC02 \
  --ac-id DEBUG-003-AC03 \
  --ac-id DEBUG-003-AC04
```

fixtureにはRuntime / Editor / EditMode / PlayMode asmdef、保存済みPrefab、Scene、Unity 6 Build Profile、正常系と故意に壊した参照の検査が含まれます。

### ハーネス自身のCI

`.github/workflows/validate-harness.yml`は、このハーネスリポジトリを自己検証するためのGitHub Actionsです。

- `Repository`: 文書・Skill構造、Pythonテスト、Python構文、Unity fixtureの静的プリフライト
- `Unity 6.4 Fixture`: GameCIでfixtureのEditMode / PlayModeと資産検査回帰テストを実行し、結果をArtifactへ保存

`tests/fixtures/`と`.github/workflows/`は`install.py`のコピー対象ではないため、導入先ゲームには入りません。導入先ゲームでは、コピーされた`.codex/skills/validate-unity-change/`のローカル検証スクリプトを利用し、ゲーム固有のCIは対象プラットフォームやライセンス方針に合わせて別途定義します。

Unity jobにはGitHub Actions Secretsとして`UNITY_EMAIL`、`UNITY_PASSWORD`、および`UNITY_LICENSE`または`UNITY_SERIAL`が必要です。Secretを取得できないfork由来Pull RequestではUnity jobを実行せず、`Repository` jobだけを実行します。

GameCIが正確な`6000.4.10f1` Docker imageを提供していることも実行条件です。2026-06-08の確認時点では該当imageを確認できていないため、ローカルUnity検証はPASS、GitHub上のUnity jobは未実行です。

## ライセンス

[MIT License](./LICENSE)
