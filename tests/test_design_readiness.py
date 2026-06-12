from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SCRIPT = SCRIPTS / "validate_design_readiness.py"
sys.path.insert(0, str(SCRIPTS))


def load_module():
    spec = importlib.util.spec_from_file_location(
        "validate_design_readiness",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


readiness = load_module()


class DesignReadinessTests(unittest.TestCase):
    def concept_sheet(self) -> str:
        hreq_rows = []
        resolved = {
            "HREQ-DESIGN-001",
            "HREQ-PROJECT-001",
            "HREQ-VALIDATION-001",
        }
        for requirement_id in readiness.PROJECT_REQUIREMENT_IDS:
            state = "継承" if requirement_id in resolved else "未決定"
            hreq_rows.append(
                f"| `{requirement_id}` | {state} | decision | なし | Owner 2026-06-11 |"
            )

        required_phases = readiness.PHASE_REQUIREMENTS["Concept"]
        phase_rows = []
        for phase_id in readiness.PHASE_IDS:
            if phase_id in required_phases:
                phase_rows.append(
                    f"| `{phase_id}` | Topic | 必須 | 人間承認済 | "
                    "confirmed | なし | なし | Owner 2026-06-11 | SELF REVIEW |"
                )
            else:
                phase_rows.append(
                    f"| `{phase_id}` | Topic | 後続 | 未着手 | "
                    "later milestone | なし | なし | 未決定 | NOT RUN |"
                )

        cross_rows = [
            f"| {area} | 不採用 | Conceptでは使用しない | なし | なし | "
            "なし | Owner | Prototypeで再評価 |"
            for area in readiness.CROSS_CUTTING_AREAS
        ]

        return "\n".join(
            [
                "# Unityゲーム個別要件・設計書",
                "## 標準要件適合表",
                "| HREQ ID | 適用状態 | このゲームでの決定・理由 | 例外時の影響・代替策 | 承認者・日付 |",
                "|---|---|---|---|---|",
                *hreq_rows,
                "## 0. 文書情報",
                "| 項目 | 決定内容 |",
                "|---|---|",
                "| プロジェクト名 | Test Game |",
                "| 作成者・責任者 | Owner |",
                "| 現在のマイルストーン | Concept |",
                "| 設計レビュー状態 | Approved |",
                "### 初期設計対話",
                "| 項目 | 状態 |",
                "|---|---|",
                "| 対象マイルストーン | Concept |",
                "| セッション状態 | マイルストーン承認済 |",
                "| 意思決定者 | Owner |",
                "| 最終監査 | SELF REVIEW |",
                "",
                "| Phase ID | テーマ | 適用 | 状態 | 確定内容・再検討理由 | Blocking未決事項ID | 関連設計ID | 確認者・日付 | 監査 |",
                "|---|---|---|---|---|---|---|---|---|",
                *phase_rows,
                "### HREQ-PLATFORM-001: Unityバージョン・対象プラットフォーム",
                "| 項目 | 決定内容 |",
                "|---|---|",
                "| 主対象プラットフォーム | Desktop |",
                "| 入力方式 | Keyboard |",
                "## 1. コンセプト",
                "| 項目 | 決定内容 |",
                "|---|---|",
                "| 一文コンセプト | Build a tiny world |",
                "| ジャンル | Puzzle |",
                "| 対象プレイヤー | Puzzle fans |",
                "| 提供する中心体験 | Discover rules |",
                "| 差別化要素 | One-screen simulation |",
                "| 今回作らないもの | Online play |",
                "### 勝利・失敗・終了条件",
                "| 種別 | 条件 | 結果 |",
                "|---|---|---|",
                "| 勝利 | Goal reached | Results shown |",
                "| 失敗 | Moves exhausted | Retry shown |",
                "| 中断・終了 | User exits | Return to title |",
                "## 2. ゲームループとメカニクス",
                "### コアループ",
                "```text",
                "Observe, act, and evaluate the board.",
                "```",
                "### メカニクス一覧",
                "| 設計ID | 状態 | メカニクス | 入力・開始条件 | ルール | 結果・報酬 |",
                "|---|---|---|---|---|---|",
                "| `MECH-001` | Approved | Move | Select a tile | Move once | Board changes |",
                "### MECH-001: Move",
                "**状態:** Approved",
                "**上流AC:** `GAME-AC-001`",
                "**仕様**",
                "Selecting a tile moves the player once.",
                "**依存・影響**",
                "Board state.",
                "#### 実装マッピング",
                "| Unity単位 | Path | Symbol / Hierarchy | 状態 |",
                "|---|---|---|---|",
                "| Script | `Assets/Game/Move.cs` | `Game.Move` | Planned |",
                "## 12. 横断機能採否",
                "### HREQ-CROSS-001: 横断機能採否",
                "| 領域 | 状態 | 理由・対象範囲 | Package / Service | データ・規制・安全性 | 設計ID・AC | 決定者 | 再評価条件・期限 |",
                "|---|---|---|---|---|---|---|---|",
                *cross_rows,
                "## 14. 未決事項・承認記録",
                "### 未決事項",
                "| ID | 状態 | 分類 | 内容 | 影響・Blocking対象 | 決定者 | 期限・マイルストーン |",
                "|---|---|---|---|---|---|---|",
                "| `Q-001` | 未解決 / 解決済 / 対象外 | 要確認 / 仮定 | `未決定` | `未決定` | `未決定` | `未決定` |",
                "",
            ]
        )

    def write_project(self, root: Path, text: str) -> Path:
        docs = root / "docs"
        docs.mkdir(parents=True)
        shutil.copy2(ROOT / "docs" / "unity_design_sheet.md", docs)
        shutil.copytree(ROOT / "docs" / "game_design", docs / "game_design")
        for path in (docs / "game_design" / "all").glob("*.md"):
            path.write_text("", encoding="utf-8")
        (docs / "game_design" / "all" / "acceptance.md").write_text(
            "\n".join(
                [
                    "<!-- UNITY_CODEX_ACCEPTANCE: GAME -->",
                    "# ゲーム全体受け入れ条件",
                    "| AC ID | 状態 | 合格条件 | 検証種別 | 検証方法 | 承認者・日付 | 関連設計ID | 旧AC ID |",
                    "|---|---|---|---|---|---|---|---|",
                    "| `GAME-AC-001` | Approved | Player can move | `AUTO:PLAY` | PlayMode test | Owner 2026-06-11 | `MECH-001` | `なし` |",
                ]
                + [""]
            ),
            encoding="utf-8",
        )
        (docs / "game_design" / "all" / "game_design.md").write_text(
            text,
            encoding="utf-8",
        )
        return root

    def test_complete_concept_passes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = self.write_project(
                Path(temporary_directory),
                self.concept_sheet(),
            )

            report = readiness.validate_readiness(project, "Concept")

            self.assertEqual(report["status"], "PASS", report["errors"])

    def test_unapproved_required_phase_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            text = self.concept_sheet().replace(
                "| `PHASE-03` | Topic | 必須 | 人間承認済 |",
                "| `PHASE-03` | Topic | 必須 | 対話中 |",
            )
            project = self.write_project(Path(temporary_directory), text)

            report = readiness.validate_readiness(project, "Concept")

            self.assertIn(
                "required phase is not human-approved: PHASE-03 -> 対話中",
                report["errors"],
            )

    def test_question_blocking_required_phase_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            text = self.concept_sheet().replace(
                "| `Q-001` | 未解決 / 解決済 / 対象外 | 要確認 / 仮定 | `未決定` | `未決定` | `未決定` | `未決定` |",
                "| `Q-010` | 未解決 | 要確認 | Decide loop | PHASE-03 | Owner | Concept |",
            )
            project = self.write_project(Path(temporary_directory), text)

            report = readiness.validate_readiness(project, "Concept")

            self.assertIn(
                "open question blocks required phase: Q-010 -> PHASE-03",
                report["errors"],
            )
            self.assertIn(
                "open question is due by target milestone: Q-010 -> Concept",
                report["errors"],
            )

    def test_prototype_requires_approved_design_item(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            text = self.concept_sheet().replace(
                "**状態:** Approved",
                "**状態:** Draft",
            )
            project = self.write_project(Path(temporary_directory), text)

            report = readiness.validate_readiness(project, "Prototype")

            self.assertIn(
                "Prototype requires an Approved design item",
                report["errors"],
            )

    def test_mandatory_hreq_cannot_be_target_excluded(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            text = self.concept_sheet().replace(
                "| `HREQ-DESIGN-001` | 継承 | decision | なし |",
                "| `HREQ-DESIGN-001` | 対象外 | reason | なし |",
            )
            project = self.write_project(Path(temporary_directory), text)

            report = readiness.validate_readiness(project, "Concept")

            self.assertIn(
                "mandatory HREQ cannot be target-excluded: HREQ-DESIGN-001",
                report["errors"],
            )

    def test_adopted_cross_cutting_requires_design_id_and_ac(self):
        text = self.concept_sheet().replace(
            "| Accessibility | 不採用 | Conceptでは使用しない | なし | なし | なし | Owner | Prototypeで再評価 |",
            "| Accessibility | 採用 | Captions | built-in | no personal data | なし | Owner | Releaseで再評価 |",
        )
        tables = readiness.parse_tables(text)
        errors: list[str] = []

        readiness.validate_cross_cutting("Prototype", tables, errors)

        self.assertIn(
            "adopted cross-cutting design ID/AC missing: Accessibility",
            errors,
        )

    def test_cli_writes_json_report(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory)
            self.write_project(project, self.concept_sheet())

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--project-root",
                    str(project),
                    "--milestone",
                    "Concept",
                    "--output",
                    "Artifacts/DesignReadiness/Concept.json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stdout)
            report = json.loads(
                (
                    project
                    / "Artifacts"
                    / "DesignReadiness"
                    / "Concept.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["milestone"], "Concept")


if __name__ == "__main__":
    unittest.main()
