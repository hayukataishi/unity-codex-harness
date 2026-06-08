# Unity ハーネスエンジニアリング設計書

## 1. 目的

Unityゲーム開発において、人間がゲームの方向性と品質判断に集中し、OpenAI Codexが設計書に基づく保守・実装・検証を継続的に行える開発ハーネスを構築する。

### 目標とする役割分担

| 担当 | 主な責務 |
|---|---|
| **人間** | 設計書のメンテナンス指示、設計レビュー、ゲームレビュー、最終判断 |
| **OpenAI Codex** | 設計書の更新、設計との整合性確認、機能実装、テスト、検証結果の報告 |

### 成功状態

- 人間は自然言語で変更目的とレビュー結果を伝えればよい。
- Codexは実装前に設計書を読み、必要なら設計書を先に更新する。
- 実装と設計書の差異を自動または半自動で検出できる。
- 機能単位で、要求・設計・実装・テストを追跡できる。
- Unity Editor上の動作確認が必要な箇所をCodexが明示する。
- 人間のゲームレビュー結果が、次の設計変更と実装タスクへ変換される。

---

## 2. 対象ドキュメント・ツール

| 種別 | 対象 |
|---|---|
| コーディングAIエージェント | OpenAI Codex |
| ゲーム設計書 | [Unityゲーム設計書](./unity_design_sheet.md) |
| MCP・Agent Skill一覧 | [Unity MCP・Codex Skills一覧](./mcp_and_skills_list.md) |
| 本書 | Unity開発ハーネス自体の運用・構成・品質保証方法を定義する |

### ドキュメントの責務

- **ゲーム設計書**：何を作るか、ゲームがどう振る舞うべきかを定義する。
- **本書**：Codexがどのような手順と制約で設計・実装・検証するかを定義する。
- **MCP・Skill一覧**：利用可能な能力、用途、使用条件、制限事項を定義する。
- **ソースコードとUnityアセット**：設計を実行可能な形で表現する。
- **テスト**：設計と実装の一致を機械的に確認する。

### 作業パスの解決

Unityプロジェクトの絶対パスは開発環境ごとに異なるため、設計書やSkillへ固定値を保存しない。CodexはUnity作業の開始時に対象プロジェクトを調査し、その作業セッション内でのみ`UNITY_PROJECT_ROOT`として扱う。

解決手順：

1. ユーザーから渡された作業ディレクトリ、外部コンテキスト、Unity MCPの接続先を確認する。
2. 候補ディレクトリに次の構造が存在することを検証する。
3. `ProjectSettings/ProjectVersion.txt`からUnityバージョンを取得する。
4. 候補が一つなら、その絶対パスをセッション内の`UNITY_PROJECT_ROOT`とする。
5. 候補が複数ある、または見つからない場合は推測せず、ユーザーへ対象パスを確認する。

Unityプロジェクトの判定条件：

```text
<UNITY_PROJECT_ROOT>/
├─ Assets/
├─ Packages/
└─ ProjectSettings/
   └─ ProjectVersion.txt
```

運用規則：

- 調査した絶対パスは作業報告へ記載してよいが、共有する設計書、Skill、スクリプトへ恒久的に書き込まない。
- 共有文書、Skill、作業報告ではUnityプロジェクトルートからの相対パスを使う。
- Unityプロジェクト外の参照が必要な場合は、その作業セッション内だけで絶対パスを扱う。
- スクリプトは固定パスではなく、引数または環境変数`UNITY_PROJECT_ROOT`を受け取る。

<a id="platform-gate"></a>

### Unityバージョン・対象プラットフォームの決定ゲート

Unityバージョンと対象プラットフォームはプロジェクト固有のため、ハーネスでは固定しない。設計・実装を始める前に、次の手順で調査または決定し、ゲーム設計書へ記録する。

#### 既存プロジェクト

1. `ProjectSettings/ProjectVersion.txt`から正確なEditorバージョンを取得する。
2. `Packages/manifest.json`と`packages-lock.json`から主要パッケージと互換性を確認する。
3. Project Settings、Build SettingsまたはBuild Profilesから現在のビルド対象を調査する。
4. 設計書の対象プラットフォームと実装設定を比較する。
5. 差異がある場合は勝手にEditor更新やBuild Target変更をせず、人間へ確認する。

#### 新規プロジェクト

1. ゲーム要件から、主対象と副対象のプラットフォームを決める。
2. プラットフォーム要件、使用予定パッケージ、アセット、Unity MCP、CI環境の互換性を調査する。
3. CodexがUnityバージョン候補とトレードオフを提示する。
4. 人間が採用する正確なUnityバージョンと対象プラットフォームを承認する。
5. 必要なUnity Build Supportモジュールを確認してからプロジェクトを作成する。

#### 記録する項目

| 項目 | 内容 |
|---|---|
| Unity Editor | 完全なバージョン文字列 |
| 決定根拠 | 既存プロジェクトから検出 / 新規選定 |
| 主対象 | リリースと品質判断の基準にするプラットフォーム |
| 副対象 | 対応予定だが主対象ではないプラットフォーム |
| 開発時検証環境 | 日常的にEditor・Play Mode・ローカルビルドを実行するOS |
| 必要モジュール | Unity Hubで追加するBuild Support |
| 制約 | ストア、SDK、入力、解像度、性能、署名など |

#### 完了条件

- 正確なUnityバージョンが記録されている。
- 主対象プラットフォームが一つ以上決まっている。
- 主対象ごとの入力方式、画面、性能、配布上の主要制約が整理されている。
- 必要なBuild Supportと外部SDKの不足が明示されている。
- 既存プロジェクトのUnityバージョンを変更する場合は、人間の承認と移行計画がある。

このゲートが未完了の場合、バージョンやプラットフォームへ依存するパッケージ導入、Render Pipeline選定、入力・UI・ビルド設定を確定しない。

---

## 3. 基本原則

### 3.1 設計書をSource of Truthにする

Codexは、実装上の都合だけでゲーム仕様を変更してはならない。仕様変更が必要な場合は、原則として次の順番で作業する。

1. 現在の設計書と実装を確認する。
2. 変更要求の影響範囲を整理する。
3. ゲーム設計書を更新する。
4. 更新後の設計に合わせて実装する。
5. テストとUnity上の確認を行う。
6. 設計・実装・テスト間の整合性を報告する。

### 3.2 人間の判断を勝手に代替しない

以下は人間の承認またはレビューを必要とする。

- ゲームコンセプトやコアメカニクスの変更
- プレイヤー体験を大きく変える変更
- 既存仕様の削除
- セーブデータ互換性を失う変更
- 採用技術、主要パッケージ、アーキテクチャの大幅な変更
- 判断基準が設計書に存在しないゲームバランス調整

### 3.3 小さく変更し、検証可能にする

- 一度の作業では、原則として一つの明確な目的だけを扱う。
- 設計変更と実装変更の対応関係を報告する。
- 既存挙動を変える場合は、回帰テストまたは確認手順を追加する。
- 大規模変更は、設計・基盤・機能実装の段階に分ける。

### 3.4 不確実性を明示する

Codexは推測を事実として扱わず、次のいずれかに分類する。

- **確定仕様**：設計書に明記されている。
- **実装上の決定**：仕様を変えない範囲でCodexが決定できる。
- **仮定**：作業継続のために一時的に置いた前提。
- **要確認**：人間の判断が必要。

---

## 4. ハーネスの全体像

```text
人間
  ├─ 設計書メンテナンス指示
  ├─ 設計レビュー
  └─ ゲームレビュー
        │
        ▼
OpenAI Codex
  ├─ コンテキスト収集
  ├─ 影響分析
  ├─ 設計書更新
  ├─ Unity機能実装
  ├─ EditMode / PlayModeテスト
  ├─ 静的検証・ビルド検証
  └─ 変更内容・残課題・人間向け確認項目の報告
        │
        ▼
設計書 ───── 整合性ゲート ───── Unityプロジェクト
   │                               │
   └──────── テスト・検証 ─────────┘
```

### ハーネスを構成する要素

1. Codex向けリポジトリ指示
2. ゲーム設計書
3. Unityプロジェクト規約
4. 自動テスト
5. 静的解析・コンパイル・ビルド検証
6. Unity Editor操作または画面確認手段
7. タスク開始時と完了時のチェックリスト
8. 人間へ返すレビュー用レポート形式

---

## 5. 標準ワークフロー

### 5.1 設計書メンテナンス

1. 人間が変更目的、背景、期待する体験を指示する。
2. Codexが関連する設計項目と実装箇所を調査する。
3. 曖昧さ、矛盾、影響範囲を整理する。
4. Codexが設計書を更新する。
5. Codexが変更点と要レビュー箇所を提示する。
6. 人間が設計レビューを行う。

### 5.2 機能実装

1. 対応する確定仕様を特定する。
2. 受け入れ条件を列挙する。
3. 既存アーキテクチャと関連テストを確認する。
4. 必要最小限の実装計画を作る。
5. コード、Prefab、Scene、設定、テストを変更する。
6. 自動検証を実行する。
7. Unity Editor上で必要な確認項目を実施または提示する。
8. 設計書との差異がないことを確認する。
9. 人間向けゲームレビュー手順を提示する。

### 5.3 ゲームレビューからの改善

人間のレビュー結果は、Codexが次の形式へ整理する。

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

レビュー内容を直接コード修正へ変換せず、ゲーム仕様の変更を伴う場合は設計書を先に更新する。

---

## 6. 整合性の管理

<a id="traceability"></a>

### 6.1 トレーサビリティ

各機能は、可能な限り以下を相互に追跡可能にする。

```text
設計項目ID
  ├─ 実装クラス / Scene / Prefab / ScriptableObject
  ├─ EditModeテスト
  ├─ PlayModeテスト
  └─ 人間向けゲームレビュー項目
```

#### 設計項目IDの正式形式

```text
<DOMAIN>-<NNN>
```

- `DOMAIN`は英大文字の固定カテゴリ名とする。
- `NNN`はカテゴリごとに`001`から採番する3桁の連番とする。
- 一度発行したIDは変更・再利用しない。廃止した項目もIDを保持し、状態を「廃止」と記録する。
- IDは見出し番号やファイル位置から独立させる。設計書の並べ替えでは変更しない。
- IDは、実装または検証へ追跡する必要がある「判断・振る舞い・制約」に付ける。説明文や記入例には付けない。
- 一つの項目に複数の独立した振る舞いがある場合は、個別のIDへ分割する。

例：

```text
CONCEPT-001
MECH-001
FLOW-001
SCENE-001
UI-001
SAVE-001
```

正式な`DOMAIN`はゲーム設計書の分類表を使用する。新しいカテゴリが必要な場合は、既存カテゴリで表現できないことを確認してから分類表へ追加する。

設計項目の見出しは、次の形を基本とする。

```markdown
### MECH-001: 敵を倒して経験値を獲得する
```

設計項目をコードコメントへ無差別に埋め込まない。テスト名、検証レポート、変更報告、必要に応じて主要クラスやアセットの説明へ記録し、検索可能性を確保する。

### 6.2 受け入れ条件

各設計項目には、実装完了を判定できる受け入れ条件を付ける。正式なMarkdown形式と検証種別は[受け入れ条件の記述形式](./unity_design_sheet.md#acceptance-criteria-format)を使用する。

受け入れ条件IDは次の形式とする。

```text
<設計項目ID>-AC<NN>
```

例：`MECH-001-AC01`

運用原則：

- 各条件は一つの観察可能な結果を表し、合否を二択で判定できるようにする。
- 自動検証と人間による確認を検証種別で明示する。
- 設計書では条件の完了チェックを付けない。実行結果は作業レポートでAC IDごとに`PASS`、`FAIL`、`BLOCKED`、`NOT RUN`として記録する。
- `PASS`には実行したテスト、ログ、スクリーンショットなどの証拠を対応付ける。
- `MANUAL:PLAY`および`MANUAL:EDITOR`は、Codexが確認手順と証拠を準備し、最終的な合否を人間が判断する。
- 一つでも有効な受け入れ条件が`FAIL`、`BLOCKED`、`NOT RUN`の場合、受け入れ完了とはしない。`MANUAL`条件だけが未実行の場合は「実装完了候補・人間レビュー待ち」として引き渡せる。例外的に受け入れ完了扱いとする場合は、人間の承認と理由を記録する。

作業レポートの最小形式：

```markdown
| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `MECH-001-AC01` | `PASS` | `ExperienceTests.AddsEnemyReward`、`Artifacts/ValidationRuns/<RunId>/Evidence/MECH001AC01` |
| `MECH-001-AC02` | `FAIL` | HUD更新が次フレームまで反映されない |
| `MECH-001-AC03` | `NOT RUN` | 人間によるプレイ確認待ち |
```

### 6.3 整合性ゲート

作業完了前に以下を確認する。

- [ ] 変更対象に対応する設計記述が存在する
- [ ] 実装が設計の受け入れ条件を満たす
- [ ] Scene、Prefab、ScriptableObjectの参照切れがない
- [ ] コンパイルエラーがない
- [ ] 関連する自動テストが成功する
- [ ] 既存機能への回帰リスクを確認した
- [ ] 設計書と実装で名称が一致している
- [ ] 未検証事項と手動確認事項を明示した

---

## 7. Unity向け検証レイヤー

| レイヤー | 主な対象 | 検証方法 |
|---|---|---|
| 静的検証 | C#、asmdef、命名、依存方向 | コンパイル、静的解析、規約チェック |
| EditMode | 純粋ロジック、データ変換、計算 | Unity Test Framework |
| PlayMode | Component連携、Scene遷移、入力、時間依存処理 | Unity Test Framework |
| アセット検証 | Prefab、Scene、ScriptableObject、参照 | Editorスクリプトによる検査 |
| ビルド検証 | 対象プラットフォームでの成立性 | CIまたはローカルのバッチビルド |
| ゲームレビュー | 操作感、分かりやすさ、楽しさ、演出 | 人間によるプレイ |

### ハーネスリポジトリのCI基準

ハーネス自身は`.github/workflows/validate-harness.yml`で次の2段階を検証する。

| Job | 実行内容 | Unityライセンス |
|---|---|---|
| `Repository` | リポジトリ検査、Python回帰テスト、Python構文、fixture静的プリフライト | 不要 |
| `Unity 6.4 Fixture` | `tests/fixtures/UnityValidationFixture`のEditMode / PlayMode | 必要 |

運用規則:

- このWorkflowとfixtureはハーネス自身の回帰検証専用とし、`scripts/install.py`でゲームプロジェクトへコピーしない。
- 導入先ゲームは、コピーされた`validate-unity-change` Skillを利用し、対象プラットフォーム、Build Profile、ライセンス方式に合わせたCIを個別に定義する。
- fork由来Pull RequestではSecretを利用できないため、Unity jobを実行せず、ライセンス不要の`Repository` jobを実行する。
- 外部GitHub Actionsは、タグではなく40桁のcommit SHAへ固定する。
- Unity jobの開始前にSecretの存在だけを検証し、値をログへ出力しない。
- Unityテスト結果とログは、成功・失敗にかかわらずGitHub Actions Artifactへ保存する。
- Workflowの定義完了と、GitHub上での実行成功は別の状態として扱う。Secret、Runner、GameCI imageなどが未準備なら`NOT RUN`または`BLOCKED`と報告する。

### Scene・Prefab・ScriptableObjectの自動検査

`Assets/UnityCodexHarness/Editor/AssetValidationBatch.cs`をEditor専用Assemblyとして導入し、Unity Editor APIで次を検査する。

- `Assets`以下のPrefabにあるMissing Scriptと解決不能なObject参照
- `Assets`以下のSceneにあるMissing Scriptと解決不能なObject参照
- `Assets`以下のScriptableObjectにある解決不能なObject参照
- 設定JSONへ列挙した必須アセットの存在と型
- 設定JSONへ列挙したPrefab、Scene、ScriptableObjectの必須参照

設定ファイル:

```text
ProjectSettings/UnityCodexHarnessAssetValidation.json
```

設定形式:

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
      "objectPath": "Player/HudAnchor",
      "componentType": "Game.PlayerHudBinder",
      "propertyPath": "healthBar"
    }
  ]
}
```

運用規則:

- `path`と`assetPath`はUnityプロジェクト相対の`Assets/...`形式とする。
- `type`と`componentType`は短い型名または完全修飾型名を使用する。
- `objectPath`はPrefabではルート相対、Sceneではルート名から始まるHierarchy pathとする。
- `propertyPath`は`SerializedObject.FindProperty`で解決できるpathとする。
- nullを許容する任意参照は設定へ列挙しない。全null参照を一律エラーにしない。
- 検査は読み取り専用とし、Missing Componentの削除や参照の自動修復を行わない。
- 結果は`Artifacts/ValidationRuns/<RunId>/Logs/AssetValidation.json`へ保存する。
- Tag、Layer、Input Action、Addressables、Build Profile Scene Listは別検査として追加する。

### 自動化を優先するもの

- コンパイル
- EditMode / PlayModeテスト
- Missing Script、Missing Referenceの検出
- 必須Scene、Prefab、設定アセットの存在確認
- Build SettingsのScene登録確認
- 設計で定義された識別子や名称の検査
- バッチモードでのビルド

### 人間に委ねるもの

- 面白さ
- 操作感
- 演出の気持ちよさ
- 難易度の納得感
- UIの理解しやすさ
- コンセプトに沿った体験になっているか

<a id="validation-artifacts"></a>

### 検証成果物の保存規則

テスト結果、ログ、スクリーンショットなどの実行成果物は、Unityプロジェクトルートからの相対パスで管理する。開発環境ごとに異なる絶対パスは記録規則へ含めない。

#### 実行成果物

各検証実行は、次の場所へ新しいRunディレクトリを作成する。

```text
<UNITY_PROJECT_ROOT>/
└─ Artifacts/
   └─ ValidationRuns/
      └─ <RunId>/
         ├─ RunManifest.json
         ├─ Report.md
         ├─ Tests/
         │  ├─ EditMode.xml
         │  ├─ PlayMode.xml
         │  └─ Coverage/
         ├─ Logs/
         │  ├─ Editor.log
         │  ├─ Tests.log
         │  └─ Build.log
         ├─ Evidence/
         │  └─ <AcceptanceCriterionIdWithoutHyphens>/
         │     ├─ Screenshots/
         │     ├─ Videos/
         │     └─ Notes.md
         ├─ Profiler/
         └─ Builds/
```

`<RunId>`はUTCの`yyyyMMddTHHmmssZ`形式とする。例：`20260608T114858Z`。同一秒に複数実行する場合は末尾へ2桁の連番を付ける。

#### ファイル形式

| 種別 | 形式 |
|---|---|
| テスト結果 | NUnit互換XML |
| Coverage | 使用ツールのHTML / XML / JSON |
| ログ | UTF-8テキスト |
| スクリーンショット | PNG |
| 動画 | MP4を基本とし、取得手段に応じて変更可 |
| Profiler | Unity Profilerで再読込可能な形式と要約 |
| Run metadata | JSON |
| 人間向け要約 | Markdown |

`RunManifest.json`には最低限、Run ID、開始日時、Git commit、Unityバージョン、対象プラットフォーム、実行コマンド、対象設計ID・AC ID、結果、成果物の相対パスを記録する。値を取得できない場合は空欄にせず、未取得理由を記録する。

#### 運用規則

- `Artifacts`は生成物としてGit管理対象から除外する。
- 同じRunディレクトリを再利用・上書きしない。再実行は新しいRun IDで保存する。
- 作業報告では、絶対パスではなく`Artifacts/ValidationRuns/<RunId>/...`形式の相対パスを記載する。
- ACごとの証拠は`Evidence/<AcceptanceCriterionIdWithoutHyphens>`へまとめる。例：`MECH001AC01`
- Console全体を画像だけで保存せず、検索可能なテキストログも残す。
- スクリーンショットには、可能な限り対象Scene、画面状態、解像度を`Notes.md`またはManifestへ記録する。
- 成功ログだけでなく、失敗時のスタックトレース、再現手順、終了コードを保存する。
- CIでは同じディレクトリ構成を生成し、CIのArtifact機能へアップロードする。保持期間は少なくとも人間レビュー完了までとし、プロジェクトごとに設定する。
- ログや画像を外部へ共有する前に、トークン、秘密情報、個人情報、ローカル絶対パスなどが含まれていないか確認する。

#### 恒久的な回帰基準

承認済みスクリーンショットやGolden Dataなど、将来の比較に必要なものだけを次へ昇格する。

```text
<UNITY_PROJECT_ROOT>/
└─ TestBaselines/
   ├─ Screenshots/
   ├─ Data/
   └─ Metadata/
```

- `TestBaselines`はGit管理する。
- `Artifacts`から`TestBaselines`への昇格には人間の承認を必要とする。
- Baseline更新時は、変更理由、対応する設計ID・AC ID、承認者を`Metadata`へ記録する。
- 単なる実行ログ、全スクリーンショット、動画、ProfilerデータはBaselineへ入れない。
- 2Dアートプロファイルの承認用スクリーンショットも、回帰比較へ使用する場合は`TestBaselines/Screenshots`へ保存する。

---

## 8. Codexの作業契約

### 作業開始時

Codexは最低限、次を確認する。

1. 本書
2. [Unityゲーム設計書](./unity_design_sheet.md)
3. [Unity MCP・Codex Skills一覧](./mcp_and_skills_list.md)
4. リポジトリ内のCodex向け指示
5. Unityバージョン、対象プラットフォーム、導入パッケージ
6. Unityバージョン・対象プラットフォーム決定ゲートの完了状態
7. 2Dアセットを扱う場合は、2Dアートプロファイル決定ゲートの完了状態
8. 関連コード、Scene、Prefab、テスト

### 作業中

- 既存設計と既存パターンを優先する。
- 新規作成・名称変更では[標準命名規則](./unity_design_sheet.md#naming-rules)を使用する。
- 新規ファイルの配置では[標準フォルダ構成](./unity_design_sheet.md#folder-layout)を使用する。
- Assemblyの作成・参照変更では[最小asmdef構成](./unity_design_sheet.md#asmdef-layout)を使用する。
- 2Dアセットの生成・取込前に[2Dアートプロファイル決定ゲート](./unity_design_sheet.md#art-profile-gate)を確認する。
- 検証成果物は[検証成果物の保存規則](#validation-artifacts)へ保存する。
- 既存プロジェクトへ命名規則を適用するためだけの一括改名は行わない。参照、GUID、シリアライズ、外部データへの影響を調査し、必要な変更だけを段階的に行う。
- 既存プロジェクトへ標準フォルダ構成を適用するためだけの一括移動は行わない。移動が必要な場合はUnity EditorまたはUnity MCP経由で行い、参照切れを検証する。
- asmdef追加・変更後は、RuntimeからEditor・Testsへの逆参照、循環参照、全対象プラットフォームでのコンパイルを検証する。
- Unityが生成するファイルを手作業で不必要に変更しない。
- `.meta` ファイルとGUIDの整合性を壊さない。
- SceneやPrefabのテキスト編集は、影響を理解できる場合に限定する。
- Editor操作が安全な場合は、直接YAMLを編集するよりEditor APIを優先する。
- 新しい依存関係は、必要性と代替案を確認してから導入する。

### 作業完了時の報告

```text
## 実施内容

## 更新した設計

## 更新した実装

## 実行した検証と結果

## 検証成果物

## Unity Editorで確認してほしいこと

## 設計との整合性

## 残課題・仮定・リスク
```

---

## 9. MCP・Agent Skillの運用方針

具体的な採用候補と設定は[Unity MCP・Codex Skills一覧](./mcp_and_skills_list.md)で管理する。

選定時には以下を記録する。

| 項目 | 内容 |
|---|---|
| 名称 | MCPサーバーまたはSkill名 |
| 目的 | ハーネス内で解決する問題 |
| 使用タイミング | 調査、設計、実装、テスト、レビューなど |
| 入力 | 必要な情報やファイル |
| 出力 | 生成物や検証結果 |
| 書き込み範囲 | 変更を許可する場所 |
| 制限・リスク | 誤操作、非決定性、コスト、セキュリティ |
| 代替手段 | 利用できない場合の手順 |

### 想定する能力カテゴリ

- Unity Editorの操作・状態取得
- Scene / Prefab / GameObject階層の検査
- Unity Test Frameworkの実行
- バッチビルドとログ取得
- ゲーム画面のスクリーンショット取得
- 入力操作を伴うPlayMode確認
- C#コード解析
- Git差分・履歴の調査
- 設計書とコード間の検索

<a id="unity-mcp-policy"></a>

### 9.1 Unity MCP優先方針

Unity Editor内で完結する操作は、対応するUnity MCPツールがある限りMCPへ任せる。Scene、Prefab、`.asset`などのUnity YAMLを直接編集する方法は、対応ツールがなく、安全性を説明できる場合の最終手段とする。

2026-06-08時点のUnity MCP beta版では、Scene、GameObject、Component、Asset、Prefab、Script、ScriptableObject、Material、Animation、Camera、UI、VFX、Shader、Texture、Graphics、Physics、Package、Build、Test、Profiler、Consoleなどを操作できる。さらに任意C#、Menu Item、プロジェクト固有Custom Toolの実行能力がある。

ツールは更新されるため、固定された一覧だけを信用しない。作業開始時に次を行う。

1. 複数Editorがある場合は対象Instanceを確認し、明示的に選択する。
2. Editor Stateを読み、コンパイル、Domain Reload、Play Modeなどの状態を確認する。
3. Project Info、Tool Groups、利用可能なPackageを確認する。
4. 対応ツールと現在のUnity APIを確認し、利用可能ならMCPを優先する。
5. 操作後はConsole、Hierarchy、Inspector相当の情報、Screenshot、Testで結果を検証する。

### 9.2 承認の考え方

ユーザーの明示的な依頼、承認済み設計項目、受け入れ条件に直接必要な操作は、すでに承認済みとみなす。同じ範囲について操作ごとの再確認を求めない。

追加承認が必要なのは、作業中に当初の依頼・設計範囲を越える高影響操作が新たに必要になった場合だけである。

承認を求める場合は、次を簡潔に提示する。

```text
操作:
対象:
必要な理由:
主な影響:
復旧方法:
```

### 9.3 自律実行してよい操作

以下は、承認済みタスクと設計の範囲内でCodexが自律実行できる。

#### 読み取り・調査

- Editor、Project、Scene、GameObject、Component、Asset、Prefab、Package、Build設定の照会
- Unity API Reflectionと公式Documentationの参照
- Console、Hierarchy、Rendering Stats、Profiler Counterの取得
- Asset、Script、GameObject、Testの検索

#### Editor・検証

- Play、Pause、Stop、Scene Viewのフォーカス
- Screenshot、動画、Profiler Capture、Memory Snapshot、Frame Debuggerの取得
- EditMode / PlayMode Test、Asset Validation、Physics Queryの実行
- Asset Database Refresh、Script Compilation、Console確認
- Undo / Redoによる作業中の復旧
- 承認済み対象プラットフォームへの検証ビルド

#### 実装・コンテンツ制作

- `Assets/Game`内のScript作成・構造化編集・検証
- GameObjectの作成、複製、配置、親子化、Component追加・設定
- 承認済みSceneの作成、保存、Additive Load、Active Scene切替、Scene間移動
- Prefab、ScriptableObject、Material、Texture、Shader、Animation、Animator、UI、VFXの作成・更新
- Camera、Cinemachine、Volume、Lighting、Physics、Collision Matrixの設定
- ProBuilderによるプロトタイプ・レベル形状の作成
- 承認済み設計に必要なTag・Layerの追加
- `Assets/Game`内のフォルダ作成、Asset Import、現在タスクで新規作成したAssetの移動・改名・削除
- 設計で確定済みのBuild Scene登録や、既存設定値への反映
- 既知の安全なMenu Itemおよび内容を確認済みのプロジェクトCustom Toolの実行

既存Scene、Prefab、ScriptableObject、Scriptを変更すること自体は承認不要である。ただし、事前に対象を読み、変更後に保存・コンパイル・参照・Test・Screenshotなど必要な検証を行う。

### 9.4 自律実行時の安全条件

- 変更前に対象Instance、Active Scene、Play/Edit Mode、コンパイル状態を確認する。
- 名前だけで対象が曖昧な場合は、Instance IDまたは完全なHierarchy Pathで指定する。
- Dirty Sceneを置き換えたり閉じたりする前に保存状態を確認する。
- Script編集ではSHAまたは構造化編集を使い、編集後にCompileとConsoleを確認する。
- 大量操作は`batch_execute`を使ってよいが、依存する操作は`fail_fast`で停止可能にする。
- 削除より無効化、上書きより更新、直接YAML編集よりEditor APIを優先する。
- 長時間操作の前後で検証成果物を保存する。
- ToolにUndo対応がある場合はUndo可能な操作を優先する。Git管理下では差分も確認する。
- `execute_code`では`safety_checks=true`を維持し、専用ツールで表現できる操作には使用しない。

### 9.5 人間の追加承認が必要な操作

次の操作は、現在の依頼または確定設計に明示されていない場合、実行前に人間の承認を得る。ユーザーが当該操作を明示的に依頼済みなら再承認は不要である。

#### 依存関係・開発基盤

- Packageの追加、削除、Version変更、Embed
- Scoped Registryの追加・削除
- `force=true`による依存Packageの強制削除
- Unity Editor Versionの変更・Upgrade
- Render Pipelineの切替
- 最小構成を越えるasmdef分割や依存方向の変更
- Unity MCP Package自体のDeploy・Restore

#### 既存資産の破壊・広範囲変更

- タスク開始前から存在するScene、Prefab、Script、ScriptableObject、Assetの削除
- 永続ID、Public API、Serialized Field名、Save Data形式を壊す改名・移動
- 複数機能や多数のAssetへ及ぶ一括削除・一括改名・一括移動
- Tag・Layerの削除
- `manage_scene(validate, auto_repair=true)`による既存Missing Componentの自動除去
- Baked DataのClear、Baselineの削除・更新
- `ThirdParty`、外部Package、生成・Vendor管理ファイルの直接変更

現在タスクでCodex自身が新規作成したAssetや一時GameObjectの削除・作り直しは承認不要とする。

#### Project・Build・Release設定

- Build Targetの切替
- Product Name、Company Name、Version、Bundle Identifierの変更
- Scripting Backend、Architecture、Scripting Define Symbolsの変更
- 署名、証明書、Keystore、Provisioning、Store、配布設定の変更
- Release Buildの作成、外部配布、Upload、Publish

承認済みPlatform・既存設定のまま`Artifacts`へ検証Buildを作る操作は承認不要である。

#### 任意実行・未知の拡張

- `execute_code`で`safety_checks=false`を使用する
- 任意C#からファイル削除、OS Process、Network、認証情報、Unityプロジェクト外へアクセスする
- 効果範囲を確認できないMenu Itemを実行する
- 内容を確認できないCustom Toolを実行する
- 実行履歴から、現在のProject状態に適合するか確認せず任意C#をReplayする

### 9.6 原則禁止

人間の個別承認があっても、次は安全な代替手段がないかを先に検討する。

- `Library`、Package Cache、Unityの生成キャッシュを直接編集する
- 秘密情報をScript、Scene、Prefab、Log、Screenshotへ保存する
- Version ControlやBackupがなく、復旧不能な状態で広範囲削除を行う
- Unity MCPの安全検査を回避する目的で任意C#や外部Processを使う

### 9.7 MCP操作後の完了条件

- 対象SceneとAssetが保存されている。
- Compile Errorがない。
- Missing Script / Missing Referenceがない。
- 変更に対応する受け入れ条件を検証している。
- 必要なScreenshot、Log、Test結果が`Artifacts/ValidationRuns/<RunId>`へ保存されている。
- 実行した高影響操作、未検証事項、Rollback方法を作業報告へ記載している。

---

## 10. 今後決定する事項

- [x] 対象Unityプロジェクトのパス解決方針
- [x] Unityバージョン・対象プラットフォームの決定プロセス
- [x] Unityプロジェクトの命名規則
- [x] Unityプロジェクト内のフォルダ構成
- [x] asmdefの分割・依存規則
- [x] 2Dアートプロファイルの決定プロセス
- [ ] Codex向け指示ファイルの配置と内容
- [x] 設計項目IDの命名規則
- [x] 設計書へ受け入れ条件を記述する形式
- [x] Unity EditorをCodexから操作する方法
- [x] 採用するMCPサーバーとAgent Skill
- [x] Unity Test Frameworkのテスト分類
- [x] CIで実行する検証項目
- [x] Scene / Prefab / ScriptableObjectの自動検査方法
- [ ] ゲームレビュー結果の記録形式
- [ ] Definition of Done
- [x] 変更の承認境界
- [ ] セーブデータ互換性ポリシー
- [x] エラー・ログ・スクリーンショットの保存場所

---

## 11. 初期Definition of Done

機能変更は、少なくとも以下を満たした時点で実装完了候補とする。

- [ ] 対応する設計が確定している
- [ ] 受け入れ条件を満たす実装がある
- [ ] コンパイルが成功する
- [ ] 必要な自動テストが成功する
- [ ] 参照切れやMissing Scriptがない
- [ ] 実施した検証結果が記録されている
- [ ] 人間向けゲームレビュー手順がある
- [ ] 未解決の仮定とリスクが明示されている
- [ ] 設計書と実装の差異がない
