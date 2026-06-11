#!/usr/bin/env python3
"""Validate inherited harness requirements in a project-owned design sheet."""

from __future__ import annotations

import argparse
from pathlib import Path


PROJECT_REQUIREMENT_IDS = (
    "HREQ-DESIGN-001",
    "HREQ-PLATFORM-001",
    "HREQ-PROJECT-001",
    "HREQ-ART-001",
    "HREQ-CAMERA-001",
    "HREQ-ARCH-001",
    "HREQ-SAVE-001",
    "HREQ-REPO-001",
    "HREQ-BUILD-001",
    "HREQ-CROSS-001",
    "HREQ-VALIDATION-001",
)
VALID_STATES = {"継承", "対象外", "例外承認", "未決定"}
PLACEHOLDER_VALUES = {"", "未決定", "`未決定`", "-", "なし"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the HREQ conformance table in a game design sheet."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Unity project root containing docs/unity_design_sheet.md",
    )
    parser.add_argument(
        "--require",
        action="append",
        default=[],
        metavar="HREQ-ID",
        help="Require a specific HREQ row to be resolved; may be repeated.",
    )
    parser.add_argument(
        "--require-all-resolved",
        action="store_true",
        help="Reject every HREQ row whose state is 未決定.",
    )
    return parser.parse_args()


def normalize_cell(value: str) -> str:
    return value.strip().strip("`").strip()


def parse_conformance_rows(text: str) -> tuple[dict[str, tuple[str, ...]], list[str]]:
    rows: dict[str, tuple[str, ...]] = {}
    errors: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.lstrip().startswith("|"):
            continue
        cells = tuple(normalize_cell(cell) for cell in line.strip().strip("|").split("|"))
        if not cells or cells[0] not in PROJECT_REQUIREMENT_IDS:
            continue
        requirement_id = cells[0]
        if requirement_id in rows:
            errors.append(
                f"duplicate HREQ row: {requirement_id} at line {line_number}"
            )
            continue
        rows[requirement_id] = cells
    return rows, errors


def validate_contract(
    design_sheet: Path,
    required_resolved: set[str] | None = None,
    require_all_resolved: bool = False,
) -> list[str]:
    if not design_sheet.is_file():
        return [f"missing game design sheet: {design_sheet}"]

    required_resolved = required_resolved or set()
    unknown_required = sorted(required_resolved.difference(PROJECT_REQUIREMENT_IDS))
    errors = [f"unknown HREQ ID: {item}" for item in unknown_required]
    rows, parse_errors = parse_conformance_rows(
        design_sheet.read_text(encoding="utf-8")
    )
    errors.extend(parse_errors)

    for requirement_id in PROJECT_REQUIREMENT_IDS:
        cells = rows.get(requirement_id)
        if cells is None:
            errors.append(f"missing HREQ row: {requirement_id}")
            continue
        if len(cells) < 5:
            errors.append(
                f"invalid HREQ row: {requirement_id} requires 5 columns"
            )
            continue

        state, decision, mitigation, approval = cells[1:5]
        if state not in VALID_STATES:
            errors.append(
                f"invalid HREQ state: {requirement_id} -> {state or '<empty>'}"
            )
            continue
        if state == "対象外" and decision in PLACEHOLDER_VALUES:
            errors.append(
                f"target-excluded HREQ requires a reason: {requirement_id}"
            )
        if state == "例外承認":
            if decision in PLACEHOLDER_VALUES:
                errors.append(
                    f"approved exception requires a reason: {requirement_id}"
                )
            if mitigation in PLACEHOLDER_VALUES:
                errors.append(
                    f"approved exception requires impact and mitigation: "
                    f"{requirement_id}"
                )
            if approval in PLACEHOLDER_VALUES:
                errors.append(
                    f"approved exception requires approver and date: "
                    f"{requirement_id}"
                )
        if state == "未決定" and (
            require_all_resolved or requirement_id in required_resolved
        ):
            errors.append(f"required HREQ remains unresolved: {requirement_id}")

    return errors


def main() -> int:
    args = parse_args()
    design_sheet = (
        args.project_root.resolve() / "docs" / "unity_design_sheet.md"
    )
    errors = validate_contract(
        design_sheet,
        required_resolved=set(args.require),
        require_all_resolved=args.require_all_resolved,
    )
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("Design contract validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
