from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_design_contract.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_design_contract", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


contract = load_module()


class DesignContractTests(unittest.TestCase):
    def create_document_set(self, root: Path) -> Path:
        docs = root / "docs"
        docs.mkdir(parents=True)
        shutil.copy2(ROOT / "docs" / "unity_design_sheet.md", docs)
        shutil.copytree(ROOT / "docs" / "game_design", docs / "game_design")
        return root

    def standards_path(self, root: Path) -> Path:
        return root / "docs" / "game_design" / "all" / "standards.md"

    def test_repository_design_sheet_has_complete_contract(self):
        errors = contract.validate_contract(ROOT)
        self.assertEqual(errors, [])

    def test_missing_requirement_row_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = self.create_document_set(Path(temporary_directory))
            path = self.standards_path(root)
            text = "\n".join(
                line
                for line in path.read_text(encoding="utf-8").splitlines()
                if "HREQ-SAVE-001" not in line
            )
            path.write_text(text + "\n", encoding="utf-8")

            errors = contract.validate_contract(root)

            self.assertIn("missing HREQ row: HREQ-SAVE-001", errors)

    def test_required_unresolved_requirement_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = self.create_document_set(Path(temporary_directory))

            errors = contract.validate_contract(
                root,
                required_resolved={"HREQ-ARCH-001"},
            )

            self.assertIn(
                "required HREQ remains unresolved: HREQ-ARCH-001",
                errors,
            )

    def test_approved_exception_requires_reason_mitigation_and_approval(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = self.create_document_set(Path(temporary_directory))
            path = self.standards_path(root)
            text = path.read_text(encoding="utf-8").replace(
                "| `HREQ-BUILD-001` | 未決定 | Player buildとBuild Profile採否を決める | `未決定` | `未決定` |",
                "| `HREQ-BUILD-001` | 例外承認 | 未決定 | 未決定 | 未決定 |",
            )
            path.write_text(text, encoding="utf-8")

            errors = contract.validate_contract(root)

            self.assertIn(
                "approved exception requires a reason: HREQ-BUILD-001",
                errors,
            )
            self.assertIn(
                "approved exception requires impact and mitigation: HREQ-BUILD-001",
                errors,
            )
            self.assertIn(
                "approved exception requires approver and date: HREQ-BUILD-001",
                errors,
            )

    def test_approved_ac_and_design_require_reciprocal_links(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = self.create_document_set(Path(temporary_directory))
            acceptance = (
                root / "docs" / "game_design" / "all" / "acceptance.md"
            )
            acceptance.write_text(
                acceptance.read_text(encoding="utf-8").replace(
                    "| `GAME-AC-001` | Draft | `未決定` | `MANUAL:PLAY` | `未決定` | `未決定` | `未決定` | `なし` |",
                    "| `GAME-AC-001` | Approved | Player wins | `AUTO:PLAY` | PlayMode test | Owner 2026-06-12 | `MECH-001` | `なし` |",
                ),
                encoding="utf-8",
            )
            design = root / "docs" / "game_design" / "all" / "game_design.md"
            design.write_text(
                design.read_text(encoding="utf-8").replace(
                    "### `<DOMAIN>-<NNN>`: `<短い名称>`",
                    "### MECH-001: Win condition",
                ).replace(
                    "**状態:** Draft / Approved / 廃止",
                    "**状態:** Approved",
                ).replace(
                    "**上流AC:** `GAME-AC-001`",
                    "**上流AC:** `GAME-AC-002`",
                ).replace(
                    "`未決定`\n\n**依存・影響**",
                    "Reach the goal.\n\n**依存・影響**",
                    1,
                ).replace(
                    "| Script / Prefab / Scene / Setting | `Assets/...` | `未決定` | Planned / Implemented / 廃止 |",
                    "| Script | `Assets/Game/Goal.cs` | `Game.Goal` | Planned |",
                ),
                encoding="utf-8",
            )

            errors = contract.validate_contract(root)

            self.assertIn(
                "design references unknown upstream AC: MECH-001 -> GAME-AC-002",
                errors,
            )
            self.assertIn(
                "design/AC link is not reciprocal: MECH-001 -> GAME-AC-001",
                errors,
            )

    def test_require_implemented_checks_mapping_path(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = self.create_document_set(Path(temporary_directory))
            acceptance = (
                root / "docs" / "game_design" / "all" / "acceptance.md"
            )
            acceptance.write_text(
                acceptance.read_text(encoding="utf-8").replace(
                    "| `GAME-AC-001` | Draft | `未決定` | `MANUAL:PLAY` | `未決定` | `未決定` | `未決定` | `なし` |",
                    "| `GAME-AC-001` | Approved | Player wins | `AUTO:PLAY` | PlayMode test | Owner 2026-06-12 | `MECH-001` | `なし` |",
                ),
                encoding="utf-8",
            )
            design = root / "docs" / "game_design" / "all" / "game_design.md"
            design.write_text(
                design.read_text(encoding="utf-8").replace(
                    "### `<DOMAIN>-<NNN>`: `<短い名称>`",
                    "### MECH-001: Win condition",
                ).replace(
                    "**状態:** Draft / Approved / 廃止",
                    "**状態:** Approved",
                ).replace(
                    "`未決定`\n\n**依存・影響**",
                    "Reach the goal.\n\n**依存・影響**",
                    1,
                ).replace(
                    "| Script / Prefab / Scene / Setting | `Assets/...` | `未決定` | Planned / Implemented / 廃止 |",
                    "| Script | `Assets/Game/Goal.cs` | `Game.Goal` | Implemented |",
                ),
                encoding="utf-8",
            )

            errors = contract.validate_contract(
                root,
                require_implemented={"MECH-001"},
            )

            self.assertIn(
                "implemented mapping path does not exist: MECH-001 -> Assets/Game/Goal.cs",
                errors,
            )


if __name__ == "__main__":
    unittest.main()
