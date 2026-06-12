<!-- UNITY_CODEX_DESIGN: ALL-PROJECT -->

# Unity Project・Build・Repository設計

<a id="platform-record"></a>
## HREQ-PLATFORM-001: Unityバージョン・対象プラットフォーム

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

<a id="project-structure-record"></a>
## HREQ-PROJECT-001: プロジェクト構造の適用記録

| 項目 | 決定内容 |
|---|---|
| 自作Asset root | `Assets/Game / 既存構成 / 例外承認` |
| 命名規則の例外 | `なし / 未決定` |
| asmdef構成 | `未決定` |
| `.meta`・GUID運用 | 標準要件を継承 / `例外承認` |

### Tag・Layer・衝突

| 種別 | 名前 | 用途 | 相互作用 |
|---|---|---|---|
| Tag / Layer | `未決定` | `未決定` | `未決定` |

<a id="repository-policy-record"></a>
<a id="hreq-repo-001-repositoryasset運用"></a>
## HREQ-REPO-001: Repository・Asset運用

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

<a id="build-profile-record"></a>
<a id="hreq-build-001-build-profile"></a>
## HREQ-BUILD-001: Build Profile

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
