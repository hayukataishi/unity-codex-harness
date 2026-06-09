#!/usr/bin/env python3
"""Install the Unity Codex harness into an existing Unity project."""

from __future__ import annotations

import argparse
import filecmp
import shutil
import subprocess
from pathlib import Path
from typing import NamedTuple


REQUIRED_UNITY_PATHS = (
    Path("Assets"),
    Path("Packages"),
    Path("ProjectSettings/ProjectVersion.txt"),
)
GITIGNORE_BEGIN = "# >>> Unity Codex Harness managed Artifacts ignore >>>"
GITIGNORE_RULE = "/Artifacts/"
GITIGNORE_END = "# <<< Unity Codex Harness managed Artifacts ignore <<<"
GITIGNORE_BLOCK = "\n".join(
    (
        GITIGNORE_BEGIN,
        GITIGNORE_RULE,
        GITIGNORE_END,
    )
)
ARTIFACTS_CHECK_PATH = "Artifacts/.unity-codex-harness-ignore-check"


class InstallSource(NamedTuple):
    source: Path
    relative: Path
    preserve_existing: bool


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
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check that Artifacts is ignored without installing files",
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


def source_files(repository_root: Path, skip_agents: bool) -> list[InstallSource]:
    mappings = [
        (repository_root / ".codex" / "skills", Path(".codex/skills")),
        (repository_root / "docs", Path("docs")),
        (repository_root / "templates" / "unity", Path(".")),
    ]
    files: list[InstallSource] = []
    for source_root, destination_root in mappings:
        for path in source_root.rglob("*"):
            if (
                not path.is_file()
                or "__pycache__" in path.parts
                or path.suffix == ".pyc"
            ):
                continue
            files.append(
                InstallSource(
                    source=path,
                    relative=destination_root / path.relative_to(source_root),
                    preserve_existing=(
                        destination_root / path.relative_to(source_root)
                        == Path(
                            "ProjectSettings/"
                            "UnityCodexHarnessAssetValidation.json"
                        )
                    ),
                )
            )
    if not skip_agents:
        files.append(
            InstallSource(
                source=repository_root / "AGENTS.md",
                relative=Path("AGENTS.md"),
                preserve_existing=False,
            )
        )
    files.append(
        InstallSource(
            source=repository_root / "harness.lock.json",
            relative=Path("harness.lock.json"),
            preserve_existing=False,
        )
    )
    return sorted(files, key=lambda item: item.relative.as_posix())


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


def managed_gitignore_text(existing: str) -> str:
    begin_count = existing.count(GITIGNORE_BEGIN)
    end_count = existing.count(GITIGNORE_END)
    if begin_count != end_count or begin_count > 1:
        raise ValueError(
            "Malformed Unity Codex Harness block in .gitignore. "
            "Expected one matching begin/end marker pair."
        )

    if begin_count == 1:
        begin = existing.index(GITIGNORE_BEGIN)
        try:
            end = existing.index(GITIGNORE_END, begin) + len(GITIGNORE_END)
        except ValueError as error:
            raise ValueError(
                "Malformed Unity Codex Harness block in .gitignore. "
                "The end marker must follow the begin marker."
            ) from error
        newline = "\r\n" if "\r\n" in existing else "\n"
        block = GITIGNORE_BLOCK.replace("\n", newline)
        return existing[:begin] + block + existing[end:]

    if not existing:
        return GITIGNORE_BLOCK + "\n"

    newline = "\r\n" if "\r\n" in existing else "\n"
    separator = newline if existing.endswith(("\n", "\r")) else newline * 2
    block = GITIGNORE_BLOCK.replace("\n", newline)
    return existing + separator + block + newline


def read_gitignore(gitignore: Path) -> str:
    if not gitignore.exists():
        return ""
    with gitignore.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def has_managed_gitignore_block(text: str) -> bool:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return GITIGNORE_BLOCK in normalized


def plan_gitignore_update(project_root: Path) -> tuple[str, str]:
    gitignore = project_root / ".gitignore"
    existing = read_gitignore(gitignore)
    updated = managed_gitignore_text(existing)
    if updated == existing:
        return "unchanged", updated
    return ("update" if gitignore.exists() else "create"), updated


def write_gitignore(
    project_root: Path,
    updated: str,
    *,
    dry_run: bool,
) -> None:
    if not dry_run:
        with (project_root / ".gitignore").open(
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:
            handle.write(updated)


def tracked_artifacts(project_root: Path) -> list[str]:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(project_root),
                "ls-files",
                "--",
                "Artifacts",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line]


def git_ignores_artifacts(project_root: Path) -> tuple[bool, str]:
    gitignore = project_root / ".gitignore"
    if not gitignore.is_file():
        return False, ".gitignore does not exist"

    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(project_root),
                "check-ignore",
                "--quiet",
                "--no-index",
                "--",
                ARTIFACTS_CHECK_PATH,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        result = None

    if result is not None and result.returncode == 0:
        tracked = tracked_artifacts(project_root)
        if tracked:
            preview = ", ".join(tracked[:3])
            suffix = "" if len(tracked) <= 3 else ", ..."
            return (
                False,
                "Artifacts contains files already tracked by Git: "
                f"{preview}{suffix}. Remove them from the Git index "
                "before continuing.",
            )
        return True, f"Git ignores {ARTIFACTS_CHECK_PATH}"
    if result is not None and result.returncode not in (1, 128):
        detail = result.stderr.strip() or f"git check-ignore exited {result.returncode}"
        return False, detail

    try:
        existing = read_gitignore(gitignore)
        managed_gitignore_text(existing)
    except ValueError as error:
        return False, str(error)
    if not has_managed_gitignore_block(existing):
        return False, "managed /Artifacts/ rule is missing"
    return True, "Managed /Artifacts/ rule is present"


def check_installation(project_root: Path) -> None:
    ignored, detail = git_ignores_artifacts(project_root)
    if not ignored:
        raise SystemExit(f"Artifacts ignore check: FAIL\n{detail}")
    print(f"Artifacts ignore check: PASS\n{detail}")


def main() -> int:
    args = parse_args()
    repository_root = Path(__file__).resolve().parent.parent
    project_root = Path(args.project_root).expanduser().resolve()
    validate_unity_project(project_root)

    if args.check:
        check_installation(project_root)
        return 0

    files = source_files(repository_root, args.skip_agents)
    conflicts: list[Path] = []
    operations: list[tuple[str, Path]] = []
    try:
        gitignore_action, gitignore_text = plan_gitignore_update(project_root)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    tracked = tracked_artifacts(project_root)
    if tracked:
        preview = "\n".join(f"  - {path}" for path in tracked[:10])
        suffix = "\n  - ..." if len(tracked) > 10 else ""
        raise SystemExit(
            "Installation stopped because Artifacts contains files already "
            f"tracked by Git:\n{preview}{suffix}\n"
            "Remove them from the Git index, then rerun the installer."
        )

    if not args.force:
        for item in files:
            source = item.source
            relative = item.relative
            destination = project_root / relative
            if not destination.exists():
                continue
            if item.preserve_existing:
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

    for item in files:
        source = item.source
        relative = item.relative
        destination = project_root / relative
        if item.preserve_existing and destination.exists() and not args.force:
            operations.append(("unchanged", relative))
            continue
        action = install_file(
            source,
            destination,
            force=args.force,
            dry_run=args.dry_run,
        )
        operations.append((action, relative))

    write_gitignore(
        project_root,
        gitignore_text,
        dry_run=args.dry_run,
    )
    operations.append((gitignore_action, Path(".gitignore")))

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
    if not args.dry_run:
        check_installation(project_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
