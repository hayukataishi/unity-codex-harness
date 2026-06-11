from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "scripts"
    / "validate_design_contract.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("validate_design_contract", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


contract = load_module()


class DesignContractTests(unittest.TestCase):
    def write_sheet(self, root: Path, rows: list[str]) -> Path:
        sheet = root / "docs" / "unity_design_sheet.md"
        sheet.parent.mkdir(parents=True)
        sheet.write_text("\n".join(rows) + "\n", encoding="utf-8")
        return sheet

    def valid_rows(self) -> list[str]:
        return [
            "| HREQ ID | 適用状態 | 決定 | 影響・代替策 | 承認者・日付 |",
            "|---|---|---|---|---|",
            *[
                f"| `{requirement_id}` | 継承 | standard | なし | initial |"
                for requirement_id in contract.PROJECT_REQUIREMENT_IDS
            ],
        ]

    def test_repository_design_sheet_has_complete_contract(self):
        errors = contract.validate_contract(
            ROOT / "docs" / "unity_design_sheet.md"
        )

        self.assertEqual(errors, [])

    def test_missing_requirement_row_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            rows = self.valid_rows()
            rows = [
                row for row in rows if "HREQ-SAVE-001" not in row
            ]
            sheet = self.write_sheet(Path(temporary_directory), rows)

            errors = contract.validate_contract(sheet)

            self.assertIn("missing HREQ row: HREQ-SAVE-001", errors)

    def test_required_unresolved_requirement_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            rows = [
                row.replace(
                    "| `HREQ-ARCH-001` | 継承 |",
                    "| `HREQ-ARCH-001` | 未決定 |",
                )
                for row in self.valid_rows()
            ]
            sheet = self.write_sheet(Path(temporary_directory), rows)

            errors = contract.validate_contract(
                sheet,
                required_resolved={"HREQ-ARCH-001"},
            )

            self.assertIn(
                "required HREQ remains unresolved: HREQ-ARCH-001",
                errors,
            )

    def test_approved_exception_requires_reason_mitigation_and_approval(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            rows = [
                row.replace(
                    "| `HREQ-BUILD-001` | 継承 | standard | なし | initial |",
                    "| `HREQ-BUILD-001` | 例外承認 | 未決定 | 未決定 | 未決定 |",
                )
                for row in self.valid_rows()
            ]
            sheet = self.write_sheet(Path(temporary_directory), rows)

            errors = contract.validate_contract(sheet)

            self.assertEqual(
                errors,
                [
                    "approved exception requires a reason: HREQ-BUILD-001",
                    (
                        "approved exception requires impact and mitigation: "
                        "HREQ-BUILD-001"
                    ),
                    (
                        "approved exception requires approver and date: "
                        "HREQ-BUILD-001"
                    ),
                ],
            )


if __name__ == "__main__":
    unittest.main()
