<!-- UNITY_CODEX_DESIGN: ALL-ARCHITECTURE -->

# Architecture・Save・性能設計

<a id="architecture-profile-record"></a>
<a id="hreq-arch-001-アーキテクチャプロファイル"></a>
## HREQ-ARCH-001: アーキテクチャプロファイル

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

<a id="save-decision-record"></a>
<a id="hreq-save-001-セーブ互換性と復旧"></a>
## HREQ-SAVE-001: セーブ互換性と復旧

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
