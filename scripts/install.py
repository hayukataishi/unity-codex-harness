#!/usr/bin/env python3
"""Install the Unity Codex harness into an existing Unity project."""

from __future__ import annotations

import argparse
import filecmp
import shutil
from pathlib import Path


REQUIRED_UNITY_PATHS = (
    Path("Assets"),
    Path("Packages"),
    Path("ProjectSettings/ProjectVersion.txt"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy Codex Skills and harness docs into a Unity project."
    )
    parser.add_argument("project_root", help="Path to the target Unity project")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing files whose contents differ",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without writing files",
    )
    parser.add_argument(
        "--skip-agents",
        action="store_true",
        help="Do not install the repository-level AGENTS.md",
    )
    return parser.parse_args()


def validate_unity_project(project_root: Path) -> None:
    missing = [
        relative.as_posix()
        for relative in REQUIRED_UNITY_PATHS
        if not (project_root / relative).exists()
    ]
    if missing:
        raise SystemExit(
            f"Not a Unity project: {project_root}\nMissing: {', '.join(missing)}"
        )


def source_files(repository_root: Path, skip_agents: bool) -> list[Path]:
    roots = [
        repository_root / ".codex" / "skills",
        repository_root / "docs",
    ]
    files = [
        path
        for root in roots
        for path in root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    ]
    if not skip_agents:
        files.append(repository_root / "AGENTS.md")
    return sorted(files)


def install_file(
    source: Path,
    destination: Path,
    *,
    force: bool,
    dry_run: bool,
) -> str:
    if destination.exists():
        if destination.is_file() and filecmp.cmp(source, destination, shallow=False):
            return "unchanged"
        if not force:
            raise FileExistsError(destination)
        action = "replace"
    else:
        action = "create"

    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return action


def main() -> int:
    args = parse_args()
    repository_root = Path(__file__).resolve().parent.parent
    project_root = Path(args.project_root).expanduser().resolve()
    validate_unity_project(project_root)

    files = source_files(repository_root, args.skip_agents)
    conflicts: list[Path] = []
    operations: list[tuple[str, Path]] = []

    if not args.force:
        for source in files:
            relative = source.relative_to(repository_root)
            destination = project_root / relative
            if not destination.exists():
                continue
            if destination.is_file() and filecmp.cmp(
                source, destination, shallow=False
            ):
                continue
            conflicts.append(relative)

    if conflicts:
        rendered = "\n".join(f"  - {path.as_posix()}" for path in conflicts)
        raise SystemExit(
            "Installation stopped because existing files differ:\n"
            f"{rendered}\n"
            "Review them, use --skip-agents where appropriate, or rerun with --force."
        )

    for source in files:
        relative = source.relative_to(repository_root)
        destination = project_root / relative
        action = install_file(
            source,
            destination,
            force=args.force,
            dry_run=args.dry_run,
        )
        operations.append((action, relative))

    prefix = "would " if args.dry_run else ""
    for action, relative in operations:
        if action != "unchanged":
            print(f"{prefix}{action}: {relative.as_posix()}")

    changed = sum(action != "unchanged" for action, _ in operations)
    unchanged = sum(action == "unchanged" for action, _ in operations)
    print(
        f"{'Dry run complete' if args.dry_run else 'Installation complete'}: "
        f"{changed} changed, {unchanged} unchanged"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
