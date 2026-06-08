# Unity MCP・Codex Skills 一覧

## 採用確定

| 名称 | 種別 | 主な責務 |
|---|---|---|
| [CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp) | MCP | Unity Editor操作、Scene・GameObject・アセット・スクリプト・テストの操作 |
| [0x0funky/agent-sprite-forge](https://github.com/0x0funky/agent-sprite-forge) | Codex Skill | 2Dスプライト、アニメーションシート、マップ、プロップ、FXの生成と後処理 |

### 責務の境界

- **Unity MCP**はUnity Editorを操作する道具であり、プロジェクト固有の設計判断や完了条件は持たせない。
- **agent-sprite-forge**は画像アセットを制作する。ゲーム仕様、Unityへのインポート設定、Prefab化、ゲームへの接続はプロジェクト側で管理する。
- **プロジェクト独自Skill**には、設計書、実装規約、検証基準、成果物の配置規則など、このプロジェクトでしか分からない手順を持たせる。

### Unity MCPへ委任する操作

Unity Editor内で対応可能な操作は、原則としてUnity MCPを使う。詳細な承認境界は[Unity MCP優先方針](./unity_harness_engineering.md#unity-mcp-policy)を参照する。

2026-06-08時点のbeta版で確認した主な能力：

- Scene、GameObject、Component、Prefab、Asset、ScriptableObjectのCRUD
- C# Scriptの作成、構造化編集、Validation、Compile
- Material、Texture、Shader、Animation、Animator、Camera、Cinemachine
- UI Toolkit、uGUI構築支援、VFX、Graphics、Lighting、Physics
- ProBuilderによるEditor内モデリング
- Package、Build、Build Profile、Build Scene、Platform設定
- EditMode / PlayMode Test、Profiler、Console、Screenshot
- Play / Pause / Stop、Tag / Layer、Undo / Redo
- Menu Item、任意C#、プロジェクトCustom Toolの実行

#### 基本方針

- 承認済み設計とユーザー依頼の範囲内では、Scene・Prefab・Script・Assetの作成と変更をMCPへ広く任せる。
- Package、既存資産の削除、Build/Releaseの恒久設定、任意コードの危険な実行は追加承認の対象とする。
- MCP操作後はCompile、Console、Test、Screenshot、参照検査で検証する。
- ツール追加・仕様変更に備え、作業開始時にEditor State、Project Info、Tool Groupsを確認する。

---

## 用意するプロジェクト独自Skill

### 優先度A：最初から必要

#### 1. `maintain-game-design`

**目的:** 人間の要求やゲームレビューを、実装可能で追跡可能な設計へ変換する。

**主な処理**

1. [Unityゲーム設計書](./unity_design_sheet.md)を読む。
2. 要求を「確定仕様・実装上の決定・仮定・要確認」に分類する。
3. 影響する設計項目を特定する。
4. 設計項目ID、受け入れ条件、検証方法を追加・更新する。
5. 人間の承認が必要な変更を分離する。

**持たせるもの**

- [設計項目IDの規則](./unity_harness_engineering.md#traceability)
- [受け入れ条件の記述テンプレート](./unity_design_sheet.md#acceptance-criteria-format)
- ゲームレビューから設計変更へ変換するテンプレート
- 人間の承認が必要な変更の判定表

---

#### 2. `implement-unity-feature`

**目的:** 確定した設計項目を、既存アーキテクチャに沿って小さく実装する。

**主な処理**

1. 対象の設計項目IDと受け入れ条件を確認する。
2. 関連するコード、Scene、Prefab、ScriptableObject、テストを調査する。
3. 変更計画と回帰リスクを整理する。
4. C#、アセット、Editor設定、テストを変更する。
5. Unity MCPを使ってEditor上の作成・接続・確認を行う。

**持たせるもの**

- [Unityプロジェクトの命名規則](./unity_design_sheet.md#naming-rules)
- [Unityプロジェクトのフォルダ規則](./unity_design_sheet.md#folder-layout)
- [asmdefの分割・依存規則](./unity_design_sheet.md#asmdef-layout)
- レイヤー分離と依存方向
- Scene・Prefab・ScriptableObjectの編集方針
- `.meta`とGUIDを壊さないための制約
- 新規パッケージ導入時の承認条件

---

#### 3. `validate-unity-change`

**目的:** 変更が設計と一致し、Unityプロジェクトを壊していないことを機械的に検証する。

**主な処理**

- コンパイルエラー確認
- EditMode / PlayModeテスト実行
- Missing Script / Missing Reference検査
- Scene、Prefab、ScriptableObjectの必須参照検査
- Build Settings、Tag、Layer、Input設定の確認
- 対象プラットフォームのビルド検証
- 設計項目IDとテスト・実装の対応確認

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

1. [2Dアートプロファイル](./unity_design_sheet.md#art-profile-gate)の完了状態を確認する。
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
| `migrate-save-data` | セーブ形式と互換性ポリシーが決まった時 |
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
│  └─ skills/
│     ├─ maintain-game-design/
│     ├─ implement-unity-feature/
│     ├─ validate-unity-change/
│     ├─ report-unity-work/
│     ├─ integrate-2d-assets/
│     └─ review-gameplay/
└─ docs/
   ├─ unity_harness_engineering.md
   ├─ unity_design_sheet.md
   └─ mcp_and_skills_list.md
```

ただし、実運用では以下の3つから開始してもよい。

1. `maintain-game-design`
2. `implement-unity-feature`
3. `validate-unity-change`

`report-unity-work`は小さいため、当初は`implement-unity-feature`と`validate-unity-change`の共通出力規則に含め、繰り返し利用が確認できてから独立させてもよい。

---

## 次に決めること

- [x] 設計項目IDの正式な形式 — `<DOMAIN>-<NNN>`、発行後は変更・再利用しない
- [x] 受け入れ条件のMarkdown形式 — AC表、`<設計項目ID>-AC<NN>`、検証種別と合格条件を明記
- [x] Unityプロジェクトのパス解決方針 — 固定せず、作業開始時に調査・検証する
- [x] Unityバージョンと対象プラットフォームの決定プロセス — 既存は検出、新規は互換性調査後に人間が承認
- [x] プロジェクトの命名規則 — 英語ASCII、意味を優先したPascalCase/camelCase、永続IDは`lower-kebab-case`
- [x] プロジェクトのフォルダ構成 — 自作物は`Assets/Game`、種類別の上位構成と機能別Runtimeコード
- [x] asmdefの分割・依存規則 — Runtime、Editor、EditMode Tests、PlayMode Testsの4 Assembly
- [x] 2Dアセット設定の決定プロセス — アート方式とカテゴリ別プロファイルを代表アセットで検証し、人間が承認
- [x] テスト結果、ログ、スクリーンショットの保存先 — 実行成果物は`Artifacts/ValidationRuns/<RunId>`、承認済み基準は`TestBaselines`
- [x] Unity MCPで許可する書き込み操作と、人間承認が必要な操作 — 原則MCPへ委任し、依存関係・不可逆削除・Release設定・危険な任意実行のみ追加承認
