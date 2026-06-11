# Unity Codex Harness

Unityゲーム開発で、OpenAI Codexが設計・実装・検証・報告を一貫して進めるためのリポジトリ内ハーネスです。

このリポジトリには以下が含まれます。

- `.codex/skills/`: Unity開発向けのCodex Skills
- `docs/unity_harness_engineering.md`: ハーネスの運用・安全・品質ルール
- `docs/unity_harness_capabilities.md`: ハーネスとして標準実装済みの能力
- `docs/unity_harness_requirements.md`: 導入先へ適用する標準・推奨要件
- `docs/unity_design_sheet.md`: 配布先ゲームの個別要件・適用・例外記録
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
├─ .codex/
│  ├─ agents/                                  Project Custom Subagent
│  └─ skills/                                  Codex用Unity開発Skill
├─ .gitignore                                  成果物・外部ツールのローカル配置を除外
├─ .unity-codex-harness/
│  ├─ install-manifest.json                    所有区分とsource hash
│  ├─ install-manifest.sha256                  manifest自体の改変検知
│  └─ baselines/                               project-owned templateの比較元
├─ Assets/UnityCodexHarness/Editor/            Unity Editor資産検査
├─ docs/
│  ├─ unity_harness_capabilities.md              ハーネス管理の標準実装
│  ├─ unity_harness_requirements.md              ハーネス管理の標準・推奨要件
│  └─ unity_design_sheet.md                     ゲーム側所有の個別要件
├─ harness.lock.json                           外部ツールの固定情報
├─ ProjectSettings/
│  └─ UnityCodexHarnessAssetValidation.json    ゲーム固有の資産検査設定
├─ scripts/unity_codex_harness/
│  ├─ check_external_dependencies.py           外部依存の未導入・版違い検査
│  ├─ validate_design_contract.py              HREQ適用・例外・未決定の検査
│  ├─ validate_design_readiness.py             マイルストーン別設計完成度の検査
│  └─ verify_harness_integrity.py              標準実装の欠落・改変検査
└─ AGENTS.md                                   Codex向けリポジトリ指示
```

`Assets/UnityCodexHarness/Editor/`はEditor専用Assemblyで、Missing Script、Missing Reference、必須資産を検査します。Player Buildには含まれません。

インストーラーは導入対象を`harness-managed`と`project-owned`へ分けます。`docs/unity_harness_capabilities.md`と`docs/unity_harness_requirements.md`は`harness-managed`、ゲーム固有の`docs/unity_design_sheet.md`は`project-owned`です。`.gitignore`には管理マーカー付きで`/Artifacts/`、`/.codex/external/`、外部Skillのローカルコピーを除外するルールを追加し、既存ルールや改行形式を保持します。

`project-owned`として保護されるファイル:

- `docs/unity_design_sheet.md`
- `docs/mcp_and_skills_list.md`
- `AGENTS.md`
- `harness.lock.json`
- `ProjectSettings/UnityCodexHarnessAssetValidation.json`

これらは存在しない場合だけ生成され、導入後はゲーム側が所有します。通常更新、`--force`、`--force-file`のいずれでも既存内容を上書きしません。

### 標準実装・標準推奨・ゲーム個別設計

| 文書 | 所有者 | 記載する内容 | 通常のゲーム制作で編集 |
|---|---|---|---|
| `docs/unity_harness_capabilities.md` | ハーネス | Installer、Skills、検証、fixture、CI、回帰テストとして標準実装済みの能力 | しない |
| `docs/unity_harness_requirements.md` | ハーネス | 継承される必須標準と、対話で採否・方式を決める`HREQ-*`推奨要件 | しない |
| `docs/unity_design_sheet.md` | 配布先ゲーム | 個別要件、HREQ適用状態、例外、設計項目ID、AC、承認履歴 | する |

標準実装はゲーム要件ではなく、ハーネスが提供・検証する機能です。標準・推奨要件は任意の参考資料ではありません。必須標準は導入時点で継承され、決定必須・条件付き推奨はユーザーとの対話で選択肢、推奨理由、トレードオフを確認して決定します。個別ゲームはHREQ適合表へ`継承`、`対象外`、`例外承認`、`未決定`を記録します。

標準要件と個別要件は章番号ではなく`HREQ-*` IDで対応します。章番号は各文書を読む順番にすぎません。

契約構造と、作業に必要なHREQが解決済みかを検査:

```bash
python3 scripts/unity_codex_harness/validate_design_contract.py \
  --project-root "/path/to/YourUnityProject" \
  --require HREQ-ARCH-001
```

対象マイルストーンのPhase、設計欄、HREQ、保留、設計ID・AC、監査、
人間承認をまとめて検査:

```bash
python3 scripts/unity_codex_harness/validate_design_readiness.py \
  --project-root "/path/to/YourUnityProject" \
  --milestone Prototype \
  --output "Artifacts/DesignReadiness/Prototype.json"
```

Concept、Prototype、Vertical Slice、Alpha、Beta、Releaseの順に必須範囲が
広がります。現在のマイルストーンをBlockingする未決事項、期限切れの保留、
未承認Phase、未解決HREQ、Approved設計IDのAC不足が一つでもあれば`FAIL`です。

Codex Skillsは実装・受け入れ前に関連HREQを確認します。通常のゲーム設計では`unity_design_sheet.md`だけを更新し、標準要件自体を変える場合だけ明示的なハーネス改善として`unity_harness_requirements.md`を変更します。

### 最初のゲーム設計対話

新規ゲーム、アイデア段階、設計書の大部分が未決定の場合は、
Codexへ次のように依頼します。

```text
$bootstrap-game-design を使って、このゲームのPrototype向け初期設計を
一問ずつ進め、game_design_auditor Subagentでも各Phaseを監査してください。
```

Skillは対象マイルストーンを確認し、Vision、Player Context、Core Loop、
Presentation、Technical Baseline、Save、Repository、Build、横断機能、
設計ID・ACをPhase順に対話します。技術選択は先に選択肢、推奨理由、
代替案、トレードオフを説明し、無回答や推奨案を自動確定しません。
ConceptやPrototypeでは、その時点に不要なRelease級の決定を期限付きで
保留できます。

一つの対話内で、`HREQ-*`の採否・方式・例外を決める`[標準推奨]`と、
プレイヤー体験、ルール、コンテンツ、個別制約を決める`[ゲーム個別]`を
明示します。両者が結びつく質問は`[両方]`とし、HREQ適合記録とゲーム詳細を
同時に更新します。標準推奨を決めただけでゲーム仕様を決めたことにはせず、
ゲーム仕様を書いただけで関連HREQを解決したことにもしません。

主Agentが唯一の対話窓口と設計書更新担当です。multi-agent機能が利用できる場合、
ユーザーがSubagent利用を明示した対話では、公式Project Custom Agentの
`.codex/agents/game-design-auditor.toml`を各Phase終了時と最終承認前に起動し、
質問漏れ、設計矛盾、誘導質問、未説明のトレードオフを監査します。
Subagentはユーザーへ直接質問せず、設計書を書き換えず、最終判断を代行しません。
新しくAgentを導入した直後のセッションで認識されない場合はCodexを再起動します。

`.codex/skills/bootstrap-game-design/agents/openai.yaml`はSkillの表示名、
既定プロンプトなどのmetadataであり、Subagent定義ではありません。
`AGENTS.md`はRepository全体の役割分担、Skillは対話手順、`.codex/agents/*.toml`は
実際にspawnされる専門Agentを担当します。

進行状態と、現在の質問、提示した選択肢、回答要約、反映案、確認状態は
`unity_design_sheet.md`の非規範な対話証跡へ保存されます。このため回答後の
確認待ちを含め、別セッションでも最初の未完了Phaseから再開できます。
未確認の証跡はゲーム仕様として扱いません。初期設計後の部分的な要件変更は
`$maintain-game-design`を使用します。

旧版の`unity_design_sheet.md`で共通規則とゲーム固有設計が混在している場合、インストーラーは既存内容を自動分割・上書きしません。先に`--prepare-migration`を実行し、生成された`Artifacts/HarnessInstallerMigrations/`のbase・local・incoming差分を確認して、個別要件、HREQ適用状態、ID、AC、承認履歴だけを新しいSheetへ移してください。

`.unity-codex-harness/`は更新比較に必要なハーネス状態です。ゲーム側の設計書ではなく、元templateのhashとbaselineを保持します。`Artifacts/`とは異なりGit管理へ含めてください。

次のものはゲームプロジェクトへ自動導入されません。

- Unity Editor本体とBuild Support
- Unity MCP
- agent-sprite-forge
- ハーネス自身のGitHub ActionsとUnity fixture
- ゲーム固有のCI、Build Profile、Package

Unity 6のゲームでは、[HREQ-BUILD-001](docs/unity_harness_requirements.md#build-001)を継承し、[ゲーム側の適用記録](docs/unity_design_sheet.md#build-profile-record)へ採用内容を記載してDevelopment / QA / ReleaseのBuild Profileを作成します。Build Profileは対象Platform、Scene、配布要件がプロジェクトごとに異なるため、インストーラーは自動生成しません。

Cinemachineを採用する場合もPackageは自動導入されません。[HREQ-CAMERA-001](docs/unity_harness_requirements.md#graphics-001)に従い、Unity 6の新規案件はCinemachine 3.xを基準として、ゲーム側の`Packages/manifest.json`と`packages-lock.json`へ記録された正確なバージョンを使用します。

### 手順4: 導入結果を確認する

まず、検証成果物と外部OSSのローカル配置がGit管理外であり、
harness-managed標準実装が導入時の状態から改変されていないことを確認します。

```bash
python3 scripts/install.py "/path/to/YourUnityProject" --check
```

成功時は次のように表示されます。

```text
Harness local-path ignore check: PASS
Harness integrity verification: PASS
```

完全性検査だけをCodex作業前またはゲーム側CIで実行する場合:

```bash
python3 scripts/unity_codex_harness/verify_harness_integrity.py \
  --project-root .
```

検査はharness-managedファイルの欠落、内容変更、symlink、専有管理ディレクトリ内の未知ファイル、manifest改変を失敗させます。`unity_design_sheet.md`などのproject-owned変更は許可されます。

失敗時にmanifestや`install-manifest.sha256`を手編集して追認しないでください。信頼するハーネスcheckoutから`--force-file`または`--force`を使ってbackup後に復旧します。独自ハーネスへ変更する場合は、ハーネス本体を明示的にforkし、そのcheckoutのInstallerから再配布します。

ゲーム側CIでは、コンパイルやテストより前に次を実行します。

```yaml
- name: Verify Unity Codex Harness integrity
  run: >-
    python3 scripts/unity_codex_harness/verify_harness_integrity.py
    --project-root .
```

続いてUnityプロジェクトへ移動し、外部依存を診断します。

```bash
cd "/path/to/YourUnityProject"
python3 scripts/unity_codex_harness/check_external_dependencies.py \
  --project-root .
```

Unity MCPまたは外部Skillがない場合、このコマンドは終了コード`1`と固定版の導入手順を表示します。自動ダウンロード、Package変更、Skillコピーは行いません。

その後、静的プリフライトを実行します。

```bash
python3 .codex/skills/validate-unity-change/scripts/preflight_unity_project.py \
  --project-root .
```

`"status": "PASS"`になったことを確認してからUnity Editorを開き、Consoleにコンパイルエラーがないことを確認します。

### 既存の`AGENTS.md`がある場合

通常実行は既存`AGENTS.md`を`project-owned`としてそのまま保持します。このリポジトリの`AGENTS.md`にある必須ルールを既存ファイルへ手動で統合してください。ハーネスの`AGENTS.md`を比較対象にも含めない場合は`--skip-agents`を使用します。

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

導入済みの`harness-managed`ファイルと新しいハーネスの内容が異なる場合、通常実行は全書込み前に停止します。差分を確認し、対象を限定して更新します。

```bash
python3 scripts/install.py "/path/to/YourUnityProject" \
  --force-file "docs/unity_harness_engineering.md"
```

確認済みの全`harness-managed`競合を一括更新する場合だけ`--force`を使用します。

```bash
python3 scripts/install.py "/path/to/YourUnityProject" --force
```

置換される既存ファイルは、書込み前に次へbackupされます。

```text
Artifacts/HarnessInstallerBackups/<OperationId>/
├─ BackupManifest.json
└─ files/<元の相対パス>
```

`project-owned`は`--force`でも置換されません。新しいハーネスでproject-owned templateが更新された場合、通常実行は対象を表示します。次のコマンドで三者比較用bundleを生成します。

```bash
python3 scripts/install.py "/path/to/YourUnityProject" \
  --prepare-migration
```

```text
Artifacts/HarnessInstallerMigrations/<OperationId>/
├─ MigrationManifest.json
├─ base/<相対パス>
├─ local/<相対パス>
├─ incoming/<相対パス>
└─ diff/<相対パス>.*.patch
```

`base`は前回template、`local`はゲーム側の現在値、`incoming`は新しいtemplateです。bundle生成後もゲーム側ファイルは変更されません。diffをレビューし、必要な項目だけをlocalへ統合します。harness-managed競合も同時に存在する場合は、承認した`--force-file`と組み合わせます。

旧版Installerからの更新でbaselineがない場合は、現在のlocalを`legacy-local-snapshot`としてbaseにも保存し、localからincomingへの差分を生成します。

backupから戻す場合は`BackupManifest.json`で対象とhashを確認し、`files/`以下の該当ファイルを元の相対パスへ戻します。Installerは自動rollbackを行いません。

### オプション一覧

| オプション | 用途 |
|---|---|
| `--dry-run` | ファイルを変更せず、導入予定を表示する |
| `--check` | ファイルを変更せず、ローカル専用pathのGit除外とharness-managed完全性を検査する |
| `--skip-agents` | `AGENTS.md`を導入対象から外す |
| `--force-file PATH` | 指定したharness-managedファイルだけをbackup後に置換する。複数指定可 |
| `--force` | 内容が異なる全harness-managedファイルをbackup後に置換する |
| `--prepare-migration` | project-owned templateの三者比較bundleを作る。localは変更しない |

### 手動導入

自動インストーラーを利用できない場合は、`.codex/skills/`、`docs/`、`templates/unity/`の内容、`harness.lock.json`、必要に応じて`AGENTS.md`をUnityプロジェクトルートへコピーします。ルートの`.gitignore`へ`/Artifacts/`も追加してください。Skills内の参照パスはこの配置を前提にしています。

手動導入ではinstall manifest、所有区分、baseline、backup、migration bundleが生成されないため、継続更新には推奨しません。

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

ネットワーク、ローカライズ、アクセシビリティ、分析、Privacy、課金、広告、LiveOps、UGC、XRなどは、使用しない場合も含めて[ゲーム設計書の横断機能採否](docs/unity_design_sheet.md#cross-cutting-record)へ`採用`、`不採用`、`保留`を記録します。判断規則は[横断機能採否ゲート](docs/unity_harness_requirements.md#cross-cutting-gate)を参照します。

- `採用`: 対象範囲、Package / Service、データ考慮、設計ID・AC IDを記録
- `不採用`: 理由と再評価条件を記録
- `保留`: 理由、決定責任者、期限を記録し、依存実装を開始しない

Packageや外部Service、通信、データ収集、課金・広告・UGCを追加する前に該当行を確認してください。

### 規模に合うアーキテクチャを選ぶ

実装開始前に[HREQ-ARCH-001](docs/unity_harness_requirements.md#architecture-profile-gate)に従い、[ゲーム側の適用記録](docs/unity_design_sheet.md#architecture-profile-record)で現在の制約を満たす最小のProfileを選びます。

| Profile | 目安 | 基本方針 |
|---|---|---|
| `Small` | Game Jam、試作、小規模・少人数 | Unity既定Assemblyまたは単一Runtime asmdef、直接参照、手動Composition、局所イベント |
| `Standard` | 継続開発、複数Feature・複数人 | 必要なRuntime / Editor / Tests分離、Feature境界、明示的な依存方向 |
| `Large` | 複数チーム、長期運用、Module再利用 | Feature Package、Pure C# Assembly、公開API、所有者、Architecture Test |

4層、4 Assembly、DI Container、Manager群、ScriptableObject Event Channelは必須セットではありません。選択理由、採用しない仕組み、次Profileへの移行条件を設計書へ記録し、観測可能な問題が生じた時だけ人間の承認を得て段階的に移行します。Service Locatorは規模別の推奨方式として新規採用しません。

### セーブの破損・Version差を先に設計する

進行データを保存するゲームは、[HREQ-SAVE-001](docs/unity_harness_requirements.md#save-001)に従い、実装前に[ゲーム側の適用記録](docs/unity_design_sheet.md#save-decision-record)を埋めます。

- Primaryを直接上書きせず、Temp書込み、flush、検証、置換、Backupを定義する
- `schemaVersion`、対応可能な最古Version、段階Migration、downgradeを決める
- 旧Version、破損、書込み中断、未来Version、容量・権限失敗の匿名fixtureを用意する
- Cloud Save採用時はRevision、競合候補保持、Merge禁止Field、Offline再送、Account切替を決める
- 暗号化、Integrity、鍵管理、個人データ、Platform制約を別々に確認する

`PlayerPrefs`は音量など消失しても進行を失わない設定へ限定します。暗号化しただけ、JSONへ保存しただけ、versionフィールドを追加しただけでは、破損復旧や互換性を保証したことにはなりません。

### Gitと大容量アセット運用を選ぶ

[HREQ-REPO-001](docs/unity_harness_requirements.md#project-002)に従い、[ゲーム側の適用記録](docs/unity_design_sheet.md#repository-policy-record)でBranch、LFS、Unity Merge、Asset ownershipをプロジェクトごとに決めます。

- `main / develop / feature/*`を固定せず、Team、CI、Release保守からBranch戦略を選ぶ
- `.png`などの拡張子一律ではなく、Path、実測size、変更頻度、Merge可否、LFS quotaで追跡対象を決める
- Git利用時は`Visible Meta Files`を維持し、Mergeが必要な自作Unity Assetは`Force Text`を基本候補にする
- UnityYAMLMerge後もUnity EditorでScene、Prefab、参照、Override、Console、Testを確認する
- Merge不能BinaryにはLFS lockまたはOwner、Scene・Prefabには同時編集ルールを定める
- 既存履歴のLFS移行や一括再serializeは通常変更ではなく、承認付きMigrationとして扱う

インストーラーはゲーム固有のBranch、`.gitattributes`、LFS対象、Serialization modeを自動変更しません。Repository容量、Hosting quota、既存履歴への影響がプロジェクトごとに異なるためです。

## 外部ツールと互換性マニフェスト

| ツール | 固定参照 | 用途 | ハーネスでの実行状態 |
|---|---|---|---|
| [CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp) | `v9.7.0` / `417cf351a152b483c91e6e2deaf7ae355fa8eff3` | Unity Editor操作 | `NOT RUN` |
| [0x0funky/agent-sprite-forge](https://github.com/0x0funky/agent-sprite-forge) | `fff651a89223b044ccfc0b75ed9f3754c6d739b1` | 2Dアセット生成 | `NOT RUN` |

これらは本リポジトリへ同梱していません。再現可能な導入基準、Python要件、公式参照元、検証状態は`harness.lock.json`へ記録します。固定参照は「この版を導入対象にする」という意味であり、Unity `6000.4.10f1`との実接続・実生成が成功したという意味ではありません。

### 外部ツールを明示的に導入する

外部OSSは利用者が上流ライセンスと固定参照を確認してから導入します。本ハーネスは外部リポジトリのコードを再配布せず、導入時にも自動取得しません。現在固定している両依存は記録上MITですが、ライセンス条件は固定参照の原文を確認してください。この記述は法的助言ではありません。

Unity MCP:

1. Unityの`Window > Package Management > Package Manager`を開く。
2. `Add package from git URL`へ次の固定commit URLを入力する。

```text
https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#417cf351a152b483c91e6e2deaf7ae355fa8eff3
```

3. `Window > MCP for Unity`を開き、Serverを開始してCodex clientを設定する。
4. Unity側が`Connected`になったことを確認し、診断CLIを再実行する。

Package Managerが記録する`Packages/manifest.json`と`Packages/packages-lock.json`はゲームプロジェクトの再現性情報としてGit管理します。Unity MCPのソースcheckoutやPackage cacheはゲームリポジトリへコピーしません。

agent-sprite-forgeをプロジェクト単位で導入する例:

```bash
mkdir -p .codex/external .codex/skills
git clone https://github.com/0x0funky/agent-sprite-forge.git \
  .codex/external/agent-sprite-forge
git -C .codex/external/agent-sprite-forge checkout --detach \
  fff651a89223b044ccfc0b75ed9f3754c6d739b1
python3 -m pip install -r \
  .codex/external/agent-sprite-forge/requirements.txt
cp -R .codex/external/agent-sprite-forge/skills/generate2dsprite \
  .codex/skills/generate2dsprite
cp -R .codex/external/agent-sprite-forge/skills/generate2dmap \
  .codex/skills/generate2dmap
```

上記はmacOS / Linux shellの例です。Windowsでは同じパスを`New-Item`と`Copy-Item -Recurse`で作成・コピーします。既存の外部Skillがある場合は、内容と参照元を確認してから置換してください。

`.codex/external/`と2つの外部Skillコピーはインストーラーが`.gitignore`へ追加するため、ハーネス本体やゲームリポジトリへ再配布されません。導入後はCodexを再起動し、診断CLIを再実行します。全プロジェクトで共用する場合は`$CODEX_HOME/external/agent-sprite-forge`と`$CODEX_HOME/skills/`へ同じ固定commitから導入できます。

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

テストは一時Unityプロジェクトを使い、新規・再導入、所有区分、競合、対象限定更新、backup、migration bundle、`--dry-run`、`.meta`・GUID・Missing Script異常系、Run ID衝突を検証します。Unity APIを必要とするCompile、EditMode、PlayMode、資産検査は後述のUnity fixtureで別に実行します。

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

Unity `6000.4.10f1`は維持し、GameCI imageを次へ固定しています。

```text
unityci/editor:ubuntu-6000.4.10f1-linux-il2cpp-3.2.2@sha256:53b1b2a66f4cfe5629b81799d2de8ac8082fccb99298871f11d09a3225bff552
```

Workflowは上記を一つの`tag@digest` referenceとして`customImage`へ渡します。Repository jobでは次を実行し、Docker Hub上のactive tag、Linux amd64 image、OCI digestを`harness.lock.json`と照合します。

```bash
python3 scripts/check_gameci_image.py --verify-remote
```

2026-06-10時点でimage availabilityは`PASS`です。ただし、これはUnity testの成功ではありません。GitHub Actions上のremote executionはUnity License Secret未設定のため`BLOCKED`です。

### Unity License Secretを設定する

GitHubの対象リポジトリで`Settings > Secrets and variables > Actions`を開き、`New repository secret`から設定します。

Unity Personal:

1. Unity HubへCIで使用するUnity accountでログインする。
2. `Preferences > Licenses > Add > Get a free personal license`で手動activationする。
3. macOSでは`/Library/Application Support/Unity/Unity_lic.ulf`の内容全体を`UNITY_LICENSE`へ登録する。
4. Unity accountのemailを`UNITY_EMAIL`、passwordを`UNITY_PASSWORD`へ登録する。

Unity Pro:

1. Unity subscriptionのserialを`UNITY_SERIAL`へ登録する。
2. Unity accountのemailを`UNITY_EMAIL`、passwordを`UNITY_PASSWORD`へ登録する。
3. `UNITY_LICENSE`は不要である。

Secret値をWorkflow、Issue、Pull Request、Logへ貼り付けないでください。Secretを取得できないfork由来Pull RequestではUnity jobを実行せず、`Repository` jobだけを実行します。設定後はGitHubの`Actions > Validate Harness > Run workflow`から手動実行し、`Unity 6.4 Fixture`と`unity-validation-<run_id>` Artifactを確認します。

公式手順: [GameCI Activation](https://game.ci/docs/github/activation/)

## ライセンス

[MIT License](./LICENSE)
