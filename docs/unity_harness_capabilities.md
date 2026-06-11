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
- 未承認の改変は`HCAP-INTEGRITY-001`の完全性検査で検出し、
  Codex作業、受け入れ、CIを停止する。

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
| `HCAP-INTEGRITY-001` | 実装済み | 導入済みharness-managedファイルの未承認改変を検出して作業を停止する | verifier、Installer check、Skills、CI、回帰テスト | なし |
| `HCAP-DESIGN-BOOTSTRAP-001` | 実装済み | 初期ゲーム設計をマイルストーン別の対話Phaseで決定し、独立Subagent監査する | `bootstrap-game-design`、対話進捗表、Repository回帰 | なし |
| `HCAP-DESIGN-READINESS-001` | 実装済み | 対象マイルストーンの設計完成度を機械判定する | readiness CLI、JSON report、Skills、回帰テスト | なし |

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
- `harness.lock.json`は`harness-managed`として固定commit、導入参照、license情報を記録し、完全性検査で標準pinのdriftを検出する。
- `harness.overrides.json`は`project-owned`として、承認情報付きのゲーム固有差分だけを記録する。
- 診断CLIは標準pinとoverrideを合成し、不足・版違い・不正overrideを検出するが、外部依存を変更しない。
- MCPがない場合、Editor serializationを必要とする作業をUnity YAML直接編集へ縮退しない。

受け入れ契約: `DEBUG-004-AC01`から`DEBUG-004-AC04`、
`DEBUG-004-AC05`

<a id="hcap-install-001"></a>
## HCAP-INSTALL-001 安全な導入・更新

- 導入対象を`harness-managed`と`project-owned`へ分類する。
- install manifestへpath、ownership、source SHA-256を記録する。
- project-ownedファイルを通常更新、`--force`、`--force-file`で上書きしない。
- harness-managed競合は標準実行を停止し、承認された対象だけbackup後に置換する。
- project-owned template更新は三者比較migration bundleを生成する。
- 既存`AGENTS.md`は保持しつつ、harness-managed Agent Contractへの必須参照を
  Installerと完全性Verifierで検査する。未統合の通常導入は書込み前に停止し、
  `--prepare-migration`は比較bundleを生成して導入未完了で終了する。

受け入れ契約: `DEBUG-005-AC01`から`DEBUG-005-AC04`、
`DEBUG-005-AC05`

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
- Installerはruntime文書allowlistだけを導入先へ配布し、評価レポートなどの
  source-only開発履歴をmanifestとゲームProjectへ含めない。
- 旧版で配布済みのsource-only文書は、旧manifest上のharness-managed hashと
  一致する場合だけbackup後に退役し、ローカル変更があれば無変更停止する。
- Repository validatorとInstaller回帰で文書種別と所有区分を検査する。

受け入れ契約: `DEBUG-007-AC01`、`DEBUG-007-AC02`、
`DEBUG-007-AC03`、`DEBUG-007-AC04`、`DEBUG-007-AC05`、
`DEBUG-007-AC06`

<a id="hcap-integrity-001"></a>
## HCAP-INTEGRITY-001 改変検知

状態: `実装済み`

- install manifest schema version 2へ全配布ファイルのownershipと
  source SHA-256を記録する。
- `install-manifest.sha256`でmanifest自体の意図しない変更を検出する。
- verifierはharness-managedファイルの欠落、内容変更、symlink化、
  専有管理ディレクトリ内の未知ファイル、危険なmanifest pathを拒否する。
- project-ownedファイルのゲーム固有変更は完全性エラーにしない。
- Installerの通常完了時と`--check`、7つのUnity Skill、`AGENTS.md`、
  CI回帰で完全性検査を要求する。
- 失敗時はmanifestやsidecarを手編集して追認せず、信頼するハーネスcheckoutから
  Installerを再実行して復旧する。

この検査は誤操作や未レビュー変更を防ぐ運用上の完全性ゲートであり、
リポジトリ管理者がmanifest、sidecar、検査コードを同時に悪意をもって
改ざんする攻撃への暗号学的な防御ではない。そこまで保証するには、
署名付きreleaseと保護された公開鍵を別のtrust rootとして導入する必要がある。

<a id="hcap-design-bootstrap-001"></a>
## HCAP-DESIGN-BOOTSTRAP-001 初期設計対話

状態: `実装済み`

- `$bootstrap-game-design`がConceptからReleaseまで、対象マイルストーンに
  必要な深さだけを10 Phaseで対話する。
- 技術選択の前に目的、選択肢、推奨理由、代替案、トレードオフを説明する。
- 一度に一つ、最大でも密接に関連する三つまでの質問に制限する。
- 無回答、例、推奨、仮定を確定仕様へ変換せず、人間の明示確認を要求する。
- 質問と証跡を`標準推奨`、`ゲーム個別`、`両方`へ分類し、関連HREQ IDを
  記録する。HREQ決定とゲーム固有仕様のどちらか一方だけで完了扱いにしない。
- 対話Run、現在Phase、次の質問、Blocking未決事項、関連設計ID、
  人間承認、監査結果をゲーム設計書へ記録する。
- 回答後の確認待ちでも再開できるよう、質問、提示した選択肢とトレードオフ、
  回答要約、反映案、確認状態を非規範な対話証跡へ保存する。
- ConceptやPrototypeではマイルストーン別の必須深度を適用し、後工程の判断は
  責任者と期限付きで保留できる。
- 上流判断の変更時は影響Phaseを`再検討`へ戻す。
- 主Agentだけがユーザー対話と設計書更新を行う。
- ユーザーがSubagent利用を明示し、multi-agent toolがある場合はPhase終了時と
  最終承認前に`.codex/agents/game-design-auditor.toml`の読み取り専用
  Project Custom Agentを起動し、設計書と対話証跡から漏れ、矛盾、誘導、
  未説明トレードオフを監査する。
- Subagentはユーザーへ直接質問せず、設計書を変更せず、主観判断や承認を代行しない。
- Skill内の`agents/openai.yaml`はUI metadataであり、Subagent定義には使用しない。
- multi-agent toolがない場合は同じrubricを`SELF REVIEW`として実行し、
  独立監査と偽らない。

Subagent監査は対話品質を補助するが、人間の製品判断を代替しない。

<a id="hcap-design-readiness-001"></a>
## HCAP-DESIGN-READINESS-001 マイルストーン別設計完成度

状態: `実装済み`

- `validate_design_readiness.py`がConcept、Prototype、Vertical Slice、
  Alpha、Beta、Releaseごとの必須深度を適用する。
- 必須Phaseの人間承認と監査、HREQ解決、主要設計欄、コアループ、
  勝敗・終了、横断機能、期限付き保留、未決事項を検査する。
- Prototype以降はApproved設計IDと有効AC、入力、Development Build Profile、
  Save採否を要求する。
- Vertical Slice以降は代表Scene、遷移、UI、性能、Build詳細を要求し、
  Alpha以降は実装単位とDraft残存、ReleaseではRelease Build Profileと
  signing・配布経路まで検査する。
- JSON reportを`Artifacts/DesignReadiness/`へ保存できる。
- `FAIL`中は初期設計完了、実装開始、受け入れ完了を主張しない。
