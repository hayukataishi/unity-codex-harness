<!-- UNITY_CODEX_PROJECT_OWNED: EDIT GAME-SPECIFIC DECISIONS IN THIS FILE -->

# Unityゲーム個別要件・設計書

> **所有者: このゲームプロジェクト**
>
> このファイルは、実際に制作するゲームの個別要件、標準要件の適用状態、例外、承認を記録する`project-owned`文書です。
>
> [Unityハーネス標準・推奨要件](./unity_harness_requirements.md)の必須標準は導入時点で継承され、決定必須・条件付き推奨は対話して決定します。この文書へ書かれていないことを理由に必須標準が無効になることはありません。

## 記入ルール

- 空欄や`未決定`は確定仕様ではない。実装へ必要な項目が未決定なら`要確認`として停止する。
- 標準要件と異なる個別要件は、適合表で`例外承認`として理由、影響、代替策、承認者を記録する。
- 標準要件の例を自動採用せず、このゲームで採用した判断だけを個別要件として記録する。
- プレイヤーから見える仕様、技術上の重要判断、横断機能の採否には設計IDを付ける。
- 確定した設計項目には、合否を二択で判定できる受け入れ条件を付ける。
- 発行済みの設計IDとAC IDは変更・再利用しない。不要になった場合は`廃止`と記録する。
- 実行結果の`PASS / FAIL / BLOCKED / NOT RUN`はこの文書へ書かず、Validation Runまたは作業レポートへ記録する。
- ハーネス内部の`DEBUG-*`、CI、Installer、fixture回帰結果をこのファイルへ追加しない。
- この文書の章番号は記入順であり、標準要件との対応番号ではない。対応は共通の`HREQ-*` IDで管理する。

設計ID、AC、検証種別の詳細:

- [標準要件一覧](./unity_harness_requirements.md#standard-requirement-index)
- [設計項目ID](./unity_harness_requirements.md#design-item-id)
- [受け入れ条件の記述形式](./unity_harness_requirements.md#acceptance-criteria-format)
- [DOMAIN分類](./unity_harness_requirements.md#domain-classification)

---

<a id="hreq-conformance"></a>
## 標準要件適合表

適用状態は次のいずれかとする。

| 状態 | 意味 |
|---|---|
| `継承` | 標準要件を変更せず適用する |
| `対象外` | 条件付き推奨の適用条件を満たさない。理由と再評価条件が必要 |
| `例外承認` | 標準と異なる。理由、影響、代替策、承認者が必要 |
| `未決定` | 判断前。依存する実装と受け入れを開始しない |

| HREQ ID | 適用状態 | このゲームでの決定・理由 | 例外時の影響・代替策 | 承認者・日付 |
|---|---|---|---|---|
| `HREQ-DESIGN-001` | 継承 | 設計IDとACで追跡する | なし | 初期導入 |
| `HREQ-PLATFORM-001` | 未決定 | `未決定` | なし | `未決定` |
| `HREQ-PROJECT-001` | 継承 | 命名、配置、`.meta`、GUID安全規則を適用する | なし | 初期導入 |
| `HREQ-ART-001` | 未決定 | 2D制作の採否とProfileを決める | `未決定` | `未決定` |
| `HREQ-CAMERA-001` | 未決定 | Cinemachine採否とversionを決める | `未決定` | `未決定` |
| `HREQ-ARCH-001` | 未決定 | Architecture Profileを決める | `未決定` | `未決定` |
| `HREQ-SAVE-001` | 未決定 | 進行保存の採否と互換方針を決める | `未決定` | `未決定` |
| `HREQ-REPO-001` | 未決定 | RepositoryとAsset運用を決める | `未決定` | `未決定` |
| `HREQ-BUILD-001` | 未決定 | Player buildとBuild Profile採否を決める | `未決定` | `未決定` |
| `HREQ-CROSS-001` | 未決定 | 横断機能の採否を決める | `未決定` | `未決定` |
| `HREQ-VALIDATION-001` | 継承 | 完結したValidation Runで受け入れを判定する | なし | 初期導入 |

---

## 0. 文書情報

| 項目 | 決定内容 |
|---|---|
| プロジェクト名 | `未決定` |
| 作成者・責任者 | `未決定` |
| 作成日 / 更新日 | `未決定` |
| 現在のマイルストーン | Concept / Prototype / Vertical Slice / Alpha / Beta / Release |
| 設計レビュー状態 | Draft / Review / Approved |
| 関連Issue・企画資料 | `なし / 未決定` |

<a id="platform-record"></a>
### HREQ-PLATFORM-001: Unityバージョン・対象プラットフォーム

[Unityバージョン・対象プラットフォーム決定ゲート](./unity_harness_engineering.md#platform-gate)に従って記録する。

| 項目 | 決定内容 |
|---|---|
| Unity Editor完全バージョン | `未決定` |
| 決定根拠 | 既存プロジェクトから検出 / 新規選定 / `未決定` |
| 主対象プラットフォーム | `未決定` |
| 副対象プラットフォーム | `なし / 未決定` |
| 開発時検証環境 | `未決定` |
| 必要なBuild Support | `未決定` |
| 入力方式 | `未決定` |
| 基準解像度・画面向き | `未決定` |
| 目標FPS・性能予算 | `未決定` |
| 配布先・ストア | `未決定` |
| 必要な外部SDK | `なし / 未決定` |
| 既知の制約 | `未決定` |

---

## 1. コンセプト

| 項目 | 決定内容 |
|---|---|
| 一文コンセプト | `未決定` |
| ジャンル | `未決定` |
| 対象プレイヤー | `未決定` |
| 提供する中心体験 | `未決定` |
| 差別化要素 | `未決定` |
| 1プレイの想定時間 | `未決定` |
| 継続プレイの動機 | `未決定` |
| 今回作らないもの | `未決定` |

### 勝利・失敗・終了条件

| 種別 | 条件 | 結果 |
|---|---|---|
| 勝利 | `未決定` | `未決定` |
| 失敗 | `未決定` | `未決定` |
| 中断・終了 | `未決定` | `未決定` |

---

## 2. ゲームループとメカニクス

### コアループ

```text
未決定
```

### メカニクス一覧

| 設計ID | 状態 | メカニクス | 入力・開始条件 | ルール | 結果・報酬 |
|---|---|---|---|---|---|
| `未発行` | Draft | `未決定` | `未決定` | `未決定` | `未決定` |

### パラメータ・計算式

| 名前 | 意味 | 初期値・式 | 上限・下限 | 調整根拠 |
|---|---|---|---|---|
| `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |

### 進行・難易度

| 区間 | 解放要素 | 難易度変化 | 報酬 | 検証方法 |
|---|---|---|---|---|
| `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |

---

## 3. グラフィック・アート

| 項目 | 決定内容 |
|---|---|
| 2D / 3D / Hybrid | `未決定` |
| Render Pipeline | Built-in / URP / HDRP / `未決定` |
| アートスタイル | `未決定` |
| カメラ方式 | `未決定` |
| ライティング方針 | `未決定` |
| 色・可読性方針 | `未決定` |
| VFX方針 | `未決定` |

<a id="art-profile-record"></a>
### HREQ-ART-001: 2Dアートプロファイル

2Dを採用する場合は[2Dアートプロファイル決定ゲート](./unity_harness_requirements.md#art-profile-gate)に従う。

| 項目 | 決定内容 |
|---|---|
| 基準解像度 | `対象外 / 未決定` |
| Pixels Per Unit | `対象外 / 未決定` |
| Pivot | `対象外 / 未決定` |
| Filter Mode | `対象外 / 未決定` |
| Compression | `対象外 / 未決定` |
| Sprite Atlas | `対象外 / 未決定` |
| 承認用サンプル | `対象外 / 未決定` |
| 生成物の出典・License記録先 | `対象外 / 未決定` |

<a id="camera-record"></a>
### HREQ-CAMERA-001: カメラ

| 項目 | 決定内容 |
|---|---|
| Cinemachine採否 | 採用 / 不採用 / 保留 |
| 採用Package version | `対象外 / 未決定` |
| 2.x互換・移行方針 | `対象外 / 未決定` |

| 名前 | 用途 | Package / Component | Target | 切替条件 |
|---|---|---|---|---|
| `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |

---

## 4. アーキテクチャ

<a id="architecture-profile-record"></a>

### HREQ-ARCH-001: アーキテクチャプロファイル

[アーキテクチャプロファイル決定ゲート](./unity_harness_requirements.md#architecture-profile-gate)に従い、現在必要な最小構成を選ぶ。

| 項目 | 決定内容 |
|---|---|
| 選択Profile | Small / Standard / Large / `未決定` |
| 選択理由 | `未決定` |
| Assembly / Package境界 | `未決定` |
| 依存方向 | `未決定` |
| Composition方式 | `未決定` |
| 採用する共有仕組み | `なし / 未決定` |
| 採用しない仕組み | `未決定` |
| 次Profileへの移行条件 | `未決定` |
| 承認者・承認日 | `未決定` |

---

## 5. ゲームフロー

### 状態一覧

| 状態 | 開始条件 | 許可する操作 | 終了条件 | 次状態 |
|---|---|---|---|---|
| `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |

### Scene一覧

| Scene | 役割 | Load方式 | Entry条件 | Exit条件 | Build Profile |
|---|---|---|---|---|---|
| `未決定` | `未決定` | Single / Additive / `未決定` | `未決定` | `未決定` | `未決定` |

### Scene遷移

| From | Trigger | To | 引き継ぐデータ | 失敗時 |
|---|---|---|---|---|
| `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |

---

## 6. Save / Load

<a id="save-decision-record"></a>

### HREQ-SAVE-001: セーブ互換性と復旧

進行を保存する場合は[セーブデータ耐障害性・互換性ゲート](./unity_harness_requirements.md#save-001)に従う。進行保存がない場合も不採用理由を記録する。

| 項目 | 決定内容 |
|---|---|
| 採否 | 採用 / 不採用 / 保留 |
| 保存対象 | `未決定` |
| 端末設定との分離 | `未決定` |
| 保存形式・保存先 | `未決定` |
| Current schema | `未決定` |
| Supported oldest schema | `未決定` |
| Atomic write | `未決定` |
| Backup / rollback | `未決定` |
| Migration | `未決定` |
| Future schema | `未決定` |
| Integrity / encryption | `未決定` |
| Cloud conflict | `対象外 / 未決定` |
| Platform制約 | `未決定` |
| 匿名fixture配置 | `対象外 / 未決定` |

---

## 7. Unity資産と実装単位

<a id="project-structure-record"></a>

### HREQ-PROJECT-001: プロジェクト構造の適用記録

| 項目 | 決定内容 |
|---|---|
| 自作Asset root | `Assets/Game / 既存構成 / 例外承認` |
| 命名規則の例外 | `なし / 未決定` |
| asmdef構成 | `未決定` |
| `.meta`・GUID運用 | 標準要件を継承 / `例外承認` |

### Prefab

| Prefab | 責務 | Root Component | 必須参照 | Owner |
|---|---|---|---|---|
| `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |

### ScriptableObject・マスターデータ

| 型・Asset | 用途 | 主なField | 読込方式 | 更新責任 |
|---|---|---|---|---|
| `未決定` | `未決定` | `未決定` | Direct / Addressables / `未決定` | `未決定` |

### Component・Script

| 型 | 責務 | 依存 | Lifecycle | 対応する設計ID |
|---|---|---|---|---|
| `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |

### Tag・Layer・衝突

| 種別 | 名前 | 用途 | 相互作用 |
|---|---|---|---|
| Tag / Layer | `未決定` | `未決定` | `未決定` |

---

## 8. Input・UI・Audio・演出

### Input

| Action | Device | Binding | Gameplay条件 | Rebind |
|---|---|---|---|---|
| `未決定` | `未決定` | `未決定` | `未決定` | 可 / 不可 / `未決定` |

### UI

| 画面・HUD | 用途 | 表示条件 | 操作 | Accessibility考慮 |
|---|---|---|---|---|
| `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |

### Audio

| Bus / Mixer Group | 用途 | 音量方針 | Ducking / Effect |
|---|---|---|---|
| `未決定` | `未決定` | `未決定` | `未決定` |

### Timeline・演出

| 演出 | Trigger | Timeline / Animator | Skip | 完了通知 |
|---|---|---|---|---|
| `未決定` | `未決定` | `未決定` | 可 / 不可 / `未決定` | `未決定` |

---

## 9. Addressables・性能・診断

| 項目 | 決定内容 |
|---|---|
| Addressables採否 | 採用 / 不採用 / 保留 |
| Group・Label方針 | `対象外 / 未決定` |
| Load / Release責任 | `対象外 / 未決定` |
| FPS予算 | `未決定` |
| Memory予算 | `未決定` |
| Load時間予算 | `未決定` |
| Profiler確認地点 | `未決定` |
| Debug UI / Cheat | `なし / 未決定` |
| Logging・Crash reporting | `なし / 未決定` |

---

## 10. Git・大容量アセット

<a id="repository-policy-record"></a>

### HREQ-REPO-001: Repository・Asset運用

[Git・大容量アセット・Unity Merge決定ゲート](./unity_harness_requirements.md#project-002)に従って選択する。

| 項目 | 決定内容 |
|---|---|
| Default branch | `未決定` |
| Branch寿命・命名 | `未決定` |
| Review・Required CI | `未決定` |
| Merge方式 | `未決定` |
| Release / hotfix経路 | `未決定` |
| LFS採否・対象Path | `未決定` |
| LFS size基準・Quota | `未決定` |
| Serialization mode | `未決定` |
| Meta Files | Visible Meta Files / `未決定` |
| UnityYAMLMerge | 採用 / 不採用 / 保留 |
| Scene・Prefab owner / lock | `未決定` |
| 履歴移行 | なし / 要承認 / `未決定` |

---

## 11. Build Profile・配布

<a id="build-profile-record"></a>

### HREQ-BUILD-001: Build Profile

Unity 6では[Build Profile運用方針](./unity_harness_requirements.md#build-001)に従う。

| Profile asset | Platform | 用途 | Scene List | Defines | Development options | Output |
|---|---|---|---|---|---|---|
| `未決定` | `未決定` | Development / QA / Release | `未決定` | `未決定` | `未決定` | `未決定` |

| 項目 | 決定内容 |
|---|---|
| Clean Build条件 | `未決定` |
| Scripting Backend | `未決定` |
| Architecture | `未決定` |
| Signing・証明書 | `対象外 / 未決定` |
| Store・配布経路 | `未決定` |
| CIで使用するProfile | `未決定` |

---

## 12. 横断機能採否

<a id="cross-cutting-record"></a>

### HREQ-CROSS-001: 横断機能採否

[横断機能採否ゲート](./unity_harness_requirements.md#cross-cutting-gate)に従い、空欄を残さず`採用 / 不採用 / 保留`を記録する。

| 領域 | 状態 | 理由・対象範囲 | Package / Service | データ・規制・安全性 | 設計ID・AC | 再評価条件・期限 |
|---|---|---|---|---|---|---|
| Accessibility | 保留 | `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |
| Localization | 保留 | `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |
| Multiplayer / Online | 保留 | `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |
| Account / Authentication / Cloud Save | 保留 | `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |
| Analytics / Crash Reporting | 保留 | `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |
| Privacy / Consent / Compliance | 保留 | `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |
| Security / Abuse Prevention | 保留 | `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |
| LiveOps / Remote Config | 保留 | `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |
| IAP / Ads / Entitlements | 保留 | `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |
| Moderation / Community | 保留 | `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |
| Modding / UGC | 保留 | `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |
| XR | 保留 | `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |
| Performance / Device Budgets | 保留 | `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |
| Diagnostics / Debug / Cheat Controls | 保留 | `未決定` | `未決定` | `未決定` | `未決定` | `未決定` |

---

## 13. ゲーム固有の設計項目

ここへ実際のゲーム仕様を追加する。ガイドの例をそのまま確定仕様としてコピーせず、観察可能なゲーム挙動として書く。

### `<DOMAIN>-<NNN>`: `<短い名称>`

**状態:** Draft / Approved / 廃止

**仕様**

`未決定`

**依存・影響**

`未決定`

#### 受け入れ条件

| AC ID | 状態 | 検証種別 | 合格条件 | 検証方法 |
|---|---|---|---|---|
| `<DOMAIN>-<NNN>-AC01` | 有効 | `AUTO:EDIT` | `一つの観察可能な結果` | `実行するテストまたは検査` |

---

## 14. 未決事項・承認記録

### 未決事項

| ID | 分類 | 内容 | 影響 | 決定者 | 期限・マイルストーン |
|---|---|---|---|---|---|
| `Q-001` | 要確認 / 仮定 | `未決定` | `未決定` | `未決定` | `未決定` |

### 変更・承認履歴

| 日付 | 対象ID | 変更内容 | 承認者 | 関連Issue / Report |
|---|---|---|---|---|
| `未決定` | `未決定` | `初期作成` | `未決定` | `未決定` |

<!-- UNITY_CODEX_PROJECT_OWNED: END -->
