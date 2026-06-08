#!/usr/bin/env python3
"""Validate repository-local Codex Skills and Markdown references."""

from __future__ import annotations

import re
from pathlib import Path


FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
LEGACY_PATTERNS = ("Unityハーネスエンジニアリング/", "[[")
GITHUB_ACTION_RE = re.compile(
    r"^\s*(?:-\s*)?uses:\s*([^\s#]+)",
    re.MULTILINE,
)
PINNED_ACTION_RE = re.compile(r"^[^@]+@[0-9a-f]{40}$")


def frontmatter_value(frontmatter: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", frontmatter, re.MULTILINE)
    return match.group(1).strip().strip("\"'") if match else None


def validate_skills(root: Path) -> list[str]:
    errors: list[str] = []
    skills_root = root / ".codex" / "skills"
    for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        skill_file = skill_dir / "SKILL.md"
        agent_file = skill_dir / "agents" / "openai.yaml"
        if not skill_file.is_file():
            errors.append(f"missing SKILL.md: {skill_dir.relative_to(root)}")
            continue
        if not agent_file.is_file():
            errors.append(f"missing agents/openai.yaml: {skill_dir.relative_to(root)}")

        text = skill_file.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        if not match:
            errors.append(f"invalid frontmatter: {skill_file.relative_to(root)}")
            continue
        frontmatter = match.group(1)
        name = frontmatter_value(frontmatter, "name")
        description = frontmatter_value(frontmatter, "description")
        if name != skill_dir.name:
            errors.append(
                f"skill name mismatch: {skill_file.relative_to(root)} "
                f"({name!r} != {skill_dir.name!r})"
            )
        if not description:
            errors.append(f"missing description: {skill_file.relative_to(root)}")
    return errors


def validate_markdown(root: Path) -> list[str]:
    errors: list[str] = []
    for markdown in sorted(root.rglob("*.md")):
        if ".git" in markdown.parts:
            continue
        text = markdown.read_text(encoding="utf-8")
        for pattern in LEGACY_PATTERNS:
            if pattern in text:
                errors.append(
                    f"legacy reference {pattern!r}: {markdown.relative_to(root)}"
                )

        for target in MARKDOWN_LINK_RE.findall(text):
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            path_part, _, anchor = target.partition("#")
            destination = (markdown.parent / path_part).resolve()
            if not destination.exists():
                errors.append(
                    f"broken link: {markdown.relative_to(root)} -> {target}"
                )
                continue
            if anchor and destination.suffix == ".md":
                destination_text = destination.read_text(encoding="utf-8")
                if f'<a id="{anchor}"></a>' not in destination_text:
                    errors.append(
                        f"missing stable anchor: "
                        f"{markdown.relative_to(root)} -> {target}"
                    )
    return errors


def validate_github_actions(root: Path) -> list[str]:
    errors: list[str] = []
    workflows_root = root / ".github" / "workflows"
    if not workflows_root.is_dir():
        return errors

    for workflow in sorted(
        [
            *workflows_root.glob("*.yml"),
            *workflows_root.glob("*.yaml"),
        ]
    ):
        text = workflow.read_text(encoding="utf-8")
        if "\t" in text:
            errors.append(f"tab in workflow: {workflow.relative_to(root)}")
        for action in GITHUB_ACTION_RE.findall(text):
            if action.startswith("./"):
                continue
            if not PINNED_ACTION_RE.fullmatch(action):
                errors.append(
                    f"unpinned GitHub Action: "
                    f"{workflow.relative_to(root)} -> {action}"
                )
    return errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    errors = (
        validate_skills(root)
        + validate_markdown(root)
        + validate_github_actions(root)
    )
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("Repository validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
