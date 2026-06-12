# Unity MCP・Codex Skills 一覧

## 採用確定

| 名称 | 種別 | 固定参照 | 主な責務 | 検証状態 |
|---|---|---|---|---|
| [CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp) | MCP | `v9.7.0` / `417cf351a152b483c91e6e2deaf7ae355fa8eff3` | Unity Editor操作、Scene・GameObject・アセット・スクリプト・テストの操作 | `NOT RUN` |
| [0x0funky/agent-sprite-forge](https://github.com/0x0funky/agent-sprite-forge) | Codex Skill | `fff651a89223b044ccfc0b75ed9f3754c6d739b1` | 2Dスプライト、アニメーションシート、マップ、プロップ、FXの生成と後処理 | `NOT RUN` |

正確な標準repository、channel、commit、実行要件、公式参照元は`../harness.lock.json`で管理する。ゲーム固有の承認済み差分は`../harness.overrides.json`へ記録する。固定参照を記録しただけでは互換性確認済みとは扱わず、実接続または実生成を行うまでは`NOT RUN`とする。

### 導入と配布

- Unity MCPとagent-sprite-forgeは本ハーネスへ同梱せず、標準インストーラーも自動取得しない。
- 標準の固定参照、commit固定URL、license名、固定参照のlicense URLは`harness.lock.json`を正とし、ゲーム固有pinは`harness.overrides.json`との差分合成結果を正とする。
- 利用者は上流licenseを確認し、READMEの手順で明示的に導入する。ライセンス確認は法的助言を代替しない。
- 導入先では`python3 scripts/unity_codex_harness/check_external_dependencies.py --project-root .`を実行し、Package、checkout commit、Skill配置を確認する。
- `.codex/external/`と外部SkillコピーはGit管理外とする。Unity Packageの`manifest.json`と`packages-lock.json`は再現性情報としてGit管理する。
- 静的診断の`PASS`はUnity MCPのServer、Codex connector、Editor接続を証明しない。実接続は別のsmoke testと証拠Runで確認する。

### 責務の境界

- **Unity MCP**はUnity Editorを操作する道具であり、プロジェクト固有の設計判断や完了条件は持たせない。
- **agent-sprite-forge**は画像アセットを制作する。ゲーム仕様、Unityへのインポート設定、Prefab化、ゲームへの接続はプロジェクト側で管理する。
- **プロジェクト独自Skill**には、設計書、実装規約、検証基準、成果物の配置規則など、このプロジェクトでしか分からない手順を持たせる。

### Unity MCPへ委任する操作

Unity Editor内で対応可能な操作は、原則としてUnity MCPを使う。詳細な承認境界は[Unity MCP優先方針](./unity_harness_engineering.md#unity-mcp-policy)を参照する。

能力調査で確認した主な機能：

- Scene、GameObject、Component、Prefab、Asset、ScriptableObjectのCRUD
- C# Scriptの作成、構造化編集、Validation、Compile
- Material、Texture、Shader、Animation、Animator、Camera、Cinemachine
- UI Toolkit、uGUI構築支援、VFX、Graphics、Lighting、Physics
- ProBuilderによるEditor内モデリング
- Package、Build、Build Profile、Scene List、Platform設定
- EditMode / PlayMode Test、Profiler、Console、Screenshot
- Play / Pause / Stop、Tag / Layer、Undo / Redo
- Menu Item、任意C#、プロジェクトCustom Toolの実行

#### 基本方針

- 承認済み設計とユーザー依頼の範囲内では、Scene・Prefab・Script・Assetの作成と変更をMCPへ広く任せる。
- Package、既存資産の削除、Build/Releaseの恒久設定、任意コードの危険な実行は追加承認の対象とする。
- MCP操作後はCompile、Console、Test、Screenshot、参照検査で検証する。
- ツール追加・仕様変更に備え、作業開始時にEditor State、Project Info、Tool Groupsを確認する。
- Cinemachine操作前はPackageの正確なmajor versionを確認する。3.xでは`CinemachineCamera`と同一GameObject上のPosition / Rotation Control Componentを使用し、2.x既存案件の移行は公式Upgraderを伴う別作業として扱う。

---

## 用意するプロジェクト独自Skill

### 優先度A：最初から必要

#### 1. `bootstrap-game-design`

**目的:** 新規ゲームまたは未完成の初期設計を、対象マイルストーンに必要な深さまで一問ずつ決定する。

**主な処理**

1. 対話Run、対象マイルストーン、意思決定者、既存資料を確認する。
2. Vision、Player Context、Core Loop、Presentation、Technical Baseline、Save、Repository、Build、横断機能、TraceabilityをPhase順に対話する。
3. 選択前に目的、現実的な選択肢、推奨理由、代替案、トレードオフを説明する。
4. 確定、提案、仮定、要確認、対象外を分離し、無回答や推奨を自動確定しない。
5. 質問を`標準推奨`、`ゲーム個別`、`両方`へ分類し、関連HREQ IDを証跡へ残す。
6. マイルストーン別の必須深度を使い、現時点で不要な判断は責任者と期限付きで保留する。
7. 各Phaseの進捗、Blocking未決事項、関連AC・設計ID、人間承認、監査状態と、非規範な対話証跡を`docs/game_design/`へ記録する。
8. ユーザーがSubagent利用を明示した場合、公式Project Custom Agentの`game_design_auditor`に設計書と対話証跡から漏れ、矛盾、誘導、未説明トレードオフを独立監査させる。
9. `validate_design_readiness.py`で必須Phase、設計欄、HREQ、未決事項、
   横断機能、設計ID・AC、監査、承認を機械判定する。
10. Subagent findings、完成度検査`PASS`、人間承認を経て、対象マイルストーン単位で初期設計を完了する。

Subagentは設計書を編集せず、ユーザーへ直接質問せず、承認を代行しない。主Agentが唯一の対話窓口と書込み主体になる。
`agents/openai.yaml`はSkill metadataであり、実行時Subagentは
`.codex/agents/game-design-auditor.toml`で定義する。

---

#### 2. `maintain-game-design`

**目的:** 人間の要求やゲームレビューを、実装可能で追跡可能な設計へ変換する。

**主な処理**

1. 導入済みゲームでは`verify_harness_integrity.py`を実行し、失敗中は設計作業を開始しない。
2. [Unityハーネス標準実装](./unity_harness_capabilities.md)で利用可能な能力と既知の不足を読む。
3. [Unityハーネス標準・推奨要件](./unity_harness_requirements.md)で継承される`HREQ-*`と品質ゲートを読む。
4. [Unityゲーム設計文書索引](./unity_design_sheet.md)と`docs/game_design/`で適用状態、例外、AC、設計、承認状態を読む。
5. 要求をゲーム全体AC、Scene AC、実装上の決定、仮定、要確認へ分類する。
6. ACを先に記録・承認し、影響する設計項目と横断機能採否マトリクスを特定する。
7. 関連HREQの`未決定`、対象外理由、例外承認を検査する。
8. 所有単位別の設計項目へ上流ACとUnity実装マッピングを追加・更新する。
9. AC、設計、実装の双方向整合と、人間の承認が必要な変更を分離する。

**持たせるもの**

- [設計項目IDの規則](./unity_harness_engineering.md#traceability)
- [受け入れ条件の記述テンプレート](./unity_harness_requirements.md#acceptance-criteria-format)
- ゲームレビューから設計変更へ変換するテンプレート
- 人間の承認が必要な変更の判定表

---

#### 3. `implement-unity-feature`

**目的:** 確定した設計項目を、既存アーキテクチャに沿って小さく実装する。

**主な処理**

1. 対象の設計項目IDと受け入れ条件を確認する。
2. 関連するコード、Scene、Prefab、ScriptableObject、テストを調査する。
3. 変更計画と回帰リスクを整理する。
4. C#、アセット、Editor設定、テストを変更する。
5. Unity MCPを使ってEditor上の作成・接続・確認を行う。

**持たせるもの**

- [Unityプロジェクトの命名規則](./unity_harness_requirements.md#naming-rules)
- [Unityプロジェクトのフォルダ規則](./unity_harness_requirements.md#folder-layout)
- [asmdefの分割・依存規則](./unity_harness_requirements.md#asmdef-layout)
- [Small / Standard / Largeアーキテクチャプロファイル](./unity_harness_requirements.md#architecture-profile-gate)
- 選択Profileに応じたレイヤー分離と依存方向
- Scene・Prefab・ScriptableObjectの編集方針
- `.meta`とGUIDを壊さないための制約
- 新規パッケージ導入時の承認条件

---

#### 4. `validate-unity-change`

**目的:** 変更が設計と一致し、Unityプロジェクトを壊していないことを機械的に検証する。

**主な処理**

- コンパイルエラー確認
- EditMode / PlayModeテスト実行
- Missing Script / Missing Reference検査
- Scene、Prefab、ScriptableObjectの必須参照検査
- Build Profile、Scene List、Tag、Layer、Input設定の確認
- 対象プラットフォームのビルド検証
- 設計項目IDとテスト・実装の対応確認
- Validation Runのfinalize、終端状態、成果物ハッシュ、整合性検証

**持たせるもの**

- 検証コマンドまたはEditorスクリプト
- テスト分類規則
- [エラー時のログ・証拠収集先](./unity_harness_engineering.md#validation-artifacts)
- Definition of Doneチェックリスト

> 再現性が重要なため、このSkillは説明文だけでなく、`scripts/`に検証処理を置く。

---

#### 4. `report-unity-work`

**目的:** Codexの作業結果を、人間が短時間でレビューできる形式にまとめる。

**出力形式**

```text
## 実施内容
## 更新した設計
## 更新した実装
## 実行した検証と結果
## Unity Editorで確認してほしいこと
## 設計との整合性
## 残課題・仮定・リスク
```

**追加する情報**

- 変更した設計項目ID
- 自動検証済みの範囲
- 人間のプレイ確認が必要な範囲
- `Artifacts/ValidationRuns/<RunId>`以下のスクリーンショット、ログ、ビルド

---

### 優先度B：2D制作を始める前に必要

#### 5. `integrate-2d-assets`

**目的:** agent-sprite-forgeの生成物を、このUnityプロジェクトの規格に変換して組み込む。

**主な処理**

1. [2Dアートプロファイルの規則](./unity_harness_requirements.md#art-profile-gate)と[ゲーム側の採用記録](./game_design/all/presentation_design.md#hreq-art-001-2dアートプロファイル)を確認する。
2. 必要なアセット仕様を設計書から抽出する。
3. agent-sprite-forgeで画像を生成する。
4. ファイル名と配置先をプロジェクト規約へ合わせる。
5. 承認済みプロファイルに従ってTextureImporterを設定する。
6. Sprite分割、Pivot、Pixels Per Unit、Filter Mode、Compressionを設定する。
7. AnimationClip、AnimatorController、Prefabを生成または更新する。
8. SceneまたはScriptableObjectへ接続する。
9. 承認用サンプルと比較し、表示崩れ、フレーム抜け、参照切れを検証する。

**持たせるもの**

- アートディレクション
- 2Dアートプロファイルと承認用サンプル
- 解像度、PPU、Pivot、スライス規則
- Sprite Atlasの方針
- アニメーション命名・Loop設定
- 原本、生成途中、Unity取込後アセットの配置規則
- 生成AIアセットのライセンス・出典記録方法

> 画像生成自体を再実装せず、agent-sprite-forgeとUnity MCPを接続する薄い統合Skillにする。

---

#### 6. `review-gameplay`

**目的:** ビルドまたはPlay Modeを観察し、人間のゲームレビューに必要な証拠と確認項目を作る。

**主な処理**

- 指定されたプレイ経路を実行する。
- スクリーンショット、動画、Consoleログ、Profiler情報を保存する。
- 受け入れ条件ごとに観察結果を記録する。
- 「機械的に判定可能」と「人間の感覚判断が必要」を分離する。
- 問題を、事実・期待体験・変更候補・影響設計へ整理する。

**注意:** 面白さ、気持ちよさ、難易度の納得感をCodexだけで合格判定しない。

---

## 後から追加するSkill

プロジェクトの仕様が確定してから追加する。現段階で作ると、内容が汎用論だけになりやすい。

| Skill候補 | 追加条件 |
|---|---|
| `balance-gameplay` | パラメータ、評価指標、テレメトリ形式が決まった時 |
| `migrate-save-data` | `HREQ-SAVE-001`、実Schema、対応旧Version fixture、Rollback方針が決まった時 |
| `build-release` | 対象プラットフォーム、署名、配布先、CIが決まった時 |
| `localize-game` | 対象言語とLocalization運用が決まった時 |
| `profile-unity-game` | FPS、メモリ、ロード時間などの性能予算が決まった時 |
| `author-level-content` | ステージやクエストのデータ形式が安定した時 |

---

## Skillを増やしすぎないための基準

次のいずれかを満たす場合だけSkill化する。

- 複数回繰り返す固有ワークフローである。
- 手順を間違えるとScene、Prefab、GUID、セーブデータなどを壊す。
- プロジェクト固有の判断基準や出力形式がある。
- スクリプト、テンプレート、規約を再利用すると品質が安定する。

単なるUnity知識、単発作業、短いコーディング規約は独立Skillにせず、リポジトリ指示または既存Skillの`references/`へ置く。

---

## 推奨する初期構成

```text
<UNITY_PROJECT_ROOT>/
├─ .codex/
│  └─ agents/
│     └─ game-design-auditor.toml
├─ .agents/
│  └─ skills/
│     ├─ bootstrap-game-design/
│     ├─ maintain-game-design/
│     ├─ implement-unity-feature/
│     ├─ validate-unity-change/
│     ├─ report-unity-work/
│     ├─ integrate-2d-assets/
│     └─ review-gameplay/
└─ docs/
   ├─ unity_harness_engineering.md
   ├─ unity_harness_capabilities.md
   ├─ unity_harness_requirements.md
   ├─ unity_design_sheet.md
   ├─ game_design/
   │  ├─ all/
   │  ├─ scenes/
   │  └─ shared/
   └─ mcp_and_skills_list.md
```

`.agents/skills/`はrepository-scoped Codex Skillの標準配置である。
`.codex/agents/`はProject Custom Agent用であり、Skill配置とは分けて扱う。

`unity_harness_capabilities.md`はハーネスが標準実装している能力、`unity_harness_requirements.md`は導入先へ適用する必須標準と対話で決める推奨要件であり、通常のゲーム制作では変更しない。`unity_design_sheet.md`は配布先ゲーム所有の索引で、実際のAC、HREQ適用状態、例外、設計項目、実装マッピング、承認履歴は`docs/game_design/`へ記入する。

ただし、実運用では以下の3つから開始してもよい。

1. `bootstrap-game-design`
2. `maintain-game-design`
3. `implement-unity-feature`
4. `validate-unity-change`

`report-unity-work`は小さいため、当初は`implement-unity-feature`と`validate-unity-change`の共通出力規則に含め、繰り返し利用が確認できてから独立させてもよい。

---

## 次に決めること

- [x] 設計項目IDの正式な形式 — `<DOMAIN>-<NNN>`、発行後は変更・再利用しない
- [x] 受け入れ条件のMarkdown形式 — ゲーム全体・Scene AC表、独立AC ID、検証種別、合格条件、関連設計IDを明記
- [x] Unityプロジェクトのパス解決方針 — 固定せず、作業開始時に調査・検証する
- [x] Unityバージョンと対象プラットフォームの決定プロセス — 既存は検出、新規は互換性調査後に人間が承認
- [x] プロジェクトの命名規則 — 英語ASCII、意味を優先したPascalCase/camelCase、永続IDは`lower-kebab-case`
- [x] プロジェクトのフォルダ構成 — 自作物は`Assets/Game`、種類別の上位構成と機能別Runtimeコード
- [x] アーキテクチャとasmdefの分割・依存規則 — Small / Standard / Largeから最小の十分なProfileを選び、4 AssemblyはStandardの基準例として扱う
- [x] 2Dアセット設定の決定プロセス — アート方式とカテゴリ別プロファイルを代表アセットで検証し、人間が承認
- [x] 横断機能の採否ゲート — 14領域を採用・不採用・保留へ分類し、依存・データ・AC・再評価条件を記録
- [x] セーブデータ耐障害性・互換性 — Atomic write、Backup、Integrity、Schema migration、Cloud競合、Platform制約、旧Version fixture
- [x] Git・大容量アセット運用 — Branch戦略、LFS基準、Visible Meta Files、Force Text、UnityYAMLMerge、Asset ownershipを選択式で記録
- [x] テスト結果、ログ、スクリーンショットの保存先 — 実行成果物は`Artifacts/ValidationRuns/<RunId>`、承認済み基準は`TestBaselines`
- [x] Unity MCPで許可する書き込み操作と、人間承認が必要な操作 — 原則MCPへ委任し、依存関係・不可逆削除・Release設定・危険な任意実行のみ追加承認
