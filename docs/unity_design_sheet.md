<!-- UNITY_CODEX_GAME_DESIGN_INDEX: PROJECT-OWNED -->

# Unityゲーム設計文書索引

> **所有者: このゲームプロジェクト**
>
> ゲーム固有の正本は`docs/game_design/`配下です。このファイルは入口と
> 所有境界だけを示し、受け入れ条件や設計本文を重複記録しません。

## 整合契約

ゲーム制作の追跡方向は次の順序です。

```text
受け入れ条件 -> 設計項目 -> Unity実装単位 -> Validation Run
```

- ユーザー要求は、まずゲーム全体またはSceneの受け入れ条件として記録する。
- 設計項目は一つ以上の上流AC IDを参照する。
- 実装は承認済み設計IDを参照し、設計項目の実装マッピングへ記録する。
- AC、設計ID、実装マッピングは発行後に変更・再利用せず、不要時は`廃止`にする。
- 実行結果の`PASS / FAIL / BLOCKED / NOT RUN`はValidation Runまたは作業レポートへ記録する。

## 文書セット

| スコープ | 正本 |
|---|---|
| ゲーム全体の受け入れ条件 | [all/acceptance.md](./game_design/all/acceptance.md) |
| 標準要件の適用・例外 | [all/standards.md](./game_design/all/standards.md) |
| 初期設計対話 | [all/initial_design.md](./game_design/all/initial_design.md) |
| コンセプト・ゲーム全体仕様 | [all/game_design.md](./game_design/all/game_design.md) |
| Unity Project・Build・Repository設定 | [all/project_design.md](./game_design/all/project_design.md) |
| 表現・入力・UI・Audio | [all/presentation_design.md](./game_design/all/presentation_design.md) |
| Architecture・Save・性能 | [all/architecture.md](./game_design/all/architecture.md) |
| 横断機能 | [all/cross_cutting.md](./game_design/all/cross_cutting.md) |
| 未決事項・承認履歴 | [all/open_questions.md](./game_design/all/open_questions.md) |
| Scene別AC・設計 | [scenes/README.md](./game_design/scenes/README.md) |
| 共通Prefab | [shared/prefabs/README.md](./game_design/shared/prefabs/README.md) |
| 共通Script・System | [shared/scripts/README.md](./game_design/shared/scripts/README.md) |
| ScriptableObject・Data | [shared/data/README.md](./game_design/shared/data/README.md) |
| 共通UI | [shared/ui/README.md](./game_design/shared/ui/README.md) |
| 共通Audio | [shared/audio/README.md](./game_design/shared/audio/README.md) |
| 共通Asset・Material・Animation | [shared/assets/README.md](./game_design/shared/assets/README.md) |

<a id="game-design-document-tree"></a>
## 完全な文書階層

次がゲーム設計文書セットの正規構造です。`[必須]`はInstallerが作成して
存在を検査する固定ファイル、`[雛形]`は複製元、`[追加]`はゲームの構成に応じて
作成するproject-owned文書を表します。

```text
docs/
├─ unity_design_sheet.md                         [必須] この索引・所有境界・構造定義
└─ game_design/                                  [必須] ゲーム固有AC・設計の正本root
   ├─ all/                                       [必須] ゲーム全体を所有する文書
   │  ├─ acceptance.md                           [必須] ゲーム全体・複数Sceneに跨るAC
   │  ├─ standards.md                            [必須] HREQ適用状態・対象外・例外承認
   │  ├─ initial_design.md                       [必須] 初期設計対話・Phase・監査証跡
   │  ├─ game_design.md                          [必須] Concept・Core Loop・全体Flow
   │  ├─ project_design.md                       [必須] Unity Project・Build・Repository
   │  ├─ presentation_design.md                  [必須] Graphics・Input・UI・Audio方針
   │  ├─ architecture.md                         [必須] Architecture・Save・性能・診断
   │  ├─ cross_cutting.md                        [必須] Online・Privacy等の横断機能採否
   │  └─ open_questions.md                       [必須] 未決事項・変更・承認履歴
   │
   ├─ scenes/                                    [必須] Unity Sceneを所有境界にした文書
   │  ├─ README.md                               [必須] Scene key・配置・分割規則
   │  ├─ _template/                              [雛形] 実ゲームSceneとして扱わない
   │  │  ├─ acceptance.md                        [雛形] Scene AC
   │  │  └─ design.md                            [雛形] Scene構成・Hierarchy・依存
   │  └─ <scene-key>/                            [追加] 例: title、main-game
   │     ├─ acceptance.md                        [追加] そのSceneだけで完結するAC
   │     └─ design.md                            [追加] Scene asset・遷移・実装マッピング
   │
   └─ shared/                                    [必須] 複数Sceneから共有するUnity単位
      ├─ prefabs/
      │  ├─ README.md                            [必須] 共通Prefab設計規則
      │  └─ <prefab-key>.md                      [追加] Prefab・Variant単位の設計
      ├─ scripts/
      │  ├─ README.md                            [必須] Script・System設計規則
      │  └─ <system-key>.md                      [追加] System・Service・Component単位
      ├─ data/
      │  ├─ README.md                            [必須] Data設計規則
      │  └─ <data-key>.md                        [追加] ScriptableObject・Schema・Master
      ├─ ui/
      │  ├─ README.md                            [必須] 共通UI設計規則
      │  └─ <ui-key>.md                          [追加] HUD・Menu・Dialog・Navigation
      ├─ audio/
      │  ├─ README.md                            [必須] 共通Audio設計規則
      │  └─ <audio-key>.md                       [追加] Mixer・Bus・Snapshot・共通Cue
      └─ assets/
         ├─ README.md                            [必須] 共通Asset設計規則
         └─ <asset-key>.md                       [追加] Material・Shader・Animation・VFX
```

`<scene-key>`、`<prefab-key>`などは説明用placeholderであり、その名前の
ファイルを作るという意味ではありません。実際の対象を表すASCII
kebab-caseへ置き換えます。

## 階層ごとの意図

| 階層 | 所有するもの | ここへ置かないもの |
|---|---|---|
| `unity_design_sheet.md` | 文書構造、入口、ID規則、所有境界 | AC本文、設計本文、検証結果 |
| `game_design/all/` | ゲーム全体、複数Scene、Project全体へ効く判断 | 一つのScene内だけで完結する仕様 |
| `game_design/scenes/<scene-key>/` | 一つのUnity Sceneの体験、Entry/Exit、Hierarchy、Scene固有依存 | 複数Sceneから再利用するPrefabやSystemの詳細 |
| `game_design/shared/` | 複数Sceneから参照する再利用単位とその契約 | Scene固有の配置、演出順、Hierarchy詳細 |
| 各`README.md` | その分類の作成・分割・記述規則 | 承認済みゲーム仕様そのもの |
| `scenes/_template/` | 新しいScene文書の複製元 | 実在SceneのAC、設計、承認記録 |

この分割はファイル数を増やすことが目的ではありません。Unityで変更競合、
所有者、Lifecycle、検証範囲が分かれる単位に設計責任を合わせ、Codexが対象外の
設計まで同時編集することを避けるための境界です。

## 配置判断

新しい要求または設計を記録するときは、次の順で配置先を決めます。

```text
要求は複数Scene・ゲーム全体へ影響するか？
├─ Yes -> all/acceptance.md
└─ No  -> scenes/<scene-key>/acceptance.md

ACを満たす設計は一つのSceneが所有するか？
├─ Yes -> scenes/<scene-key>/design.md
└─ No
   ├─ ゲーム全体のRule・Flow・設定 -> all/の該当文書
   └─ 複数Sceneで再利用するUnity単位 -> shared/<category>/<key>.md
```

- Scene固有UI、Audio cue、Prefab配置はScene設計へ記録する。
- UI shell、AudioMixer、共通Prefabなど複数Sceneで再利用する契約は
  `shared/`へ記録し、Scene設計からその設計IDを参照する。
- 一つの設計項目が複数のUnity単位へ実装される場合も、責務の所有者となる
  文書を一つ決め、実装マッピングへすべてのpathを列挙する。
- 一つのファイルが大きくなったことだけを理由に分割しない。所有者、責務、
  Lifecycle、変更・検証範囲が独立するときに分割する。
- Validation Runや作業レポートは実行証拠であり、この文書階層へ保存しない。

## 文書間の参照

```text
all/acceptance.md または scenes/<scene-key>/acceptance.md
  └─ 関連設計ID: MECH-001
       ⇅ 双方向一致
     all・scene・sharedの所有文書
       ├─ 上流AC: GAME-AC-001 / SCENE-<KEY>-AC-001
       └─ 実装マッピング
          ├─ Unity単位
          ├─ Project相対Path
          ├─ Symbol / Hierarchy
          └─ Planned / Implemented / 廃止
```

ACは期待結果、設計はその期待を満たすルールと構成、実装マッピングは実際の
Unity資産・コードの所在を記録します。同じ内容を複数文書へ複製せず、IDで
参照します。

## ID規則

- ゲーム全体AC: `GAME-AC-001`
- Scene AC: `SCENE-<SCENE-KEY>-AC-001`
- 設計項目: `<DOMAIN>-001`
- 検証Run: 設計IDと上流AC IDの両方を記録する

Scene keyと文書ディレクトリ名は同じASCII kebab-caseとし、AC IDでは大文字の
kebab-caseを使います。例: `title` -> `SCENE-TITLE-AC-001`。

<!-- UNITY_CODEX_PROJECT_OWNED: END -->
