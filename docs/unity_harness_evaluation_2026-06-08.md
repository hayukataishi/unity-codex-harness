# Unity Codex Harness 評価レポート

- 評価日: 2026-06-08
- 評価対象: Unity Codex Harness リポジトリ全体
- 評価目的: 最新のUnityゲーム開発をジャンル・規模・対象プラットフォームに依存せず進めるための汎用ハーネスとして、設計、実装支援、検証、再現性、安全性を評価する

## 1. 結論

本テンプレートは、**CodexにUnityプロジェクトを安全かつ追跡可能に扱わせるための運用設計としては高品質**である。一方、**インストール後すぐにコンパイル、テスト、アセット検査、ビルド、CIまで自動実行できる完成済み開発環境ではない**。

現状の最も正確な位置づけは、次の通り。

> 設計・承認・証拠管理の規約がよく整った「Unity AI開発ハーネスの初期基盤」。  
> 実行可能なUnity Editor側ツール、CI、依存バージョン固定、サンプルプロジェクトを追加すれば、汎用的な実運用テンプレートへ発展できる。

### 総合評価

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
- `validate-unity-change`の2つの補助スクリプト

このリポジトリ自体には`Assets/`、`Packages/`、`ProjectSettings/ProjectVersion.txt`がなく、Unityプロジェクト本体ではない。そのため、以下は未評価である。

- 実Unity Editorでのコンパイル
- Unity MCPとの実接続
- EditMode / PlayModeテスト
- Scene、Prefab、ScriptableObjectのEditor API検査
- 実プラットフォーム向けビルド
- Play Modeの操作と映像・Profiler取得

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

### P0: 実行可能なCI・Unityバッチ検証がない

設計書ではコンパイル、EditMode、PlayMode、アセット検査、ビルドを要求しているが、実装済みスクリプトはRun作成と静的プリフライトだけである。

不足しているもの:

- Unity Editorのバッチ起動ラッパー
- EditMode / PlayModeテスト実行
- NUnit XMLの保存
- Code Coverage実行
- Build Profileを指定した検証ビルド
- Editor.logと終了コードの収集
- GitHub ActionsなどのCI定義
- ライセンス認証方式とSecret運用

**改善案:** `scripts/unity/`またはUnity Package内に、`run-tests`、`validate-assets`、`build-player`、`finalize-validation-run`を実装する。CIでは最低でもリポジトリ検査、コンパイル、EditMode、PlayMode、代表Build Profileのビルドを実行する。

### P0: Missing Referenceと必須資産検査が実装されていない

`preflight_unity_project.py`が検出するのは、主に次の項目である。

- 必須パス
- `.meta`不足・孤立
- GUID形式・重複
- YAML上の`m_Script: {fileID: 0}`パターン

一般的なMissing Reference、Prefab/Scene/SOの必須フィールド、Build ProfileのScene、Tag、Layer、Input Action、Addressables設定は検査していない。設計書とSkillが掲げる検証範囲との間に差がある。

**改善案:** Unity Editor Assemblyへ検証Packageを追加し、`SerializedObject`、`AssetDatabase`、`PrefabUtility`、Scene API、Build Profile APIを使って検査する。PythonのYAML検査は高速プリフライトに限定し、正式なアセット合格判定はEditor APIへ寄せる。

### P0: 外部依存のバージョンが固定されていない

Unity MCPとagent-sprite-forgeは同梱されず、「最新版を確認」とだけ記載されている。2026-06-08時点でCoplayDev/unity-mcpのREADMEにはv9.7.0が直近リリースとして掲載されているが、本テンプレートは対応確認済みバージョン、Git commit、導入チャネルを記録していない。

agent-sprite-forgeは`Pillow`と`numpy`を必要とするが、ハーネス側に存在確認やバージョン確認がない。

**改善案:** `harness.lock.json`のような互換性マニフェストを追加し、以下を記録する。

- Harness version
- 対応Unity Editor範囲
- Unity MCPの確認済みversion / commit / channel
- agent-sprite-forgeの確認済みversion / commit
- 必須Python versionとPackage
- 検証日

「最新版追従」と「再現可能性」を分離し、更新Botまたは定期検証で互換性を更新する。

### P0: インストール後に`Artifacts/`除外が保証されない

ハーネス自身の`.gitignore`には`Artifacts/`があるが、インストーラーは対象Unityプロジェクトへ`.gitignore`をコピー・更新しない。そのため、対象側の設定によっては検証ログ、動画、Build、ローカルパスを誤ってGitへ追加できる。

**改善案:** インストーラーへ次を追加する。

- `.gitignore`へ`/Artifacts/`を安全に追記するオプション
- `--check`で除外状態を検証
- 既存設定を壊さないマーカー付き管理
- Secretや絶対パスを含む成果物のスキャン

### P1: Unity 6向けBuild Profile記述へ統一されていない

設計書にはBuild Profilesも登場するが、シーンフローでは旧来の`Build Settings`を中心に説明している。Unity 6のBuild ProfileはVersion Control可能なアセットであり、プロファイルごとにScene List、Scripting Defines、Player設定の差分を持てる。

**改善案:** 次を標準テンプレートへ加える。

- Development / QA / ReleaseのProfile分類
- ProfileごとのScene List
- Scripting Defines
- Development Build、Profiler、Script Debugging
- Clean Buildの実行条件
- Build Profileアセットの保存場所と命名

### P1: Cinemachineの例が2系の名称

`docs/unity_design_sheet.md`のカメラ例は`CinemachineVirtualCamera`を使用している。Unity 6向けにリリースされているCinemachine 3.1では、中心コンポーネントは`CinemachineCamera`である。

**改善案:** Packageバージョンで例を分岐する。

- Cinemachine 3.x: `CinemachineCamera`
- Cinemachine 2.x既存案件: `CinemachineVirtualCamera`

ハーネスは既存案件も扱うため、単純置換ではなく移行ガイドへのリンクとPackage検出が必要である。

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

1. `Artifacts/`のGit除外をインストーラーで保証する。
2. Unity 6.4 Update用の最小fixtureプロジェクトを追加する。
3. Unityバッチ実行でCompile、EditMode、PlayModeを自動化する。
4. Editor APIによるMissing Referenceと必須参照検査を追加する。
5. GitHub Actionsでリポジトリ検査とUnityテストを実行する。

完了条件:

- Pull Requestごとに自動検証が走る
- 失敗時に`Artifacts/ValidationRuns/<RunId>`相当の証拠を取得できる
- 文書上の主要検証項目と実装済み検証項目が一致する

### フェーズ2: 再現性とUnity 6対応

1. Harness、Unity MCP、agent-sprite-forgeの互換性マニフェストを追加する。
2. Build Profile中心のビルド設計へ更新する。
3. Cinemachine 3、Input System、Code Coverageの現行例へ更新する。
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
| インストーラー`--dry-run` | PASS | 一時fixture Unityプロジェクトへ18ファイルを検出 |
| インストーラー通常実行 | PASS | 一時fixtureへ18ファイルを導入 |
| Validation Run作成 | PASS | UTC Run ID、Manifest、Report、成果物ディレクトリを生成 |
| 静的プリフライト | PASS | 最小fixtureで必須パス、`.meta`、GUIDを検査 |
| Unity Editor compile | NOT RUN | このリポジトリはUnityプロジェクトではない |
| EditMode / PlayMode | NOT RUN | Unity Editorとテストfixtureがない |
| AssetDatabase参照検査 | NOT RUN | Editor検査コードがない |
| Build Profile build | NOT RUN | UnityプロジェクトとBuild Profileがない |
| Unity MCP接続 | NOT RUN | 評価セッションに対象Unity Editorがない |

一時fixtureの`ProjectVersion.txt`にはスクリプト動作確認用として`6000.3.0f1`を記載したが、実Unity Editorを起動したものではない。

## 9. 設計との整合性

設計文書、AGENTS指示、各Skillの責務は概ね整合している。主な差異は、**文書が要求する検証能力より、同梱スクリプトの実装範囲が狭いこと**である。

特に次は文書上は要求されるが、ハーネス単体では自動実行できない。

- Compile
- EditMode / PlayMode
- Missing Reference
- Scene / Prefab / ScriptableObjectの必須参照
- Build Profile / Scene List
- Input / Tag / Layer
- Build
- Profiler

## 10. 残課題・リスク

- Unity MCPは第三者プロジェクトであり、更新頻度が高い。バージョン固定なしではツール名や挙動の変化を吸収できない。
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
- Build Profile scene list  
  https://docs.unity3d.com/Manual/build-profile-scene-list.html
- Unity Test Framework  
  https://docs.unity3d.com/Manual/com.unity.test-framework.html
- Code Coverage  
  https://docs.unity3d.com/Manual/com.unity.testtools.codecoverage.html
- Cinemachine package information  
  https://docs.unity3d.com/Manual/com.unity.cinemachine.html
- Cinemachine Camera component 3.1  
  https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/manual/CinemachineCamera.html
- Input System  
  https://docs.unity3d.com/Manual/com.unity.inputsystem.html
- CoplayDev/unity-mcp  
  https://github.com/CoplayDev/unity-mcp
- 0x0funky/agent-sprite-forge  
  https://github.com/0x0funky/agent-sprite-forge

## 12. 最終判定

**条件付き採用を推奨する。**

- 設計・承認・安全規約の土台としては採用価値が高い。
- 小規模な試作やCodexとの共同作業には現状でも利用できる。
- チーム開発、継続運用、複数プラットフォーム、本番リリースへ使う前に、P0項目を実装する必要がある。
- 「最新のUnityゲーム開発を汎用的に行える完成環境」と呼ぶには、Unity Editor側検証、CI、Build Profile、依存固定、実動fixtureが不足している。

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

残るP0:

- Editor APIによるMissing Referenceと必須資産検査
- GitHub ActionsなどのCI
- 外部依存の互換性マニフェスト
- インストール先プロジェクトの`Artifacts/` Git除外保証
