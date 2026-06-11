#!/usr/bin/env python3
"""Install the Unity Codex harness into an existing Unity project."""

from __future__ import annotations

import argparse
import difflib
import filecmp
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple


REQUIRED_UNITY_PATHS = (
    Path("Assets"),
    Path("Packages"),
    Path("ProjectSettings/ProjectVersion.txt"),
)
GITIGNORE_BEGIN = "# >>> Unity Codex Harness managed Artifacts ignore >>>"
GITIGNORE_RULE = "/Artifacts/"
GITIGNORE_RULES = (
    GITIGNORE_RULE,
    "/.codex/external/",
    "/.codex/skills/generate2dsprite/",
    "/.codex/skills/generate2dmap/",
)
GITIGNORE_END = "# <<< Unity Codex Harness managed Artifacts ignore <<<"
GITIGNORE_BLOCK = "\n".join(
    (
        GITIGNORE_BEGIN,
        *GITIGNORE_RULES,
        GITIGNORE_END,
    )
)
GITIGNORE_CHECK_PATHS = (
    "Artifacts/.unity-codex-harness-ignore-check",
    ".codex/external/.unity-codex-harness-ignore-check",
    ".codex/skills/generate2dsprite/.unity-codex-harness-ignore-check",
    ".codex/skills/generate2dmap/.unity-codex-harness-ignore-check",
)
LOCAL_ONLY_PATHS = (
    "Artifacts",
    ".codex/external",
    ".codex/skills/generate2dsprite",
    ".codex/skills/generate2dmap",
)
OWNERSHIP_HARNESS = "harness-managed"
OWNERSHIP_PROJECT = "project-owned"
INSTALL_STATE_ROOT = Path(".unity-codex-harness")
INSTALL_MANIFEST_PATH = INSTALL_STATE_ROOT / "install-manifest.json"
INSTALL_MANIFEST_HASH_PATH = INSTALL_STATE_ROOT / "install-manifest.sha256"
BASELINE_ROOT = INSTALL_STATE_ROOT / "baselines"
BACKUP_ROOT = Path("Artifacts/HarnessInstallerBackups")
MIGRATION_ROOT = Path("Artifacts/HarnessInstallerMigrations")
EXCLUSIVE_MANAGED_ROOTS = (
    Path("Assets/UnityCodexHarness"),
    Path(".codex/skills/bootstrap-game-design"),
    Path(".codex/skills/implement-unity-feature"),
    Path(".codex/skills/integrate-2d-assets"),
    Path(".codex/skills/maintain-game-design"),
    Path(".codex/skills/report-unity-work"),
    Path(".codex/skills/review-gameplay"),
    Path(".codex/skills/validate-unity-change"),
    Path("scripts/unity_codex_harness"),
)
PROJECT_OWNED_PATHS = {
    Path("AGENTS.md"),
    Path("docs/mcp_and_skills_list.md"),
    Path("docs/unity_design_sheet.md"),
    Path("harness.lock.json"),
    Path("ProjectSettings/UnityCodexHarnessAssetValidation.json"),
}


class InstallSource(NamedTuple):
    source: Path
    relative: Path
    ownership: str


class ProjectTemplateChange(NamedTuple):
    item: InstallSource
    baseline: Path
    destination: Path
    base_kind: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy Codex Skills and harness docs into a Unity project."
    )
    parser.add_argument("project_root", help="Path to the target Unity project")
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Replace all differing harness-managed files after backing them up; "
            "project-owned files are never replaced"
        ),
    )
    parser.add_argument(
        "--force-file",
        action="append",
        default=[],
        metavar="RELATIVE_PATH",
        help=(
            "Replace one differing harness-managed file after backup. "
            "May be repeated."
        ),
    )
    parser.add_argument(
        "--prepare-migration",
        action="store_true",
        help=(
            "Create three-way migration bundles for changed project-owned "
            "templates without modifying project-owned files"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without writing files",
    )
    parser.add_argument(
        "--skip-agents",
        action="store_true",
        help=(
            "Do not install the repository-level AGENTS.md. "
            "Project custom agents under .codex/agents are still installed."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check that harness local-only paths are ignored",
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
        (repository_root / ".codex" / "agents", Path(".codex/agents")),
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
                    ownership=ownership_for(
                        destination_root / path.relative_to(source_root)
                    ),
                )
            )
    if not skip_agents:
        files.append(
            InstallSource(
                source=repository_root / "AGENTS.md",
                relative=Path("AGENTS.md"),
                ownership=OWNERSHIP_PROJECT,
            )
        )
    files.append(
        InstallSource(
            source=repository_root / "harness.lock.json",
            relative=Path("harness.lock.json"),
            ownership=OWNERSHIP_PROJECT,
        )
    )
    files.append(
        InstallSource(
            source=(
                repository_root
                / "scripts"
                / "check_external_dependencies.py"
            ),
            relative=Path(
                "scripts/unity_codex_harness/check_external_dependencies.py"
            ),
            ownership=OWNERSHIP_HARNESS,
        )
    )
    files.append(
        InstallSource(
            source=repository_root / "scripts" / "validate_design_contract.py",
            relative=Path(
                "scripts/unity_codex_harness/validate_design_contract.py"
            ),
            ownership=OWNERSHIP_HARNESS,
        )
    )
    files.append(
        InstallSource(
            source=repository_root / "scripts" / "validate_design_readiness.py",
            relative=Path(
                "scripts/unity_codex_harness/validate_design_readiness.py"
            ),
            ownership=OWNERSHIP_HARNESS,
        )
    )
    files.append(
        InstallSource(
            source=repository_root / "scripts" / "verify_harness_integrity.py",
            relative=Path(
                "scripts/unity_codex_harness/verify_harness_integrity.py"
            ),
            ownership=OWNERSHIP_HARNESS,
        )
    )
    return sorted(files, key=lambda item: item.relative.as_posix())


def ownership_for(relative: Path) -> str:
    if relative in PROJECT_OWNED_PATHS:
        return OWNERSHIP_PROJECT
    return OWNERSHIP_HARNESS


def normalized_relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise SystemExit(
            f"--force-file must be a project-relative path: {value}"
        )
    normalized = Path(*[part for part in path.parts if part not in ("", ".")])
    if not normalized.parts:
        raise SystemExit(
            f"--force-file must be a project-relative path: {value}"
        )
    return normalized


def selected_force_paths(
    files: list[InstallSource],
    values: list[str],
) -> set[Path]:
    requested = {normalized_relative_path(value) for value in values}
    by_path = {item.relative: item for item in files}
    unknown = sorted(path for path in requested if path not in by_path)
    if unknown:
        rendered = ", ".join(path.as_posix() for path in unknown)
        raise SystemExit(f"Unknown --force-file path: {rendered}")
    project_owned = sorted(
        path
        for path in requested
        if by_path[path].ownership == OWNERSHIP_PROJECT
    )
    if project_owned:
        rendered = ", ".join(path.as_posix() for path in project_owned)
        raise SystemExit(
            "Project-owned files cannot be replaced by the installer: "
            f"{rendered}"
        )
    return requested


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def write_text_if_changed(
    path: Path,
    text: str,
    *,
    dry_run: bool,
) -> str:
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return "unchanged"
    action = "update" if path.exists() else "create"
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return action


def copy_if_changed(
    source: Path,
    destination: Path,
    *,
    dry_run: bool,
) -> str:
    if (
        destination.is_file()
        and filecmp.cmp(source, destination, shallow=False)
    ):
        return "unchanged"
    action = "update" if destination.exists() else "create"
    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return action


def next_operation_id(project_root: Path) -> str:
    base = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = base
    suffix = 2
    while (
        (project_root / BACKUP_ROOT / candidate).exists()
        or (project_root / MIGRATION_ROOT / candidate).exists()
    ):
        candidate = f"{base}-{suffix:02d}"
        suffix += 1
    return candidate


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


def backup_replacements(
    project_root: Path,
    replacements: list[InstallSource],
    operation_id: str,
    *,
    dry_run: bool,
) -> Path | None:
    if not replacements:
        return None

    backup_root = project_root / BACKUP_ROOT / operation_id
    entries = []
    for item in replacements:
        destination = project_root / item.relative
        backup = backup_root / "files" / item.relative
        entries.append(
            {
                "path": item.relative.as_posix(),
                "originalSha256": sha256_file(destination),
                "replacementSha256": sha256_file(item.source),
                "backupPath": (
                    Path("files") / item.relative
                ).as_posix(),
            }
        )
        if not dry_run:
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup)

    manifest = {
        "schemaVersion": 1,
        "operationId": operation_id,
        "files": entries,
    }
    if not dry_run:
        (backup_root / "BackupManifest.json").write_text(
            json_text(manifest),
            encoding="utf-8",
        )
    return backup_root


def unified_diff_text(
    before: Path,
    after: Path,
    before_label: str,
    after_label: str,
) -> str:
    before_lines = before.read_text(encoding="utf-8").splitlines(keepends=True)
    after_lines = after.read_text(encoding="utf-8").splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=before_label,
            tofile=after_label,
        )
    )


def create_migration_bundle(
    project_root: Path,
    changes: list[ProjectTemplateChange],
    operation_id: str,
    *,
    dry_run: bool,
) -> Path | None:
    if not changes:
        return None

    migration_root = project_root / MIGRATION_ROOT / operation_id
    entries = []
    for change in changes:
        relative = change.item.relative
        base_target = migration_root / "base" / relative
        local_target = migration_root / "local" / relative
        incoming_target = migration_root / "incoming" / relative
        local_diff = migration_root / "diff" / Path(
            relative.as_posix() + ".local.patch"
        )
        incoming_diff = migration_root / "diff" / Path(
            relative.as_posix() + ".incoming.patch"
        )
        entries.append(
            {
                "path": relative.as_posix(),
                "baseSha256": sha256_file(change.baseline),
                "localSha256": sha256_file(change.destination),
                "incomingSha256": sha256_file(change.item.source),
                "baseKind": change.base_kind,
                "basePath": (Path("base") / relative).as_posix(),
                "localPath": (Path("local") / relative).as_posix(),
                "incomingPath": (Path("incoming") / relative).as_posix(),
                "localDiffPath": (
                    Path("diff") / Path(relative.as_posix() + ".local.patch")
                ).as_posix(),
                "incomingDiffPath": (
                    Path("diff")
                    / Path(relative.as_posix() + ".incoming.patch")
                ).as_posix(),
            }
        )
        if not dry_run:
            for source, destination in (
                (change.baseline, base_target),
                (change.destination, local_target),
                (change.item.source, incoming_target),
            ):
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            local_diff.parent.mkdir(parents=True, exist_ok=True)
            local_diff.write_text(
                unified_diff_text(
                    change.baseline,
                    change.destination,
                    f"base/{relative.as_posix()}",
                    f"local/{relative.as_posix()}",
                ),
                encoding="utf-8",
            )
            incoming_diff.write_text(
                unified_diff_text(
                    change.baseline,
                    change.item.source,
                    f"base/{relative.as_posix()}",
                    f"incoming/{relative.as_posix()}",
                ),
                encoding="utf-8",
            )

    manifest = {
        "schemaVersion": 1,
        "operationId": operation_id,
        "instruction": (
            "Review base, local, incoming, and both diffs. Apply only the "
            "approved changes to the project-owned local file."
        ),
        "files": entries,
    }
    if not dry_run:
        (migration_root / "MigrationManifest.json").write_text(
            json_text(manifest),
            encoding="utf-8",
        )
    return migration_root


def plan_project_templates(
    project_root: Path,
    files: list[InstallSource],
    *,
    prepare_migration: bool,
) -> tuple[
    list[InstallSource],
    list[ProjectTemplateChange],
    list[Path],
]:
    baseline_updates: list[InstallSource] = []
    migration_changes: list[ProjectTemplateChange] = []
    update_notices: list[Path] = []
    for item in files:
        if item.ownership != OWNERSHIP_PROJECT:
            continue
        baseline = project_root / BASELINE_ROOT / item.relative
        destination = project_root / item.relative
        if not baseline.is_file():
            if not destination.is_file() or filecmp.cmp(
                item.source,
                destination,
                shallow=False,
            ):
                baseline_updates.append(item)
                continue
            update_notices.append(item.relative)
            if prepare_migration:
                migration_changes.append(
                    ProjectTemplateChange(
                        item=item,
                        baseline=destination,
                        destination=destination,
                        base_kind="legacy-local-snapshot",
                    )
                )
                baseline_updates.append(item)
            continue
        if filecmp.cmp(item.source, baseline, shallow=False):
            continue
        if destination.is_file() and filecmp.cmp(
            item.source,
            destination,
            shallow=False,
        ):
            baseline_updates.append(item)
            continue
        update_notices.append(item.relative)
        if prepare_migration and destination.is_file():
            migration_changes.append(
                ProjectTemplateChange(
                    item=item,
                    baseline=baseline,
                    destination=destination,
                    base_kind="recorded-template",
                )
            )
            baseline_updates.append(item)
    return baseline_updates, migration_changes, update_notices


def harness_release(repository_root: Path) -> tuple[str, str]:
    lock = json.loads(
        (repository_root / "harness.lock.json").read_text(encoding="utf-8")
    )
    harness = lock.get("harness", {})
    return str(harness.get("release", "UNKNOWN")), str(
        lock.get("updatedAt", "UNKNOWN")
    )


def install_manifest(
    repository_root: Path,
    project_root: Path,
    files: list[InstallSource],
) -> dict[str, object]:
    release, lock_updated_at = harness_release(repository_root)
    entries = []
    for item in files:
        entry = {
            "path": item.relative.as_posix(),
            "ownership": item.ownership,
            "sourceSha256": sha256_file(item.source),
        }
        if item.ownership == OWNERSHIP_PROJECT:
            baseline = project_root / BASELINE_ROOT / item.relative
            if baseline.is_file():
                entry["baselineSha256"] = sha256_file(baseline)
        entries.append(entry)
    return {
        "schemaVersion": 2,
        "harness": {
            "release": release,
            "lockUpdatedAt": lock_updated_at,
        },
        "exclusiveManagedRoots": [
            path.as_posix() for path in EXCLUSIVE_MANAGED_ROOTS
        ],
        "files": entries,
    }


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


def tracked_local_only_paths(project_root: Path) -> list[str]:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(project_root),
                "ls-files",
                "--",
                *LOCAL_ONLY_PATHS,
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


def tracked_artifacts(project_root: Path) -> list[str]:
    return [
        path
        for path in tracked_local_only_paths(project_root)
        if path == "Artifacts" or path.startswith("Artifacts/")
    ]


def git_ignores_local_only_paths(project_root: Path) -> tuple[bool, str]:
    gitignore = project_root / ".gitignore"
    if not gitignore.is_file():
        return False, ".gitignore does not exist"

    tracked = tracked_local_only_paths(project_root)
    if tracked:
        preview = ", ".join(tracked[:3])
        suffix = "" if len(tracked) <= 3 else ", ..."
        return (
            False,
            "Harness local-only paths contain files already tracked by Git: "
            f"{preview}{suffix}. Remove them from the Git index before continuing.",
        )

    git_results: list[tuple[str, subprocess.CompletedProcess[str]]] = []
    try:
        for check_path in GITIGNORE_CHECK_PATHS:
            git_results.append(
                (
                    check_path,
                    subprocess.run(
                        [
                            "git",
                            "-C",
                            str(project_root),
                            "check-ignore",
                            "--quiet",
                            "--no-index",
                            "--",
                            check_path,
                        ],
                        check=False,
                        capture_output=True,
                        text=True,
                    ),
                )
            )
    except FileNotFoundError:
        git_results = []

    if git_results and all(
        result.returncode == 0 for _, result in git_results
    ):
        return True, "Git ignores all harness local-only paths"
    for check_path, result in git_results:
        if result.returncode not in (0, 1, 128):
            detail = (
                result.stderr.strip()
                or f"git check-ignore exited {result.returncode}"
            )
            return False, detail
        if result.returncode == 1:
            return False, f"Git does not ignore {check_path}"

    try:
        existing = read_gitignore(gitignore)
        managed_gitignore_text(existing)
    except ValueError as error:
        return False, str(error)
    if not has_managed_gitignore_block(existing):
        return False, "managed harness ignore rules are missing"
    return True, "Managed harness ignore rules are present"


def git_ignores_artifacts(project_root: Path) -> tuple[bool, str]:
    return git_ignores_local_only_paths(project_root)


def verify_installed_harness(
    repository_root: Path,
    project_root: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(repository_root / "scripts" / "verify_harness_integrity.py"),
            "--project-root",
            str(project_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stdout.strip() or result.stderr.strip()
        raise SystemExit(f"Harness integrity verification: FAIL\n{detail}")
    print(result.stdout.strip())


def check_installation(repository_root: Path, project_root: Path) -> None:
    ignored, detail = git_ignores_local_only_paths(project_root)
    if not ignored:
        raise SystemExit(f"Harness local-path ignore check: FAIL\n{detail}")
    print(f"Harness local-path ignore check: PASS\n{detail}")
    verify_installed_harness(repository_root, project_root)


def main() -> int:
    args = parse_args()
    repository_root = Path(__file__).resolve().parent.parent
    project_root = Path(args.project_root).expanduser().resolve()
    validate_unity_project(project_root)

    if args.check:
        check_installation(repository_root, project_root)
        return 0

    files = source_files(repository_root, args.skip_agents)
    force_paths = selected_force_paths(files, args.force_file)
    conflicts: list[Path] = []
    operations: list[tuple[str, Path]] = []
    invalid_destinations = [
        item.relative
        for item in files
        if (project_root / item.relative).exists()
        and not (project_root / item.relative).is_file()
    ]
    if invalid_destinations:
        rendered = "\n".join(
            f"  - {path.as_posix()}" for path in invalid_destinations
        )
        raise SystemExit(
            "Installation stopped because file destinations are not files:\n"
            f"{rendered}"
        )
    try:
        gitignore_action, gitignore_text = plan_gitignore_update(project_root)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    tracked = tracked_local_only_paths(project_root)
    if tracked:
        preview = "\n".join(f"  - {path}" for path in tracked[:10])
        suffix = "\n  - ..." if len(tracked) > 10 else ""
        raise SystemExit(
            "Installation stopped because harness local-only paths contain "
            "files already "
            f"tracked by Git:\n{preview}{suffix}\n"
            "Remove them from the Git index, then rerun the installer."
        )

    replacements: list[InstallSource] = []
    for item in files:
        destination = project_root / item.relative
        if not destination.exists():
            continue
        if item.ownership == OWNERSHIP_PROJECT:
            continue
        if destination.is_file() and filecmp.cmp(
            item.source,
            destination,
            shallow=False,
        ):
            continue
        if args.force or item.relative in force_paths:
            replacements.append(item)
        else:
            conflicts.append(item.relative)

    if conflicts:
        rendered = "\n".join(f"  - {path.as_posix()}" for path in conflicts)
        raise SystemExit(
            "Installation stopped because harness-managed files differ:\n"
            f"{rendered}\n"
            "Review them, then use --force-file <relative-path> for each "
            "approved replacement or --force for all listed "
            "harness-managed files."
        )

    baseline_updates, migration_changes, update_notices = (
        plan_project_templates(
            project_root,
            files,
            prepare_migration=args.prepare_migration,
        )
    )
    operation_id = (
        next_operation_id(project_root)
        if replacements or migration_changes
        else ""
    )
    backup_root = backup_replacements(
        project_root,
        replacements,
        operation_id,
        dry_run=args.dry_run,
    )
    if backup_root is not None:
        operations.append(
            (
                "backup",
                backup_root.relative_to(project_root),
            )
        )
    migration_root = create_migration_bundle(
        project_root,
        migration_changes,
        operation_id,
        dry_run=args.dry_run,
    )
    if migration_root is not None:
        operations.append(
            (
                "migration",
                migration_root.relative_to(project_root),
            )
        )

    for item in files:
        source = item.source
        relative = item.relative
        destination = project_root / relative
        if item.ownership == OWNERSHIP_PROJECT and destination.exists():
            operations.append(("preserve", relative))
            continue
        action = install_file(
            source,
            destination,
            force=(args.force or relative in force_paths),
            dry_run=args.dry_run,
        )
        operations.append((action, relative))

    for item in baseline_updates:
        baseline = project_root / BASELINE_ROOT / item.relative
        action = copy_if_changed(
            item.source,
            baseline,
            dry_run=args.dry_run,
        )
        operations.append(
            (
                f"baseline-{action}",
                BASELINE_ROOT / item.relative,
            )
        )

    write_gitignore(
        project_root,
        gitignore_text,
        dry_run=args.dry_run,
    )
    operations.append((gitignore_action, Path(".gitignore")))

    manifest = install_manifest(repository_root, project_root, files)
    manifest_text = json_text(manifest)
    manifest_action = write_text_if_changed(
        project_root / INSTALL_MANIFEST_PATH,
        manifest_text,
        dry_run=args.dry_run,
    )
    operations.append((f"manifest-{manifest_action}", INSTALL_MANIFEST_PATH))
    manifest_hash = hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()
    manifest_hash_text = (
        f"{manifest_hash}  {INSTALL_MANIFEST_PATH.name}\n"
    )
    manifest_hash_action = write_text_if_changed(
        project_root / INSTALL_MANIFEST_HASH_PATH,
        manifest_hash_text,
        dry_run=args.dry_run,
    )
    operations.append(
        (
            f"manifest-hash-{manifest_hash_action}",
            INSTALL_MANIFEST_HASH_PATH,
        )
    )

    prefix = "would " if args.dry_run else ""
    unchanged_actions = {
        "unchanged",
        "preserve",
        "baseline-unchanged",
        "manifest-unchanged",
        "manifest-hash-unchanged",
    }
    for action, relative in operations:
        if action not in unchanged_actions:
            print(f"{prefix}{action}: {relative.as_posix()}")
    for relative in update_notices:
        if args.prepare_migration:
            print(
                f"{prefix}review migration for project-owned file: "
                f"{relative.as_posix()}"
            )
        else:
            print(
                "project-owned template update available: "
                f"{relative.as_posix()} "
                "(rerun with --prepare-migration)"
            )

    changed = sum(action not in unchanged_actions for action, _ in operations)
    unchanged = sum(action in unchanged_actions for action, _ in operations)
    print(
        f"{'Dry run complete' if args.dry_run else 'Installation complete'}: "
        f"{changed} changed, {unchanged} unchanged"
    )
    if not args.dry_run:
        check_installation(repository_root, project_root)
        print(
            "Verify harness-managed files before Codex work with:\n"
            "  python3 scripts/unity_codex_harness/"
            "verify_harness_integrity.py --project-root ."
        )
        print(
            "External dependencies are not bundled. Check them with:\n"
            "  python3 scripts/unity_codex_harness/"
            "check_external_dependencies.py --project-root ."
        )
        print(
            "Validate inherited HREQ entries with:\n"
            "  python3 scripts/unity_codex_harness/"
            "validate_design_contract.py --project-root ."
        )
        print(
            "Validate milestone design readiness with:\n"
            "  python3 scripts/unity_codex_harness/"
            "validate_design_readiness.py --project-root . "
            "--milestone Prototype"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
