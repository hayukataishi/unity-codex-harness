<!-- UNITY_CODEX_HARNESS_CAPABILITIES: IMPLEMENTED AND HARNESS-MANAGED -->

# Unityハーネス標準実装

> **所有者: Unity Codex Harness**
>
> このファイルは、ハーネスがコード、Skill、Installer、検証スクリプト、
> fixture、CI、回帰テストとして標準実装している能力を定義する
> `harness-managed`文書です。
>
> ゲームごとに選択する要件は
> [Unityハーネス標準・推奨要件](./unity_harness_requirements.md)、
> ゲーム固有の決定は
> [Unityゲーム個別要件・設計書](./unity_design_sheet.md)へ記録します。

## 標準実装の契約

- 標準実装はユーザーへ選択を求めるゲーム要件ではない。
- 「実装済み」は、実装ファイル、検証方法、回帰テストが対応付いている状態を指す。
- ゲーム固有の設計判断やHREQ適用状態をこの文書へ記録しない。
- 通常のゲーム制作では変更せず、ハーネス改善として明示された場合だけ変更する。
- 導入先ではInstallerが`harness-managed`として配布・更新する。
- 未承認の改変を常時検出して作業を停止する完全性検査は未実装であり、
  `HCAP-INTEGRITY-001`として改善対象にする。

## 標準実装一覧

| Capability ID | 状態 | 標準実装 | 主な実装・証拠 | 旧契約ID |
|---|---|---|---|---|
| `HCAP-VALIDATION-001` | 実装済み | Validation Runを終端状態と検証可能な証拠で完結させる | `validate-unity-change`、Validation Run scripts、回帰テスト | `DEBUG-001` |
| `HCAP-REGRESSION-001` | 実装済み | ハーネステンプレート自身をPython回帰テストする | `tests/`、Repository job | `DEBUG-002` |
| `HCAP-FIXTURE-001` | 実装済み | Unity 6.4 fixtureでEditor APIとserializationを検証する | `tests/fixtures/UnityValidationFixture/` | `DEBUG-003` |
| `HCAP-EXTERNAL-001` | 実装済み | 外部MCP・Skillを同梱せず固定参照から診断・導入する | `harness.lock.json`、依存診断CLI | `DEBUG-004` |
| `HCAP-INSTALL-001` | 実装済み | ゲーム所有ファイルを保護して導入・更新する | Installer、manifest、backup、migration bundle | `DEBUG-005` |
| `HCAP-CI-001` | 一部BLOCKED | GameCI runnerとUnity imageを固定して可用性を検査する | Workflow、image検査CLI。remote Unity jobはLicense Secret待ち | `DEBUG-006` |
| `HCAP-DOCS-001` | 実装済み | 標準実装、標準・推奨要件、ゲーム個別設計の所有境界を検査する | Repository validator、Installer回帰 | `DEBUG-007` |
| `HCAP-INTEGRITY-001` | 未実装 | 導入済みharness-managedファイルの未承認改変を常時検出する | 改善ロードマップ | なし |

<a id="hcap-validation-001-validation-run"></a>
## HCAP-VALIDATION-001 Validation Run

- `RunManifest.json`はschema version 2で作成時の`RUNNING`から
  finalize後の`COMPLETED`へ一方向に遷移する。
- `FAIL`、`BLOCKED`、`NOT RUN`を含むRunを`PASS`にしない。
- Unity、License、timeout、Process起動の障害を製品コード失敗と区別する。
- 実在する成果物だけを証拠登録し、サイズとSHA-256を検証する。
- 完了済みRunは上書きせず、追加検証は新しいRunで行う。

実装:

- `.codex/skills/validate-unity-change/scripts/create_validation_run.py`
- `.codex/skills/validate-unity-change/scripts/finalize_validation_run.py`
- `.codex/skills/validate-unity-change/scripts/verify_validation_run.py`
- `.codex/skills/validate-unity-change/scripts/run_unity_validation.py`

受け入れ契約: `DEBUG-001-AC01`、`DEBUG-001-AC02`、
`DEBUG-001-AC03`、`DEBUG-001-AC04`

<a id="hcap-regression-001"></a>
## HCAP-REGRESSION-001 テンプレート回帰

- Installer、静的preflight、Validation Run、文書境界、外部依存、CI定義をPythonテストする。
- 正常系だけでなく、競合、dry-run、欠落、GUID重複、Missing Scriptなどの異常系を検証する。
- Repository jobは`python3 -m unittest discover -s tests -p "test_*.py" -v`を実行する。
- Unity APIを必要とする検証はPythonだけで実行済みと扱わない。

受け入れ契約: `DEBUG-002-AC01`から`DEBUG-002-AC04`

<a id="hcap-fixture-001"></a>
## HCAP-FIXTURE-001 Unity 6.4 fixture

- `tests/fixtures/UnityValidationFixture`をハーネス自身のUnity実行回帰に使用する。
- Unity `6000.4.10f1`、Test Framework、Runtime / Editor / EditMode /
  PlayMode asmdef、Prefab、Scene、Build Profileを固定する。
- Missing Reference、必須参照不足、Prefab instance、Scene、Build Profileを
  Editor APIとPlayModeで検証する。
- fixtureは導入先ゲームへコピーしない。

受け入れ契約: `DEBUG-003-AC01`から`DEBUG-003-AC04`

<a id="hcap-external-001"></a>
## HCAP-EXTERNAL-001 外部MCP・Skill

- Unity MCPと外部Skillをvendorせず、標準Installerも自動取得しない。
- `harness.lock.json`へ固定commit、導入参照、license情報を記録する。
- 診断CLIは不足・版違いを検出するが、外部依存を変更しない。
- MCPがない場合、Editor serializationを必要とする作業をUnity YAML直接編集へ縮退しない。

受け入れ契約: `DEBUG-004-AC01`から`DEBUG-004-AC04`

<a id="hcap-install-001"></a>
## HCAP-INSTALL-001 安全な導入・更新

- 導入対象を`harness-managed`と`project-owned`へ分類する。
- install manifestへpath、ownership、source SHA-256を記録する。
- project-ownedファイルを通常更新、`--force`、`--force-file`で上書きしない。
- harness-managed競合は標準実行を停止し、承認された対象だけbackup後に置換する。
- project-owned template更新は三者比較migration bundleを生成する。

受け入れ契約: `DEBUG-005-AC01`から`DEBUG-005-AC04`

<a id="hcap-ci-001"></a>
## HCAP-CI-001 GameCI

- fixtureのUnity Editorを`6000.4.10f1`へ固定する。
- GameCI test runner commit、Unity image tag、OCI digest、platformをlockする。
- Workflow実行前にDocker Hub metadataとlockを照合する。
- image availabilityとGitHub Actions上のUnity実行結果を別状態で扱う。
- License情報はGitHub Actions Secretsだけで管理する。

受け入れ契約: `DEBUG-006-AC01`、`DEBUG-006-AC02`、
`DEBUG-006-AC03`、`DEBUG-006-AC04`、`DEBUG-006-AC05`

現在の残件:

- Unity License Secretを設定したremote Unity jobの成功
- EditMode / PlayMode Artifactの保存と成功Run記録

<a id="hcap-docs-001"></a>
## HCAP-DOCS-001 文書所有境界

- 本書は標準実装だけを保持する。
- `unity_harness_requirements.md`はゲームへ適用する標準・推奨要件だけを保持する。
- `unity_design_sheet.md`はゲーム固有の決定、適用状態、例外、ACだけを保持する。
- 標準・推奨要件とゲーム個別設計は`HREQ-*` IDで対応付ける。
- Repository validatorとInstaller回帰で文書種別と所有区分を検査する。

受け入れ契約: `DEBUG-007-AC01`、`DEBUG-007-AC02`、
`DEBUG-007-AC03`、`DEBUG-007-AC04`、`DEBUG-007-AC05`

<a id="hcap-integrity-001"></a>
## HCAP-INTEGRITY-001 改変検知

状態: `未実装`

現在はInstaller再実行時にharness-managedファイルの差異を検出できるが、
通常作業開始時、Skill実行前、CIでinstall manifestのSHAと導入済みファイルを
照合する完全性ゲートはない。

完了条件:

1. harness-managedファイルの欠落、内容変更、未知ファイルを検出する。
2. Codexの設計・実装・検証開始前に検査する。
3. CIで未承認改変を失敗させる。
4. 意図的なforkは明示操作と記録を必要とする。
