# Unity Codex Harness 評価レポート

- 評価日: 2026-06-08
- 最終更新日: 2026-06-11
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

GitHub ActionsのUnity jobにはUnityライセンスSecretと、GameCIが提供する正確な`6000.4.10f1` imageが必要である。2026-06-08時点では後者を確認できなかったが、2026-06-10に`ubuntu-6000.4.10f1-linux-il2cpp-3.2.2`のactive tagとOCI digestを確認し、Workflowへ固定した。リモートUnity実行はLicense Secret未設定のため引き続き`BLOCKED`である。

**改善案:** Unity License Secret設定後にGitHub Actionsを実行してEditMode / PlayMode Artifactを確定し、その後Code Coverageと代表Build Profileの`build-player`を追加する。

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
| GameCI Unity image | PASS | `6000.4.10f1` linux-il2cpp imageのactive tagとOCI digestを固定 |
| GitHub Actions Unity job | BLOCKED | GameCI imageは利用可能。Unity License Secret未設定 |
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
- GameCI Unity imageは利用可能だが、GitHub Actions Unity jobはUnity License Secret未設定のため`BLOCKED`
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
- GameCI Unity imageは利用可能だが、GitHub Actions Unity jobはUnity License Secret未設定のため`BLOCKED`
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
| 障害再現Unity fixture Run | `20260610T003455Z`: Licensing Client protocol mismatch | `BLOCKED` |
| 修正後Unity fixture Run | `20260610T024841Z`: Compile、EditMode 6件、PlayMode 2件、Asset validation | `PASS` |
| 修正後Runの整合性検証 | Completed PASS RunのManifestとartifact hash | `PASS` |
| 最新GitHub Actions Repository job | Run 14、commit `1577fcf` | `PASS` |
| 最新GitHub Actions Unity job | Secret検査で停止、Unity testsはskip | `FAIL` |
| GameCI `6000.4.10f1` image metadata | active tag、Linux amd64、OCI digest一致 | `PASS` |
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

#### P0-1: Unity起動失敗時にCompileが誤ってPASSになる（対応済み）

`run_unity_validation.py`はログに`error CSxxxx`がない場合、Unityの終了コードやNUnit XMLの有無に関係なくCompileを`PASS`にする。今回、Unityがライセンス初期化前に終了してEditMode XMLを生成しなかったRunでもCompileが`PASS`になった。

さらに、EditMode、PlayMode、Asset validationの出力が存在しない場合も、そのpathをAC証拠へ登録するため、finalize済みRunが`verify_validation_run.py`でmissing evidenceになる。

必要な改善:

- CompileはUnity process成功とcompile完了を示すログまたは生成物がある場合だけ`PASS`にする
- License、Editor起動、timeout、crashをCompile失敗と分離して`BLOCKED`または`FAIL`へ分類する
- 存在しない証拠pathをManifestとAC evidenceへ登録しない
- UnityがXML / JSONを生成しない異常系でも、完成Runのintegrity verificationが`PASS`する回帰テストを追加する

2026-06-10に`DEBUG-001-AC04`として対応した。Compileは同じRunで生成された有効なNUnit XMLとCompiler Error不在を必要とし、License、timeout、Process起動失敗を`BLOCKED`へ分類する。期待するXML / JSONがない場合は実在するLogだけを証拠登録し、EditModeがインフラ要因で`BLOCKED`ならPlayModeとAsset validationを再実行せず同じ理由で閉じる。

#### P0-2: Unity MCPが中核方針なのに導入・接続・互換性が未検証（導入診断対応済み・実接続未検証）

Scene、Prefab、Component、Screenshot、Play操作はUnity MCP優先と定義しているが、InstallerはMCPを導入せず、`harness.lock.json`も`NOT RUN`である。現在のCodex sessionにもUnity MCP toolは接続されていない。

必要な改善:

- 固定版Unity MCPをfixtureまたは統合fixtureへ導入する
- CodexからEditor state取得、Scene作成、Prefab接続、Compile、Play、Screenshotを実行するsmoke testを用意する
- 導入先でMCP package、server、Codex connector、Editor接続を検査する`doctor`を追加する
- MCPが使えない時の安全な縮退動作と、停止すべき操作を明示する

2026-06-10に`DEBUG-004`として、外部OSSをハーネスへ同梱せず固定参照から明示導入する契約を追加した。

- Unity MCP `v9.7.0`はrelease commit固定のUPM URLを記録し、Package不足と版違いを診断する
- agent-sprite-forgeは固定commit checkoutと`generate2dsprite` / `generate2dmap`配置を診断する
- 両依存の`bundled: false`、`explicit-user-action`、MIT license URLをlockへ記録する
- Installerは診断CLIをゲームへ導入するが、外部コードの取得、Package変更、Skillコピーは行わない
- `.codex/external/`と外部SkillコピーをGit管理外にする
- MCP不在時はEditor serialization変更を停止し、Unity YAML直接編集へ縮退しない

これにより「未導入を検出し、権利・配布境界を保った固定導入へ案内する」部分は対応した。一方、Server起動、Codex connector、Editor接続、基本Editor操作のE2E smoke testは引き続き`NOT RUN`であり、P0-2全体は未完了である。

#### P0-3: `--force`更新がゲーム固有設計書を上書きできる（対応済み）

Installerは`.codex/skills`、`docs`、Unity templateを同じ更新単位として扱う。既存保持対象はAsset validation設定だけで、`--force`はゲーム側で編集した`docs/unity_design_sheet.md`を含む全競合ファイルをbackupなしで置換できる。

設計書をSource of Truthとするハーネスで、その設計書を更新時に失う可能性があるため、継続運用の重大リスクである。

必要な改善:

- Harness管理ファイルとゲーム所有ファイルを分離する
- 設計書はtemplateから初回生成し、upgrade対象から外す
- versioned manifest、backup、diff、三方向mergeまたはmigrationを追加する
- `--force`をファイル単位に限定し、ゲーム所有ファイルへの使用を拒否する

2026-06-10に`DEBUG-005`として対応した。

- 導入対象を`harness-managed`と`project-owned`へ分類した
- ゲーム設計書、MCP・Skill一覧、`AGENTS.md`、外部依存lock、資産検査設定をproject-ownedとして保護した
- project-ownedは通常実行、`--force`、`--force-file`のいずれでも既存内容を置換しない
- `.unity-codex-harness/install-manifest.json`へschema、release、path、ownership、source hash、baseline hashを記録する
- `--force-file`でharness-managedの置換対象を相対path単位に限定できる
- `--force`はharness-managedだけを対象とし、置換前にhash付きbackupを`Artifacts/HarnessInstallerBackups/`へ作る
- project-owned template更新は`--prepare-migration`でbase、local、incoming、unified diffを出力し、localを変更しない
- `--dry-run`ではmanifest、baseline、backup、migrationを含め対象プロジェクトへ書き込まない

#### P0-4: 公開CIのUnity jobが赤い（image対応済み・Secret未設定）

2026-06-10の最新GitHub ActionsではRepository jobは成功したが、Unity jobは`Verify Unity license secrets`で失敗した。Unity test runner、GameCI image、artifact取得まで到達していない。

2026-06-10の追加確認で、`unity-test-runner v4.3.1`がLinux fixture testに使用する`linux-il2cpp` imageを特定し、次を実施した。

- Unity fixtureは`6000.4.10f1`を維持
- test runnerをcommit `0ff419b913a3630032cbe0de48a0099b5a9f0ed9`へ固定
- `ubuntu-6000.4.10f1-linux-il2cpp-3.2.2`とOCI digestをlockへ記録
- Workflowの`customImage`へ完全な`tag@digest` referenceを指定
- Docker Hub metadataのactive状態、Linux amd64、digestを検査するCLIと回帰テストを追加
- image availabilityを`PASS`、remote executionをLicense Secret未設定の`BLOCKED`として分離

残る改善:

- Unity license Secretを設定してworkflowを成功させる
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

1. 残るP0-2とP0-4を解消する。P0-1とP0-3は対応済み
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

### 14.8 P0-1対応結果

実装:

- `DEBUG-001-AC04`へCompile証明、インフラ障害分類、実在証拠限定を追加
- `run_unity_validation.py`へLicense、timeout、Process起動失敗の`BLOCKED`分類を追加
- 有効なNUnit XMLがない場合はCompileを`PASS`にしない
- 未生成のEditMode / PlayMode XMLとAsset validation JSONを証拠登録しない
- EditModeのインフラ障害後は後続Unity processを繰り返さず、理由付き`BLOCKED`で閉じる
- License警告後に正常復旧してXMLが生成された場合は誤って`BLOCKED`にしない

検証:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `DEBUG-001-AC04` | `PASS` | Python異常系回帰とUnity `6000.4.10f1` Validation Run `20260610T024841Z` |

- リポジトリ検証: `PASS`
- Python構文コンパイル: `PASS`
- Python回帰テスト: `PASS`、80件
- 偽Unity License失敗CLI: `COMPLETED / BLOCKED`、Compile `BLOCKED`、欠落証拠なし、integrity `PASS`
- 実Unity fixture: Compile `PASS`、EditMode 6件`PASS`、PlayMode 2件`PASS`、Asset validation `PASS`
- Validation Run integrity: `PASS`

### 14.9 P0-2導入診断対応結果

実装:

- `DEBUG-004`へ外部OSSの非同梱、明示導入、固定参照、license記録、MCP不在時の停止境界を追加
- `check_external_dependencies.py`へUnity MCP Packageとagent-sprite-forge Skillの不足・版違い検査を追加
- Installerへ診断CLIの配布と外部checkout・SkillコピーのGit除外を追加
- `harness.lock.json`へ固定導入URL、配布方式、固定参照のlicense URLを追加
- READMEへUnity Package Managerと外部Skillの手動導入手順を追加

検証:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `DEBUG-004-AC01` | `PASS` | lock検証が非同梱とcommit固定URLを検査 |
| `DEBUG-004-AC02` | `PASS` | Installer回帰が診断CLIとGit除外を検査 |
| `DEBUG-004-AC03` | `PASS` | 不足・版違いfixtureで終了コード`1`と固定導入手順を確認 |
| `DEBUG-004-AC04` | `PASS` | 固定Package・checkout・Skill fixtureで静的診断`PASS`、接続は`NOT CHECKED` |

- リポジトリ検証: `PASS`
- Python構文コンパイル: `PASS`
- Python回帰テスト: `PASS`、88件

残件:

- Unity MCP Server、Codex connector、Unity `6000.4.10f1` Editorの実接続
- CodexからEditor state、Scene、Prefab、Compile、Play、Screenshotを確認するE2E smoke test
- agent-sprite-forgeの実生成、Unity import、Animation、Prefab接続

### 14.10 P0-3安全更新対応結果

実装:

- `DEBUG-005`へInstaller所有区分、project-owned保護、対象限定更新、backup、migration bundleを追加
- `InstallSource`へ`harness-managed` / `project-owned`を追加
- `.unity-codex-harness/install-manifest.json`とproject template baselineを生成
- `--force-file`、置換前Backup Manifest、`--prepare-migration`を追加
- READMEの導入・更新・復旧手順を新しい所有権契約へ更新

検証:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `DEBUG-005-AC01` | `PASS` | install manifestのschema、ownership、source / baseline hashを確認 |
| `DEBUG-005-AC02` | `PASS` | 5つのproject-ownedが`--force`でも不変、`--force-file`指定は書込み前拒否 |
| `DEBUG-005-AC03` | `PASS` | 対象限定置換と元ファイル・hash付きBackup Manifestを確認 |
| `DEBUG-005-AC04` | `PASS` | base・local・incoming・2種diffを生成し、local不変とbaseline更新を確認 |

- リポジトリ検証: `PASS`
- Python構文コンパイル: `PASS`
- Python回帰テスト: `PASS`、93件
- Unity fixture: `NOT RUN`。Unity資産とEditor実装を変更していないため

Unity Scene、Prefab、Package、GUIDの変更はない。InstallerとPython回帰だけの変更であるため、Unity fixtureはこの対応では再実行しない。

### 14.11 P0-4 GameCI image固定対応結果

実装:

- `DEBUG-006`へUnity version維持、GameCI test runner、image tag、OCI digest、事前可用性検査を追加
- Unity `6000.4.10f1`を維持し、`linux-il2cpp-3.2.2` imageを完全な`tag@digest`で固定
- `check_gameci_image.py`へlock整合性、Docker Hub active tag、Linux amd64、digest検査を追加
- Workflowへremote image検査と`customImage`指定を追加
- READMEへPersonal / ProのUnity License Secret設定手順を追加
- lockでimage availabilityを`PASS`、remote executionを`BLOCKED`として分離

検証:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `DEBUG-006-AC01` | `PASS` | lockのUnity version、test runner commit、image tag、OCI digest、reference整合性 |
| `DEBUG-006-AC02` | `PASS` | WorkflowのUnity version、action commit、`customImage`がlockと一致 |
| `DEBUG-006-AC03` | `PASS` | Docker Hub remote metadata照合とPython正常・異常系回帰 |
| `DEBUG-006-AC04` | `PASS` | README、lock、評価レポートでavailabilityとremote executionを分離 |
| `DEBUG-006-AC05` | `BLOCKED` | Unity License Secret未設定。GitHub Actions Unity test Artifactは未生成 |

- リポジトリ検証: `PASS`
- Python構文コンパイル: `PASS`
- Python回帰テスト: `PASS`、103件
- GameCI remote image metadata: `PASS`
- Unity fixture: `NOT RUN`。Unity資産、Package、Editor実装を変更していないため

P0-4はGameCI image未対応問題を解消した。残件はUnity License Secret設定、remote Unity job成功、EditMode / PlayMode Artifactの記録である。

### 14.12 設計ガイドとゲーム固有設計書の分離

2026-06-11に`DEBUG-007`として対応した。

実装:

- 旧設計書の共通規則、選択肢、品質ゲート、例、ハーネス`DEBUG-*`を`docs/unity_harness_requirements.md`へ移し、`harness-managed`とした
- `docs/unity_design_sheet.md`をゲーム企画、採用結果、設計項目ID、AC、承認履歴だけを書く`project-owned`文書として再構成した
- GuideとSheetへ所有者マーカーを追加し、README、Engineering Guide、`AGENTS.md`で編集境界を明記した
- 6つのUnity SkillがGuideを規約として読み、ゲーム固有の決定とACはSheetだけを正本として扱うよう更新した
- 旧混在Sheetを自動上書き・自動分割せず、`--prepare-migration`の三者比較からゲーム固有情報だけを移す手順を追加した
- Repository validatorへ所有境界、必須anchor、Sheet内の`DEBUG-*`混入を検出する検査を追加した
- Installer回帰でGuideは更新・backup可能、Sheetは`--force`でも保持されることを確認した

検証:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `DEBUG-007-AC01` | `PASS` | Guide / Sheetの管理マーカー、所有者説明、必須anchorを静的検査 |
| `DEBUG-007-AC02` | `PASS` | Installer manifestでGuide=`harness-managed`、Sheet=`project-owned`を確認 |
| `DEBUG-007-AC03` | `PASS` | Design / Implement / Validate / Review / Integrate / Report Skillの境界記述を検査 |
| `DEBUG-007-AC04` | `PASS` | READMEとEngineering Guideの移行手順、既存Sheet保持、Guide backupを回帰テスト |

- リポジトリ検証: `PASS`
- Python構文コンパイル: `PASS`
- Python回帰テスト: `PASS`、107件
- Unity fixture静的preflight: `PASS`、29 Asset / Directoryと29 `.meta`を検査
- Installer dry-run: `PASS`。Guideはharness-managed作成、Sheetはproject-owned baseline作成として計画
- Unity fixture: `NOT RUN`。Unity資産、Package、Editor実装を変更していないため

この時点の対応は所有権分離には成功したが、標準規則を「Guide」と表現したため、個別ゲームが継承する必須契約であることと、両文書の対応キーが不明確だった。次の14.13で契約モデルを再設計した。

### 14.13 HREQ標準要件継承モデルへの再設計

2026-06-11に`DEBUG-007`の契約を強化した。

実装:

- `unity_design_guide.md`という概念を廃止し、`docs/unity_harness_requirements.md`を任意参考ではないハーネス標準要件とした
- 評価改善で追加したArchitecture、Save、Repository、Build Profile、Cinemachine、横断機能、Validation、Installer、CI等を`HREQ-*`一覧へ対応付けた
- ゲーム設計書へ標準要件適合表を追加し、`継承`、`対象外`、`例外承認`、`未決定`を記録するようにした
- 標準要件とゲーム個別要件の対応を章番号ではなく共通の`HREQ-*` IDへ統一した
- 個別要件が標準を弱める場合は、理由、影響、代替策、承認者、日付を持つ`例外承認`を必須とした
- `validate_design_contract.py`を導入先へ配布し、HREQ欠落、未解決要件、不完全な対象外・例外承認を失敗させるようにした
- 6つのUnity Skillと`AGENTS.md`を、HREQを継承要件として実装・検証する契約へ更新した

検証:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `DEBUG-007-AC01` | `PASS` | 標準要件、個別要件、HREQ適合表、共通anchorを静的検査 |
| `DEBUG-007-AC02` | `PASS` | 標準要件=`harness-managed`、ゲーム設計書=`project-owned`をInstaller回帰で確認 |
| `DEBUG-007-AC03` | `PASS` | SkillsがHREQ、適合状態、例外承認、未決定時停止を要求 |
| `DEBUG-007-AC04` | `PASS` | 契約CLIの正常系、HREQ欠落、未決定、例外情報不足を回帰テスト |
| `DEBUG-007-AC05` | `PASS` | 旧混在Sheetのmigrationと既存ゲーム設計保護を維持 |

- リポジトリ検証: `PASS`
- Python構文コンパイル: `PASS`
- Python回帰テスト: `PASS`、111件
- HREQ契約検査: `PASS`
- `HREQ-ARCH-001`未決定を要求した異常系: 期待どおり`FAIL`
- Unity fixture静的preflight: `PASS`、29 Asset / Directoryと29 `.meta`を検査
- Unity fixture Editor実行: `NOT RUN`。Unity資産、Package、Editor実装を変更していないため

### 14.14 標準実装・標準推奨・ゲーム個別設計の再評価

2026-06-11に、HREQ継承モデルを次の4観点で再評価した。

| 評価項目 | 点数 | 判定 |
|---|---:|---|
| 標準実装、標準推奨、ゲーム個別設計の分離 | 70 / 100 | 文書上は区別できるが、標準要件文書へハーネス内部契約が混在 |
| 標準実装の未承認改変防止 | 30 / 100 | Installer再実行時の競合検出はあるが、通常作業・Skill・CIでの完全性検査がない |
| 標準推奨要件を理解して決定する対話フロー | 58 / 100 | HREQ未決定ゲートはあるが、全選択肢を説明して順番に決める案内型セッションがない |
| ゲーム個別仕様・設計を一通り更新する対話フロー | 52 / 100 | Sheetは広範囲だが、全章を対話完了させる進行状態と完成度検査がない |

総合評価は`53 / 100`とする。

主な問題:

1. `unity_harness_requirements.md`に、ゲームへ適用する要件とInstaller、CI、fixture、回帰テストなどの実装契約が同居している。
2. `harness-managed`は所有区分として定義されているが、導入後の未承認改変を常時検出して作業を停止しない。
3. `maintain-game-design`は変更要求に関係する項目を更新する方式で、標準推奨を一問ずつ説明・決定する初期設計セッションではない。
4. `validate_design_contract.py`はHREQ適合表を検査するが、ゲーム設計書全章のマイルストーン別完成度を検査しない。

改善順序:

1. 標準実装、標準・推奨要件、ゲーム個別設計を物理的に3文書へ分離する。
2. install manifestのSHAと導入済みharness-managedファイルを照合する完全性検査を追加し、Codex作業開始時とCIで失敗させる。
3. 標準推奨要件の選択肢、推奨理由、トレードオフを一問ずつ説明して決定する初期設計Skillを追加する。
4. Concept、Prototype、Vertical Slice、Alpha、Beta、Releaseごとの必須設計項目と完成度Validatorを追加する。

### 14.15 3文書への物理分離

14.14の改善順序1へ対応した。

実装:

- `docs/unity_harness_capabilities.md`を追加し、Installer、Validation Run、Python回帰、Unity fixture、外部依存、GameCI、文書境界を`HCAP-*`標準実装として分離した
- `docs/unity_harness_requirements.md`から`DEBUG-*`内部契約とハーネス内部HREQを除き、`必須標準`、`決定必須`、`条件付き推奨`だけを保持する文書へ変更した
- `docs/unity_design_sheet.md`は引き続き`project-owned`とし、ゲーム固有の決定、HREQ適用状態、例外、設計ID、ACだけを保持した
- `AGENTS.md`、6つのUnity Skill、Engineering Guide、README、MCP・Skill一覧の必読順と責務を3文書構造へ更新した
- Repository validatorへCapabilitiesの必須構造と、Requirementsへの`DEBUG-*`再混入、Sheetへの`HCAP-*`混入を拒否する検査を追加した
- Installer回帰へCapabilitiesとRequirementsが`harness-managed`で更新・backupされ、Sheetが保持される検査を追加した

検証:

- リポジトリ検証: `PASS`
- Python構文コンパイル: `PASS`
- Python回帰テスト: `PASS`、112件
- HREQ契約検査: `PASS`
- Installer dry-run: `PASS`。Capabilities、Requirements、Sheetの3文書を配布対象として確認
- Unity fixture静的preflight: `PASS`、29 Asset / Directoryと29 `.meta`を検査
- Requirementsへの`DEBUG-*`再混入異常系: 期待どおり`FAIL`
- Installer回帰: CapabilitiesとRequirementsをbackup後に更新し、ゲーム設計書を保持
- Unity fixture Editor実行: `NOT RUN`。Unity資産、Package、Editor実装を変更していないため

残件:

- この時点では`HCAP-INTEGRITY-001`が未実装だった。14.16で改変検知と停止ゲートを追加した
- 標準推奨要件の案内型対話フローと、ゲーム設計全章の完成度フローは改善順序3、4で対応する

### 14.16 HCAP-INTEGRITY-001 標準実装の改変防止

14.14の改善順序2へ対応した。

実装:

- install manifestをschema version 2へ更新し、全配布fileのownership、
  source SHA-256、専有管理rootを記録した
- `install-manifest.sha256`を生成し、manifest単体の意図しない変更を検出するようにした
- `verify_harness_integrity.py`を追加し、harness-managed fileの欠落、
  SHA不一致、symlink化、危険なmanifest path、専有管理root内の未知fileを拒否した
- project-owned fileは完全性検査対象から除外し、ゲーム固有設計の更新を許可した
- Installer完了時と`--check`へ完全性検査を統合した
- `AGENTS.md`と6つのUnity Skillで、設計・実装・Asset統合・検証・Gameplay review・
  受け入れ報告前の完全性`PASS`を必須にした
- GitHub Actionsへ完全性回帰を明示的に追加し、ゲーム側CI用コマンドをREADMEへ記載した
- 意図的な独自変更はmanifest手編集ではなく、ハーネス本体をforkして
  そのInstallerから再配布する契約にした

検証対象:

- 正常な導入
- harness-managed fileの内容変更と欠落
- project-owned file変更の許可
- manifest変更とsidecar不一致
- `../`を含む危険なmanifest path
- Skill専有rootへの未知file追加
- Installer `--check`による改変停止

検証結果:

- リポジトリ検証: `PASS`
- Python構文コンパイル: `PASS`
- Python回帰テスト: `PASS`、124件
- HREQ契約検査: `PASS`
- Installer dry-run: `PASS`。verifier、schema 2 manifest、manifest sidecarを配布予定として確認
- Unity fixture静的preflight: `PASS`、29 Asset / Directoryと29 `.meta`を検査
- 完全性正常fixture: `PASS`
- harness-managed改変、欠落、manifest改変、危険path、未知file異常系:
  期待どおり`FAIL`
- project-owned設計変更: 完全性`PASS`
- Unity fixture Editor実行: `NOT RUN`。Unity資産、Package、Editor実装を変更していないため

再評価:

| 評価項目 | 対応前 | 対応後 | 判定 |
|---|---:|---:|---|
| 標準実装の未承認改変防止 | 30 / 100 | 85 / 100 | 運用上達成 |

残余リスク:

- リポジトリ管理者が検査code、manifest、sidecarを同時に意図的改ざんする攻撃は、
  同一Repository内のhashだけでは暗号学的に防げない
- これを100点へ上げるには、署名付きrelease、保護された公開鍵、署名検証を
  Repository外のtrust rootとして導入する必要がある
- 一般的なゲーム制作での誤操作、Codexの無断変更、未レビュー差分については、
  作業開始とCIで検出・停止できる

4観点の暫定総合点は、3文書分離`92`、改変防止`85`、
標準推奨対話`58`、ゲーム個別対話`52`として`72 / 100`へ更新する。

### 14.17 HCAP-DESIGN-BOOTSTRAP-001 初期設計対話Skill

14.14の改善順序3へ対応した。

設計判断:

- `agents/openai.yaml`はSkill一覧の表示metadataであり、実行時Subagentそのものではない
- ユーザーとの会話と設計書更新をSubagentへ渡すと、質問順序、承認、
  書込み責任が分散するため、主Agentを唯一の対話窓口と書込み主体にした
- Subagentは各Phase終了時と最終承認前の読み取り専用監査役とし、
  漏れ、矛盾、誘導質問、未説明トレードオフを独立確認する
- multi-agent機能がない場合は同じrubricを`SELF REVIEW`として実行し、
  独立Subagent監査と偽らない
- 公式Codex Subagent仕様を再確認し、Project Custom Agentは
  `.codex/agents/*.toml`で定義する構成へ更新した

実装:

- `.codex/skills/bootstrap-game-design/`を追加した
- Concept、Prototype、Vertical Slice、Alpha、Beta、Releaseの
  対象マイルストーンに応じて必要な深さを変える10 Phaseを定義した
- Vision、Player Context、Core Loop、Presentation、Technical Baseline、Save、
  Repository、Build、横断機能、Traceabilityを一問ずつ対話する
- 技術選択前に目的、現実的な選択肢、推奨理由、代替案、
  トレードオフを説明する契約を追加した
- 無回答、例、推奨、仮定を確定仕様として扱わず、人間の明示確認を要求した
- `spawn_agent`を使う読み取り専用Subagent audit rubricを同梱した
- `.codex/agents/game-design-auditor.toml`へ`game_design_auditor`を追加し、
  `sandbox_mode = "read-only"`、高reasoning、編集・直接質問・承認禁止を設定した
- `AGENTS.md`をRepository全体の役割契約、Skillを対話workflow、
  `agents/openai.yaml`をSkill metadata、Custom Agent TOMLを実行時役割へ分離した
- 標準推奨要件とゲーム個別仕様は同じ10 Phaseに含まれていたが、質問単位の
  境界表示が弱かったため、`標準推奨`、`ゲーム個別`、`両方`の区分と
  関連HREQ IDを対話証跡へ追加した
- ゲーム設計書へ対話Run、対象マイルストーン、現在Phase、次の質問、
  Blocking未決事項、関連設計ID、確認者、監査状態を追加した
- 回答後の確認待ちでも再開できるよう、質問、提示した選択肢と
  トレードオフ、回答要約、反映案、確認状態を非規範な対話証跡へ追加した
- Concept、Prototype、Vertical Slice、Alpha以降についてPhase別の必須深度を
  定義し、後工程の判断を責任者と期限付きで保留できるようにした
- Player Contextを先に確認し、Unity完全version、Build Support、render pipeline、
  性能予算などの技術baselineはCore LoopとPresentationの後に決める順序へ修正した
- Phase状態を`未着手`、`対話中`、`提案レビュー中`、`人間承認済`、
  `保留`、`対象外`、`再検討`へ分けた
- 上流判断変更時に影響Phaseを`再検討`へ戻す契約を追加した
- 横断機能matrixのtemplate状態を、不完全な`保留`から正直な`未決定`へ変更した
- `AGENTS.md`、README、Engineering Guide、MCP・Skill一覧、
  Capabilitiesを初期設計Skill優先のworkflowへ更新した
- Repository validatorへPhase、Subagent境界、人間承認、resume情報の
  回帰検査を追加した

検証結果:

- Skill Creator `quick_validate.py`: `PASS`
- リポジトリ検証: `PASS`
- Python回帰テスト: `PASS`、130件
- Installer dry-run: `PASS`。Skill本体、Skill metadata、2つのreference、
  Project Custom Agent TOMLを配布予定として確認
- Custom Agent TOML検査: `PASS`。公式必須field、`game_design_auditor`名、
  `sandbox_mode = "read-only"`、両対話区分の監査指示を確認
- 初期設計契約の異常系: Subagent書込み禁止、`PHASE-09`、
  マイルストーン別深度、対話証跡の欠落を期待どおり検出
- 独立Subagent設計レビュー: 初期実装前に実施し、Phase状態、対話Run、
  Blocking未決事項、上流変更時の再検討規則へ反映
- 独立Subagent forward review: 6件を検出し、正当な保留、対話証跡、
  確認待ちresume、技術判断の順序、マイルストーン別深度、明示確認へ反映
- Unity fixture Editor実行: `NOT RUN`。Unity資産、Package、Editor実装を変更していないため

再評価:

| 評価項目 | 対応前 | 対応後 | 判定 |
|---|---:|---:|---|
| 標準推奨要件を理解して決定する対話フロー | 58 / 100 | 90 / 100 | 質問区分とHREQ追跡まで達成 |
| ゲーム個別仕様・設計を一通り更新する対話フロー | 52 / 100 | 86 / 100 | 再開・独立監査まで達成、機械的完成度判定は残る |

残件:

- マイルストーン別の必須field、許容する保留、Blocking未決事項を
  機械判定する完成度Validator
- 実際の利用者との長時間対話で、質問量、resume、Phase再検討が
  過不足なく機能するかのE2E user test

4観点の暫定総合点は、3文書分離`92`、改変防止`85`、
標準推奨対話`90`、ゲーム個別対話`86`として`88 / 100`へ更新する。

### 14.18 HCAP-DESIGN-READINESS-001 マイルストーン別設計完成度

14.14の改善順序4へ対応した。

実装:

- `scripts/validate_design_readiness.py`を追加した
- Concept、Prototype、Vertical Slice、Alpha、Beta、Releaseの順に、
  必須Phase、HREQ、設計欄、実装準備情報を累積的に厳しくする
- 必須Phaseの`人間承認済`、確認者・日付、`SELF REVIEW`または
  `SUBAGENT PASS`、Blocking未決事項なしを検査する
- 対象マイルストーンと設計書の現在・対象マイルストーン、
  `Approved`、`マイルストーン承認済`の一致を検査する
- HREQ適合表の形式検査を再利用し、マイルストーン必須HREQの
  `未決定`を拒否する
- コアループ、勝利・失敗・終了、メカニクス、Platform、Presentation、
  Architecture、Save、Repository、Build、性能などを深度別に検査する
- Prototype以降はApproved設計ID、有効AC、検証種別、入力、
  Development Build Profileを要求する
- Vertical Slice以降は状態、Scene、遷移、UI、性能を要求し、
  Alpha以降はPrefab、Component、Draft残存、QA Build Profileを検査する
- ReleaseではRelease Build Profile、signing、配布経路まで要求する
- 横断機能の`採用 / 不採用 / 保留`、理由、依存、データ、安全性、
  設計ID・AC、保留責任者、期限を検査する
- 未決事項へ`状態`と`影響・Blocking対象`、横断機能へ`決定者`を追加し、
  現在の必須PhaseをBlockingする質問、対象マイルストーン以前の期限、
  期限切れ日付を拒否する
- `--output`で`Artifacts/DesignReadiness/<Milestone>.json`へ
  machine-readable reportを保存できる
- Bootstrap、Maintain、Implement、Validate、Report Skillと`AGENTS.md`へ
  完成度`PASS`ゲートを組み込んだ
- Installerと完全性manifestへValidatorを追加した

検証結果:

- Repository検証: `PASS`
- Python構文コンパイル: `PASS`
- Python回帰テスト: `PASS`、140件
- Concept正常fixture: `PASS`
- 未承認必須Phase、現在PhaseをBlockingする未決事項、
  対象マイルストーン期限、PrototypeのApproved設計ID不足、
  必須HREQの不正な`対象外`、採用横断機能の設計ID・AC不足:
  期待どおり`FAIL`
- JSON report生成: `PASS`
- Installer dry-run: `PASS`。導入先へreadiness Validatorを配布予定として確認
- 一時Unityプロジェクトへの実Installer後CLI: `PASS`。未記入Conceptを
  exit code 1で拒否し、JSON reportを生成
- Unity 6.4 fixture静的preflight: `PASS`
- Unity fixture Editor実行: `NOT RUN`。Unity資産、Package、Editor実装を
  変更していないため

再評価:

| 評価項目 | 対応前 | 対応後 | 判定 |
|---|---:|---:|---|
| 標準推奨要件を理解して決定する対話フロー | 90 / 100 | 94 / 100 | HREQ解決を完成度ゲートへ接続 |
| ゲーム個別仕様・設計を一通り更新する対話フロー | 86 / 100 | 95 / 100 | マイルストーン別の機械判定まで達成 |

残余リスク:

- Validatorは構造、明示状態、追跡可能性を判定する。面白さ、可読性、
  難易度、アート品質などの主観品質は人間レビューが必要
- ゲーム固有の特殊要件は汎用fieldだけでは判定できないため、
  Approved設計IDとACで追加する
- 実利用者との長時間E2E対話試験は引き続き必要

4観点の暫定総合点は、3文書分離`92`、改変防止`85`、
標準推奨対話`94`、ゲーム個別対話`95`として`92 / 100`へ更新する。

## 15. 2026-06-11 再評価: Unityプロジェクトへ取り込めば誰でもCodexへ任せられるか

### 15.1 最終判定

**No。現時点では、導入だけでUnity未経験者を含む誰もがゲーム制作全体を
Codexへ完全委任できる状態ではない。**

一方で、Unity、Git、Codexの基本セットアップができ、ゲームの方向性、
承認、主観的品質判断を人間が担当する条件では、設計から実装、検証、報告を
Codexへ安全に委任するための基盤として実用水準にある。

| 評価軸 | 点数 | 判定 |
|---|---:|---|
| Codex向け制御基盤 | **88 / 100** | Skill、設計ゲート、完全性、証拠管理は強い |
| 導入・更新の安全性 | **90 / 100** | 競合停止、ownership、backup、migrationを実装 |
| ローカルUnity検証 | **85 / 100** | Compile、EditMode、PlayMode、資産検査が実動 |
| 初心者オンボーディング | **58 / 100** | MCP、License、Build Support、CIを利用者が設定 |
| ゲーム制作E2E実証 | **47 / 100** | 自然言語からPlayable・Buildまでの完走証拠がない |
| **「誰でもお任せ」のターンキー性** | **64 / 100** | 前回61点から初期設計・readiness・Skill実測分を加点 |

### 15.2 今回の実測

| 検証 | 結果 | 証拠・意味 |
|---|---|---|
| Repository検証 | `PASS` | `python3 scripts/validate_repository.py` |
| Python回帰 | `PASS` | 140件 |
| 新規相当Projectへのdry-run / install / check | `PASS` | 41変更、完全性とignore検査もPASS |
| 導入先でのCodex Skill検出 | `PASS` | Codex CLI `0.137.0`が7 Skillを検出 |
| 導入直後の外部依存診断 | `ACTION REQUIRED` | Unity MCPとagent-sprite-forgeが未導入 |
| 導入直後のDesign Contract | `PASS` | 文書構造は有効 |
| 未記入ConceptのDesign Readiness | `FAIL` | 未決定、未承認、未監査を正しく拒否 |
| Unity fixture | `COMPLETED / PASS` | Run `20260611T110543Z` |
| EditMode / PlayMode | `PASS` | 6件 / 2件 |
| Asset validation | `PASS` | error 0、warning 0 |
| Player Build | `NOT RUN` | Build Profile指定の実Player build証拠なし |
| Unity MCP E2E | `NOT RUN` | Server、Codex、Editor操作の接続証拠なし |
| Remote Unity CI | `BLOCKED` | License Secret未設定 |
| Harness release | `UNRELEASED` | tag、changelog、互換性表なし |

Unity fixtureの証拠:

- `tests/fixtures/UnityValidationFixture/Artifacts/ValidationRuns/20260611T110543Z/`
- Static preflight、Compile、EditMode、PlayMode、Asset validation、Run integrityがPASS

### 15.3 現在できること

- 曖昧なゲーム案をPhase別の対話で設計へ変換する
- HREQ、設計ID、AC、承認、未決事項を追跡する
- 承認済みの小さなC#機能を既存構造へ実装する
- `.meta`、GUID、Scene、Prefab、Save、Package変更の危険を抑える
- Compile、EditMode、PlayMode、Missing Reference、必須参照を検証する
- 未実行、環境障害、主観判断を成功扱いせず報告する
- ハーネス標準とゲーム所有ファイルを分離して安全に更新する

### 15.4 新しいP0

#### P0-1: 中核ワークフローのゲーム制作E2Eが未証明

fixtureは検証基盤の非回帰を証明するが、利用者の自然言語要求から
初期設計、C#、Scene、Prefab、入力、Play、Screenshot、Player Build、
最終Reportまでを一つの小さなゲームで完走していない。

このため「各部品が存在する」ことは証明できても、「Codexへゲーム制作を
任せると全工程が接続される」ことはまだ証明できない。

#### P0-2: Unity MCPが標準経路なのに実接続が未証明

Scene、Prefab、ScriptableObject、Import、Play、ScreenshotはMCP優先だが、
InstallerはMCPを導入せず、診断もPackage参照の静的確認までである。
Server起動、Codex設定、Editor接続、固定版互換性、基本操作のsmoke testがない。

#### P0-3: Buildと配布可能性が未証明

保存済みBuild Profileのfixtureはあるが、それを指定したPlayer build、
生成物の起動smoke test、導入先CI template、成功したremote Unity jobがない。
したがってPrototypeのコード検証から配布可能なゲームまでの経路は未完成である。

#### P0-4: 既存`AGENTS.md`があると作業契約なしでも導入成功になる（対応済み）

既存Projectの`AGENTS.md`はproject-ownedとして保持される。今回の再現では、
ハーネス指示を含まない既存`AGENTS.md`でもInstallerは
`Installation complete`、完全性検査`PASS`となった。

Skill自身にも安全ゲートはあるが、必須文書、優先workflow、設計更新順序、
完了条件をCodexへ常時適用するRepository契約は保証されない。Installerまたは
doctorは、必須指示の統合済み状態を検査し、未統合なら導入準備完了を名乗らない
必要がある。2026-06-11にSection 15.9の対応を実施した。

### 15.5 P1

#### P1-1: 現行Codexの標準配布形態へ未追随

2026-06-11の公式Codex ManualはRepository Skillの標準配置を
`.agents/skills`、複数Skillの再利用配布をPluginとして案内している。
本ハーネスは`.codex/skills`を使用する。

Codex CLI `0.137.0`では、source repositoryと新規導入先の両方で7 Skillを
実際に検出したため、現時点の不動作ではない。ただし互換経路への依存であり、
CLI、IDE、App、将来versionを対象にした配布契約としてはPlugin化または
`.agents/skills`への移行・二重検証が望ましい。

公式参照:

- https://developers.openai.com/codex/skills
- https://developers.openai.com/codex/guides/agents-md
- https://developers.openai.com/codex/mcp
- https://developers.openai.com/codex/subagents

#### P1-2: `harness.lock.json`がproject-owned（対応済み）

外部依存の固定参照と互換性根拠を持つ`harness.lock.json`はproject-ownedであり、
完全性検査はゲーム側変更を許可する。固定する標準値とゲーム側overrideを分離し、
標準pinの偶発的driftを検出できる構造が必要である。
2026-06-11にSection 15.10の対応を実施した。

#### P1-3: 評価履歴まで導入先ゲームへ配布される

Installerは`docs/`全体をコピーするため、1,600行を超える過去評価レポートも
harness-managedとして各ゲームへ導入する。実行に必要な標準文書と、開発履歴・
評価記録の配布範囲を分けるべきである。

#### P1-4: versioned releaseがない

`harness.release`は`UNRELEASED`で、Git tag、changelog、対応Codex version、
Unity version帯、migration policyの公開単位がない。導入済みProjectが
「どのHarness契約で動くか」を安定して説明できない。

#### P1-5: 自動検査範囲がまだ限定的

Input System、Tag、Layer、Addressables、Code Coverage、Profiler、Memory、
Build Profile Player build、Platform実機、3D、Audio、Localization、Online、
Store提出は文書ゲート中心で、共通の実行fixtureや自動検査が不足する。

#### P1-6: 初心者ユーザーテストがない

READMEは詳細だが、Unity初心者がREADMEだけで導入し、Codexへ最初の依頼を行い、
設計対話、MCP接続、Playable確認、検証Reportまで到達した記録がない。

### 15.6 利用者別の回答

| 利用者 | 判定 | 現実的に任せられる範囲 |
|---|---|---|
| Unity・Git経験者 | `YES, 条件付き` | Prototypeから継続開発。環境構築とレビューは人間 |
| 開発経験はあるUnity初心者 | `PARTIAL` | 設計とC#は有効。Editor、MCP、Buildで支援が必要 |
| 非技術者 | `NO` | 導入、障害復旧、CI、Build、配布を単独では完結しにくい |
| 小規模Prototype | `実用候補` | コアループ中心なら適合 |
| Commercial Release | `未到達` | Build、署名、Store、運用、法務、実機検証が不足 |

### 15.7 「誰でもお任せ」に近づく完了条件

1. `install / doctor / upgrade`を分け、Unity、Build Support、License、Git、
   LFS、Skill検出、`AGENTS.md`統合、MCP接続を一括診断する。
2. 固定版Unity MCPでEditor state、Scene、Prefab、Compile、Play、
   Screenshotを実行するE2E smoke testを追加する。
3. 小さなPlayable sampleを、自然言語から設計、実装、検証、Reportまで完走する。
4. Build Profile指定Player buildと起動smoke testをローカル・CIで成功させる。
5. Codex Pluginまたは公式Skill配置へ移行し、CLI、IDE、Appで検出を回帰する。
6. 標準pinとゲームoverrideを分離し、互換性matrixを検査する。
7. versioned release、tag、changelog、migration guideを公開する。
8. Unity初心者によるREADMEのみのユーザーテストを完走する。

### 15.8 回答

> このハーネスは、CodexへUnity作業を安全かつ追跡可能に任せるための
> 高品質な制御基盤である。しかし、取り込むだけで誰でも企画から配布までを
> 完全委任できるターンキー製品ではない。

現時点の推奨対象は、ゲームの意図と品質判断を人間が持ち、Unity環境、
MCP、Build、CIのセットアップを扱える個人またはチームである。

### 15.9 P0-4 Agent Contract統合ゲート対応結果

既存のゲーム固有`AGENTS.md`を上書きせず、Codexへ必須作業契約を確実に
適用するため、契約本体と参照を分離した。

実装:

- `docs/unity_harness_agent_contract.md`をharness-managed契約として追加
- project-ownedの`AGENTS.md`へ固定マーカーと契約path参照を要求
- 未統合の既存`AGENTS.md`では通常Installerを全書込み前に停止
- `--prepare-migration`では`AGENTS.md`だけのbase・local・incoming・diffを
  生成し、local不変・終了コード`1`の導入未完了とする
- `--skip-agents`をAgent Contract検査の明示的免除として維持
- install manifestへ`AGENTS.md`が含まれる場合、
  `verify_harness_integrity.py`とInstaller `--check`がマーカー、契約path、
  `AGENTS.md`欠落を検出
- 契約本体はharness-managedなので、将来の標準更新をゲーム固有
  `AGENTS.md`の上書きなしで配布可能

`DEBUG-005-AC05`:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `DEBUG-005-AC05` | `PASS` | 未統合時の無変更停止、migration-only未完了、統合済み保持、`--check`拒否、`--skip-agents`免除をPython回帰で確認 |

検証結果:

- Repository検証: `PASS`
- Python回帰テスト: `PASS`、144件
- Python構文コンパイル: `PASS`
- Unity `6000.4.10f1` fixture: `COMPLETED / PASS`
  - Run ID: `20260611T141954Z`
  - Compile: `PASS`
  - EditMode: `PASS`、6件
  - PlayMode: `PASS`、2件
  - Asset validation: `PASS`
  - Validation Run integrity: `PASS`

この対応により、既存`AGENTS.md`を持つProjectが必須作業契約なしで
`Installation complete`と完全性`PASS`になる経路を閉じた。

### 15.10 P1-2 harness.lock.json所有境界対応結果

標準pinとゲーム固有差分の所有者を分離した。

実装:

- `harness.lock.json`を`harness-managed`へ変更し、install manifestと完全性
  Verifierで欠落・変更を検出
- 空の`harness.overrides.json`を`project-owned` templateとして追加
- overrideはdependency単位で`reason`、`approvedBy`、`approvedAt`、
  `values`を必須化
- 依存診断CLIが標準lockへoverrideをdeep mergeし、未知field、承認情報不足、
  commit固定不整合、bundled化・自動導入化を拒否
- JSON診断結果へ`activeOverrides`を追加
- 旧project-owned lockに差分がある場合、通常Installerを全書込み前に停止
- `--prepare-migration`でlockのbase・local・incomingとoverride templateを
  生成し、local不変・終了コード`1`の導入未完了とする
- 移行後は`--force-file harness.lock.json`でbackup付き標準化

`DEBUG-004-AC05`:

| AC ID | 結果 | 証拠・備考 |
|---|---|---|
| `DEBUG-004-AC05` | `PASS` | 標準lock drift拒否、project override許可、承認metadata、不正field、旧lock migrationをPython回帰で確認 |

検証結果:

- Repository検証: `PASS`
- Python回帰テスト: `PASS`、154件
- Python構文コンパイル: `PASS`
- Unity fixture: `NOT RUN`
  - Unity C#、Asset、Scene、Prefab、ProjectSettings、検証runnerの変更なし
  - 変更範囲はInstaller、Python依存診断、所有区分、文書に限定

この対応により、ゲーム側が標準pinを偶発的に変更しても完全性`PASS`となる
経路を閉じ、意図した差分だけをレビュー可能なproject-owned記録へ分離した。
