#!/usr/bin/env python3
"""Discover and parse the project-owned Unity game design document set."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


DESIGN_INDEX_PATH = Path("docs/unity_design_sheet.md")
DESIGN_ROOT = Path("docs/game_design")
DESIGN_INDEX_MARKER = "<!-- UNITY_CODEX_GAME_DESIGN_INDEX: PROJECT-OWNED -->"
GLOBAL_ACCEPTANCE_PATH = DESIGN_ROOT / "all/acceptance.md"
STANDARDS_PATH = DESIGN_ROOT / "all/standards.md"
REQUIRED_DOCUMENT_PATHS = (
    DESIGN_INDEX_PATH,
    GLOBAL_ACCEPTANCE_PATH,
    STANDARDS_PATH,
    DESIGN_ROOT / "all/initial_design.md",
    DESIGN_ROOT / "all/game_design.md",
    DESIGN_ROOT / "all/project_design.md",
    DESIGN_ROOT / "all/presentation_design.md",
    DESIGN_ROOT / "all/architecture.md",
    DESIGN_ROOT / "all/cross_cutting.md",
    DESIGN_ROOT / "all/open_questions.md",
    DESIGN_ROOT / "scenes/README.md",
    DESIGN_ROOT / "scenes/_template/acceptance.md",
    DESIGN_ROOT / "scenes/_template/design.md",
    DESIGN_ROOT / "shared/prefabs/README.md",
    DESIGN_ROOT / "shared/scripts/README.md",
    DESIGN_ROOT / "shared/data/README.md",
    DESIGN_ROOT / "shared/ui/README.md",
    DESIGN_ROOT / "shared/audio/README.md",
    DESIGN_ROOT / "shared/assets/README.md",
)
ACCEPTANCE_HEADERS = (
    "AC ID",
    "状態",
    "合格条件",
    "検証種別",
    "検証方法",
    "承認者・日付",
    "関連設計ID",
    "旧AC ID",
)
VALID_AC_STATES = {"Draft", "Approved", "廃止"}
VALID_VERIFICATION_TYPES = {
    "AUTO:STATIC",
    "AUTO:EDIT",
    "AUTO:PLAY",
    "AUTO:ASSET",
    "AUTO:BUILD",
    "MANUAL:EDITOR",
    "MANUAL:PLAY",
}
DESIGN_ID_RE = re.compile(r"\b[A-Z][A-Z0-9]*-\d{3}\b")
GLOBAL_AC_RE = re.compile(r"GAME-AC-\d{3}")
SCENE_AC_RE = re.compile(r"SCENE-[A-Z0-9]+(?:-[A-Z0-9]+)*-AC-\d{3}")
AC_ID_RE = re.compile(
    rf"(?:{GLOBAL_AC_RE.pattern}|{SCENE_AC_RE.pattern})"
)


@dataclass(frozen=True)
class MarkdownTable:
    path: Path
    section: str
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class DesignDocumentSet:
    project_root: Path
    paths: tuple[Path, ...]
    acceptance_paths: tuple[Path, ...]
    design_paths: tuple[Path, ...]
    text: str
    errors: tuple[str, ...]


def normalize_cell(value: str) -> str:
    return value.strip().strip("`").strip()


def split_row(line: str) -> tuple[str, ...]:
    return tuple(
        normalize_cell(cell)
        for cell in line.strip().strip("|").split("|")
    )


def is_separator(line: str) -> bool:
    if not line.lstrip().startswith("|"):
        return False
    cells = split_row(line)
    return bool(cells) and all(
        re.fullmatch(r":?-{3,}:?", cell) is not None for cell in cells
    )


def parse_tables(path: Path, text: str) -> list[MarkdownTable]:
    lines = text.splitlines()
    tables: list[MarkdownTable] = []
    section = ""
    index = 0
    while index < len(lines):
        heading = re.match(r"^#{2,4}\s+(.+?)\s*$", lines[index])
        if heading:
            section = normalize_cell(heading.group(1))
            index += 1
            continue
        if (
            lines[index].lstrip().startswith("|")
            and index + 1 < len(lines)
            and is_separator(lines[index + 1])
        ):
            headers = split_row(lines[index])
            rows: list[tuple[str, ...]] = []
            index += 2
            while index < len(lines) and lines[index].lstrip().startswith("|"):
                row = split_row(lines[index])
                if len(row) < len(headers):
                    row += ("",) * (len(headers) - len(row))
                rows.append(row)
                index += 1
            tables.append(
                MarkdownTable(path, section, headers, tuple(rows))
            )
            continue
        index += 1
    return tables


def resolve_project_root(value: Path) -> Path:
    resolved = value.expanduser().resolve()
    if resolved.is_file():
        if resolved.name == DESIGN_INDEX_PATH.name:
            return resolved.parent.parent
        raise ValueError(f"expected project root or design index: {resolved}")
    return resolved


def _project_documents(project_root: Path) -> tuple[Path, ...]:
    root = project_root / DESIGN_ROOT
    if not root.is_dir():
        return ()
    return tuple(
        sorted(
            (
                path.relative_to(project_root)
                for path in root.rglob("*.md")
                if "_template" not in path.parts
            ),
            key=Path.as_posix,
        )
    )


def load_document_set(value: Path) -> DesignDocumentSet:
    project_root = resolve_project_root(value)
    errors: list[str] = []
    for relative in REQUIRED_DOCUMENT_PATHS:
        if not (project_root / relative).is_file():
            errors.append(f"missing game design document: {relative.as_posix()}")
    scenes_root = project_root / DESIGN_ROOT / "scenes"
    if scenes_root.is_dir():
        for scene_dir in sorted(scenes_root.iterdir()):
            if not scene_dir.is_dir() or scene_dir.name == "_template":
                continue
            if re.fullmatch(
                r"[a-z0-9]+(?:-[a-z0-9]+)*",
                scene_dir.name,
            ) is None:
                errors.append(
                    "invalid scene design directory name: "
                    f"{scene_dir.relative_to(project_root).as_posix()}"
                )
            for filename in ("acceptance.md", "design.md"):
                if not (scene_dir / filename).is_file():
                    errors.append(
                        "missing scene design document: "
                        f"{(scene_dir / filename).relative_to(project_root).as_posix()}"
                    )

    index = project_root / DESIGN_INDEX_PATH
    if index.is_file() and DESIGN_INDEX_MARKER not in index.read_text(
        encoding="utf-8"
    ):
        errors.append(
            "legacy game design sheet requires migration: "
            f"{DESIGN_INDEX_PATH.as_posix()}"
        )

    documents = _project_documents(project_root)
    paths = (DESIGN_INDEX_PATH, *documents)
    acceptance_paths = tuple(
        path
        for path in documents
        if path == GLOBAL_ACCEPTANCE_PATH
        or (
            DESIGN_ROOT / "scenes" in path.parents
            and path.name == "acceptance.md"
        )
    )
    design_paths = tuple(
        path for path in documents if path not in acceptance_paths
    )
    chunks = []
    for relative in paths:
        path = project_root / relative
        if path.is_file():
            chunks.append(
                f"\n<!-- SOURCE: {relative.as_posix()} -->\n"
                + path.read_text(encoding="utf-8")
            )
    return DesignDocumentSet(
        project_root=project_root,
        paths=paths,
        acceptance_paths=acceptance_paths,
        design_paths=design_paths,
        text="\n".join(chunks),
        errors=tuple(errors),
    )


def acceptance_tables(
    documents: DesignDocumentSet,
) -> list[MarkdownTable]:
    tables: list[MarkdownTable] = []
    for relative in documents.acceptance_paths:
        path = documents.project_root / relative
        for table in parse_tables(relative, path.read_text(encoding="utf-8")):
            if set(ACCEPTANCE_HEADERS).issubset(table.headers):
                tables.append(table)
    return tables


def design_item_blocks(
    documents: DesignDocumentSet,
) -> list[tuple[Path, str, str]]:
    pattern = re.compile(
        r"^###\s+`?([A-Z][A-Z0-9]*-\d{3})`?:\s+(.+?)\s*$",
        re.MULTILINE,
    )
    blocks: list[tuple[Path, str, str]] = []
    for relative in documents.design_paths:
        text = (documents.project_root / relative).read_text(encoding="utf-8")
        scan_text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        matches = list(pattern.finditer(scan_text))
        for index, match in enumerate(matches):
            end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(scan_text)
            )
            blocks.append(
                (relative, match.group(1), scan_text[match.end():end])
            )
    return blocks
