#!/usr/bin/env python3
"""Validate HREQ and AC -> design -> implementation traceability."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from design_document_set import (
    ACCEPTANCE_HEADERS,
    AC_ID_RE,
    DESIGN_ID_RE,
    GLOBAL_AC_RE,
    SCENE_AC_RE,
    VALID_AC_STATES,
    VALID_VERIFICATION_TYPES,
    acceptance_tables,
    design_item_blocks,
    load_document_set,
    normalize_cell,
    parse_tables,
)


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
PLACEHOLDER_VALUES = {
    "",
    "未決定",
    "`未決定`",
    "-",
    "なし",
    "Draft / Approved / 廃止",
    "Planned / Implemented / 廃止",
}
IMPLEMENTATION_HEADERS = (
    "Unity単位",
    "Path",
    "Symbol / Hierarchy",
    "状態",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate HREQ conformance and AC -> design -> implementation "
            "traceability in docs/game_design."
        )
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Unity project root containing docs/game_design/",
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
    parser.add_argument(
        "--require-implemented",
        action="append",
        default=[],
        metavar="DESIGN-ID",
        help=(
            "Require an Approved design item to have an Implemented mapping "
            "whose project-relative path exists; may be repeated."
        ),
    )
    return parser.parse_args()


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


def _is_placeholder(value: str) -> bool:
    normalized = normalize_cell(value)
    return (
        normalized in PLACEHOLDER_VALUES
        or "未決定" in normalized
        or "<" in normalized
    )


def _linked_ids(value: str, pattern: re.Pattern[str]) -> set[str]:
    return set(pattern.findall(normalize_cell(value)))


def _validate_hreqs(
    text: str,
    required_resolved: set[str],
    require_all_resolved: bool,
) -> list[str]:
    unknown_required = sorted(required_resolved.difference(PROJECT_REQUIREMENT_IDS))
    errors = [f"unknown HREQ ID: {item}" for item in unknown_required]
    rows, parse_errors = parse_conformance_rows(text)
    errors.extend(parse_errors)
    for requirement_id in PROJECT_REQUIREMENT_IDS:
        cells = rows.get(requirement_id)
        if cells is None:
            errors.append(f"missing HREQ row: {requirement_id}")
            continue
        if len(cells) < 5:
            errors.append(f"invalid HREQ row: {requirement_id} requires 5 columns")
            continue
        state, decision, mitigation, approval = cells[1:5]
        if state not in VALID_STATES:
            errors.append(
                f"invalid HREQ state: {requirement_id} -> {state or '<empty>'}"
            )
            continue
        if state == "対象外" and _is_placeholder(decision):
            errors.append(f"target-excluded HREQ requires a reason: {requirement_id}")
        if state == "例外承認":
            if _is_placeholder(decision):
                errors.append(
                    f"approved exception requires a reason: {requirement_id}"
                )
            if _is_placeholder(mitigation):
                errors.append(
                    "approved exception requires impact and mitigation: "
                    f"{requirement_id}"
                )
            if _is_placeholder(approval):
                errors.append(
                    f"approved exception requires approver and date: {requirement_id}"
                )
        if state == "未決定" and (
            require_all_resolved or requirement_id in required_resolved
        ):
            errors.append(f"required HREQ remains unresolved: {requirement_id}")
    return errors


def _scene_prefix(path: Path) -> str | None:
    parts = path.parts
    try:
        scene_index = parts.index("scenes")
    except ValueError:
        return None
    if scene_index + 1 >= len(parts):
        return None
    key = parts[scene_index + 1]
    return f"SCENE-{key.upper()}-AC-"


def _validate_acceptance(
    documents,
) -> tuple[dict[str, set[str]], dict[str, str], list[str]]:
    links: dict[str, set[str]] = {}
    states: dict[str, str] = {}
    errors: list[str] = []
    seen: set[str] = set()
    tables = acceptance_tables(documents)
    table_paths = {table.path for table in tables}
    for path in documents.acceptance_paths:
        if path not in table_paths:
            errors.append(
                f"missing acceptance table with required columns: {path.as_posix()}"
            )
    for table in tables:
        indices = {name: table.headers.index(name) for name in ACCEPTANCE_HEADERS}
        expected_scene_prefix = _scene_prefix(table.path)
        for row in table.rows:
            ac_id = row[indices["AC ID"]]
            if "<" in ac_id or ac_id in {"", "未発行"}:
                continue
            if AC_ID_RE.fullmatch(ac_id) is None:
                errors.append(f"invalid acceptance-criterion ID: {ac_id}")
                continue
            if ac_id in seen:
                errors.append(f"duplicate acceptance-criterion ID: {ac_id}")
                continue
            seen.add(ac_id)
            if table.path.name == "acceptance.md" and expected_scene_prefix:
                if not ac_id.startswith(expected_scene_prefix):
                    errors.append(
                        f"scene AC prefix mismatch: {table.path.as_posix()} -> {ac_id}"
                    )
            elif table.path.parts[-2:] == ("all", "acceptance.md"):
                if GLOBAL_AC_RE.fullmatch(ac_id) is None:
                    errors.append(f"global acceptance file requires GAME AC ID: {ac_id}")
            state = row[indices["状態"]]
            if state not in VALID_AC_STATES:
                errors.append(f"invalid AC state: {ac_id} -> {state}")
                continue
            states[ac_id] = state
            design_ids = _linked_ids(
                row[indices["関連設計ID"]],
                DESIGN_ID_RE,
            )
            links[ac_id] = design_ids
            if state != "Approved":
                continue
            for column in ("合格条件", "検証方法", "承認者・日付"):
                if _is_placeholder(row[indices[column]]):
                    errors.append(f"approved AC field unresolved: {ac_id} -> {column}")
            verification = row[indices["検証種別"]]
            if verification not in VALID_VERIFICATION_TYPES:
                errors.append(
                    f"invalid verification type: {ac_id} -> {verification}"
                )
            if not design_ids:
                errors.append(f"approved AC has no related design ID: {ac_id}")
    return links, states, errors


def _implementation_rows(path: Path, block: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for table in parse_tables(path, block):
        if not set(IMPLEMENTATION_HEADERS).issubset(table.headers):
            continue
        indices = {name: table.headers.index(name) for name in IMPLEMENTATION_HEADERS}
        for row in table.rows:
            rows.append({name: row[index] for name, index in indices.items()})
    return rows


def _validate_designs(
    documents,
    ac_links: dict[str, set[str]],
    ac_states: dict[str, str],
    require_implemented: set[str],
) -> list[str]:
    errors: list[str] = []
    designs: dict[str, tuple[Path, str, set[str], list[dict[str, str]]]] = {}
    for path, design_id, block in design_item_blocks(documents):
        if design_id in designs:
            errors.append(f"duplicate design ID: {design_id}")
            continue
        state_match = re.search(
            r"^\*\*状態:\*\*\s*(Draft|Approved|廃止)\s*$",
            block,
            re.MULTILINE,
        )
        state = state_match.group(1) if state_match else ""
        upstream_match = re.search(
            r"^\*\*上流AC:\*\*\s*(.+?)\s*$",
            block,
            re.MULTILINE,
        )
        upstream = (
            _linked_ids(upstream_match.group(1), AC_ID_RE)
            if upstream_match
            else set()
        )
        mappings = _implementation_rows(path, block)
        designs[design_id] = (path, state, upstream, mappings)
        if state != "Approved":
            continue
        if not upstream:
            errors.append(f"approved design item has no upstream AC: {design_id}")
        spec_match = re.search(
            r"\*\*仕様\*\*\s*(.*?)(?:\n\*\*依存・影響\*\*|\n####|\Z)",
            block,
            re.DOTALL,
        )
        if spec_match is None or _is_placeholder(spec_match.group(1)):
            errors.append(f"approved design item lacks specification: {design_id}")
        complete_mappings = [
            row
            for row in mappings
            if all(not _is_placeholder(row[column]) for column in IMPLEMENTATION_HEADERS)
        ]
        if not complete_mappings:
            errors.append(f"approved design item has no implementation mapping: {design_id}")
        for ac_id in upstream:
            if ac_id not in ac_links:
                errors.append(f"design references unknown upstream AC: {design_id} -> {ac_id}")
            elif ac_states.get(ac_id) != "Approved":
                errors.append(
                    f"approved design references non-Approved AC: "
                    f"{design_id} -> {ac_id}"
                )
            elif design_id not in ac_links[ac_id]:
                errors.append(
                    f"AC/design link is not reciprocal: {ac_id} -> {design_id}"
                )

    for ac_id, related_designs in ac_links.items():
        for design_id in related_designs:
            if design_id not in designs:
                errors.append(f"AC references unknown design ID: {ac_id} -> {design_id}")
            else:
                _, design_state, upstream, _ = designs[design_id]
                if ac_states.get(ac_id) == "Approved" and design_state != "Approved":
                    errors.append(
                        f"approved AC references non-Approved design: "
                        f"{ac_id} -> {design_id}"
                    )
                if ac_id in upstream:
                    continue
                errors.append(
                    f"design/AC link is not reciprocal: {design_id} -> {ac_id}"
                )

    for design_id in sorted(require_implemented):
        item = designs.get(design_id)
        if item is None:
            errors.append(f"required implemented design ID not found: {design_id}")
            continue
        _, state, _, mappings = item
        if state != "Approved":
            errors.append(
                f"required implemented design is not Approved: {design_id} -> {state}"
            )
            continue
        implemented = [row for row in mappings if row["状態"] == "Implemented"]
        if not implemented:
            errors.append(f"design has no Implemented mapping: {design_id}")
            continue
        for row in implemented:
            relative = Path(row["Path"])
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or not (documents.project_root / relative).exists()
            ):
                errors.append(
                    f"implemented mapping path does not exist: "
                    f"{design_id} -> {row['Path']}"
                )
    return errors


def validate_contract(
    project_root_or_index: Path,
    required_resolved: set[str] | None = None,
    require_all_resolved: bool = False,
    require_implemented: set[str] | None = None,
) -> list[str]:
    try:
        documents = load_document_set(project_root_or_index)
    except ValueError as error:
        return [str(error)]
    errors = list(documents.errors)
    errors.extend(
        _validate_hreqs(
            documents.text,
            required_resolved or set(),
            require_all_resolved,
        )
    )
    ac_links, ac_states, acceptance_errors = _validate_acceptance(documents)
    errors.extend(acceptance_errors)
    errors.extend(
        _validate_designs(
            documents,
            ac_links,
            ac_states,
            require_implemented or set(),
        )
    )
    return errors


def main() -> int:
    args = parse_args()
    errors = validate_contract(
        args.project_root,
        required_resolved=set(args.require),
        require_all_resolved=args.require_all_resolved,
        require_implemented=set(args.require_implemented),
    )
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("Design contract validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
