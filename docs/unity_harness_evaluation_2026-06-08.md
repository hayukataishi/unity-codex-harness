# Unity Codex Harness 評価レポート

- 評価日: 2026-06-08
- 最終更新日: 2026-06-10
- 評価対象: Unity Codex Harness リポジトリ全体
- 評価目的: 最新のUnityゲーム開発をジャンル・規模・対象プラットフォームに依存せず進めるための汎用ハーネスとして、設計、実装支援、検証、再現性、安全性を評価する

## 1. 結論

本テンプレートは、**CodexにUnityプロジェクトを安全かつ追跡可能に扱わせるための運用設計としては高品質**である。一方、**インストール後すぐにコンパイル、テスト、アセット検査、ビルド、CIまで自動実行できる完成済み開発環境ではない**。

現状の最も正確な位置づけは、次の通り。

> 設計・承認・証拠管理に加え、ローカルUnityバッチ検証とハーネス専用CI定義を備えた「Unity AI開発ハーネスの基盤」。
> Editor APIによる資産検査と外部依存の固定は追加済み。ビルド検証、リモートUnity CI、固定した外部ツールの実接続検証を加えることで、汎用的な実運用テンプレートへ発展できる。

### 初回総合評価

| 観点 | 評価 |
|---|---:|
| 運用・承認・トレーサビリティ | 9.0 / 10 |
| Unity資産を壊さないための安全設計 | 8.5 / 10 |
| ゲーム設計テンプレートの網羅性 | 7.5 / 10 |
| Unity 6世代への適合 | 6.5 / 10 |
| ローカル自動化 | 4.0 / 10 |
| CI・ビルド再現性 | 2.0 / 10 |
| 外部ツール・Packageの再現性 | 4.0 / 10 |
| 導入直後の即戦力性 | 3.5 / 10 |
| **総合** | **63 / 100** |

別の言い方をすると、**運用設計テンプレートとしては8/10、ターンキー開発環境としては4/10**である。

### 2026-06-10 再評価サマリー

初回レポートで挙げたP0からP2は、設計契約、Skills、Installer、静的検証、Unity fixtureの範囲では大きく改善した。同じ評価軸での現在値は**78 / 100**、Codex向けUnityハーネス基盤としては**82 / 100**と評価する。

ただし、今回の問いである「Unityプロジェクトへ取り込めば、誰でもCodexへゲーム制作を任せられるか」に対するターンキー評価は**61 / 100**であり、回答は**まだNo**である。

現状で任せやすい範囲:

- 自然言語要求を設計IDと受け入れ条件へ整理する
- C#中心の小規模機能を実装し、静的プリフライトとUnity Test Frameworkで検証する
- Missing Script、Missing Reference、必須資産・必須参照をEditor APIで検査する
- 変更、証拠、未実行、人間レビュー項目を追跡可能に報告する

まだ人間またはプロジェクト固有セットアップが必要な範囲:

- Unity MCPの導入、Codex接続、固定版との互換性確認
- Unityライセンス、Build Support、CI Secret、GameCI実行環境
- Build Profileを使った実Player Build、署名、配布、Store提出
- ゲーム固有Package、入力、Addressables、性能、オンライン機能
- アート方向性、面白さ、操作感、難易度、最終品質の判断
- ハーネス更新時のゲーム固有設計書・設定の安全な移行

詳細な再評価、実行証拠、新しいP0 / P1は[Section 14](#14-2026-06-10-再評価codexへゲーム制作を任せられるか)へ記録する。

## 2. 評価範囲と制約

確認した対象:

- `AGENTS.md`
- `README.md`
- `docs/unity_harness_engineering.md`
- `docs/unity_design_sheet.md`
- `docs/mcp_and_skills_list.md`
- `.codex/skills/`以下の6 Skill
- `scripts/install.py`
- `scripts/validate_repository.py`
- `validate-unity-change`のUnityバッチ検証スクリプト
- `tests/fixtures/UnityValidationFixture`
- `.github/workflows/validate-harness.yml`

このリポジトリのルート自体はUnityプロジェクトではないが、`tests/fixtures/UnityValidationFixture`に自己検証用の最小Unityプロジェクトがある。fixtureではコンパイル、EditMode、PlayModeをローカル実行したが、以下は未評価である。

- Unity MCPとの実接続
- Scene、Prefab、ScriptableObjectのEditor API検査
- 実プラットフォーム向けビルド
- Play Modeの操作と映像・Profiler取得
- GitHub Actions上のUnity job

したがって、本レポートは**テンプレートと自動化コードの評価**であり、実ゲームプロジェクトでのエンドツーエンド合格を示すものではない。

## 3. 最新Unityとの照合

2026-06-08時点で、Unity 6.3は最新LTSとして2027年12月までのサポートが案内されている。Unity 6.4 Updateも公開済みで、新規・開発途中のプロジェクト向けに最新機能、プラットフォーム対応、性能改善を提供するリリース系列である。本ハーネスの実動fixtureは、ローカルへ導入済みの`6000.4.10f1`で検証した。

本テンプレートがUnityバージョンを固定せず、プロジェクトごとにEditor、Package、対象プラットフォームを決定する方針は正しい。ただし、選定を人間とCodexの調査だけに任せており、サポート期限、Package互換性、外部ツール互換性を機械判定する仕組みはない。

現行Unity 6では、次の要素をテンプレートの標準評価対象へ加えるべきである。

- Version Control可能なBuild Profileアセット
- Development / ReleaseごとのBuild Profile
- Unity Test FrameworkとCode Coverage
- Cinemachine 3系
- Input SystemのPackageバージョンと入力デバイス検証
- Accessibilityとスクリーンリーダー対応
- 対象デバイス上でのProfiler・メモリ・ロード時間検証
- Platform Toolkitまたは各プラットフォームサービスの採否
- Addressablesのコンテンツ更新、依存、メモリ、Playerとの互換性検証

## 4. 良い点

### 4.1 設計から検証までの追跡が明確

`<DOMAIN>-<NNN>`と`<DesignId>-AC<NN>`を使い、設計、実装、テスト、証拠を結び付ける方針は強い。`PASS`、`FAIL`、`BLOCKED`、`NOT RUN`の定義も明確で、未実行項目を成功扱いしない。

特に、主観的な「面白さ」「操作感」「難易度」を人間の判断として分離している点は、AIエージェント運用として適切である。

### 4.2 Unity資産の安全境界が具体的

以下の方針は実用性が高い。

- `.meta`とGUIDを保存する
- Scene、Prefab、`.asset`の直接YAML編集を最終手段にする
- Unity MCPまたはEditor APIを優先する
- Package、Unityバージョン、Render Pipeline、Release設定を追加承認対象にする
- 既存資産の一括削除・一括移動・一括改名を抑制する
- 操作後にCompile、Console、参照、Test、Screenshotを確認する

### 4.3 検証証拠の形式がよく設計されている

`Artifacts/ValidationRuns/<RunId>/`以下へ、テストXML、ログ、スクリーンショット、動画、Profiler、Buildを保存する構成は、ローカル作業とCIの両方へ拡張しやすい。

Runを上書きせず、承認済みの比較基準だけを`TestBaselines/`へ昇格する方針も妥当である。

### 4.4 新規・既存プロジェクト双方への配慮がある

既存プロジェクトへ標準フォルダ、命名、asmdefを強制移行しないため、導入時の破壊リスクが低い。Unityプロジェクトルートを固定パスにせず、構造から解決する方針も移植性が高い。

### 4.5 Skillの責務分割が理解しやすい

設計、実装、2Dアセット統合、検証、プレイ観察、報告が分離されている。Skillを増やす条件も定義され、単なるUnity知識を無制限にSkill化しない方針になっている。

## 5. 主要な不足と改善点

### P0: 実行可能なCI・Unityバッチ検証がない（改善中）

初回評価時点では、設計書が要求するコンパイル、EditMode、PlayMode、アセット検査、ビルドに対し、実装済みスクリプトはRun作成と静的プリフライトだけであった。

2026-06-08に、Unity `6000.4.10f1`のfixture、ローカルUnityバッチ検証、Validation Run集計、ハーネス専用GitHub Actionsを追加した。ローカルではCompile、EditMode、PlayModeがPASSしている。

残っているもの:

- Code Coverage実行
- Build Profileを指定した検証ビルド
- GitHub Actions上でのUnity job実行確認
- 導入先ゲーム向けCIテンプレート

GitHub ActionsのUnity jobにはUnityライセンスSecretと、GameCIが提供する正確な`6000.4.10f1` imageが必要である。Workflowは定義済みだが、2026-06-08時点では後者を確認できず、リモート実行結果は`NOT RUN`である。

**改善案:** 次にCode Coverageと代表Build Profileの`build-player`を追加する。GameCI image公開後にGitHub Actionsを実行し、リモート証拠を確定する。

### P0: Missing Referenceと必須資産検査が実装されていない（対応済み）

初回評価時点の`preflight_unity_project.py`が検出するのは、主に次の項目だけであった。

- 必須パス
- `.meta`不足・孤立
- GUID形式・重複
- YAML上の`m_Script: {fileID: 0}`パターン

2026-06-08にEditor API検査器を追加し、Prefab、Scene、ScriptableObjectのMissing Script、解決不能なObject参照、設定JSONで宣言した必須アセットと必須参照を検査可能にした。

引き続き未対応なのは、Build ProfileのScene、Tag、Layer、Input Action、Addressables設定である。PythonのYAML検査は高速プリフライト、正式なオブジェクト参照判定はEditor APIという役割分担になった。

### P0: 外部依存のバージョンが固定されていない（マニフェスト対応済み・実行未検証）

初回評価時点では、Unity MCPとagent-sprite-forgeは同梱されず、「最新版を確認」とだけ記載されていた。

2026-06-09に`harness.lock.json`を追加し、Unity fixtureとPython環境、Unity MCP `v9.7.0`のrelease commit、agent-sprite-forgeのmain commit、`Pillow`と`numpy`の条件、公式参照元を固定した。リポジトリ検査はfixtureのUnity version、40桁commit SHA、Package情報、Python依存、検証状態と理由を検査する。インストーラーはこのマニフェストを導入先ゲームへコピーする。

固定した外部ツールはfixtureへ導入していないため、Unity MCPの実接続とagent-sprite-forgeの実生成は`NOT RUN`である。したがって、現時点で保証するのは「導入対象を再現できること」であり、「Unity `6000.4.10f1`で動作確認済み」であることではない。

**次の改善:** 固定した版を隔離fixtureまたは専用統合プロジェクトへ導入し、接続、基本Editor操作、画像生成、Unity importまでを検証する。定期更新は固定値を自動変更せず、公式情報の検出と人間レビュー付きの回帰検証に分ける。

### P0: インストール後に`Artifacts/`除外が保証されない（対応済み）

初回評価時点では、ハーネス自身の`.gitignore`にだけ`Artifacts/`があり、インストーラーは対象Unityプロジェクトの`.gitignore`を更新していなかった。

2026-06-09にインストーラーへ次を追加した。

- 通常インストールで`.gitignore`へ`/Artifacts/`を安全に追記
- 既存ルール、コメント、LF / CRLF改行を保持するマーカー付き管理
- 再実行時の冪等更新と、壊れたマーカーの拒否
- `--dry-run`で更新予定だけを表示
- `--check`によるGitの実際のignore判定
- Git追跡済み`Artifacts`ファイルの検出と安全な停止

Secret、個人情報、ローカル絶対パスを含む成果物の内容スキャンは、Git除外とは別の多層防御として未対応である。

### P1: Unity 6向けBuild Profile記述へ統一されていない（記述対応済み・実ビルド未検証）

初回評価時点では、設計書にBuild Profilesも登場する一方、シーンフローと検証Skillは旧来の`Build Settings`を中心に説明していた。

2026-06-09に、Unity 6では保存済みBuild Profileアセットをビルド構成の正とする`BUILD-001`を追加した。次を標準化している。

- Development / QA / ReleaseのProfile分類
- ProfileごとのScene List
- 排他的なProfile固有Scripting Defines
- Development Build、Profiler、Deep Profiling、Script Debugging
- Clean Buildの実行条件
- `Assets/Settings/BuildProfiles/<Platform>/`への保存と命名
- Player Settings overrideとグローバル設定の責務分離
- CIでの`-activeBuildProfile`指定
- ProfileまたはPlatformごとのUnityプロセス分離
- 旧Unityと移行前案件のLegacy Build Settings互換方針

リポジトリ検査へ必須記述と旧表現の回帰検査を追加した。Build Profileアセットの作成とProfile指定Player buildはプロジェクト固有のため、ハーネスfixtureでは引き続き`NOT RUN`である。

### P1: Cinemachineの例が2系の名称（記述対応済み・実Package検証未実施）

旧`docs/unity_design_sheet.md`のカメラ例は`CinemachineVirtualCamera`を使用していた。Unity 6の新規案件向け例をCinemachine 3.xの`CinemachineCamera`へ更新し、Package検出と移行規則を`GRAPHICS-001`として定義した。

対応内容:

- `Packages/manifest.json`と`packages-lock.json`から正確なPackageバージョンを検出
- 3.xの`Unity.Cinemachine`名前空間、`CinemachineCamera`、Tracking Targetを標準化
- `CinemachineFollow`、`CinemachinePositionComposer`などのPosition / Rotation Control Componentを使用
- 複数BrainはCinemachine Channelで振り分け
- 2.x既存案件は互換対象として維持し、3.x移行はCinemachine Upgraderと参照検査を伴う独立作業にする
- 旧`FollowCamera`例の再混入をリポジトリ回帰検査で検出

fixtureにはCinemachine PackageとCamera Sceneがないため、実Component作成、2.xから3.xへの移行、Play Mode映像確認は`NOT RUN`である。

### P1: 検証Runが開始状態のまま完結しない（対応済み）

初回評価後に基本的な`finalize_validation_run.py`は追加されていたが、状態遷移、再finalize防止、途中Runの閉鎖、完了後の整合性検証が不足していた。

2026-06-09に`DEBUG-001`として次を追加した。

- schema version 2と`RUNNING`から`COMPLETED`への一方向の状態遷移
- 完了日時、duration、コマンド終了コード、Check・AC別結果、最終結果
- 成果物の相対パス、サイズ、SHA-256
- `RunManifest.sha256`によるManifestの改変検知
- `verify_validation_run.py`による証拠パス、欠落、改変、未記録成果物の検査
- 完了済みRunの再finalize拒否
- `--blocked-reason`による継続不能Runの`BLOCKED`完了
- 不正schema、結果値、AC ID、Run外path、空Checkの拒否

Unity `6000.4.10f1` fixtureでfinalizeとintegrity verificationまで`PASS`した。OS強制終了や電源断はプロセス内で自動finalizeできないため、残った`RUNNING` Runは再開または理由付き`BLOCKED`で閉じる運用とする。

### P1: テンプレート自身の回帰テストが不足（対応済み）

2026-06-09に`DEBUG-002`として、標準Python `unittest`によるテンプレート自己回帰を追加した。

- Installer CLI: 新規導入、冪等な再導入、競合時の無変更停止、`--force`、`--dry-run`、`--skip-agents`、ゲーム固有設定保持
- 静的プリフライト: 正常資産、必須パス不足、`.meta`不足・孤立、不正・重複GUID、Missing Script marker
- Validation Run作成: Unityプロジェクト判定、Run ID衝突・上限、schema、設計ID・AC ID・Platform・Unity version
- 既存回帰: `.gitignore`管理、Run完結・整合性、文書規約、外部依存マニフェスト、GitHub Actions
- `validate_repository.py`: 必須テストファイル、重要な異常系、CIの`unittest discover`規約を自己検査

Python回帰59件とUnity `6000.4.10f1` fixture非回帰が`PASS`した。Pythonテストはファイル操作とCLI契約、Unity fixtureはEditorコンパイル、EditMode、PlayMode、AssetDatabase検査を担当し、両者を別の証拠として扱う。

### P1: 実動サンプルまたはfixture Unityプロジェクトがない（対応済み）

`tests/fixtures/UnityValidationFixture`は以前のP0対応で追加済みであり、この評価項目の前提は古くなっていた。ただし当初はRuntime / EditMode / PlayModeと動的な資産検査だけで、保存済みScene、Prefab、Build Profile、fixture専用Editor asmdefが不足していた。

2026-06-09に`DEBUG-003`として次を追加し、実動fixture契約を完成させた。

- Unity `6000.4.10f1`とTest Framework `1.6.0`
- Runtime / Editor / EditMode / PlayMode asmdef
- `CounterFixture.prefab`と必須`target`参照
- `FixtureScene.unity`と保存済みPrefab instance
- `FixtureDevelopment.asset` Build Profile、Scene List override、`UNITY_CODEX_FIXTURE` Define
- 純粋C#、保存済み資産、PlayMode Sceneロードの正常系
- 動的に生成するMissing Referenceと必須参照不足の異常系
- 必須ファイル、`.meta`、asmdef、Package、資産検査設定を確認するPython fixture契約テスト
- 任意のEditorレビュー手順

基盤fixtureには主観的なゲーム体験がないため、常設の有効な`MANUAL:*` ACは設けず、Inspector確認をREADMEの任意手順として分離した。全有効ACはローカルとCIで再現可能な自動検証とする。

### P1: 汎用性に必要な横断設計が「付録」に留まる（対応済み）

2026-06-09に`PROJECT-001`として、横断機能を付録から正式な実装前ゲートへ昇格した。

- 14領域をAccessibility、Localization、Online、Account、Analytics / Crash、Privacy、Security、LiveOps、IAP / Ads、Moderation、UGC、XR、Performance、Diagnosticsに分類
- 全行を`採用`、`不採用`、`保留`のいずれかへ分類し、空欄を暗黙の不採用として扱わない
- `採用`には対象範囲、Package / Service、データ・規制・安全性、設計ID・AC IDを要求
- `不採用`には理由と再評価条件、`保留`には理由、責任者、期限・マイルストーンを要求
- 保留中の依存導入、通信、データ収集、課金、広告、UGC実装を開始しない
- 高影響領域は人間承認と必要な専門レビューを要求し、Codexが法務・Store・安全性判断を代替しない
- 企画確定、Vertical Slice、Alpha、Release Candidateと条件変更時に再評価
- 設計、Engineering、実装・検証・報告Skill、READMEを同じ契約へ統一

テンプレートのマトリクスは意図的に空欄で配布する。これは「不採用」を意味せず、導入先ゲームが実装開始前に判断すべき未決定事項を可視化するためである。

### P2: アーキテクチャ例が規模に対して強すぎる（対応済み）

初回評価時点では、4層アーキテクチャ、4 asmdef、Manager群、ScriptableObject Event Channel、DI候補が標準形として読めた。中・大規模案件には有用だが、小規模ゲームやGame Jamでは過剰であり、大規模案件ではFeature PackageやPure C# Assemblyの分離が不足する状態だった。

2026-06-09に`ARCH-001`として、`Small`、`Standard`、`Large`の3プロファイル、選択理由、採用しない仕組み、観測可能な移行条件、人間承認、段階移行を正式な実装前ゲートへ追加した。

- `Small`: Unity既定Assemblyまたは単一Runtime asmdef、直接参照、手動Composition、局所イベントを許容する。
- `Standard`: 必要なRuntime / Editor / Tests分離、Feature境界、Pure C#ロジック、Composition Root、依存方向を明示する。
- `Large`: Feature / Module asmdefまたはUPM Package、`No Engine References`を使うPure C# Assembly、公開API、所有者、Architecture Testを扱う。
- 4層、4 Assembly、DI Container、Manager群、ScriptableObject Event Channelを必須セットにしない。
- `Service Locator`は中規模向けの推奨方式から外し、Legacy隔離または段階移行の境界に限定する。
- 既存プロジェクトはテンプレートへ合わせる全面移行をせず、現在の構造を記録して段階的に改善する。

設計、Engineering、実装・検証・報告Skill、README、MCP・Skill一覧を同じ契約へ統一し、旧固定例への回帰をPythonテストで検出する。

### P2: セーブ設計が最低限に留まる（対応済み）

初回評価時点では、JSON、PlayerPrefs、暗号化、versionフィールドだけが例示され、実運用で必要な書込み中断、破損復旧、旧Version移行、未来Version、Cloud競合、鍵管理、Platform差を扱えていなかった。

2026-06-09に`SAVE-001`として、次を正式な実装前ゲートへ追加した。

- Temp、flush、再読込検証、Primary置換によるAtomic writeと、複数ファイルのTransaction境界
- 世代Backup、復旧順、破損隔離、容量・権限・強制終了時のlast known-good保持
- Checksum、認証付き暗号、暗号化の役割分離と鍵管理
- `schemaVersion`、対応可能な最古Version、`N → N+1` Migration、Migration前Backup、downgrade、未来Versionの非破壊拒否
- Stable IDの廃止・統合時に使用する置換表、Tombstone、既定値
- Cloud Revision、競合候補保持、Merge禁止Field、Offline再送、Account切替、削除伝播
- 個人データ、Log除外、保持・削除、Platform別の保存領域・Quota・Suspend・Certification制約
- 旧Version、破損、書込み中断、Backup、未来Version、Storage失敗、Cloud競合の匿名fixtureとテスト行列
- `PlayerPrefs`を非重要な端末設定へ限定し、主セーブやEntitlementの正としない規則

設計、Engineering、実装・検証・報告Skill、README、MCP・Skill一覧を同じ契約へ統一し、旧い最小記述への回帰をPythonテストで検出する。

### P2: Gitと大容量アセット方針が固定例に寄りすぎる（対応済み）

初回評価時点では、`main / develop / feature/*`と`.psd .png .fbx .wav`の一律Git LFS化が記入例になっており、チーム規模、Release方式、Repository容量、Hosting quota、Assetの変更頻度とMerge可否を考慮できなかった。

2026-06-10に`PROJECT-002`として、次を選択・記録する実装前ゲートへ変更した。

- Trunk-based、Short-lived PR branch、Release branch併用、Long-lived integration branchの選択条件
- Default branch、Branch寿命、Required CI、Review、Merge方式、Release / hotfix経路
- Repository容量、増加量、Clone / CI時間、LFS quotaとBandwidth
- 拡張子一律ではなくPath、実測size、変更頻度、Merge可否、再生成可否で決めるLFS基準
- `.meta`をLFSへ入れずAssetと同じ変更へ含め、Generated fileはGit除外する規則
- `Visible Meta Files`、`Force Text`、UnityYAMLMerge、`.gitattributes`、OS別Tool解決
- Scene、Prefab、ProjectSettings、Merge不能BinaryのOwner、Lock、Single-writer、分割方針
- Smart Merge後のUnity Editor、参照、Override、Console、Test検証
- `git lfs migrate`などの履歴rewriteと一括再serializeを承認付きMigrationにする規則

インストーラーはBranch、`.gitattributes`、LFS対象、Serialization modeを自動変更しない。これらは導入先のRepository履歴、Hosting機能、Quota、Team運用を確認した上で決定する。

## 6. 推奨ロードマップ

### フェーズ1: 最低限の実運用化

1. `[完了]` `Artifacts/`のGit除外をインストーラーで保証する。
2. Unity 6.4 Update用の最小fixtureプロジェクトを追加する。
3. Unityバッチ実行でCompile、EditMode、PlayModeを自動化する。
4. Editor APIによるMissing Referenceと必須参照検査を追加する。
5. GitHub Actionsでリポジトリ検査とUnityテストを実行する。

完了条件:

- Pull Requestごとに自動検証が走る
- 失敗時に`Artifacts/ValidationRuns/<RunId>`相当の証拠を取得できる
- 文書上の主要検証項目と実装済み検証項目が一致する

### フェーズ2: 再現性とUnity 6対応

1. `[完了]` Harness、Unity MCP、agent-sprite-forgeの互換性マニフェストを追加する。
2. `[完了]` Build Profile中心のビルド設計へ更新する。
3. `[一部完了: Cinemachine 3]` Cinemachine 3、Input System、Code Coverageの現行例へ更新する。
4. `[完了]` Validation Runのfinalize処理、schema、integrity verificationを追加する。
5. インストーラーへupgrade、backup、diff、version表示を追加する。

### フェーズ3: 汎用ゲーム開発の拡張

1. `[完了]` Accessibility、Localization、Multiplayer、Privacy、LiveOpsを含む14領域の採否ゲートを追加する。
2. `[完了]` Small / Standard / Largeのアーキテクチャプロファイルを追加する。
3. 2Dに加えて3Dアセット、Shader、Lighting、性能予算の統合Skillを追加する。
4. 対象デバイスProfiler、Memory Profiler、ロード時間、Build sizeをACへ接続する。
5. Release前検査、署名、Store提出は別Skillとして承認境界付きで実装する。

## 7. 推奨する完成形

```text
<UNITY_PROJECT_ROOT>/
├─ .codex/skills/
├─ Assets/
│  └─ Game/
│     ├─ Scripts/
│     ├─ Tests/
│     └─ Editor/Validation/
├─ Packages/
├─ ProjectSettings/
├─ BuildProfiles/
├─ TestBaselines/
├─ Artifacts/
├─ docs/
├─ scripts/
│  ├─ unity/
│  │  ├─ run_tests.*
│  │  ├─ validate_assets.*
│  │  ├─ build_player.*
│  │  ├─ finalize_validation_run.py
│  │  └─ verify_validation_run.py
│  └─ harness/
├─ .github/workflows/
├─ harness.lock.json
└─ AGENTS.md
```

Build Profileの実際の保存場所はプロジェクト規約で決定し、Unityが管理するアセットとしてVersion Controlへ含める。

## 8. 実行した検証と結果

| 検証 | 結果 | 備考 |
|---|---|---|
| `python3 scripts/validate_repository.py` | PASS | Skill構造、frontmatter、ローカル文書リンク |
| Python構文コンパイル | PASS | `PYTHONPYCACHEPREFIX`を一時領域へ指定 |
| テンプレート自己回帰 | PASS | Python `unittest` 75件。Installer、preflight、Validation Run、fixture、横断設計、アーキテクチャProfile、Save互換性、Git・LFS規約、文書・CI規約 |
| 横断機能採否ゲート | PASS | `PROJECT-001`、14領域、3状態、承認・停止・再評価規則 |
| アーキテクチャProfile | PASS | `ARCH-001`、Small / Standard / Large、Service Locator非推奨、移行条件 |
| セーブ耐障害性・互換性 | PASS | `SAVE-001`、Atomic write、Backup、Migration、Cloud競合、旧Version fixture |
| Git・大容量アセット運用 | PASS | `PROJECT-002`、Branch選択、LFS基準、Force Text、UnityYAMLMerge、Ownership |
| インストーラー通常実行 | PASS | 一時Unityプロジェクトへ28ファイルを導入 |
| インストーラー再実行 | PASS | 0変更、28ファイルunchanged |
| Validation Run lifecycle | PASS | schema v2、`RUNNING`→`COMPLETED`、finalize、再実行拒否 |
| Validation Run integrity | PASS | Manifest sidecar hash、成果物SHA-256、改変・欠落・未記録検出 |
| 静的プリフライト | PASS | Unity 6.4 fixtureで必須パス、`.meta`、GUIDを検査 |
| Unity Editor compile | PASS | ローカルUnity `6000.4.10f1` |
| EditMode / PlayMode | PASS | EditMode 6件、PlayMode 2件 |
| Unity fixture契約 | PASS | Unity 6.4、4 asmdef、Prefab、Scene、Build Profile、正常系・異常系 |
| GitHub Actions静的job | 定義済み | Workflow構文とローカル相当コマンドはPASS、GitHub上はNOT RUN |
| GitHub Actions Unity job | NOT RUN | Unity Secretと正確なGameCI imageが必要 |
| AssetDatabase参照検査 | PASS | Missing Referenceと必須参照の正常系・異常系 |
| 外部依存マニフェスト | PASS | Unity MCPとagent-sprite-forgeのcommit、要件、`NOT RUN`理由を検査 |
| Build Profile文書規約 | PASS | `BUILD-001`、3分類、Scene List、Defines、Clean Build、CI指定 |
| Build Profile build | NOT RUN | 保存済みProfileとPlayer SceneのEditor API・PlayMode検査はPASS。Player buildは未実行 |
| Cinemachine 3文書規約 | PASS | `GRAPHICS-001`、3.x API、Package検出、2.x移行規則 |
| Cinemachine 3実Component | NOT RUN | fixtureにCinemachine PackageとCamera Sceneがない |
| Unity MCP接続 | NOT RUN | 固定版MCPをfixtureへ未導入・未接続 |

fixtureの`ProjectVersion.txt`は、ローカルで実行確認したUnity `6000.4.10f1`へ固定している。

## 9. 設計との整合性

設計文書、AGENTS指示、各Skillの責務は概ね整合している。主な差異は、**文書が要求する検証能力より、同梱スクリプトの実装範囲が狭いこと**である。

特に次は文書上は要求されるが、ハーネス単体ではまだ自動実行できない。

- Build Profileアセット実体検査 / Profile指定Player build
- Input / Tag / Layer
- Build
- Profiler

## 10. 残課題・リスク

- Unity MCPとagent-sprite-forgeは固定済みだが、fixtureでの実行互換性は未検証である。上流更新の採用には再固定と回帰検証が必要。
- 「最新Unityへの対応」と「既存Unity案件への互換性」は別要件である。Package検出とバージョン別ガイドが必要。
- 文書量が多いため、毎作業で全設計書を読むとコンテキスト効率が落ちる。設計シートを索引と機能別文書へ分割する余地がある。
- 実ゲームでの性能、ビルド、入力、UI、アセット参照は未検証であり、本評価だけで本番利用可能とは判断できない。

## 11. 公式参照

- Unity 6 Releases & Support  
  https://unity.com/releases/unity-6/support
- Unity 6.3 LTS announcement  
  https://unity.com/blog/unity-6-3-lts-is-now-available
- Unity 6.4 release notes  
  https://unity.com/releases/editor/whats-new
- Build Profiles overview  
  https://docs.unity3d.com/Manual/build-profiles.html
- Build Profiles window reference: https://docs.unity3d.com/Manual/build-profiles-reference.html
- Build Profile scene list  
  https://docs.unity3d.com/Manual/build-profile-scene-list.html
- Build a player from the command line: https://docs.unity3d.com/Manual/build-command-line.html
- BuildPlayerWithProfileOptions: https://docs.unity3d.com/ScriptReference/BuildPlayerWithProfileOptions.html
- [PrefabUtility.LoadPrefabContents](https://docs.unity3d.com/ScriptReference/PrefabUtility.LoadPrefabContents.html)
- [SerializedObject](https://docs.unity3d.com/ScriptReference/SerializedObject.html)
- [EditorSceneManager](https://docs.unity3d.com/ScriptReference/SceneManagement.EditorSceneManager.html)
- Unity Test Framework  
  https://docs.unity3d.com/Manual/com.unity.test-framework.html
- Code Coverage  
  https://docs.unity3d.com/Manual/com.unity.testtools.codecoverage.html
- [GameCI Test Runner](https://game.ci/docs/github/test-runner/)
- [GameCI activation](https://game.ci/docs/github/activation)
- [game-ci/unity-test-runner v4.3.1](https://github.com/game-ci/unity-test-runner/releases/tag/v4.3.1)
- Cinemachine package information  
  https://docs.unity3d.com/Manual/com.unity.cinemachine.html
- Cinemachine Camera component 3.1  
  https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/manual/CinemachineCamera.html
- Install and upgrade Cinemachine
  https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/manual/InstallationAndUpgrade.html
- Input System  
  https://docs.unity3d.com/Manual/com.unity.inputsystem.html
- CoplayDev/unity-mcp  
  https://github.com/CoplayDev/unity-mcp/releases/tag/v9.7.0
- CoplayDev/unity-mcp v9.7.0 commit: https://github.com/CoplayDev/unity-mcp/commit/417cf351a152b483c91e6e2deaf7ae355fa8eff3
- 0x0funky/agent-sprite-forge  
  https://github.com/0x0funky/agent-sprite-forge/commit/fff651a89223b044ccfc0b75ed9f3754c6d739b1

## 12. 最終判定

**条件付き採用を推奨する。**

- 設計・承認・安全規約の土台としては採用価値が高い。
- 小規模な試作やCodexとの共同作業には現状でも利用できる。
- チーム開発、継続運用、複数プラットフォーム、本番リリースへ使う前に、P0項目を実装する必要がある。
- 「最新のUnityゲーム開発を汎用的に行える完成環境」と呼ぶには、CIのリモート実行証拠、Build Profileビルド、固定した外部依存の実行確認が不足している。

## 13. 改善進捗

### 2026-06-08: P0-1 ローカルUnity検証基盤

次を追加し、Unity `6000.4.10f1`で実行確認した。

- 最小Unity fixtureプロジェクト
- Runtime、EditMode、PlayMode Assembly
- EditMode / PlayModeテスト各1件
- Unity Editor自動検出とバッチテスト実行
- Validation Runの最終結果、終了時刻、所要時間、終了コード
- 成果物一覧、サイズ、SHA-256
- ランナーと集計処理のPython回帰テスト

実行結果:

- Static preflight: `PASS`
- Compile: `PASS`
- EditMode: `PASS`、1件
- PlayMode: `PASS`、1件

### 2026-06-08: P0-1 ハーネス専用CI定義

次を追加した。

- GitHub Actionsの`Repository` job
- Unity 6.4 fixtureを実行する`Unity 6.4 Fixture` job
- UnityライセンスSecretの事前検査
- 外部Actionのcommit SHA固定検査
- Unityテスト結果とログのArtifact保存
- fork由来Pull RequestでUnity Secretを使用しない実行条件

境界:

- CIとfixtureはハーネス自身の回帰検証専用
- `scripts/install.py`はSkill、docs、AGENTSに加え、Editor検査器と設定JSONを導入先ゲームへコピー
- 導入先ゲームにはこのWorkflowやfixtureをコピーしない

確認結果:

- Workflow YAML解析: `PASS`
- リポジトリ検査: `PASS`
- Python回帰テスト: `PASS`、14件
- fixture静的プリフライト: `PASS`
- GitHub Actions上のUnity job: `NOT RUN`

リモートUnity jobは、Repository Secretsの設定と、GameCIによる正確なUnity `6000.4.10f1` imageの提供を確認してから実行する。

未実施:

- GitHub Repository Secretsの`UNITY_EMAIL`、`UNITY_PASSWORD`、`UNITY_LICENSE`または`UNITY_SERIAL`は未設定
- GameCIの正確なUnity `6000.4.10f1` Docker imageは未確認
- 上記2点が未完了のため、GitHub Actionsの`Unity 6.4 Fixture` jobは未実行

### 2026-06-08: P0-2 Editor API資産検査

次を追加した。

- Editor専用の`UnityCodexHarness.Validation.Editor` Assembly
- Prefab、Scene、ScriptableObjectのMissing Script検査
- 解決不能なSerialized Object参照の検査
- 必須アセットの存在・型検査
- Prefab、Scene、ScriptableObjectの必須参照検査
- `ProjectSettings/UnityCodexHarnessAssetValidation.json`によるゲーム固有ルール
- `run_unity_validation.py`へのAsset validation checkとJSON証拠
- インストーラーによるEditor検査器と設定JSONの導入

Unity `6000.4.10f1`実行結果:

- Validation Run: `Artifacts/ValidationRuns/20260608T145026Z`
- Static preflight: `PASS`
- Compile: `PASS`
- EditMode: `PASS`、4件
- PlayMode: `PASS`、1件
- Asset validation: `PASS`
- 必須参照欠落の異常系: 検出テスト`PASS`
- 参照先Asset削除によるMissing Reference異常系: 検出テスト`PASS`

未対応:

- Tag、Layer、Input Action、Addressables設定
- Build ProfileのScene Listと必須Build Profile
- Material、Animator Controllerなど、Scene・Prefab・ScriptableObject以外の専用検査

残るP0:

- GitHub Actions Unity jobのリモート実行確認

- インストール先プロジェクトの`Artifacts/` Git除外保証

### 2026-06-09: P0-3 外部依存の互換性マニフェスト

次を追加した。

- `harness.lock.json`によるUnity fixture、Python、外部ツールの固定情報
- Unity MCP `v9.7.0`とrelease commit `417cf351a152b483c91e6e2deaf7ae355fa8eff3`
- agent-sprite-forge commit `fff651a89223b044ccfc0b75ed9f3754c6d739b1`
- `numpy>=1.26`、`Pillow>=10.0`のPython依存条件
- Release、commit、Package metadata、requirementsへの公式参照
- fixtureのUnity version、commit SHA、Package情報、Python依存、検証状態の静的検査
- インストーラーによる導入先ゲームへのマニフェスト配布

確認結果:

- リポジトリ検査: `PASS`
- Python回帰テスト: `PASS`、19件
- Unity `6000.4.10f1`回帰検証: `PASS`
- Compile: `PASS`
- EditMode: `PASS`、4件
- PlayMode: `PASS`、1件
- Asset validation: `PASS`
- Unity MCP `v9.7.0`のfixture接続: `NOT RUN`
- agent-sprite-forgeの画像生成とUnity import: `NOT RUN`

検証成果物:

- `tests/fixtures/UnityValidationFixture/Artifacts/ValidationRuns/20260609T000618Z/`

検証中、sandbox内ではUnity Package ManagerがIPC socketを作成できず失敗し、sandbox外の初回実行では孤立したLicensing Clientとの競合が発生した。孤立プロセスを終了したクリーン再実行で全チェックがPASSした。これはコード回帰ではなくローカル実行環境の制約として扱う。

未実施:

- Unity MCPはfixtureへ未導入で、基本Editor操作との互換性を実行確認していない
- agent-sprite-forgeは未導入で、固定Python依存による生成を実行確認していない
- 固定値の更新通知と定期回帰検証は未実装

残るP0:

- GitHub Actions Unity jobのリモート実行確認

### 2026-06-09: P1-1 Unity 6 Build Profile記述の統一

次を追加・更新した。

- `BUILD-001`による保存済みBuild Profile中心の設計
- `Assets/Settings/BuildProfiles/<Platform>/`の保存場所と命名
- Development / QA / Releaseの用途と標準設定
- ProfileごとのScene Listと`Override Global Scene List`
- `GAME_BUILD_DEVELOPMENT`、`GAME_BUILD_QA`、`GAME_BUILD_RELEASE`
- Profile固有Player Settings overrideとグローバル設定の責務分離
- Development Build、Profiler、Debugger設定
- Clean Build条件と`BuildOptions.CleanBuildCache`
- CIの`-activeBuildProfile`指定とPlatformごとのUnityプロセス分離
- Legacy Build Settingsを旧Unity・移行前案件だけに限定する互換方針
- 実装、検証、報告SkillのBuild Profile対応
- 旧Build Settings中心の表現を検出するリポジトリ回帰検査

`BUILD-001`受け入れ条件:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `BUILD-001-AC01` | `PASS` | Scene・Build説明がBuild Profile Scene List中心 |
| `BUILD-001-AC02` | `PASS` | 3分類、Defines、Debug、Clean Build、保存規則を確認 |
| `BUILD-001-AC03` | `PASS` | CIが`-activeBuildProfile`を明示 |

確認結果:

- リポジトリ検査: `PASS`
- Python回帰テスト: `PASS`、33件
- Build Profile必須記述検査: `PASS`
- 旧Build Settings表現の異常系: 検出テスト`PASS`
- Unity `6000.4.10f1` fixture回帰: `PASS`
  - Run ID: `20260609T014700Z`
  - Compile: `PASS`
  - EditMode: `PASS`、4件
  - PlayMode: `PASS`、1件
  - Asset validation: `PASS`、error 0 / warning 0
  - 証拠: `tests/fixtures/UnityValidationFixture/Artifacts/ValidationRuns/20260609T014700Z/`

未実施:

- fixtureへの保存済みBuild ProfileとPlayer Sceneの追加
- Profileを指定した実Player build
- Build Profile Scene ListとProfile固有設定のEditor API自動検査

このP1は「Build Profile記述の統一」として対応済みである。実Profileの作成・ビルド・検査は後続のビルド自動化課題として残る。

### 2026-06-09: P0-4 インストール先の`Artifacts/` Git除外保証

次を追加した。

- 通常インストールでの管理マーカー付き`/Artifacts/`ルール
- 既存`.gitignore`のルール、コメント、LF / CRLF改行の保持
- 再インストール時に重複しない冪等更新
- 壊れた管理マーカーの検出と安全な停止
- `--dry-run`での`.gitignore`更新予定表示
- `--check`による実際のGit ignore判定
- Git追跡済み`Artifacts`ファイルがある場合の検出とインストール停止
- 新規・既存Unityプロジェクトを模したCLI統合テスト

確認結果:

- リポジトリ検査: `PASS`
- Python回帰テスト: `PASS`、31件
- fixtureの`Artifacts` ignore検査: `PASS`
- installer CLI導入・再検査: `PASS`
- dry-run非変更確認: `PASS`
- 追跡済み`Artifacts`異常系: 検出テスト`PASS`
- Unity `6000.4.10f1`回帰検証: `PASS`
- Compile: `PASS`
- EditMode: `PASS`、4件
- PlayMode: `PASS`、1件
- Asset validation: `PASS`

検証成果物:

- `tests/fixtures/UnityValidationFixture/Artifacts/ValidationRuns/20260609T003033Z/`

未対応:

- 成果物内のSecret、個人情報、ローカル絶対パスの自動スキャン
- GitHub Actions Unity jobのリモート実行確認

残るP0:

- GitHub Actions Unity jobのリモート実行確認

### 2026-06-09: P1-2 Cinemachine 3.x記述への統一

次を追加・更新した。

- `GRAPHICS-001`によるUnity 6向けCinemachine 3.x設計
- `CinemachineVirtualCamera`だった追従カメラ例を`CinemachineCamera`へ更新
- `Unity.Cinemachine`名前空間、Tracking Target、Look At Targetの使い分け
- `CinemachineFollow`、`CinemachinePositionComposer`などのPosition / Rotation Control Component
- `CinemachineBrain`とCinemachine Channelの責務
- `Packages/manifest.json`と`packages-lock.json`による正確なPackageバージョン検出
- Cinemachine 2.x既存案件を互換対象とする方針
- 2.xから3.xへの移行でCinemachine UpgraderとScene・Prefab・Timeline・Animation・コード参照を検査する規則
- 実装、検証、報告SkillのCinemachine 3.x対応
- 旧2.x追従カメラ例の再混入を検出するリポジトリ回帰検査

`GRAPHICS-001`受け入れ条件:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `GRAPHICS-001-AC01` | `PASS` | カメラ例が`CinemachineCamera`と3.x制御Componentを使用 |
| `GRAPHICS-001-AC02` | `PASS` | Package検出、名前空間、Target、Channelを確認 |
| `GRAPHICS-001-AC03` | `PASS` | 2.x互換方針とUpgraderを使う移行規則を確認 |

確認結果:

- リポジトリ検査: `PASS`
- Python回帰テスト: `PASS`、35件
- Cinemachine 3必須記述検査: `PASS`
- 旧Cinemachine 2カメラ例の異常系: 検出テスト`PASS`
- Unity `6000.4.10f1` fixture非回帰: `PASS`
  - Run ID: `20260609T032827Z`
  - Compile: `PASS`
  - EditMode: `PASS`、4件
  - PlayMode: `PASS`、1件
  - Asset validation: `PASS`、error 0 / warning 0
  - 証拠: `tests/fixtures/UnityValidationFixture/Artifacts/ValidationRuns/20260609T032827Z/`

未実施:

- fixtureへのCinemachine 3.x Package導入
- `CinemachineBrain`、`CinemachineCamera`、Tracking Target、ChannelのEditor API検査
- Cinemachine 2.xから3.xへの実移行
- Cinemachineカメラを使用したPlay Mode映像確認

このP1は「Cinemachineの例を3.xへ統一する」ところまで対応済みである。実Package、Camera Scene、移行検証は、Cinemachineを採用するゲームプロジェクトで行う。

### 2026-06-09: P1-3 Validation Runの完結性と整合性

次を追加・更新した。

- `DEBUG-001`によるValidation Runライフサイクル設計
- schema version 2の`RUNNING` / `COMPLETED`状態
- 完了日時、duration、コマンド終了コード、Check・AC別結果、最終結果
- 原子的なReport・Manifest更新
- 成果物の相対パス、サイズ、SHA-256
- `RunManifest.sha256` sidecar
- 完了済みRunの再finalize拒否
- `--blocked-reason`による継続不能Runの明示的な終了
- `verify_validation_run.py`によるManifest、証拠パス、成果物の整合性検査
- 不正なNUnit数値属性を`FAIL`として完結させる処理
- 導入先ゲームへfinalizerとverifierをコピーするインストーラー回帰検査

`DEBUG-001`受け入れ条件:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `DEBUG-001-AC01` | `PASS` | Python CLI回帰とUnity実Runで`RUNNING`から`COMPLETED`を確認 |
| `DEBUG-001-AC02` | `PASS` | 再finalize拒否と理由付き`BLOCKED`完了を確認 |
| `DEBUG-001-AC03` | `PASS` | sidecar hash、成果物SHA-256、完了後の変更検出を確認 |

確認結果:

- リポジトリ検査: `PASS`
- Python回帰テスト: `PASS`、40件
- Python構文コンパイル: `PASS`
- Unity `6000.4.10f1` lifecycle回帰: `PASS`
  - Run ID: `20260609T045212Z`
  - State: `COMPLETED`
  - Result: `PASS`
  - Compile: `PASS`
  - EditMode: `PASS`、4件
  - PlayMode: `PASS`、1件
  - Asset validation: `PASS`、error 0 / warning 0
  - Integrity verification: `PASS`
  - 証拠: `tests/fixtures/UnityValidationFixture/Artifacts/ValidationRuns/20260609T045212Z/`

既知の境界:

- OS強制終了、電源断、プロセス強制killでは、そのプロセス自身によるfinalizeはできない
- その場合は残った`RUNNING` Runを調査し、再開するか`--blocked-reason`で閉じる
- 暗号署名や外部の改ざん防止ストレージは提供しない。SHA-256は偶発的な変更と成果物不整合の検出を目的とする

### 2026-06-09: P1-4 テンプレート自身の回帰テスト

次を追加・更新した。

- `DEBUG-002`によるテンプレート自己回帰の設計と受け入れ条件
- Installer CLIの正常系・異常系7件
- 静的プリフライトの正常系・異常系6件
- Validation Run作成とRun ID衝突の正常系・異常系4件
- 必須回帰ファイル、重要ケース、CIの`unittest discover`を守るリポジトリ自己検査2件
- README、Engineering、検証・報告Skillの自己回帰実行規約

`DEBUG-002`受け入れ条件:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `DEBUG-002-AC01` | `PASS` | 一時UnityプロジェクトでInstaller CLIの導入、再導入、競合、force、dry-run、skip、設定保持を検証 |
| `DEBUG-002-AC02` | `PASS` | `.meta`、GUID、Missing Script、必須パスの正常系・異常系を検証 |
| `DEBUG-002-AC03` | `PASS` | 無効プロジェクトの無変更拒否、Run ID衝突・上限、Manifest記録を検証 |
| `DEBUG-002-AC04` | `PASS` | Workflowの自動検出コマンドと必須回帰ファイルをリポジトリ検査で検証 |

確認結果:

- リポジトリ検査: `PASS`
- Python回帰テスト: `PASS`、59件
- Python構文コンパイル: `PASS`
- Unity `6000.4.10f1` fixture非回帰: `PASS`
  - Run ID: `20260609T053752Z`
  - State: `COMPLETED`
  - Result: `PASS`
  - Compile: `PASS`
  - EditMode: `PASS`、4件
  - PlayMode: `PASS`、1件
  - Asset validation: `PASS`、error 0 / warning 0
  - Integrity verification: `PASS`
  - 証拠: `tests/fixtures/UnityValidationFixture/Artifacts/ValidationRuns/20260609T053752Z/`

既知の境界:

- GitHub Actions Repository jobは定義とローカル相当コマンドが`PASS`だが、GitHub上ではまだ`NOT RUN`
- GitHub Actions Unity jobはUnityライセンスSecretと正確なGameCI Unity imageが未準備のため`NOT RUN`
- Unity fixtureはハーネス基盤の非回帰を確認する最小プロジェクトであり、実ゲーム固有のScene、Build Profile、Package構成は導入先ごとに追加検証する

### 2026-06-09: P1-5 Unity 6.4実動fixture

既存の`tests/fixtures/UnityValidationFixture`を棚卸しし、部分対応だった実動fixtureを`DEBUG-003`として完成させた。

追加・更新内容:

- fixture専用Editor asmdefと資産パス契約
- Unity Editor APIで生成した保存済みPrefab、Scene、Build Profileと`.meta`
- Build ProfileのScene List overrideと`UNITY_CODEX_FIXTURE` Define
- Prefab必須参照とScene内Prefab instanceのEditMode検査
- 保存済み`FixtureScene`をロードするPlayMode検査
- Missing Referenceと必須参照不足を動的生成する異常系
- fixtureの必須ファイル、asmdef、Package、資産検査設定を守るPython回帰4件
- `DEBUG-003`の設計、AC、README、Engineering契約

`DEBUG-003`受け入れ条件:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `DEBUG-003-AC01` | `PASS` | Python fixture契約と静的プリフライトでUnity version、Test Framework、4 asmdef、保存済み資産と`.meta`を確認 |
| `DEBUG-003-AC02` | `PASS` | EditModeでPrefab参照、Scene内Prefab instance、Build Profile Scene List・Defineを公開Editor APIから確認 |
| `DEBUG-003-AC03` | `PASS` | 正常fixtureのAsset validationと、Missing Reference・必須参照不足の異常系を確認 |
| `DEBUG-003-AC04` | `PASS` | PlayModeで`FixtureScene`をロードし、`CounterFixture`の参照とカウンター動作を確認 |

確認結果:

- リポジトリ検査: `PASS`
- Python回帰テスト: `PASS`、63件
- 静的プリフライト: `PASS`、asset / directory 29件、`.meta` 29件
- Unity `6000.4.10f1` fixture: `PASS`
  - Run ID: `20260609T062753Z`
  - State: `COMPLETED`
  - Result: `PASS`
  - Compile: `PASS`
  - EditMode: `PASS`、6件
  - PlayMode: `PASS`、2件
  - Asset validation: `PASS`、Scene 1 / Prefab 1 / 必須資産 4 / 必須参照 1 / error 0
  - Integrity verification: `PASS`
  - 証拠: `tests/fixtures/UnityValidationFixture/Artifacts/ValidationRuns/20260609T062753Z/`

既知の境界:

- 保存済みBuild Profileを使用したPlayer buildはまだ`NOT RUN`
- GitHub Actions Unity jobはUnityライセンスSecretと正確なGameCI Unity imageが未準備のため`NOT RUN`
- fixtureはハーネス自身の回帰専用であり、`scripts/install.py`から導入先ゲームへコピーしない

### 2026-06-09: P1-6 横断機能採否ゲート

横断機能を付録の検討候補から、全ゲームで採否を記録するSection 20へ移動した。

追加・更新内容:

- `PROJECT-001`と3つの静的AC
- 14領域の横断機能採否マトリクス
- `採用` / `不採用` / `保留`の記録要件と実装可否
- 高影響領域の人間承認、専門レビュー、法務判断を代替しない規則
- 企画確定、Vertical Slice、Alpha、Release Candidate、条件変更時の再評価
- `maintain-game-design`、`implement-unity-feature`、`validate-unity-change`、`report-unity-work`へのゲート接続
- READMEとMCP・Skill一覧の導入手順
- Privacy行欠落と横断領域の付録回帰を検出するPythonテスト3件

`PROJECT-001`受け入れ条件:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `PROJECT-001-AC01` | `PASS` | 14領域と3状態をリポジトリ文書検査で確認 |
| `PROJECT-001-AC02` | `PASS` | 採用時の設計・依存・データ要件、不採用・保留時の理由・再評価要件を確認 |
| `PROJECT-001-AC03` | `PASS` | 人間承認、保留中の実装停止、マイルストーン・条件変更時の再評価を確認 |

確認結果:

- リポジトリ検査: `PASS`
- Python回帰テスト: `PASS`、66件
- Python構文コンパイル: `PASS`
- 横断領域必須記述検査: `PASS`
- Privacy行欠落の異常系: 検出テスト`PASS`
- 付録だけへ戻る異常系: 検出テスト`PASS`
- Unity fixture: 非該当。Unityコード、Scene、Prefab、Package、ProjectSettingsは変更していない

導入先ゲームで必要な作業:

- テンプレートの空欄は未決定を表すため、実装開始前に全14行を埋める
- `採用`を選んだ領域はゲーム固有の設計ID・ACへ接続する
- Privacy、課金、広告、Online、Account、Analytics、UGC、Moderationは対象地域・Store・年齢区分に応じて専門レビューを行う

### 2026-06-09: P2-1 規模別アーキテクチャプロファイル

固定的な4層・4 Assembly・Manager群・DI・Event Channel例を、プロジェクト規模と観測された複雑さに応じて選ぶゲートへ変更した。

追加・更新内容:

- `ARCH-001`と3つの静的AC
- `Small`、`Standard`、`Large`の適用状況、構造、非必須事項
- 選択Profile、理由、現在の複雑さ、採用境界、採用しない仕組み、移行条件、承認の記録欄
- `Small`から`Standard`、`Standard`から`Large`への観測可能な再評価条件
- Profile変更時の人間承認、依存図、公開API、serialized reference、Package、テスト、Build Profile影響の確認
- 4 Assemblyを`Standard`の基準例へ変更し、`Small`ではUnity既定Assemblyも許容
- `Large`でFeature / Module asmdef、UPM Package、Pure C# Assembly、`No Engine References`、Architecture Testを選択可能にした
- Service Locatorを規模別推奨から外し、Legacy隔離または段階移行へ限定
- Manager、Singleton、DI Container、ScriptableObject Event Channelを用途と生存期間が明確な場合だけ採用する規則
- Engineering、実装・検証・報告Skill、README、MCP・Skill一覧へのゲート接続
- Large Profile欠落とService Locator中規模推奨への回帰を検出するPythonテスト3件

`ARCH-001`受け入れ条件:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `ARCH-001-AC01` | `PASS` | 3 Profileの適用状況、構造、非必須事項、選択記録を静的検査で確認 |
| `ARCH-001-AC02` | `PASS` | asmdef、Layer、DI、Manager、イベントを選択事項とし、Service Locatorの規模別推奨を除去 |
| `ARCH-001-AC03` | `PASS` | 観測可能な再評価条件、人間承認、影響調査、段階移行を確認 |

確認結果:

- リポジトリ検査: `PASS`
- Python回帰テスト: `PASS`、69件
- Python構文コンパイル: `PASS`
- アーキテクチャProfile必須記述検査: `PASS`
- Large Profile欠落の異常系: 検出テスト`PASS`
- Service Locator中規模推奨の異常系: 検出テスト`PASS`
- Unity fixture: 非該当。Unityコード、Scene、Prefab、Package、ProjectSettingsは変更していない

導入先ゲームで必要な作業:

- 新規ゲームは実装開始前に`Small`、`Standard`、`Large`のいずれかと選択理由を記録する
- 既存ゲームは現在の構造を調査し、テンプレートへ合わせる全面移行を行わない
- 移行条件が観測された場合だけ、影響範囲と段階計画を作成して人間承認を得る

### 2026-06-09: P2-2 セーブデータ耐障害性・互換性

保存形式とversionフィールドだけだったSection 8を、進行データを破損・中断・Version差・Cloud競合から守る実装前ゲートへ変更した。

追加・更新内容:

- `SAVE-001`と4つの静的AC
- 保存対象、Slot / Profile / Account、Serialization、Data model、保存先、保存契機、Transaction境界の決定表
- Atomic write、世代Backup、Integrity、復旧順、Save要求直列化、失敗時UX
- `schemaVersion`、対応可能な最古Version、`N → N+1` Migration、Migration前Rollback、未来Versionとdowngrade
- 複数ファイルSaveのGeneration / Commit manifestとStable ID Migration
- Cloud conflict、Revision、Merge禁止Field、Offline retry idempotency、Account切替
- 暗号・Integrity・改ざん検出の役割分離、鍵管理、Privacy、Platform制約
- 匿名fixtureとRound trip、Interrupted write、Corruption、Backup、Migration、Future schema、Storage failure、Cloud conflictのテスト行列
- Engineering、実装・検証・報告Skill、README、MCP・Skill一覧へのゲート接続
- Atomic write欠落とPlayerPrefs主セーブ化への回帰を検出するPythonテスト3件

`SAVE-001`受け入れ条件:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `SAVE-001-AC01` | `PASS` | Atomic write、Backup、Integrity、復旧順、直列化、失敗時UXの決定欄を静的検査で確認 |
| `SAVE-001-AC02` | `PASS` | Migration、未来Version、downgrade、最古対応Version、Migration前Rollbackを確認 |
| `SAVE-001-AC03` | `PASS` | Cloud競合、Platform制約、鍵管理、Privacy、PlayerPrefs用途制限を確認 |
| `SAVE-001-AC04` | `PASS` | 旧Version、書込み中断、破損、Backup、未来Version、失敗処理、Cloud競合のテスト行列を確認 |

確認結果:

- リポジトリ検査: `PASS`
- Python回帰テスト: `PASS`、72件
- Python構文コンパイル: `PASS`
- セーブ互換性必須記述検査: `PASS`
- Atomic write欠落の異常系: 検出テスト`PASS`
- PlayerPrefs主セーブ化の異常系: 検出テスト`PASS`
- Unity fixture: 非該当。Unityコード、Scene、Prefab、Package、ProjectSettingsは変更していない

導入先ゲームで必要な作業:

- `SAVE-001`の決定表をゲーム固有のSchema、Platform、Slot、Cloud採否で埋める
- 対応する旧Schemaの匿名fixtureを作成し、Migrationと中断・破損・失敗注入テストを実装する
- Cloud Save採用時はAccount、Privacy、Securityの横断機能行を承認し、競合規則をゲーム固有に決定する

### 2026-06-10: P2-3 Git・大容量アセット・Unity Merge方針

固定的なBranch名と拡張子一律LFS例を、Repository特性とTeam運用に応じて選ぶ`PROJECT-002`へ変更した。

追加・更新内容:

- `PROJECT-002`と4つの静的AC
- Git hosting、Default branch、Branch strategy、Branch lifetime、Merge policy、Release / hotfixの選択記録
- Repository容量、増加量、Clone時間、CI checkout / cache、LFS quotaの予算
- Path、実測size、変更頻度、Merge可否、Source / Generated区分によるLFS criteria
- Git attributesがsize条件を直接表現しないため、閾値をpre-commitまたはCIで検査する規則
- `.meta`の通常Git管理、LFS object取得、pointer、`git lfs fsck`検査
- `Visible Meta Files`と`Force Text`、既存Projectの承認付き再serialize移行
- UnityYAMLMerge、`.gitattributes`、Binary fallback、Merge後のEditor検証
- Scene、Prefab、ProjectSettings、Lighting、NavMesh、Timeline、TerrainなどのOwner / Lock / Single-writer規則
- `git lfs migrate`やfilter-repoによる履歴rewriteのBackup、承認、全Clone再同期
- Engineering、実装・検証・報告Skill、README、MCP・Skill一覧へのゲート接続
- Visible Meta Files欠落と固定Branch・拡張子一律LFSへの回帰を検出するPythonテスト3件

`PROJECT-002`受け入れ条件:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `PROJECT-002-AC01` | `PASS` | Branch strategy、Default branch、CI、Review、Release / hotfix、再評価条件を静的検査で確認 |
| `PROJECT-002-AC02` | `PASS` | size・変更頻度・Merge可否・QuotaによるLFS判断、`.meta`、Generated file、履歴rewrite規則を確認 |
| `PROJECT-002-AC03` | `PASS` | Visible Meta Files、Force Text、UnityYAMLMerge、`.gitattributes`、既存Project移行を確認 |
| `PROJECT-002-AC04` | `PASS` | Scene、Prefab、ProjectSettings、Binary AssetのOwnership、Lock、分割、競合後検証を確認 |

確認結果:

- リポジトリ検査: `PASS`
- Python回帰テスト: `PASS`、75件
- Python構文コンパイル: `PASS`
- Git・LFS方針必須記述検査: `PASS`
- Visible Meta Files欠落の異常系: 検出テスト`PASS`
- 固定Branch・拡張子一律LFSの異常系: 検出テスト`PASS`
- Unity fixture: 非該当。Unityコード、Scene、Prefab、Package、ProjectSettings、`.gitattributes`は変更していない

導入先ゲームで必要な作業:

- `PROJECT-002`へ実際のHosting、Branch、LFS quota、size閾値、Owner、Serialization modeを記録する
- 採用したPathだけを`.gitattributes`へ追加し、CI / Build machineでLFS object取得とpointer検査を行う
- 既存ProjectをForce TextまたはLFSへ移行する場合は、通常機能変更と分離して人間承認を得る

## 14. 2026-06-10 再評価: Codexへゲーム制作を任せられるか

### 14.1 判定

**Codexと人間が共同でUnityゲームを作るためのハーネスとしては採用を推奨する。インストールだけで、Unity未経験者を含む誰もが制作全体をCodexへ完全委任できる状態ではない。**

このハーネスはゲームエンジン、完成済みゲームフレームワーク、アセット集ではない。Codexが設計、実装、検証、報告を一貫した契約で行うための制御基盤である。その目的にはかなり近づいたが、Editor操作、CI、Build、外部制作ツール、更新経路の実証が不足している。

| 評価 | 点数 | 意味 |
|---|---:|---|
| 初回レポート互換の総合評価 | **78 / 100** | 初回63点から、Installer、Unity fixture、Editor API検査、回帰テスト、横断設計を改善 |
| Codex向けハーネス基盤 | **82 / 100** | 設計・安全・追跡・ローカル検証の基盤品質 |
| 「誰でも完全委任」のターンキー性 | **61 / 100** | 導入後の外部設定、MCP、CI、Build、人間判断を含む実利用評価 |

### 14.2 実査した結果

| 検証 | 2026-06-10の結果 | 判定 |
|---|---|---|
| リポジトリ静的検証 | `python3 scripts/validate_repository.py` | `PASS` |
| Python構文 | HarnessとValidation scripts | `PASS` |
| テンプレート自己回帰 | Python `unittest` 75件 | `PASS` |
| Unity Editor検出 | `/Applications/Unity/Hub/Editor/6000.4.10f1` | `PASS` |
| 過去Unity fixture Run | `20260609T062753Z`: Compile、EditMode 6件、PlayMode 2件、Asset validation | `PASS` |
| 現在Unity fixture Run | `20260610T003455Z`: Licensing Client protocol mismatch | `BLOCKED` |
| 現在Runの整合性検証 | Completed BLOCKED RunのManifestとartifact hash | `PASS` |
| 最新GitHub Actions Repository job | Run 14、commit `1577fcf` | `PASS` |
| 最新GitHub Actions Unity job | Secret検査で停止、Unity testsはskip | `FAIL` |
| Unity MCP接続 | fixtureとCodex sessionへ未導入 | `NOT RUN` |
| agent-sprite-forge | 未導入・未生成 | `NOT RUN` |
| Build Profile Player build | 未実行 | `NOT RUN` |

最新CI証拠:

- [Validate Harness run 14](https://github.com/hayukataishi/unity-codex-harness/actions/runs/27243709575)
- [Repository job: success](https://github.com/hayukataishi/unity-codex-harness/actions/runs/27243709575/job/80452971299)
- [Unity 6.4 Fixture job: failure](https://github.com/hayukataishi/unity-codex-harness/actions/runs/27243709575/job/80453000473)

ローカルの現在Runでは、Unity `6000.4.10f1`がUnity Hub側のLicensing Client `1.18.1`とのhandshakeを拒否し、`Unsupported protocol version '1.18.1'`で停止した。これはfixtureコードの失敗ではないが、導入者がUnity Hub、Editor、Licenseを正しく揃えないと自動検証が動かないことを示す。

### 14.3 強み

- `AGENTS.md`から必須文書とSkillへ誘導でき、Codexの作業順序が安定している。
- 設計ID、AC ID、`PASS / FAIL / BLOCKED / NOT RUN`、証拠Runが一貫している。
- Scene、Prefab、GUID、`.meta`、Package、Save、Git LFSなどUnity特有の破壊リスクを具体的に抑制している。
- Small / Standard / Large、横断機能採否、Save互換性、Git運用を固定解ではなく選択ゲートにしている。
- Installerは初回導入、競合停止、dry-run、冪等性、`Artifacts/`除外を回帰テストしている。
- Unity 6.4 fixtureにRuntime、Editor、EditMode、PlayMode、Prefab、Scene、Build Profile、参照検査が存在する。
- 失敗や未実行を成功扱いしない原則が文書とReport Skillへ浸透している。

### 14.4 新しいP0

#### P0-1: Unity起動失敗時にCompileが誤ってPASSになる

`run_unity_validation.py`はログに`error CSxxxx`がない場合、Unityの終了コードやNUnit XMLの有無に関係なくCompileを`PASS`にする。今回、Unityがライセンス初期化前に終了してEditMode XMLを生成しなかったRunでもCompileが`PASS`になった。

さらに、EditMode、PlayMode、Asset validationの出力が存在しない場合も、そのpathをAC証拠へ登録するため、finalize済みRunが`verify_validation_run.py`でmissing evidenceになる。

必要な改善:

- CompileはUnity process成功とcompile完了を示すログまたは生成物がある場合だけ`PASS`にする
- License、Editor起動、timeout、crashをCompile失敗と分離して`BLOCKED`または`FAIL`へ分類する
- 存在しない証拠pathをManifestとAC evidenceへ登録しない
- UnityがXML / JSONを生成しない異常系でも、完成Runのintegrity verificationが`PASS`する回帰テストを追加する

#### P0-2: Unity MCPが中核方針なのに導入・接続・互換性が未検証

Scene、Prefab、Component、Screenshot、Play操作はUnity MCP優先と定義しているが、InstallerはMCPを導入せず、`harness.lock.json`も`NOT RUN`である。現在のCodex sessionにもUnity MCP toolは接続されていない。

必要な改善:

- 固定版Unity MCPをfixtureまたは統合fixtureへ導入する
- CodexからEditor state取得、Scene作成、Prefab接続、Compile、Play、Screenshotを実行するsmoke testを用意する
- 導入先でMCP package、server、Codex connector、Editor接続を検査する`doctor`を追加する
- MCPが使えない時の安全な縮退動作と、停止すべき操作を明示する

#### P0-3: `--force`更新がゲーム固有設計書を上書きできる

Installerは`.codex/skills`、`docs`、Unity templateを同じ更新単位として扱う。既存保持対象はAsset validation設定だけで、`--force`はゲーム側で編集した`docs/unity_design_sheet.md`を含む全競合ファイルをbackupなしで置換できる。

設計書をSource of Truthとするハーネスで、その設計書を更新時に失う可能性があるため、継続運用の重大リスクである。

必要な改善:

- Harness管理ファイルとゲーム所有ファイルを分離する
- 設計書はtemplateから初回生成し、upgrade対象から外す
- versioned manifest、backup、diff、三方向mergeまたはmigrationを追加する
- `--force`をファイル単位に限定し、ゲーム所有ファイルへの使用を拒否する

#### P0-4: 公開CIのUnity jobが赤い

2026-06-10の最新GitHub ActionsではRepository jobは成功したが、Unity jobは`Verify Unity license secrets`で失敗した。Unity test runner、GameCI image、artifact取得まで到達していない。

必要な改善:

- Unity license Secretを設定してworkflowを成功させる
- 正確な`6000.4.10f1` image利用可否を実runで確定する
- 成功したEditMode / PlayMode artifactを保持し、READMEとlockへ最終成功runを記録する
- Secret未設定時は全workflowを赤くするか、明示的な`BLOCKED / SKIPPED`表示にするか運用方針を決める

### 14.5 P1

- 導入先ゲーム用のCI templateまたは生成コマンドがない
- Build Profileを指定したPlayer build、Build artifact、起動smoke testがない
- Python、Unity、Build Support、License、MCP、Git、LFS、Packageを一括診断するbootstrap / doctorがない
- 要求入力から設計、C#、Scene、Prefab、Play、Screenshot、Reportまで通した小さな実ゲームE2E sampleがない
- Input System、Addressables、Tag、Layer、Profiler、Memory、Code Coverageは文書中心で自動検査が不足する
- agent-sprite-forgeは固定しただけで、生成、import、animation、Prefab接続が未検証
- 3D、Audio、UI、Shader、VFX、Localization、Online、Releaseは採否ゲートが中心で、実装Skillとfixtureがない
- `harness.release`が`UNRELEASED`でGit tagもなく、互換Version、更新履歴、migration policyがない
- 2,000行を超える設計書を毎回必須読込するため、Codexのcontext効率と初心者の記入負荷が高い

### 14.6 100点の完了条件

1. P0-1からP0-4を解消し、失敗経路を含むValidation Runが必ず整合性検証を通る
2. 固定版Unity MCPを導入したE2E fixtureをCodexから実行し、Editor操作証拠を残す
3. 導入先CI templateとBuild Profile Player buildを少なくともmacOSまたはWindowsの一系統で成功させる
4. Installerをinstall / doctor / upgradeへ分離し、ゲーム所有ファイルをbackupなしで上書きしない
5. 小さなPlayable sampleを自然言語要求から設計、実装、Play、Screenshot、Reportまで完走する
6. Input、Addressables、Profiler、Coverage、Buildの代表検査を自動化する
7. versioned release、changelog、migration、互換性表を公開する
8. Unity初心者がREADMEだけで導入し、Codexへの最初の依頼と検証完了まで到達するユーザーテストを行う

### 14.7 最終回答

「このハーネスを取り込めば誰でもCodexにお任せしてゲーム制作ができるか」への回答は、次の通り。

> **現時点では、Codexへ安全に多くのUnity作業を任せるための優秀な基盤である。ただし、インストールだけで誰でも制作全体を完全委任できる製品ではない。**

UnityとGitの基本セットアップができ、ゲームの方向性、承認、主観的品質判断を人間が担うなら、小規模試作から継続開発の土台として実用可能である。非技術者がセットアップなしで完成ゲーム、ビルド、配布まで任せる用途には、P0解消とE2E実証が必要である。
