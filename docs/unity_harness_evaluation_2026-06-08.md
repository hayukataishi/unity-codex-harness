# Unity Codex Harness 評価レポート

- 評価日: 2026-06-08
- 最終更新日: 2026-06-09
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

### P1: 検証Runが開始状態のまま完結しない

`create_validation_run.py`は`result: NOT RUN`のManifestとReportを作るが、終了時刻、コマンド終了コード、AC別結果、成果物一覧、最終結果を確定する処理がない。「immutable」という名称に対して、完了後の整合性や改ざん検知もない。

**改善案:** `finalize_validation_run.py`を追加し、次を行う。

- テストXMLとログを解析
- AC別結果を確定
- `completedAtUtc`とdurationを記録
- コマンドと終了コードを記録
- 成果物の相対パス、サイズ、SHA-256を記録
- `FAIL`、`BLOCKED`、`NOT RUN`があれば受け入れ未完了にする
- Manifest schema versionを記録

### P1: テンプレート自身の回帰テストが不足

`validate_repository.py`はSkill frontmatterと一部Markdownリンクを確認するが、インストーラー、プリフライト、Run作成の自動テストはない。

**改善案:** 標準Python `unittest`で次を追加する。

- 新規導入
- 再導入
- 競合検出
- `--force`
- `--dry-run`
- `.gitignore`更新
- `.meta`不足、孤立、重複GUID
- Missing Script
- Run ID衝突
- Manifest schema

### P1: 実動サンプルまたはfixture Unityプロジェクトがない

文書とSkillだけでは、Unity Package、asmdef、Test Framework、Build Profile、Scene、Prefab検査が実際に成立するか継続確認できない。

**改善案:** 小さな`Samples~/`または別fixtureプロジェクトを用意し、次を含める。

- Unity 6.4 Update基準
- Runtime / Editor / EditMode / PlayMode asmdef
- 1つのSceneとPrefab
- 1つの設計IDとAUTO/MANUAL AC
- EditMode / PlayModeテスト
- Build Profile
- 故意に壊した検証用fixture

### P1: 汎用性に必要な横断設計が「付録」に留まる

ネットワーク、ローカライズ、UGS、性能、デバッグ、XRは付録扱いで、アクセシビリティ、プライバシー、クラッシュ収集、分析、課金、モデレーション、セキュリティ、ライブ運用のゲートがない。

すべてを初期必須にする必要はないが、該当性を判定するチェックは必要である。

**改善案:** 設計シートへ「横断機能採否マトリクス」を追加する。

| 領域 | 採用 | 理由 | 対象Package/Service | ACあり |
|---|---|---|---|---|
| Accessibility | | | | |
| Localization | | | | |
| Multiplayer | | | | |
| Analytics / Crash | | | | |
| Privacy / Consent | | | | |
| LiveOps / Remote Config | | | | |
| IAP / Ads | | | | |
| Modding / UGC | | | | |
| XR | | | | |

### P2: アーキテクチャ例が規模に対して強すぎる

4層アーキテクチャ、4 asmdef、Manager群、ScriptableObject Event Channel、DI候補が標準形として読める。中・大規模案件には有用だが、小規模ゲームやGame Jamでは過剰であり、大規模案件ではFeature PackageやPure C# Assemblyの分離が不足する場合がある。

また、`ServiceLocator`を中規模向けとする表現は、依存の不可視化を招くため推奨表現としては弱い。

**改善案:** Small / Standard / Largeの3プロファイルに分け、選択理由と移行条件を記録する。

### P2: セーブ設計が最低限に留まる

JSON、PlayerPrefs、暗号化、versionフィールドだけでは、実運用で必要な破損対策を扱えない。

**改善案:** 次の決定欄を追加する。

- Atomic writeと一時ファイル
- Backup / rollback
- Checksum / integrity
- Schema migrationとdowngrade方針
- Cloud conflict resolution
- 暗号化と鍵管理
- 個人情報・規制対象データ
- プラットフォーム別保存制約
- セーブ互換テストfixture

### P2: Gitと大容量アセット方針が固定例に寄りすぎる

`main / develop / feature/*`や`.png`を一律Git LFS対象にする記述は、チーム規模やリポジトリ特性によって適否が変わる。

**改善案:** ブランチ戦略、LFS閾値、UnityYAMLMerge、Force Text、Visible Meta Files、シーン・Prefab競合の所有ルールを選択式にする。

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
4. Validation Runのfinalize処理とschemaを追加する。
5. インストーラーへupgrade、backup、diff、version表示を追加する。

### フェーズ3: 汎用ゲーム開発の拡張

1. Accessibility、Localization、Multiplayer、Privacy、LiveOpsの採否ゲートを追加する。
2. Small / Standard / Largeのアーキテクチャプロファイルを追加する。
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
│  │  └─ finalize_validation_run.py
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
| インストーラー通常実行 | PASS | 一時Unityプロジェクトへ28ファイルを導入 |
| インストーラー再実行 | PASS | 0変更、28ファイルunchanged |
| Validation Run作成 | PASS | UTC Run ID、Manifest、Report、成果物ディレクトリを生成 |
| 静的プリフライト | PASS | Unity 6.4 fixtureで必須パス、`.meta`、GUIDを検査 |
| Unity Editor compile | PASS | ローカルUnity `6000.4.10f1` |
| EditMode / PlayMode | PASS | EditMode 4件、PlayMode 1件 |
| GitHub Actions静的job | 定義済み | Workflow構文とローカル相当コマンドはPASS、GitHub上はNOT RUN |
| GitHub Actions Unity job | NOT RUN | Unity Secretと正確なGameCI imageが必要 |
| AssetDatabase参照検査 | PASS | Missing Referenceと必須参照の正常系・異常系 |
| 外部依存マニフェスト | PASS | Unity MCPとagent-sprite-forgeのcommit、要件、`NOT RUN`理由を検査 |
| Build Profile文書規約 | PASS | `BUILD-001`、3分類、Scene List、Defines、Clean Build、CI指定 |
| Build Profile build | NOT RUN | fixtureに保存済みBuild ProfileとPlayer Sceneがない |
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
