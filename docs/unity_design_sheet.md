# 🎮 Unity ゲーム設計書

| 項目 | 内容 |
|---|---|
| **プロジェクト名** | `________________` |
| **Unity Editor** | `________________` |
| **決定根拠** | 既存プロジェクトから検出 / 新規選定 |
| **Unityプロジェクトパス** | `________________` |
| **作成者** | `________________` |
| **作成日 / 更新日** | `____.__.__` / `____.__.__` |
| **ジャンル** | `________________` |
| **主対象プラットフォーム** | `________________` |
| **副対象プラットフォーム** | `なし / ________________` |
| **開発時検証環境** | `________________` |

> 📘 本書は **ジャンル非依存のテンプレート**。アクション / パズル / カード / ノベル・ADV / RPG / リズム / SLG・ストラテジー / シミュレーション等、いずれにも適用できる構造です。ジャンル固有の選択は各セクションに **「ジャンル別パターン」** として併記しています。

### Unityバージョン・対象プラットフォーム決定記録

実装開始前に[Unityバージョン・対象プラットフォームの決定ゲート](./unity_harness_engineering.md#platform-gate)を完了する。

| 項目 | 決定内容 |
|---|---|
| Unity Editor完全バージョン | |
| バージョンの決定理由 | |
| 主対象プラットフォーム | |
| 副対象プラットフォーム | |
| 必要なBuild Support | |
| 入力方式 | |
| 基準解像度・画面向き | |
| 目標FPS・性能予算 | |
| 配布先・ストア | |
| 必要な外部SDK | |
| 既知の制約・未決事項 | |

---

## 🆔 設計項目ID

実装・テスト・ゲームレビューへ追跡する必要がある確定仕様には、`<DOMAIN>-<NNN>`形式のIDを付ける。

```markdown
### MECH-001: 敵を倒して経験値を獲得する
```

- `NNN`はカテゴリごとに`001`から採番する。
- 発行済みIDは変更・再利用しない。
- 説明文や記入例ではなく、実装または検証の対象となる判断・振る舞い・制約へ付ける。
- 詳細な運用規則は[トレーサビリティ](./unity_harness_engineering.md#traceability)を参照する。

### DOMAIN分類

| DOMAIN | 対象 |
|---|---|
| `CONCEPT` | コンセプト、対象体験、差別化 |
| `MECH` | コアループ、ルール、勝敗、難易度、報酬 |
| `PROJECT` | プロジェクト構造、フォルダ、命名 |
| `GRAPHICS` | 2D/3D、Render Pipeline、カメラ、ライト、VFX |
| `ARCH` | レイヤー、依存、DI、イベント |
| `FLOW` | ゲーム状態、画面・Scene遷移 |
| `SAVE` | セーブ、ロード、互換性 |
| `SCENE` | Scene一覧、GameObject階層 |
| `PREFAB` | Prefabの責務と構成 |
| `DATA` | ScriptableObject、マスターデータ |
| `COMPONENT` | 共通・個別Component |
| `CONTROL` | プレイヤー・対象制御、Animator |
| `TIME` | 時間軸、Timeline、演出進行 |
| `INPUT` | 入力アクションとデバイス対応 |
| `UI` | HUD、メニュー、画面レイアウト |
| `PHYSICS` | Tag、Layer、衝突規則 |
| `ASSET` | Addressables、アセット読込・解放 |
| `AUDIO` | BGM、SE、Voice、AudioMixer |
| `BUILD` | ビルド対象、品質、配布設定 |
| `NET` | ネットワーク同期 |
| `LOCALIZE` | ローカライズ |
| `PERF` | FPS、メモリ、ロード時間などの性能予算 |
| `DEBUG` | デバッグ機能、ログ、チート操作 |
| `XR` | VR / AR |

新しいDOMAINは、既存分類で表現できない場合のみ追加する。

<a id="acceptance-criteria-format"></a>

### 受け入れ条件の記述形式

設計項目ごとに、仕様本文の直後へ次の表を置く。

```markdown
### MECH-001: 敵を倒して経験値を獲得する

**仕様**

敵を倒したプレイヤーへ、敵データに設定された経験値を加算する。

#### 受け入れ条件

| AC ID | 状態 | 検証種別 | 合格条件 | 検証方法 |
|---|---|---|---|---|
| `MECH-001-AC01` | `有効` | `AUTO:EDIT` | 経験値10の敵を倒すと、プレイヤーの経験値が10増加する | EditModeテスト |
| `MECH-001-AC02` | `有効` | `AUTO:PLAY` | 敵撃破時に経験値表示が更新される | PlayModeテスト |
| `MECH-001-AC03` | `有効` | `MANUAL:PLAY` | 通常プレイで撃破から表示更新までを確認できる | 指定Sceneで人間がプレイ確認 |
```

#### AC ID

- 形式は`<設計項目ID>-AC<NN>`とする。例：`MECH-001-AC01`
- `NN`は設計項目ごとに`01`から採番する。
- 発行済みAC IDは変更・再利用しない。
- 不要になった条件は削除せず、状態を`廃止`にする。

#### 検証種別

| 値 | 用途 |
|---|---|
| `AUTO:STATIC` | コンパイル、静的解析、規約検査 |
| `AUTO:EDIT` | EditModeテスト |
| `AUTO:PLAY` | PlayModeテスト |
| `AUTO:ASSET` | Scene、Prefab、ScriptableObject、参照の検査 |
| `AUTO:BUILD` | 対象プラットフォームのビルド検証 |
| `MANUAL:EDITOR` | Inspector、Hierarchy、見た目などのEditor確認 |
| `MANUAL:PLAY` | 操作感、分かりやすさ、演出などの人間によるプレイ確認 |

#### 記述ルール

- 一つの行には、一つの観察可能な合格条件だけを書く。
- 可能な限り具体的な入力、操作、数値、結果を含め、合否を二択で判定可能にする。
- 内部実装ではなく、外部から確認できる振る舞いを優先する。ただし`ARCH`や`PROJECT`など構造自体が仕様の場合は例外とする。
- 「正常に動く」「適切」「いい感じ」など、判定基準が不明な表現を使わない。
- 人間の感覚判断が必要な条件は`MANUAL:PLAY`とし、確認するScene、操作、観点を検証方法へ書く。
- 設計書の表は合格条件の定義であり、実行結果ではないためチェックボックスにしない。実行結果は作業レポートへ記録する。
- 確定仕様では、`有効`な条件の検証種別と検証方法を空欄にしない。

---

## 📑 目次

- [🆔 設計項目ID](#-設計項目id)
- [受け入れ条件の記述形式](#受け入れ条件の記述形式)
- [🧭 設計の進め方 — 順番と並行関係](#-設計の進め方--順番と並行関係)
- [0. Unity 基本概念 — 6つのキーワード](#0-unity-基本概念--6つのキーワード)

**🎯 Phase 1: 企画 — What を決める**
- [1. コンセプト — このゲームは何か](#1-コンセプト--このゲームは何か)
- [2. ゲーム仕様 — メカニクス / サイクル](#2-ゲーム仕様--メカニクス--サイクル)

**🏗️ Phase 2: 技術選定（並行可）**
- [3. プロジェクト構造 — 階層 / フォルダ / 命名](#3-プロジェクト構造--階層--フォルダ--命名)
- [4. グラフィック方針 — 2D/3D / Render Pipeline / カメラ / ライト](#4-グラフィック方針--2d3d--render-pipeline--カメラ--ライト)
- [5. アーキテクチャ — クラス依存 / DI / イベント設計](#5-アーキテクチャ--クラス依存--di--イベント設計)

**🔄 Phase 3: フロー設計（並行可）**
- [6. ゲーム進行ステートマシン](#6-ゲーム進行ステートマシン)
- [7. シーンフロー — 読まれる順番](#7-シーンフロー--読まれる順番)
- [8. Save / Load — 2種類を分ける](#8-save--load--2種類を分ける)

**🎬 Phase 4: シーン中身を設計する**
- [9. Scene 一覧](#9-scene-一覧)
- [10. Scene 内 GameObject 階層 — 親要素ごと（ジャンル別パターン）](#10-scene-内-gameobject-階層--親要素ごとジャンル別パターン)
- [11. Prefab — 再利用テンプレート](#11-prefab--再利用テンプレート)
- [12. データ層 — ScriptableObject](#12-データ層--scriptableobject)

**⚙️ Phase 5: 挙動を組む（並行可）**
- [13. Component と共通スクリプト](#13-component-と共通スクリプト)
- [14. プレイヤー操作・対象制御 — ジャンル別](#14-プレイヤー操作対象制御--ジャンル別)
- [15. 時間軸 — Lifecycle と Timeline](#15-時間軸--lifecycle-と-timeline)
- [16. 入力層 / UI 層](#16-入力層--ui-層)

**🌐 Phase 6: 横断ルール（常時意識）**
- [17. Tag / Layer / 衝突マトリクス](#17-tag--layer--衝突マトリクス)
- [18. アセット読み込み — Addressables](#18-アセット読み込み--addressables)
- [19. プロジェクト規約 — Audio / Git / ビルド](#19-プロジェクト規約--audio--git--ビルド)

- [付録A：ジャンル別 追加検討項目](#付録aジャンル別-追加検討項目)
- [付録B：ジャンル別 設計チェックリスト](#付録bジャンル別-設計チェックリスト)

---

## 🧭 設計の進め方 — 順番と並行関係

> セクション番号は **「アイデアを考える順番」** に並んでいる。ただしすべて直列ではない。**Phase内のセクションは並行で進めて良い**。

```
┌─ Phase 1: 企画 ────────────────────────┐
│  1. コンセプト                          │ ← 最上流。何を作るかを言語化
│  2. ゲーム仕様（コアメカニクス）         │ ← ここが決まらないと先に進めない
└────────────┬───────────────────────────┘
             ▼
┌─ Phase 2: 技術選定（3つを並行検討）─────┐
│  3. プロジェクト構造                    │
│  4. グラフィック方針（2D/3D・RP）        │ ← まず「2Dか3Dか」を確定
│  5. アーキテクチャ（DI / イベント）      │
└────────────┬───────────────────────────┘
             ▼
┌─ Phase 3: フロー設計（3つを並行）───────┐
│  6. ゲーム進行ステートマシン            │
│  7. シーンフロー                        │ ← 6と7は表裏一体
│  8. Save / Load                        │
└────────────┬───────────────────────────┘
             ▼
┌─ Phase 4: シーン中身（順次）────────────┐
│  9. Scene 一覧                          │
│  10. Scene 内 GameObject 階層           │ ← Sceneごとに親要素単位で記載
│  11. Prefab                            │
│  12. データ層 ScriptableObject          │
└────────────┬───────────────────────────┘
             ▼
┌─ Phase 5: 挙動を組む（並行）────────────┐
│  13. Component と共通スクリプト         │ ← 共通ロジックの抽出
│  14. プレイヤー操作・対象制御           │ ← ジャンルにより選択
│  15. 時間軸 / Timeline                  │
│  16. 入力 / UI                          │
└────────────┬───────────────────────────┘
             ▼
┌─ Phase 6: 横断ルール（常時意識）────────┐
│  17. Tag / Layer / 衝突マトリクス       │
│  18. Addressables                       │
│  19. プロジェクト規約                   │
└─────────────────────────────────────────┘
```

### 🔁 行ったり来たりして良い箇所

- Phase 4（シーン中身）を考えると Phase 2（アーキテクチャ）の見直しが発生しがち → **戻ってOK**
- Phase 5（挙動）を組むと Phase 2（仕様）の数値調整が入る → **戻ってOK**
- Phase 6 は最後ではなく **Phase 2 の時点から並行して育てる**（特に Tag/Layer / フォルダ規約）

---

## 0. Unity 基本概念 — 6つのキーワード

> Unity というエンジンの **登場用語** を6語で把握する。設計書全体で繰り返し登場する語の意味を揃えておくセクション。**ゲーム内容の記入欄ではない**（コンセプトはセクション1へ）。

| キーワード | 役割（一言） | 比喩 |
|---|---|---|
| **Project** | 全アセットと設定の器 | 世界 |
| **Scene** | ステージ・画面の単位（重ねてロード可） | ステージ |
| **GameObject** | 登場物すべて。親子の階層を持つ箱 | 登場人物 |
| **Component** | 箱に挿す部品。機能の正体 | 能力 |
| **ScriptableObject** | 設定データの器。シーン外に住む | 設定資料 |
| **Prefab** | 再利用の型紙。量産と一括修正 | 量産型紙 |

---

# 🎯 Phase 1: 企画 — What を決める

## 1. コンセプト — このゲームは何か

> このゲームの **「What」と「Why」** を1ページで定義するセクション。続くセクション2以降のあらゆる判断の拠り所になる。**ここが曖昧だと後工程すべてがブレる**。

### 1.1 ▼ 記入テンプレート（コンセプト）

```
タイトル（仮）            :
ジャンル                  : 例）2Dパズル / 3Dアクション / カードゲーム / ノベルADV
ターゲット層              : 例）コアゲーマー / カジュアル / 子供向け / 大人向け
1行で説明すると           : 「__するゲーム」
プレイヤーが感じる体験    : 例）爽快感 / 達成感 / 探索の楽しさ / 物語への没入
セールスポイント（3つ）   :
  1.
  2.
  3.
類似タイトル（参考）      : 例）〇〇 / △△
本作の差別化要素          :
プレイ時間の目安          : 1プレイ__分 / 全クリア__時間
```

### 1.2 ▼ 記入テンプレート（ジャンル分類 — 技術選定に直結する分類）

> このゲームが **どのカテゴリに属するか** を複数の軸で押さえる。Phase 2 以降の技術選定がここで自動的に決まる。

| 分類軸 | 選択肢 | 本作の選択 |
|---|---|---|
| **次元** | 2D / 2.5D / 3D | |
| **視点** | 一人称 / 三人称 / 俯瞰 / トップダウン / サイドビュー / 固定画面 | |
| **時間軸** | リアルタイム / ターン制 / イベント駆動（テキスト送り） / リズム同期 | |
| **主操作** | 移動・物理 / 配置・選択 / ドラッグ&ドロップ / タッチタイミング / コマンド選択 | |
| **多人数性** | シングル / ローカルマルチ / オンラインマルチ / 非同期マルチ | |
| **ステージ性** | ステージ制 / オープンワールド / ローグライク / 1画面完結 / 章立て | |
| **進行** | 線形 / 分岐 / 自由 / ループ | |

### 1.3 ▼ 記入テンプレート（勝利条件・終了条件）

```
勝利・成功条件            :
失敗・終了条件            :
リプレイ性                : 例）ハイスコア更新 / 周回要素 / ランダム生成
```

---

## 2. ゲーム仕様 — メカニクス / サイクル

> セクション1のコンセプトを **「実装可能なルール」** にまで落とし込む層。**ここが決まらないと Phase 2 以降に進めない**。

### 2.1 ゲームサイクル（1プレイの流れ）

```
[開始] → [中核アクション] → [成功 or 失敗] → [報酬 / 次の試行] → [終了 or 継続]
```

### 2.2 ▼ 記入テンプレート（コアメカニクス）

```
中核アクション            : 例）"移動して敵を倒す" / "ピースを揃える" / "カードを場に出す" / "選択肢を選ぶ"
プレイヤーの目的          :
失敗条件                  : 例）HP 0 / 手詰まり / 制限時間切れ / 山札切れ
成功条件                  : 例）ゴール到達 / 全消し / 相手LP 0 / エンディング到達
1試行の想定時間           : __秒〜__分
試行の繰り返し方          : リトライ / 次のステージ / ターン継続 / 章進行
```

### 2.3 ▼ 記入テンプレート（パラメータ・計算式）

> 数値の設計。ジャンルにより内容が大きく変わる。

| パラメータ | 値・式 | 備考 |
|---|---|---|
| 例）プレイヤーHP | 100 | アクション・RPG |
| 例）スコア計算 | `score = base * combo` | アクション・パズル・リズム |
| 例）ターン上限 | 30 | パズル・SLG |
| 例）山札枚数 | 40 | カード |
| 例）BPM | 140 | リズム |
| 例）選択肢数 / フラグ数 | 3択 / 12フラグ | ノベル・ADV |
| `________` | `________` | `________` |

### 2.4 ▼ 記入テンプレート（進行・難易度カーブ）

| 区切り | 解放条件 | 難易度・複雑度 | 報酬 / 解放要素 |
|---|---|---|---|
| Stage01 / Lv1 / 第1章 | 初期解放 | 易 | チュートリアル / 100G |
| Stage02 / Lv2 / 第2章 | 前段クリア | 中 | 新ユニット / 新カード |
| `________` | `________` | `________` | `________` |

---

# 🏗️ Phase 2: 技術選定 — How の大方針

> セクション 3・4・5 は **並行で検討してOK**。ただし **「4. 2D/3D と Render Pipeline」を最優先で確定** すること（後から変えるとコストが大きい）。

## 3. プロジェクト構造 — 階層 / フォルダ / 命名

> 「シーンの中にオブジェクト、オブジェクトの中にコンポーネント」が基本三層。データ層は別系統。

```
Project（プロジェクト＝世界）
├─ Project Settings        物理・入力・品質・ビルド対象
└─ Assets（素材庫）
    ├─ Scenes ──► 実行時にロード
    │   └─ Scene（ステージ／画面）
    │       └─ GameObject（親子で階層化）
    │           ├─ Transform（必須・位置/回転/スケール）
    │           ├─ Renderer / Collider / Rigidbody …
    │           ├─ Script (C#)        ロジック：Update軸
    │           └─ PlayableDirector   Timeline軸：演出
    ├─ Prefabs（再利用テンプレート）
    ├─ ScriptableObjects（データ層・設定）
    ├─ Scripts / Models / Textures / Audio / Materials
    └─ Timeline / UI / Input
```

<a id="naming-rules"></a>

### 3.1 標準命名規則

この規則は、プロジェクトごとの明確な理由がない限り標準として使用する。既存プロジェクトでは、全面改名によるGUID・参照・履歴への影響を避け、変更対象と新規作成物から段階的に適用する。

#### 共通原則

- 技術識別子、ファイル名、アセット名は**英語ASCII**で記述する。日本語は表示テキストとローカライズデータに限定する。
- 名前から責務や内容を推測できる、短く具体的な名詞または動詞を使う。
- 同じ概念には同じ単語を使い、類義語を混在させない。例：`Enemy`と`Foe`を混在させない。
- 意味が伝わらない独自省略語を避ける。一般的な技術・ゲーム用語は単語として扱う。例：`PlayerId`、`UiController`、`HudView`、`JsonLoader`
- 技術名、ファイル名、アセット名ではスペース、全角文字、ハイフンを使用しない。後述する安定文字列IDは例外とする。
- アンダースコアはテストメソッド名と外部仕様で要求される名前を除き使用しない。
- 連番は末尾に2桁のゼロ埋めで付ける。100件以上を前提とする場合のみ3桁にする。例：`Stage01`、`SpawnPoint03`
- `New`、`Temp`、`Final`、`Latest`、`Copy`、`Test1`など、意味や寿命が不明な名前を正式な成果物へ使用しない。
- 型や拡張子から明らかな情報を重複させない。Prefabに`Prefab`、Sceneに`Scene`を機械的に付けない。

#### C#識別子

| 対象 | 形式 | 例 |
|---|---|---|
| Namespace | `<RootNamespace>.<Feature>[.<Layer>]` | `MyGame.Combat.Domain` |
| class / struct / record | PascalCase | `PlayerController`, `DamageResult` |
| interface | `I` + PascalCase | `IDamageable` |
| enum / enum member | 単数形PascalCase | `GameState.Playing` |
| method | 動詞を含むPascalCase | `ApplyDamage`, `LoadStageAsync` |
| async method | PascalCase + `Async` | `SaveGameAsync` |
| property | PascalCase | `CurrentHealth` |
| event | 状態・発生事実のPascalCase | `HealthChanged`, `StageCleared` |
| event handler | `On` + event名 | `OnHealthChanged` |
| private field | `_camelCase` | `_currentHealth` |
| `[SerializeField]` field | `private _camelCase` | `[SerializeField] private int _maxHealth;` |
| parameter / local variable | camelCase | `damageAmount`, `spawnPosition` |
| constant / static readonly | PascalCase | `DefaultCapacity`, `EmptyResult` |
| boolean | `is` / `has` / `can` / `should` + 状態 | `isAlive`, `hasSaveData` |
| generic type parameter | `T`または`T` + 意味 | `T`, `TItem` |
| test class | 対象型 + `Tests` | `PlayerHealthTests` |
| test method | `Method_WhenCondition_ExpectedResult` | `TakeDamage_WhenLethal_SetsIsAliveFalse` |

C#ファイル名は主要なpublic型と完全一致させ、原則として一つのファイルに一つのpublic型を置く。

`Manager`は、サブシステム全体の調停やライフサイクル管理を担う場合に限定する。より具体的な責務を表せる場合は、`Loader`、`Service`、`Repository`、`Factory`、`Controller`、`Presenter`、`View`などを使う。

#### Unityファイル・アセット

| 対象 | 形式 | 例 |
|---|---|---|
| Folder | 内容を表すPascalCase。コレクションは複数形 | `Scenes`, `Scripts`, `Prefabs` |
| Scene | 役割または内容を表すPascalCase | `Bootstrap`, `MainMenu`, `Stage01Forest` |
| Prefab | 対象 + 必要な役割・バリアント | `Player`, `EnemyGoblin`, `PrimaryButton` |
| ScriptableObject型 | 用途に応じて`Definition` / `Config` | `EnemyDefinition`, `GameBalanceConfig` |
| ScriptableObjectアセット | 内容 + 種別 | `GoblinEnemy`, `DefaultGameBalance` |
| Material | 対象 + 用途 + `Material` | `PlayerBodyMaterial` |
| Texture | 対象 + 用途 | `PlayerBodyAlbedo`, `ForestBackground` |
| Sprite sheet | 対象 + action + `Sheet` | `PlayerRunSheet` |
| AnimationClip | 対象 + action | `PlayerIdle`, `GoblinAttack` |
| AnimatorController | 対象 + `Animator` | `PlayerAnimator` |
| AudioClip | 内容 + 種別 | `TitleBgm`, `PlayerJumpSfx` |
| VFX / Particle | 内容 + `Vfx` | `FireImpactVfx` |
| Input Action Map | 操作コンテキスト | `Gameplay`, `Menus` |
| Input Action | 操作を表すPascalCase | `Move`, `Attack`, `Submit` |
| asmdef | `<RootNamespace>.<Feature>[.<Role>]` | `MyGame.Combat`, `MyGame.Combat.Editor` |
| asmdefテスト | 対象assembly + テスト種別 | `MyGame.Combat.Tests.EditMode` |

`<RootNamespace>`は新規プロジェクト開始時に決定する。会社名や製品名が未確定の場合でも、意味のない`DefaultCompany`や`NewProject`は使用しない。

#### GameObject・Hierarchy

- GameObjectはPascalCaseで、個体は単数形、グループ親は複数形にする。例：`Player`、`Enemies`、`SpawnPoints`
- Scene直下の整理用ルートは責務で命名する。例：`Systems`、`World`、`Actors`、`Cameras`、`Ui`
- 同種の個体を識別する必要がある場合のみ連番または役割を付ける。例：`EnemyGoblin03`、`BossSpawnPoint`
- Unityが自動生成する`(1)`付き名称を正式な状態で残さない。
- コンポーネント名を並べただけの名前より、Scene内での役割を優先する。例：`MainCamera`、`DialogueTextBox`

#### 安定した文字列ID

セーブデータ、Addressables、外部データなどで永続化されるIDは、表示名やアセット名と分離し、`lower-kebab-case`を使う。

```text
enemy-goblin
stage-01-forest
item-health-potion
```

発行済みIDは、表示名やファイル名を変更しても変更・再利用しない。

<a id="folder-layout"></a>

### 3.2 標準フォルダ構成

自作アセットは`Assets/Game`へ集約する。上位は種類別に分け、スクリプト内部は責務・機能別に分ける。使用しないフォルダは作成しない。

```text
Assets/
├─ Game/                         自作アセット
│   ├─ Art/
│   │   ├─ Animations/
│   │   ├─ Materials/
│   │   ├─ Models/
│   │   ├─ Shaders/
│   │   ├─ Sprites/
│   │   ├─ Textures/
│   │   └─ Vfx/
│   ├─ Audio/
│   │   ├─ Music/
│   │   ├─ Sfx/
│   │   └─ Voice/
│   ├─ Data/
│   │   ├─ Configs/
│   │   ├─ Definitions/
│   │   └─ Localization/
│   ├─ Prefabs/
│   │   ├─ Actors/
│   │   ├─ Environment/
│   │   ├─ Gameplay/
│   │   └─ Ui/
│   ├─ Scenes/
│   │   ├─ Bootstrap/
│   │   ├─ Gameplay/
│   │   ├─ Menus/
│   │   └─ Sandboxes/
│   ├─ Scripts/
│   │   ├─ Runtime/
│   │   │   ├─ <RootNamespace>.Runtime.asmdef
│   │   │   ├─ Core/
│   │   │   ├─ Features/
│   │   │   │   └─ <Feature>/
│   │   │   └─ Shared/
│   │   └─ Editor/
│   │       └─ <RootNamespace>.Editor.asmdef
│   ├─ Settings/
│   │   ├─ Audio/
│   │   ├─ Input/
│   │   └─ Rendering/
│   ├─ Tests/
│   │   ├─ EditMode/
│   │   │   └─ <RootNamespace>.Tests.EditMode.asmdef
│   │   └─ PlayMode/
│   │       └─ <RootNamespace>.Tests.PlayMode.asmdef
│   ├─ Timelines/
│   └─ Ui/
│       ├─ Documents/
│       ├─ Fonts/
│       ├─ Icons/
│       └─ Styles/
├─ ThirdParty/                   手動導入した外部アセット
├─ Plugins/                      UnityまたはSDKが要求するネイティブPlugin
├─ StreamingAssets/              原文のままビルドへ含めるファイル
└─ Gizmos/                       Editor用Gizmo画像

Packages/
└─ com.<company>.<package>/       自作・埋め込みUPM packageが必要な場合のみ

TestBaselines/                    承認済み回帰基準。Git管理
├─ Screenshots/
├─ Data/
└─ Metadata/

Artifacts/                        テスト・ログ・画像などの生成物。Git管理外
└─ ValidationRuns/
```

#### フォルダの責務

| フォルダ | 入れるもの | 入れないもの |
|---|---|---|
| `Art` | 描画用アセット | Prefab、ゲーム設定データ |
| `Audio` | BGM、効果音、音声 | AudioMixerや音量設定は`Settings` |
| `Data` | ScriptableObjectアセット、マスターデータ、ローカライズデータ | C#型定義 |
| `Prefabs` | 再利用するGameObjectテンプレート | Scene専用で再利用しないGameObject |
| `Scenes` | 実行・検証するScene | Scene内でのみ使う一時ファイルの乱雑な保管 |
| `Scripts/Runtime` | ビルドへ含めるC# | Editor APIへ依存するコード |
| `Scripts/Editor` | Editor拡張、Importer、検証ツール | ランタイムコード |
| `Settings` | Input、Rendering、AudioMixerなどのプロジェクト用設定アセット | ゲーム内容を表すマスターデータ |
| `Tests` | EditMode / PlayModeテスト | 本番実装 |
| `Ui` | UI Toolkit文書・スタイル、フォント、アイコン | UI用Prefabは`Prefabs/Ui` |
| `ThirdParty` | 手動導入した外部製品 | 自作コード、Package Manager管理物 |

#### 分割ルール

- 最上位へ機能名フォルダを増やさず、まず上記カテゴリへ配置する。
- `Scripts/Runtime/Features/<Feature>`は、プレイヤーから見える機能または独立した業務領域で分ける。例：`Combat`、`Inventory`、`Dialogue`
- 複数機能から使うコードは、ゲーム起動・基盤なら`Core`、小さな再利用部品なら`Shared`へ置く。
- `Common`、`Misc`、`Others`、`Temp`のように責務が広がり続けるフォルダは作らない。
- 一つの機能にアセットが増えた場合、各カテゴリ配下で同じ機能名を使う。例：`Prefabs/Combat`、`Art/Sprites/Combat`
- Sceneは用途で分類する。`Sandboxes`は開発用の隔離Sceneに限定し、リリース用Build Profileへ含めない。
- フォルダ階層は必要以上に深くしない。`Scripts/Runtime/Features/<Feature>`など責務を明確にする場合を除き、`Game`配下4階層程度を目安にする。

#### Unity予約・生成フォルダ

- `Resources`は依存関係が見えにくくなるため原則使用しない。外部SDKまたは明確な実行時要件がある場合のみ、必要最小限で使用する。
- `StreamingAssets`、`Plugins`、`Gizmos`などUnityが意味を持つ名前は、用途を理解した場合のみ作成する。
- `AddressableAssetsData`などツールが生成・管理するフォルダは、手作業で移動・整理しない。
- `Library`、`Temp`、`Logs`、`Obj`、`Builds`、`Artifacts`は`Assets`へ入れず、Git管理対象から除外する。

#### 外部アセット

- Package Managerで導入できる依存は`Packages`で管理し、`Assets`へコピーしない。
- 手動導入アセットは原則`Assets/ThirdParty/<VendorOrProduct>`へ置く。
- 外部アセットが固定パスや独自構造を要求する場合は移動せず、その構造を尊重する。
- 外部アセットのファイルを直接改変せず、自作のAdapterや設定を`Assets/Game`側へ置く。
- ライセンス、バージョン、導入元を追跡できるようにする。

#### 適用方針

- 新規プロジェクトはこの構成から開始する。
- 既存プロジェクトでは現状を調査し、参照切れや大規模差分を発生させてまで一括移行しない。
- ファイル移動はUnity EditorまたはUnity MCP経由で行い、`.meta`とGUIDを維持する。
- フォルダ構成を変更した場合は、asmdef、Namespace、Addressables、Build Profile、外部データのパス参照を検証する。

<a id="asmdef-layout"></a>

### 3.3 最小asmdef構成

新規プロジェクトは次の4 Assemblyから開始する。機能単位のasmdefは、必要性が確認されるまで追加しない。

```text
<RootNamespace>.Editor             ──→ <RootNamespace>.Runtime
<RootNamespace>.Tests.EditMode     ──→ <RootNamespace>.Runtime
<RootNamespace>.Tests.PlayMode     ──→ <RootNamespace>.Runtime
```

正確な依存関係：

```text
Runtime            → Unity API、採用Package
Editor             → Runtime、UnityEditor API
Tests.EditMode     → Runtime
Tests.PlayMode     → Runtime
```

`Tests.EditMode`がEditor拡張自体をテストする場合のみ、例外として`Editor`も参照する。

#### 配置と設定

| Assembly | asmdef配置先 | 参照 | Platform | Test Assemblies |
|---|---|---|---|---|
| `<RootNamespace>.Runtime` | `Assets/Game/Scripts/Runtime` | 必要なUnity Packageのみ | Any Platform | 無効 |
| `<RootNamespace>.Editor` | `Assets/Game/Scripts/Editor` | `Runtime` | Editorのみ | 無効 |
| `<RootNamespace>.Tests.EditMode` | `Assets/Game/Tests/EditMode` | `Runtime` | Editorのみ | 有効 |
| `<RootNamespace>.Tests.PlayMode` | `Assets/Game/Tests/PlayMode` | `Runtime` | Any Platform | 有効 |

#### 共通設定

- asmdefのファイル名とAssembly Nameを一致させる。
- Root Namespaceには同じ`<RootNamespace>`を設定する。
- プロジェクト内asmdefへの参照は、名称変更に強いGUID参照を使用する。
- `Allow Unsafe Code`は無効とし、必要な場合だけ理由と対象範囲を記録して有効化する。
- `Override References`は無効から開始する。
- `No Engine References`は無効から開始する。Pure C# Assemblyへの分離を行う場合にのみ再検討する。
- `Auto Referenced`はRuntimeとEditorで有効とする。テストAssemblyは本番コードから参照しない。
- Test Framework Packageを導入し、テストasmdefでは`Test Assemblies`を有効にする。
- Package参照やDefine Constraintsは、実際に必要になった時だけ追加する。

#### 依存方向

- RuntimeはEditorとTestsを参照してはならない。
- EditorはRuntimeを参照できる。
- Testsはテスト対象を参照できるが、RuntimeとEditorはTestsを参照してはならない。
- PlayModeテストはEditor Assemblyおよび`UnityEditor` APIへ依存させない。
- 外部Packageへの参照は使用するAssemblyだけに追加する。
- asmdef間の循環参照は禁止する。

#### 機能別asmdefへ分割する条件

次のいずれかが実際の問題として確認された場合のみ、追加分割を検討する。

- コンパイル時間を計測し、特定機能の変更による再コンパイル範囲が問題になっている。
- 依存方向をコンパイラで強制しなければ、レイヤー違反を防げない。
- 独立したPackage、SDK、サンプル、再利用ライブラリとして切り出す必要がある。
- 対応プラットフォームやDefine Constraintsが他のコードと異なる。
- チーム所有範囲が明確に分かれ、独立した公開APIが存在する。

単にフォルダが増えた、ファイル数が多いという理由だけでは分割しない。分割時は人間の承認を得て、依存図、参照先、テストAssemblyへの影響を更新する。

---

## 4. グラフィック方針 — 2D/3D / Render Pipeline / カメラ / ライト

> **最初に「2Dか3Dか」**を決める。2D系では続けてアートプロファイルを決定し、Render Pipeline、カメラ、ライトへ進む。後から変更すると既存アセットへの影響が大きい。

### 4.1 2D / 3D の選択

| 種別 | 採用 | 主なコンポーネント | 適性ジャンル例 |
|---|---|---|---|
| **2D（スプライト）** | ☐ | SpriteRenderer / Tilemap / 2D Physics | パズル / カード / 2Dアクション / ノベル |
| **2.5D** | ☐ | 3D空間に2D配置 | 横スクロールアクション / 一部RPG |
| **3D** | ☐ | MeshRenderer / 3D Physics | 3Dアクション / FPS / TPS / レース |
| **UIのみ（CanvasベースGame）** | ☐ | Canvas / UI Toolkit のみ | カード / 育成 / クリッカー / ノベル |

<a id="art-profile-gate"></a>

### 4.2 2Dアートプロファイル決定ゲート

2D、2.5D、または画像中心のUIゲームでは、大量のアセット制作前にアート方式とUnity取込プロファイルを決定する。PPUなどの値はハーネスで固定せず、プロジェクトの見た目、カメラ、対象端末に合わせて決める。

#### 決定プロセス

1. **前提を確認する**
   - アート方式：Pixel Art / 通常ラスターイラスト / ベクター中心 / 複合
   - 視点、カメラ投影、基準解像度、画面向き、対象プラットフォーム
   - Pixel Perfectの要否、拡大縮小の範囲、想定する最大表示サイズ
2. **代表アセットを用意する**
   - プレイヤーまたは主要キャラクター
   - 背景またはタイル・地形
   - 小物
   - アニメーション
   - エフェクト
   - UIアイコンまたはボタン
3. **候補プロファイルを作る**
   - アセットカテゴリごとに、解像度、PPU、Pivot、Filter Mode、圧縮などを設定する。
4. **Unity上で比較する**
   - 基準Sceneへ配置し、実際のカメラ、基準解像度、最小・最大表示倍率で確認する。
   - アニメーションの位置ずれ、輪郭のぼけ、透明境界、メモリ、Atlas化後の表示を確認する。
5. **人間が見た目を承認する**
   - Codexは比較結果と推奨案を提示するが、最終的なアート品質は人間が判断する。
6. **設計書へ記録して自動化する**
   - 承認された値を下記プロファイル表へ記録する。
   - `integrate-2d-assets`がTextureImporterへ同じ設定を適用できるようにする。
7. **サンプルを回帰基準として保存する**
   - 承認済みSceneまたは`TestBaselines/Screenshots`の画像を、後続アセットの比較基準にする。

#### プロファイルの単位

一つのグローバル設定ですべてを扱わず、必要なカテゴリごとにプロファイルを作る。

| 推奨カテゴリ | 主な対象 |
|---|---|
| `Characters` | プレイヤー、敵、NPC |
| `Environment` | 背景、タイル、地形、小物 |
| `Effects` | 攻撃、魔法、ヒット、パーティクル用画像 |
| `Ui` | アイコン、ボタン、パネル、装飾 |

カテゴリ内で同じ用途・表示条件なら同じプロファイルを共有する。アセット一枚ごとの例外設定は避け、必要なら理由のあるサブカテゴリを追加する。

#### 2Dアートプロファイル記録

| 項目 | 決定内容 |
|---|---|
| アート方式 | |
| Pixel Perfect | 使用 / 不使用 |
| 基準解像度・画面向き | |
| 基準カメラ・表示倍率 | |
| 承認用Scene | |
| 承認者・承認日 | |

| Profile | 対象 | 基準解像度・フレームサイズ | PPU | Pivot | Filter | Compression | Mipmap | Wrap | Mesh | Sprite Mode | Atlas | Animation FPS |
|---|---|---|---:|---|---|---|---|---|---|---|---|---:|
| `Characters` | | | | | | | | | | | | |
| `Environment` | | | | | | | | | | | | |
| `Effects` | | | | | | | | | | | | |
| `Ui` | | | | | | | | | | | | |

#### 初期候補の考え方

以下は選定開始時の候補であり、プロジェクトの確定値ではない。

| アート方式 | Filter候補 | PPUの決め方 | Mipmap候補 | 圧縮方針 |
|---|---|---|---|---|
| Pixel Art | Point | タイルまたは基準キャラクターのピクセル寸法から決定 | 原則無効 | 輪郭が変化しない設定を優先 |
| 通常ラスターイラスト | Bilinear | Unity空間上の基準サイズと最大表示解像度から決定 | 2D固定表示では原則無効 | 対象端末で画質と容量を比較 |
| ベクター中心UI | UI方式に合わせる | Spriteとして使う場合のみ決定 | 原則無効 | UIの表示倍率と端末密度で検証 |
| 複合 | カテゴリ別 | カテゴリ別 | カテゴリ別 | カテゴリ別 |

#### Pivotの基準候補

| 対象 | Pivot候補 |
|---|---|
| 地面に立つキャラクター・設置物 | Bottom Center |
| 弾、アイコン、放射状エフェクト | Center |
| タイル | タイル配置方式に合わせて統一 |
| UI | RectTransformのレイアウト基準に合わせる |

Sprite sheetでは、全フレームで同じセル寸法とPivotを使い、アニメーション中の見かけの基準点が動かないことを確認する。

#### 完了条件

- アート方式とPixel Perfectの要否が決まっている。
- 使用する全カテゴリのプロファイル表が埋まっている。
- 代表アセットを実際のカメラと対象解像度で確認している。
- agent-sprite-forgeの出力寸法・シート構成とUnityのスライス規則が一致している。
- 人間が見た目を承認している。
- 後続アセットへ同じ設定を再適用できる。

このゲートが未完了の場合、量産アセットの生成、Sprite Atlasの本構成、AnimationClipの大量作成を開始しない。

### 4.3 Render Pipeline

| RP | 用途 | 備考 |
|---|---|---|
| **Built-in** | レガシー資産流用時 | 採用Unityバージョンと資産互換性を確認 |
| **URP** | モバイル・スイッチ・軽量PC・2D | 2D Rendererにも対応。対象環境との互換性を確認 |
| **HDRP** | ハイエンドPC / 据置機の高画質3D | モバイル不可・2D不向き |

### ▼ 記入テンプレート

```
採用パイプライン      : URP / HDRP / Built-in
2D Renderer 使用      : する / しない（2Dゲームならする）
Renderer Feature      : 例）Decal, SSAO, Render Objects, 2D Light
Quality Level         : 低 / 中 / 高（プラットフォーム別）
Color Space           : Linear / Gamma
シェーダー方針        : Shader Graph 中心 / 一部 HLSL 手書き
VFX                   : Particle System / VFX Graph
```

### 4.4 カメラ設計

| 項目 | 選択肢 |
|---|---|
| Cinemachine 使用 | する / しない（固定カメラなら不要） |
| Cinemachine Package | 未使用 / `com.unity.cinemachine`の正確な導入バージョン |
| カメラの動き | 固定 / 追従 / 切替 / ズーム / プレイヤー操作 |
| カメラ視点 | 2D固定 / 2D追従(横スク) / 俯瞰 / トップダウン / 3D追従(TPS) / FPS / 等角投影 |
| 投影 | Perspective / Orthographic（2D・トップダウンは Orthographic） |
| ポストエフェクト | Volume + Post Processing（Bloom / DOF / ColorGrading）|
| 視野角(FOV) / Ortho Size | |

### ▼ 記入テンプレート（カメラ一覧）

| カメラ名 | 用途 | 仕組み | Priority |
|---|---|---|---|
| `MainCamera` | 出力先 | Camera + AudioListener (+ CinemachineBrain) | — |
| `FollowCamera` | プレイヤー追従 | CinemachineCamera + CinemachineFollow / CinemachinePositionComposer | 10 |
| `BoardCamera` | 盤面俯瞰固定 | Orthographic 固定 | 10 |
| `________` | `________` | `________` | `________` |

<a id="graphics-001"></a>

### GRAPHICS-001: Unity 6のCinemachine例は3.x APIを基準とする

**仕様**

- Unity 6の新規プロジェクトでCinemachineを採用する場合は、Package Managerが対象Editor向けに提供する安定版`com.unity.cinemachine` 3.xを基準とする。`Packages/manifest.json`と`packages-lock.json`から正確な導入バージョンを記録し、文書だけからバージョンを推測しない。
- Cinemachine 3.xのコードは`Unity.Cinemachine`名前空間を使用する。
- Unity Cameraには`CinemachineBrain`を設定し、ショット側の中心コンポーネントには`CinemachineCamera`を使用する。
- 追従・注視対象は`CinemachineCamera`のTracking Targetを基本とし、別の注視対象が必要な場合だけLook At Targetを設定する。
- 位置制御と回転制御は、`CinemachineFollow`、`CinemachineOrbitalFollow`、`CinemachinePositionComposer`、`CinemachineRotationComposer`など、Cinemachine 3.xの標準Componentを同じGameObjectへ追加して構成する。
- 複数Brainを使用する場合の振り分けには、Unity LayerではなくCinemachine ChannelとBrainのChannel Maskを使用する。
- Cinemachine 2.xを使用する既存プロジェクトでは、`CinemachineVirtualCamera`などの2.x名称を互換対象として維持してよい。3.xへの移行はPackage更新、API・名前空間変更、Cinemachine Upgrader、Scene・Prefab・Timeline・Animation・スクリプト参照の検査を含む独立作業とし、単純な文字列置換やUnity YAML直接編集では行わない。
- `CINEMACHINE_NO_CM2_SUPPORT`は、2.x Component、スクリプト、Scene、Prefab、Timeline、Animation参照が残っていないことを検証した後だけ使用する。

#### 受け入れ条件

| AC ID | 状態 | 検証種別 | 合格条件 | 検証方法 |
|---|---|---|---|---|
| `GRAPHICS-001-AC01` | `有効` | `AUTO:STATIC` | Unity 6向けカメラ例が`CinemachineCamera`とCinemachine 3.xのPosition / Rotation Control Componentを使用している | リポジトリ文書検査 |
| `GRAPHICS-001-AC02` | `有効` | `AUTO:STATIC` | Packageバージョン検出、`Unity.Cinemachine`名前空間、Tracking Target、Cinemachine Channelが規定されている | リポジトリ文書検査 |
| `GRAPHICS-001-AC03` | `有効` | `AUTO:STATIC` | Cinemachine 2.x既存案件を互換対象とし、3.x移行にUpgraderと参照検査が必要だと規定されている | リポジトリ文書検査 |

### 4.5 ライティング

```
ライティング方式      : ベイク / リアルタイム / 混合 / 不使用(2D)
2D Light              : 使用 / 不使用（URP 2D Renderer の場合）
Light Probe           : 使用 / 不使用
Reflection Probe      : 使用 / 不使用
影                    : Hard / Soft, 解像度__
時間帯演出            : 朝/昼/夜 切替の有無
```

---

## 5. アーキテクチャ — クラス依存 / DI / イベント設計

> 「Manager / Singleton / イベント駆動」を **具体的に何で実装するか** を決める層。ここを曖昧にすると、後でスパゲッティ化する。

### 5.1 レイヤー分離方針

```
┌─────────────────────────────────────────┐
│ Presentation 層 （View / UI / Animation）│ ← MonoBehaviour
├─────────────────────────────────────────┤
│ Application 層 （ユースケース / Manager）│ ← C# クラス
├─────────────────────────────────────────┤
│ Domain 層     （ロジック / ルール）       │ ← Pure C#
├─────────────────────────────────────────┤
│ Infrastructure層（Save / Net / Asset）   │ ← I/O 担当
└─────────────────────────────────────────┘
```

### 5.2 DI / Manager 方針

| 方式 | 採用 | 備考 |
|---|---|---|
| 素の Singleton | ☐ | 小規模向け |
| ServiceLocator | ☐ | 中規模向け |
| **VContainer** | ☐ | 軽量。採用Unityバージョンとの互換性を確認 |
| Zenject | ☐ | 機能豊富・重め |

### ▼ 記入テンプレート（主要 Manager 一覧）

| Manager 名 | 責務 | 生存期間 | 依存先 |
|---|---|---|---|
| `GameManager` | 進行ステート管理 | DontDestroyOnLoad | SceneLoader, SaveManager |
| `SceneLoader` | シーンの非同期ロード | DontDestroyOnLoad | — |
| `SaveManager` | ディスク I/O | DontDestroyOnLoad | — |
| `AudioManager` | BGM/SE 再生 | DontDestroyOnLoad | AudioMixer |
| `InputManager` | Input System ラッパー | DontDestroyOnLoad | — |
| `________` | `________` | `________` | `________` |

### 5.3 イベント・メッセージング設計

| 方式 | 用途 |
|---|---|
| **C# `event` / `Action`** | 同一アセンブリ内の通知 |
| **UnityEvent** | Inspector で接続したい時 |
| **ScriptableObject Event Channel** | シーン跨ぎ・疎結合な通知（推奨） |
| **R3 / UniRx** | 値の変化を購読・非同期合成したい時 |

### ▼ 記入テンプレート（主要イベント）

| イベント名 | 発火元 | 購読者 | ペイロード |
|---|---|---|---|
| 例）`OnPlayerDamaged` | PlayerHealth | UI / SE / Camera Shake | `int damage` |
| 例）`OnStageCleared` | StageController | GameManager / SaveManager | `int stageId` |
| 例）`OnCardPlayed` | HandManager | BoardManager / UI | `CardData` |
| 例）`OnChoiceSelected` | DialogueSystem | StoryFlagManager | `int choiceId` |
| `________` | `________` | `________` | `________` |

---

# 🔄 Phase 3: フロー設計

> セクション 6・7・8 は **並行で検討**。特に 6（ステート）と 7（シーン）は **表裏一体** で、片方を決めるともう片方が自動的に決まる。

## 6. ゲーム進行ステートマシン

> シーン遷移とは別の **「ゲーム全体の状態」** を管理する。`GameManager` が保持する。ジャンルによりステート構成は変わる。

### 6.1 汎用ステート遷移図（テキスト版）

```
              ┌────────┐
   起動 ───►  │  Boot  │
              └───┬────┘
                  ▼
              ┌────────┐
              │ Title  │ ◄────────┐
              └───┬────┘          │
        New/Continue              │ Quit to Title
                  ▼               │
              ┌────────┐          │
        ┌────►│  Play  │──────────┤
        │     └───┬────┘  Failure
        │ Resume  │ Pause
        │         ▼
        │     ┌────────┐
        └─────│ Pause  │
              └────────┘
                  │ Clear / End
                  ▼
              ┌────────┐
              │ Result │
              └────────┘
```

> 💡 ジャンル別の例：
> - **アクション**：Boot → Title → Play → Pause → Result
> - **ターン制（カード・SLG）**：Boot → Title → PlayerTurn ⇄ EnemyTurn → Result
> - **ノベル・ADV**：Boot → Title → Reading → Choice → Reading → Ending
> - **リズム**：Boot → Title → SongSelect → Play → Result

### ▼ 記入テンプレート（状態定義）

| State | 入る条件 | 抜ける条件 | 入った時の処理 | 抜ける時の処理 |
|---|---|---|---|---|
| `Boot` | 起動時 | 初期化完了 | Manager常駐化 | — |
| `Title` | Boot完了 / Quit | New/Continue押下 | TitleUI表示 / BGM | UI閉じる |
| `Play` | Title → 開始 | Pause / Clear / Failure | Time.timeScale=1 | 入力ロック |
| `Pause` | Play → Pause入力 | Resume / Quit | Time.timeScale=0 | timeScale復帰 |
| `Result` | Play → Clear/End | 戻るボタン | スコア集計 / セーブ | — |
| `________` | `________` | `________` | `________` | `________` |

### ▼ 実装メモ

```
実装方式 : enum + switch / State パターン / UniTask の StateMachine / Animator 流用
通知方式 : OnStateChanged イベントで UI・Audio・Input が反応
セクション7（シーンフロー）との関係 :
  - State.Title  → Title シーン
  - State.Play   → Stage / Battle / Reading シーン
  - State.Pause  → PauseMenu シーンを Additive
```

---

## 7. シーンフロー — 読まれる順番

> 公式の「シーンチャート」機能は無い。Unity 6では**Build ProfileのScene List（ビルド対象）＋ SceneManager（遷移コード）**で設計し、それを図にする。

### シーンを束ねる2つの仕組み

| 仕組み | 役割 |
|---|---|
| **Build Profile Scene List** | Profileごとのビルド対象Sceneと順序を定義する。直接`SceneManager`でロードするSceneは有効なScene Listへ含める |
| **SceneManager** | ロード・アンロード・問い合わせ、すべての操作が通る管制塔 |

Unity 6では各保存済みProfileで`Override Global Scene List`を有効にし、Development / QA / ReleaseごとのScene差分を明示する。Build IndexはProfileごとに変化し得るため、永続IDとして使用しない。Addressablesなど別経路で配信するSceneは、そのロード方式とCatalog管理をセクション18へ記録する。

### ロードの2モード

| モード | 動き | 比喩 |
|---|---|---|
| **Single** | 現在の全GameObjectを破棄して新シーンを読む | チャンネルを丸ごと変える |
| **Additive** | 既存を壊さず重ねて読む（UI・常駐・広大ワールド） | 新レイヤーを重ねる |

> ⚡ 大きいステージやモバイルは `LoadSceneAsync`（非同期）でローディング画面を出すのが定石。

### フロー図（テキスト版・汎用）

```
[起動]
  │
  ▼
┌────────────────────┐  Additiveで常駐
│ Bootstrap / Manager │ ← GameManager・Audio・SaveData をここに常駐
└────────────────────┘
  │ Single
  ▼
[Title 画面] ──「Continue」──► セーブ読込
  │「Start」
  ▼ Single
[メインプレイ画面]  ◄── Additive ── [HudOverlay]
  │ クリア / 章末 / バトル終了
  ▼ Single
[Result / 次の画面]
```

### ▼ 記入テンプレート（遷移表）

| From | トリガー（条件） | To | ロード方式 |
|---|---|---|---|
| Title | Start ボタン | メインシーン | Single |
| メイン | クリア / 章末 | 次のシーン | Single |
| 任意 | Pause | PauseMenu | Additive |
| `________` | `________` | `________` | `________` |

---

## 8. Save / Load — 2種類を分ける

> 「ロード」は2つの別物。混同しないこと。

| | A. シーンのロード | B. セーブデータのロード |
|---|---|---|
| 対象 | シーンファイル（ステージ・画面） | 進行状況（数値・フラグ） |
| 担当 | `SceneManager` | 自前のファイル保存 |
| 例 | ステージ2を読む | HP・所持金・章進行・既読フラグを復元 |

### データ保持の2レベル

| レベル | 手段 | 用途 |
|---|---|---|
| ① 実行中の保持（シーンまたぎ） | `DontDestroyOnLoad` / Managerシーン常駐 | 進行中のスコア・状態 |
| ② ディスク永続（電源OFFでも残る） | `PlayerPrefs` / `JSON` / 暗号化 | 本セーブデータ |

### ▼ 記入テンプレート（セーブ設計）

```
保存方式      : JSON ファイル / PlayerPrefs / 暗号化  （いずれか）
保存先パス    : Application.persistentDataPath + "/save.json"
保存するデータ : ※ジャンルにより内容は異なる
  - 例（アクション）: hp / stage / gold / clearedStages[]
  - 例（カード）   : ownedCards[] / deckPresets[] / playerLevel
  - 例（ノベル）   : currentScene / flags[] / readLines[]
  - 例（RPG）     : party[] / inventory[] / questFlags[] / mapPos
保存タイミング : クリア時 / 手動 / オートセーブ間隔(__分) / 章切替
ロードタイミング: Title の Continue 押下時
スロット数    :
バージョン管理 : セーブデータの version フィールドでマイグレーション対応
```

---

# 🎬 Phase 4: シーン中身を設計する

> Phase 3 のフローが決まったら、各シーンの中身を順に埋めていく。**1シーンずつ完成させる**進め方が安全。

## 9. Scene 一覧

> 環境やメニューを格納する単位。1シーン＝1ステージ・1画面と考える。複数シーンの同時ロード（Multi-Scene）も可能。

### ▼ 記入テンプレート（シーン一覧）

| Scene名 | 役割 | ロード方式 | 主要な親GameObject群 | 備考 |
|---|---|---|---|---|
| `Bootstrap` | 常駐マネージャー起動 | 最初/常駐 | Managers | DontDestroyOnLoad |
| `Title` | タイトル画面 | Single | UI, Camera | New/Continue |
| `Stage01` | メインプレイ画面 | Single | ジャンルによる（→ セクション10） | |
| `HudOverlay` | 共通UI | Additive | HudCanvas | 常駐表示 |
| `________` | `________` | `________` | `________` | |

---

## 10. Scene 内 GameObject 階層 — 親要素ごと（ジャンル別パターン）

> **シーンの中身を「親要素」単位で設計する**。各シーンごとにツリーを書き、親GameObject（フォルダ代わり）の下に子を並べる。Hierarchy の見た目とそのまま対応させる。ジャンルにより典型的な親要素は変わるため、**複数のパターン**を併記する。

> ⚙ **階層の目安**：1オブジェクトあたり子は約50個・深さ4階層まで。**空の親 GameObject をフォルダ代わりに使う**と整理しやすい。

### 10.1 GameObject カテゴリ（共通）

| カテゴリ | 例 |
|---|---|
| 操作対象 | Player / 駒 / カーソル / 手札 |
| 環境・舞台 | 地形 / 背景 / 盤面 / 立ち絵 |
| システム系 | Camera / Light / AudioSource |
| UI | Button / Panel / Text / HUD |
| 管理用（空Obj） | GameManager / フォルダ代わり |
| 経由点・トリガー | Waypoint / SpawnPoint / セル / ゾーン |

### 10.2 親要素テンプレ — ジャンル別パターン

#### 🎮 パターンA：アクション / プラットフォーマー / RPG（3D）

```
[Scene Root]
├─ Managers          シーン固有Manager
├─ World             地形・建物・小道具
├─ Cameras           Cinemachine 群
├─ Characters        Player / Enemies / NPCs
├─ Spawners          ランタイム生成
├─ Triggers          当たり判定発火
└─ UI                シーン固有UI
```

#### 🧩 パターンB：パズル / ボードゲーム

```
[Scene Root]
├─ Managers          BoardManager, ScoreManager
├─ Board             盤面の親
│   ├─ Cells/        セル群（Grid配置）
│   └─ Pieces/       駒・ピース群（実行時生成も）
├─ Cursor            選択カーソル（あれば）
├─ Cameras           Orthographic 固定が多い
├─ Effects           マッチ消去エフェクト等
└─ UI                スコア・残り手数・Next
```

#### 🃏 パターンC：カードゲーム

```
[Scene Root]
├─ Managers          DuelManager, TurnManager
├─ Field             場の親
│   ├─ PlayerArea/
│   │   ├─ Hand/         手札
│   │   ├─ Deck/         山札
│   │   ├─ MonsterZone/  場のカード
│   │   └─ Graveyard/    墓地
│   └─ EnemyArea/        相手側（同構成）
├─ Cameras
├─ Effects           召喚演出など
└─ UI                LP表示・ターン表示・操作ボタン
```

#### 📖 パターンD：ノベル / ADV

```
[Scene Root]
├─ Managers          DialogueManager, FlagManager
├─ Background        背景画像（差し替え式）
├─ Characters        立ち絵レイヤー
│   ├─ Left/
│   ├─ Center/
│   └─ Right/
├─ Cameras           固定 Orthographic
├─ Effects           フェード・揺れ・パーティクル
└─ UI
    ├─ DialogueTextBox   本文・名前ウィンドウ
    ├─ Choices           選択肢
    └─ DialogueMenu      バックログ・セーブ
```

#### 🎵 パターンE：リズムゲーム

```
[Scene Root]
├─ Managers          ConductorManager（時間軸の主）, ScoreManager
├─ NoteLane          ノーツが流れるレーン群
│   └─ Lane01 ～ LaneNN
├─ JudgeLine         判定ライン
├─ NoteSpawner       Noteを生成
├─ Cameras
├─ Effects           判定エフェクト
└─ UI                スコア・コンボ・ライフ
```

#### 🏰 パターンF：SLG / ストラテジー（ターン制）

```
[Scene Root]
├─ Managers          TurnManager, AIManager
├─ Map               マップ親
│   ├─ Tiles/        グリッドタイル
│   └─ Units/        ユニット駒
├─ Cameras           俯瞰 + ユニット注視
├─ Highlights        移動範囲・攻撃範囲ハイライト
└─ UI                ターン表示・ユニット情報
```

> 💡 ハイブリッドジャンルの場合は複数パターンを合成して書く。

### 10.3 ▼ 記入テンプレート（シーンごと・親要素ごと）

> 各シーンについて、以下の表を1枚作る。**親要素ごとに行をまとめる**ことで Hierarchy と1対1対応する。

#### 📋 Scene: `________`（パターン選択：A / B / C / D / E / F）

##### 親要素：`________`

| 子オブジェクト名 | カテゴリ | 主なComponent | アタッチScript（※共通） | 役割 |
|---|---|---|---|---|
| `________` | `________` | `________` | `________` | `________` |
| `________` | `________` | `________` | `________` | `________` |

##### 親要素：`________`

| 子オブジェクト名 | カテゴリ | 主なComponent | アタッチScript（※共通） | 役割 |
|---|---|---|---|---|
| `________` | `________` | `________` | `________` | `________` |

> 同じテンプレートを **全シーン分** 複製して埋める。

---

## 11. Prefab — 再利用テンプレート

> GameObject をコンポーネントごと資産化した「型紙」。同じものを大量配置する場面で必須。Variant（派生）で「色違い」「強化版」なども管理可。

### ▼ 記入テンプレート（Prefab一覧 — ジャンル別の典型例を含む）

| Prefab名 | 元オブジェクト | 用途 | 採用ジャンル例 | 生成方法 |
|---|---|---|---|---|
| 例）`EnemySlime` | Enemy | 雑魚敵 | アクション / RPG | Spawnerが生成 |
| 例）`CardView` | Card | カード表示 | カード | 手札に追加時 |
| 例）`GrassTile` | Tile | マップタイル | SLG / パズル | 初期化時に配置 |
| 例）`TapNote` | Note | リズムのノーツ | リズム | NoteSpawnerが生成 |
| 例）`CharacterPortrait` | 立ち絵 | ノベル登場人物 | ノベル | シナリオから生成 |
| 例）`HitVfx` | エフェクト | 衝突演出 | 全般 | ObjectPool |
| `________` | `________` | `________` | `________` | `________` |

---

## 12. データ層 — ScriptableObject

> シーンではなくプロジェクトに住む「設定データの器」。ロジック(Component)とデータを分離する。**ジャンルに応じて「データ単位」が異なる**。

| 向いている用途 | 利点 |
|---|---|
| 武器/アイテム / カードデータ / ステージデータ / 対話データ / 楽曲データ / クエストデータ など | メモリ効率（参照共有）・Inspectorで非プログラマも編集可・シーンをまたいでも保持 |

### ▼ 記入テンプレート（ScriptableObject定義 — ジャンル別例）

```
─ アクション / RPG ─
SO名       : WeaponData
保持データ  : weaponName, damage, attackSpeed, icon
参照元      : PlayerController, InventorySystem

─ カードゲーム ─
SO名       : CardData
保持データ  : cardName, cost, attack, defense, effectId, art
参照元      : Deck, HandManager, CardView

─ パズル / SLG ─
SO名       : StageData
保持データ  : stageName, gridSize, initialBoard[], goal
参照元      : BoardManager

─ ノベル / ADV ─
SO名       : DialogueData
保持データ  : speaker, lines[], choices[], nextSceneId
参照元      : DialogueManager

─ リズム ─
SO名       : SongData
保持データ  : title, bpm, audioClip, notes[], offset
参照元      : ConductorManager, NoteSpawner

─ 共通 ─
SO名       : GameSettings
保持データ  : masterVolume, language, difficulty
参照元      : 全Manager
```

### ▼ 記入テンプレート（自作SO）
```
SO名       :
保持データ  :
作成数      :
参照元      :
```

---

# ⚙️ Phase 5: 挙動を組む

> シーン中身が決まったら、Componentを実装して動かす。セクション 13〜16 は **並行で進めて良い**。

## 13. Component と共通スクリプト

> GameObject（箱）に挿す部品。`Transform` だけは全オブジェクト必須。**「共通スクリプト」を先に抽出**してから、個別スクリプトを書くのが定石。

### 13.1 標準 Component（Unity 提供）

| Component | 役割 |
|---|---|
| `Transform` | 位置・回転・スケール（必須・唯一） |
| `Renderer` / `SpriteRenderer` | 見た目の描画（3D / 2D） |
| `Collider` / `Collider2D` | 当たり判定 |
| `Rigidbody` / `Rigidbody2D` | 物理挙動 |
| `AudioSource` | 音の再生 |
| `Animator` | アニメーション制御 |
| `Canvas` / `UIDocument` | UI ルート（uGUI / UI Toolkit） |
| `Script (C#)` | 独自ロジック・振る舞い |

### 13.2 共通スクリプト（横断ロジック・ジャンル汎用）

> **複数の GameObject にアタッチされる汎用 Component**。ここで先に切り出すことで、個別スクリプトが薄くなる。

#### ▼ 記入テンプレート（共通スクリプト一覧 — ジャンルマーカー付き）

| スクリプト名 | 責務 | 主な採用ジャンル | アタッチ先（複数） | 公開パラメータ |
|---|---|---|---|---|
| `HealthSystem` | HP管理・ダメージ受け | アクション / RPG / SLG | Player / Enemies / 破壊物 | maxHp |
| `DamageDealer` | 衝突時にダメージを与える | アクション / RPG | 武器・弾・体当たり | damage |
| `Interactable` | 「調べる」対象のマーカー | アクション / RPG / ADV | NPC / Item / Door | interactType |
| `FollowTarget` | ターゲット追従の汎用 | 全般 | カメラ / UIマーカー / お供 | target, offset, smooth |
| `ObjectPoolItem` | プール対象マーカー | 全般（特に量産系） | 弾 / Note / ピース | poolId |
| `AutoDestroy` | 一定時間で自動消滅 | 全般 | エフェクト・弾 | lifeTime |
| `EventTrigger2D/3D` | 領域進入をイベント発火 | アクション / RPG | チェックポイント・ゾーン | OnEnterEvent |
| `SoundEmitter` | 音再生の薄いラッパー | 全般 | 何でも | clip, volume |
| `Selectable2D/3D` | クリック/タップで選択可 | パズル / カード / SLG | セル / 駒 / カード | OnSelectEvent |
| `Draggable` | ドラッグ&ドロップ対応 | カード / パズル / UI | カード / ピース | dropZone |
| `GridCell` | グリッド上の1セル | パズル / SLG | Cells/ 配下 | gridPos |
| `TweenAnimator` | 簡易アニメ（移動・拡縮） | 全般 | UI / 駒 / カード | target, duration |
| `Highlightable` | 強調表示の切替 | パズル / SLG / カード | セル / カード / 駒 | highlightColor |
| `________` | `________` | `________` | `________` | `________` |

> 💡 **アクション系の HealthSystem** と **カード系の Selectable / Draggable** は別物だが、**ジャンルが違っても「共通スクリプトを抽出する考え方」は同じ**。

### 13.3 個別スクリプト（特定のオブジェクト専用）

#### ▼ 記入テンプレート（個別スクリプト仕様）

```
スクリプト名 : 例）PlayerController / DuelManager / DialogueManager
アタッチ先   : 例）Player / Systems / DialogueTextBox
責務         :
公開パラメータ:
参照する物    :
主なメソッド  :
```
```
スクリプト名 :
アタッチ先   :
責務         :
公開パラメータ:
参照する物    :
主なメソッド  :
```

### 13.4 共通スクリプトと個別スクリプトの関係

```
例）アクションゲームの場合
[Player] というGameObject
  ├─ PlayerController (個別)   ← 入力・状態判定
  ├─ HealthSystem    (共通)   ← HP保有・他からダメージ受け
  ├─ SoundEmitter    (共通)   ← SE再生
  └─ ObjectPoolItem  (共通)   ← (不要なら付けない)

例）カードゲームの場合
[CardView] というGameObject
  ├─ CardController  (個別)   ← カード固有の効果発動
  ├─ Selectable      (共通)   ← クリックで選択
  ├─ Draggable       (共通)   ← ドラッグで場に出す
  └─ TweenAnimator   (共通)   ← 移動アニメ
```

> 同じ責務を別スクリプトで書くな。**「共通」へ寄せられないか毎回問う**。

---

## 14. プレイヤー操作・対象制御 — ジャンル別

> **「プレイヤーが何をどう操作するか」** は実装直結。ジャンルにより制御方式が大きく異なるため、**該当パターンを選んで詳細設計**する。

### 14.1 制御パターンの選択

| パターン | 操作の主体 | 主な実装方式 | 採用ジャンル例 |
|---|---|---|---|
| **A. キャラ移動・物理制御** | プレイヤー＝キャラ | Rigidbody / CharacterController | アクション / FPS / TPS |
| **B. カーソル・選択制御** | プレイヤー＝カーソル | Raycast / EventSystem | パズル / SLG |
| **C. ドラッグ&ドロップ制御** | プレイヤー＝手 | EventSystem / IDrag* | カード / パズル |
| **D. クリック/タップ反応制御** | プレイヤー＝指 | OnPointerClick / IPointer* | クリッカー / ノベル / ADV |
| **E. テキスト送り・選択肢制御** | プレイヤー＝読み手 | 入力で次の行へ / 選択肢分岐 | ノベル / ADV |
| **F. タイミング判定制御** | プレイヤー＝叩き手 | 音楽時刻 vs 入力時刻の差分 | リズム |
| **G. コマンド選択制御** | プレイヤー＝指揮官 | メニュー駆動 | コマンドRPG / SLG |

### 14.2 ▼ 記入テンプレート（採用パターン）

```
採用パターン       : A / B / C / D / E / F / G （複数も可）
主な実装方式       :
入力デバイス       : キーボード / マウス / コントローラ / タッチ / マイク
入力反映タイミング :
```

### 14.3 パターンA：キャラ移動・物理制御の詳細（アクション系のみ）

> 採用ジャンルでない場合はスキップ可。

| 方式 | 適性 | 特徴 |
|---|---|---|
| `Rigidbody` + `AddForce` | 物理感重視 | 物理挙動が自然・調整難 |
| `Rigidbody` + `MovePosition` | バランス型 | 物理と直接制御の中間 |
| `CharacterController` | 操作感重視 | Capsule前提・斜面処理が楽 |
| `NavMeshAgent` | AI / 自動移動 | クリックトゥムーブ等 |
| `Transform` 直接 | 2D / 簡易 | 物理無視 |

```
プレイヤー移動方式    :
接地判定              : Raycast / SphereCast / Collider Stay / CharacterController.isGrounded
ジャンプ実装          : 速度直接代入 / AddForce(Impulse)
入力反映タイミング    : Update（入力取得）→ FixedUpdate（物理適用）
カメラ追従との結合    : CinemachineCamera の Tracking Target が Player Transform を参照
```

### 14.4 物理設定（採用ジャンルのみ）

| 項目 | 設定 |
|---|---|
| 次元 | 2D / 3D / 物理なし |
| 重力 | Default(-9.81) / カスタム / なし |
| Rigidbody 種別 | Dynamic / Kinematic |
| Interpolate | Interpolate / Extrapolate / None |
| Collision Detection | Discrete / Continuous |
| PhysicsMaterial | 摩擦 __ / 反発 __ |

> ⚠ **Layer Collision Matrix** はセクション 17 と必ず連携させること。

### 14.5 Animator 状態遷移（キャラがアニメーションするジャンルのみ）

#### ▼ 記入テンプレート（Animator パラメータ）

| パラメータ名 | 型 | 用途 |
|---|---|---|
| `Speed` | float | Idle ↔ Run のブレンド |
| `IsGrounded` | bool | Jump 状態の切替 |
| `JumpTrigger` | Trigger | ジャンプ開始 |
| `AttackIndex` | int | 攻撃モーション切替 |
| `________` | `________` | `________` |

#### ▼ ステート遷移図（テキスト版・例）

```
   ┌──────┐  Speed>0.1   ┌──────┐
   │ Idle │ ───────────► │ Run  │
   │      │ ◄─────────── │      │
   └──┬───┘  Speed<0.1   └──┬───┘
      │                     │
      └─── JumpTrigger ─────┘
              │
              ▼
        ┌──────────┐
        │   Jump   │
        └──────────┘
```

```
追加考慮事項 :
  - Root Motion : 使用 / 不使用
  - IK          : Foot IK / Look IK / Animation Rigging の使用有無
  - Layer       : Base（全身）/ Upper（攻撃）の分割
```

### 14.6 パターン別・実装メモテンプレ

```
─ パターンB（カーソル・選択）─
選択方式 : マウスRaycast / コントローラで Selectable 移動
ハイライト : Outline / TweenAnimator で拡大

─ パターンC（D&D）─
ドラッグ実装 : EventSystem の IBeginDrag/IDrag/IEndDrag
ドロップ判定 : OverlapPoint / IDropHandler

─ パターンE（テキスト送り）─
送り方式 : クリック / 自動 / スキップ
速度設定 : 文字送りCPS / オート間隔(秒)

─ パターンF（リズム判定）─
時間軸基準 : AudioSource.time / DSP Time / Conductor自前カウント
判定窓 : Perfect ±__ms / Good ±__ms / Miss ±__ms
```

---

## 15. 時間軸 — Lifecycle と Timeline

> 「シーンにタイムラインがある」は2つの別概念。分けて理解する。

### A. 実行ライフサイクル（毎フレーム回る軸）

```
Awake → Start → Update（毎フレーム反復）→ … → OnDestroy
```
ゲームロジック・操作・物理はこの軸で動く。リアルタイム/ターン制を問わずほぼ全ジャンルが使う。

### B. Timeline アセット（演出の軸）

動画編集ソフトのように、動き・音・カメラ切替をトラックで時系列配置。カットシーン・イベント演出に。実体は `PlayableDirector` を持つ GameObject。**ノベル・カットシーン重視のジャンルで特に有効**。

### ▼ 記入テンプレート（演出一覧）

| 演出名 | 発生タイミング | 内容 | 使用方式 |
|---|---|---|---|
| 例）`OpeningCutscene` | ゲーム開始時 | カメラワーク＋BGM | Timeline |
| 例）`CardSummonVfx` | カード召喚時 | カメラズーム+SE+VFX | Timeline / Tween |
| 例）`StoryEvent01` | 章開始時 | テキスト+立ち絵切替 | DialogueManager制御 |
| `________` | `________` | `________` | `________` |

---

## 16. 入力層 / UI 層

### 入力層 — Input System

操作（キー / パッド / マウス / タッチ）をアクション単位で設計する。**ジャンルにより必要なアクションは異なる**。

### ▼ 記入テンプレート（入力アクション）

| アクション名 | 入力（キーボード） | 入力（パッド） | 入力（タッチ） | 紐づく処理 |
|---|---|---|---|---|
| 例）Move | WASD | 左スティック | 仮想スティック | 移動 |
| 例）Confirm | Space / Enter | A ボタン | タップ | 決定 |
| 例）Cancel | Esc | B ボタン | バックスワイプ | キャンセル |
| 例）Drag | マウスドラッグ | — | スワイプ | カード移動 |
| 例）Tap | クリック | A | タップ | ノーツ判定 |
| `________` | `________` | `________` | `________` | `________` |

### UI層 — UI Toolkit / uGUI

UXML(構造)＋USS(見た目)。HUD・メニュー・設定画面を独立レイヤーで設計。**カード・ノベル・経営など UI 比重が高いジャンルは UI Toolkit が有利**。

### ▼ 記入テンプレート（画面一覧）

| 画面名 | 種別 | 要素 | 遷移元 |
|---|---|---|---|
| Title Menu | メニュー | Start, Continue, Settings, Quit | 起動時 |
| HUD | ゲーム中常駐 | 例）HP・スコア / ターン表示 / 残り時間 / コンボ | プレイ中 |
| Result | リザルト | スコア・報酬・次へボタン | プレイ終了 |
| `________` | `________` | `________` | `________` |

### ▼ UI解像度・対応

```
基準解像度        : 例）1920x1080 / 1080x1920（縦持ち）
Canvas Scaler     : Scale With Screen Size / Reference Resolution
Safe Area対応     : する / しない（モバイルは必須）
向き              : 横 / 縦 / 両対応
```

---

# 🌐 Phase 6: 横断ルール（常時意識）

> このフェーズは **「Phase 2 の時点から並行して育てる」**。最後にまとめて整備するものではない。

## 17. Tag / Layer / 衝突マトリクス

### ▼ 記入テンプレート（Tag / Layer）

| 種別 | 名前 | 用途 |
|---|---|---|
| Tag | Player | プレイヤー識別 |
| Tag | Enemy | 敵識別 |
| Tag | Interactable | 調べる対象 |
| Layer | Ground | 接地判定 |
| Layer | UI | UIレイキャスト |
| Layer | `________` | `________` |

### ▼ 記入テンプレート（衝突マトリクス例 — 物理使用ジャンルのみ）

|  | Player | Enemy | Ground | Item |
|---|:---:|:---:|:---:|:---:|
| **Player** | — | ✓ | ✓ | ✓ |
| **Enemy** | ✓ | ✗ | ✓ | ✗ |
| **Ground** | ✓ | ✓ | — | ✓ |
| **Item** | ✓ | ✗ | ✓ | — |

---

## 18. アセット読み込み — Addressables

> アセットを「必要な時だけ」ロード/アンロードする仕組み。容量と性能に直結。ローカル同梱でもCDN配信でも使える。

| 機能 | 内容 |
|---|---|
| 分割ロード | ステージ・章・楽曲単位で読み書き |
| 依存解決 | 関連アセットを自動ロード |
| リモート配信 | CDNから後から追加DL（追加楽曲・追加カード等） |

### ▼ 記入テンプレート

```
Addressables 使用      : する / しない
グループ分け            :
  - 常駐 (Manager, 共通UI)
  - コンテンツ別 (Stage01 / Song01 / Chapter01 / CardSet01)
  - リモート配信 (追加コンテンツ・DLC)
配信方式               : ローカル同梱 / CDN
```

---

## 19. プロジェクト規約 — Audio / Git / ビルド

### ▼ 記入チェックリスト

- [x] **標準命名規則**（セクション3.1）
- [x] **標準フォルダ構成**（セクション3.2）
- [ ] **Audio 設計**（BGM / SE / Voice / Mixer グループ・Snapshot）
- [ ] **バージョン管理**（Git / `.gitignore` / LFS）とシーンのマージ方針
- [ ] **ビルド対象プラットフォームと品質設定**
- [ ] **ログ規約**（Debug.Log / 本番ストリップ方針）

### ▼ 記入テンプレート（Audio Mixer）

| グループ | 用途 | 子グループ |
|---|---|---|
| Master | 全体 | BGM / SE / Voice |
| BGM | 楽曲 | — |
| Sfx | 効果音 | UiSfx / GameplaySfx |
| Voice | 音声 | — |

### ▼ 記入テンプレート（Git / ビルド）

```
Git管理       : する / しない
.gitignore    : Unity標準テンプレート + Artifacts, Builds を除外
Git LFS       : .psd .png .fbx .wav 等を対象
ブランチ運用  : main / develop / feature/*
Build Profile保存先:
主Build Profile:
検証Build Profile:
Release Build Profile:
```

<a id="build-001"></a>

### BUILD-001: Unity 6では保存済みBuild Profileをビルド構成の正とする

**仕様**

Unity 6プロジェクトは、対象プラットフォームと用途ごとに保存済みBuild Profileアセットを作成し、Scene List、Scripting Defines、ビルドオプション、必要なPlayer Settings差分をVersion Controlで管理する。CI、ローカル検証、Release作成では使用したProfileのアセットパスを記録し、Editorで最後に選択されていた構成へ依存しない。

旧Unityまたは移行前案件ではLegacy Build Settingsを互換経路として使用できるが、Unity 6 Profileへ移行するまでは制約として設計書と作業報告へ記録する。

#### 保存場所と命名

- 保存先: `Assets/Settings/BuildProfiles/<Platform>/`
- 名前: `<ProjectName><Platform><Purpose>.asset`
- `Platform`: `Windows`、`MacOS`、`Linux`、`Android`、`IOS`、`Web`など、対象を一意に識別するPascalCase
- `Purpose`: `Development`、`QA`、`Release`
- Build Profileアセットと`.meta`をGit管理する

例:

```text
Assets/Settings/BuildProfiles/
├─ Windows/
│  ├─ MyGameWindowsDevelopment.asset
│  ├─ MyGameWindowsQA.asset
│  └─ MyGameWindowsRelease.asset
└─ Android/
   ├─ MyGameAndroidDevelopment.asset
   └─ MyGameAndroidRelease.asset
```

#### 標準Profile分類

| Purpose | 用途 | Scene List | Profile固有Define | Development Build | Profiler / Debugger |
|---|---|---|---|---|---|
| `Development` | 日常開発、診断、端末確認 | 開発に必要なScene。Sandbox追加可 | `GAME_BUILD_DEVELOPMENT` | ON | 必要な項目だけON |
| `QA` | 継続テスト、受け入れ確認、Release候補前確認 | Release相当。QA専用Sceneは明示追加 | `GAME_BUILD_QA` | 原則OFF | 原則OFF。調査時だけ別ProfileでON |
| `Release` | 配布物作成 | 配布対象Sceneのみ | `GAME_BUILD_RELEASE` | OFF | すべてOFF |

各Profileは`Override Global Scene List`を有効にし、Scene順序を明示する。3つの`GAME_BUILD_*`シンボルは同一Profileへ複数設定しない。Profile固有DefineはProject / Player SettingsのDefineへ追加され、置換しない。

#### Profile記録テンプレート

| Profile asset | Platform | Purpose | Scene List | Defines | Player Settings override | Build options | 出力形式 |
|---|---|---|---|---|---|---|---|
| `Assets/Settings/BuildProfiles/____/____.asset` | | Development / QA / Release | | | | | |

Player Settings overrideは、Product Name、Bundle Identifier、Version、Scripting Backend、Architectureなど、Profile間で差が必要な値だけを列挙する。共通値はグローバルPlayer Settingsで管理する。

#### Clean Build条件

次の場合はClean Buildを実行する。

- Profileまたは対象プラットフォームで最初にビルドする
- Unity Editor、Build Target、Scripting Backend、Architectureを変更した
- Player Settings override、Scene List、Addressablesまたはビルド前処理を変更した
- Release候補を作成する
- incremental buildのキャッシュ不整合が疑われる

日常的なコード・アセット変更の反復確認ではincremental buildを使用できる。

#### CI・バッチ実行

CIは保存済みProfileを明示してUnityを起動する。

```text
<UNITY_EDITOR> -batchmode -quit \
  -projectPath <UNITY_PROJECT_ROOT> \
  -activeBuildProfile "Assets/Settings/BuildProfiles/<Platform>/<Profile>.asset" \
  -build "Artifacts/ValidationRuns/<RunId>/Builds/<ProfileName>/<PlayerPath>" \
  -logFile "Artifacts/ValidationRuns/<RunId>/Logs/Build.log"
```

カスタムBuild Scriptを使う場合も`-activeBuildProfile`を指定し、`BuildProfile.GetActiveBuildProfile()`または`BuildPlayerWithProfileOptions`でProfileを利用する。異なるPlatformはUnityプロセスを分けて実行する。

直接`-build`を使うビルドは、初回を除いてincremental buildになる。CIでClean Build条件に該当する場合はカスタムBuild Scriptを使用し、`BuildPlayerWithProfileOptions.options`へ`BuildOptions.CleanBuildCache`を追加する。

#### 受け入れ条件

| AC ID | 状態 | 検証種別 | 合格条件 | 検証方法 |
|---|---|---|---|---|
| `BUILD-001-AC01` | `有効` | `AUTO:STATIC` | Unity 6のScene・Build説明が保存済みBuild ProfileとScene Listを正としている | リポジトリ文書検査 |
| `BUILD-001-AC02` | `有効` | `AUTO:STATIC` | Development / QA / Releaseの用途、Defines、Debug設定、Clean Build条件、保存場所、命名が定義されている | リポジトリ文書検査 |
| `BUILD-001-AC03` | `有効` | `AUTO:STATIC` | CI手順が`-activeBuildProfile`でProfileアセットを明示し、Editorの前回状態へ依存しない | リポジトリ文書検査 |

<a id="debug-001"></a>

### DEBUG-001: Validation Runは終端状態と検証可能な証拠を持つ

**仕様**

- Validation Runはschema version 2の`RunManifest.json`を持ち、作成時の`RUNNING`からfinalize後の`COMPLETED`へ一方向に遷移する。
- finalize時は`completedAtUtc`、`durationSeconds`、コマンド終了コード、Check結果、AC別結果、最終結果、成果物の相対パス・サイズ・SHA-256を記録する。
- CheckまたはACに`FAIL`、`BLOCKED`、`NOT RUN`があれば、Runの最終結果を`PASS`にしない。
- 継続不能なRunは理由を記録して`BLOCKED`で完了できる。`RUNNING`のまま成功扱いにしない。
- 完了時に`RunManifest.sha256`を生成し、Manifestと記録済み成果物の改変、欠落、未記録ファイルを検証できるようにする。
- `COMPLETED` Runは再finalize・上書きせず、追加検証や証拠修正は新しいRunで行う。

#### 受け入れ条件

| AC ID | 状態 | 検証種別 | 合格条件 | 検証方法 |
|---|---|---|---|---|
| `DEBUG-001-AC01` | `有効` | `AUTO:STATIC` | 新規Runがschema version 2の`RUNNING`で始まり、finalize後に完了日時・duration・Check・AC・最終結果を持つ`COMPLETED`になる | Python CLI回帰テスト |
| `DEBUG-001-AC02` | `有効` | `AUTO:STATIC` | 完了済みRunの再finalizeが拒否され、途中Runを理由付き`BLOCKED`で完了できる | Python CLI回帰テスト |
| `DEBUG-001-AC03` | `有効` | `AUTO:STATIC` | Manifest sidecar hash、Check・AC証拠パス、成果物のサイズ・SHA-256を検証し、欠落と完了後の変更を検出できる | Python CLI回帰テスト |

---

## 付録A：ジャンル別 追加検討項目

> 作るゲーム次第で以下のセクションを追記する。

- **ネットワーク同期** … マルチプレイなら必須（Netcode for GameObjects / Mirror / Photon）
- **ローカライズ** … 多言語対応（Localization Package）
- **Unity Gaming Services** … 認証・Cloud Save・リーダーボード・IAP・Ads
- **パフォーマンス目標** … 目標FPS / メモリ予算 / Draw Call上限 / ObjectPool方針
- **デバッグ機能** … チートコマンド / デバッグUI / Unity Test Framework
- **アセット規格** … 3Dモデルのポリゴン数・ボーン数、テクスチャ解像度・圧縮
- **VR / AR 対応** … XR Interaction Toolkit / AR Foundation

---

## 付録B：ジャンル別 設計チェックリスト

> 該当ジャンルの欄が **すべて埋まっていれば実装着手OK** の目安。

### 🎮 アクション / プラットフォーマー
- [ ] 14.3 移動方式が決まっている
- [ ] 14.5 Animator 遷移図がある
- [ ] 17 Layer Collision Matrix が定義されている
- [ ] 4.4 カメラ追従（Cinemachine）が定義されている

### 🧩 パズル / ボード
- [ ] 10.2 パターンB の Board / Cells 構造がある
- [ ] 12 StageData SO がある
- [ ] 13.2 Selectable / GridCell / Highlightable がある
- [ ] 14.1 パターンB の制御方式が定義されている

### 🃏 カードゲーム
- [ ] 10.2 パターンC の Field / Hand / Deck 構造がある
- [ ] 12 CardData SO がある
- [ ] 13.2 Selectable / Draggable がある
- [ ] 5.3 OnCardPlayed イベント設計がある

### 📖 ノベル / ADV
- [ ] 10.2 パターンD の Background / Characters / TextBox 構造がある
- [ ] 12 DialogueData SO がある
- [ ] 8 セーブ内容に flags[] / readLines[] がある
- [ ] 14.1 パターンE の制御方式が定義されている

### 🎵 リズム
- [ ] 10.2 パターンE の NoteLane / JudgeLine 構造がある
- [ ] 12 SongData SO（BPM・notes・offset）がある
- [ ] 14.1 パターンF の判定窓が定義されている
- [ ] 15 Conductor の時間軸基準が決まっている

### 🏰 SLG / ストラテジー
- [ ] 10.2 パターンF の Map / Tiles / Units 構造がある
- [ ] 6.1 PlayerTurn / EnemyTurn のステートマシンがある
- [ ] 13.2 GridCell / Highlightable がある
- [ ] 14.1 パターンB or G の制御方式が定義されている

### 🗡️ RPG
- [ ] パターンA + G の複合（フィールド移動 + コマンド戦闘）
- [ ] 12 多種多様な SO（敵 / 武器 / クエスト / アイテム）
- [ ] 8 セーブ内容に party / inventory / questFlags がある
- [ ] 6 ステートに Field / Battle / Menu が含まれる

---

*SUPER ULTRA THUNDER · Unity Game Design Document Template*
