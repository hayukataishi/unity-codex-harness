# Unity Codex Harness

Unityゲーム開発で、OpenAI Codexが設計・実装・検証・報告を一貫して進めるためのリポジトリ内ハーネスです。

このリポジトリには以下が含まれます。

- `.codex/skills/`: Unity開発向けのCodex Skills
- `docs/unity_harness_engineering.md`: ハーネスの運用・安全・品質ルール
- `docs/unity_design_sheet.md`: ゲーム設計書テンプレート
- `docs/mcp_and_skills_list.md`: Unity MCPとSkillsの責務
- `AGENTS.md`: Codexが最初に読むリポジトリ指示
- `scripts/install.py`: 既存Unityプロジェクトへの安全な導入スクリプト

## 導入

### 1. リポジトリを取得

```bash
git clone https://github.com/hayukataishi/unity-codex-harness.git
cd unity-codex-harness
```

### 2. Unityプロジェクトへインストール

```bash
python3 scripts/install.py /path/to/YourUnityProject
```

インストーラーはUnityプロジェクトの目印を検証し、次をプロジェクトルートへコピーします。

```text
<UNITY_PROJECT_ROOT>/
├─ .codex/skills/
├─ docs/
└─ AGENTS.md
```

既存ファイルは標準では上書きしません。

```bash
# 変更内容だけ確認
python3 scripts/install.py /path/to/YourUnityProject --dry-run

# AGENTS.mdを既存のプロジェクト指示で管理する
python3 scripts/install.py /path/to/YourUnityProject --skip-agents

# 内容を確認したうえで既存ファイルを置換
python3 scripts/install.py /path/to/YourUnityProject --force
```

手動導入する場合は、`.codex/skills/`、`docs/`、必要に応じて`AGENTS.md`をUnityプロジェクトルートへコピーしてください。Skills内の参照パスはこの配置を前提にしています。

## Codexでの使い方

UnityプロジェクトルートをCodexで開き、設計IDと目的を指定します。

```text
$maintain-game-design を使って、敵撃破時の経験値獲得仕様と受け入れ条件を設計書へ追加してください。
```

```text
$implement-unity-feature を使って MECH-001 を実装し、
$validate-unity-change で検証してください。
```

主なSkill:

| Skill | 用途 |
|---|---|
| `maintain-game-design` | 要求やレビューを追跡可能な設計へ変換 |
| `implement-unity-feature` | 承認済み設計を小さく安全に実装 |
| `validate-unity-change` | コンパイル、テスト、参照、証拠を検証 |
| `report-unity-work` | 人間がレビューできる形式で作業を報告 |
| `integrate-2d-assets` | 2D素材を承認済みプロファイルでUnityへ統合 |
| `review-gameplay` | Play Modeやビルドの観察証拠を整理 |

## 外部ツール

- [CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp): Unity Editor操作
- [0x0funky/agent-sprite-forge](https://github.com/0x0funky/agent-sprite-forge): 2Dアセット生成

これらは本リポジトリへ同梱していません。導入方法と利用可能な機能は各プロジェクトの最新版を確認してください。

## 検証

リポジトリ内のSkill構造、ローカル文書リンク、旧Vaultパスの残存を検証:

```bash
python3 scripts/validate_repository.py
```

Unityプロジェクトの静的プリフライト:

```bash
python3 .codex/skills/validate-unity-change/scripts/preflight_unity_project.py \
  --project-root /path/to/YourUnityProject
```

## ライセンス

[MIT License](./LICENSE)
