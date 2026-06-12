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
AGENTS_PATH = Path("AGENTS.md")
AGENTS_CONTRACT_PATH = Path("docs/unity_harness_agent_contract.md")
AGENTS_CONTRACT_MARKER = (
    "<!-- UNITY_CODEX_HARNESS_AGENT_CONTRACT: REQUIRED -->"
)
HARNESS_LOCK_PATH = Path("harness.lock.json")
HARNESS_OVERRIDES_PATH = Path("harness.overrides.json")
HARNESS_RELEASE_PATH = Path("harness.release.json")
PROJECT_DESIGN_ROOT = Path("docs/game_design")
DESIGN_INDEX_PATH = Path("docs/unity_design_sheet.md")
DESIGN_INDEX_MARKER = "<!-- UNITY_CODEX_GAME_DESIGN_INDEX: PROJECT-OWNED -->"
DISTRIBUTED_DOC_PATHS = (
    Path("docs/mcp_and_skills_list.md"),
    Path("docs/unity_design_sheet.md"),
    Path("docs/unity_harness_agent_contract.md"),
    Path("docs/unity_harness_capabilities.md"),
    Path("docs/unity_harness_engineering.md"),
    Path("docs/unity_harness_release.md"),
    Path("docs/unity_harness_requirements.md"),
)
SOURCE_ONLY_DOC_PATHS = (
    Path("docs/unity_harness_evaluation_2026-06-08.md"),
)
RETIRED_MANAGED_PATHS = SOURCE_ONLY_DOC_PATHS
HARNESS_SKILL_NAMES = (
    "bootstrap-game-design",
    "implement-unity-feature",
    "integrate-2d-assets",
    "maintain-game-design",
    "report-unity-work",
    "review-gameplay",
    "validate-unity-change",
)
LEGACY_SKILLS_ROOT = Path(".codex/skills")
RETIRED_MANAGED_ROOTS = tuple(
    LEGACY_SKILLS_ROOT / name for name in HARNESS_SKILL_NAMES
)
LEGACY_EXTERNAL_SKILL_ROOTS = (
    LEGACY_SKILLS_ROOT / "generate2dsprite",
    LEGACY_SKILLS_ROOT / "generate2dmap",
)
GITIGNORE_BEGIN = "# >>> Unity Codex Harness managed Artifacts ignore >>>"
GITIGNORE_RULE = "/Artifacts/"
GITIGNORE_RULES = (
    GITIGNORE_RULE,
    "/.codex/external/",
    "/.agents/skills/generate2dsprite/",
    "/.agents/skills/generate2dmap/",
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
    ".agents/skills/generate2dsprite/.unity-codex-harness-ignore-check",
    ".agents/skills/generate2dmap/.unity-codex-harness-ignore-check",
)
LOCAL_ONLY_PATHS = (
    "Artifacts",
    ".codex/external",
    ".agents/skills/generate2dsprite",
    ".agents/skills/generate2dmap",
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
    *(Path(".agents/skills") / name for name in HARNESS_SKILL_NAMES),
    Path("scripts/unity_codex_harness"),
)
PROJECT_OWNED_PATHS = {
    Path("AGENTS.md"),
    Path("docs/mcp_and_skills_list.md"),
    Path("docs/unity_design_sheet.md"),
    HARNESS_OVERRIDES_PATH,
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


class RetiredManagedFile(NamedTuple):
    relative: Path
    destination: Path
    source_hash: str


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
        help="Check local-only paths, managed integrity, and the AGENTS contract",
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


def validate_no_legacy_external_skills(project_root: Path) -> None:
    existing = [
        root
        for root in LEGACY_EXTERNAL_SKILL_ROOTS
        if (
            (project_root / root).exists()
            or (project_root / root).is_symlink()
        )
    ]
    if not existing:
        return
    rendered = "\n".join(f"  - {path.as_posix()}" for path in existing)
    raise SystemExit(
        "Installation stopped before writing because project-owned external "
        "Skills still use the legacy Codex path:\n"
        f"{rendered}\n"
        "Review the third-party contents, move the approved Skills to "
        ".agents/skills, remove the legacy copies, then rerun."
    )


def source_files(repository_root: Path, skip_agents: bool) -> list[InstallSource]:
    mappings = [
        (repository_root / ".codex" / "agents", Path(".codex/agents")),
        (repository_root / ".agents" / "skills", Path(".agents/skills")),
        (repository_root / PROJECT_DESIGN_ROOT, PROJECT_DESIGN_ROOT),
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
    for relative in DISTRIBUTED_DOC_PATHS:
        files.append(
            InstallSource(
                source=repository_root / relative,
                relative=relative,
                ownership=ownership_for(relative),
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
            source=repository_root / "scripts" / "design_document_set.py",
            relative=Path(
                "scripts/unity_codex_harness/design_document_set.py"
            ),
            ownership=OWNERSHIP_HARNESS,
        )
    )
    files.append(
        InstallSource(
            source=repository_root / "harness.lock.json",
            relative=HARNESS_LOCK_PATH,
            ownership=OWNERSHIP_HARNESS,
        )
    )
    files.append(
        InstallSource(
            source=repository_root / "harness.overrides.json",
            relative=HARNESS_OVERRIDES_PATH,
            ownership=OWNERSHIP_PROJECT,
        )
    )
    files.append(
        InstallSource(
            source=repository_root / HARNESS_RELEASE_PATH,
            relative=HARNESS_RELEASE_PATH,
            ownership=OWNERSHIP_HARNESS,
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
    if (
        relative in PROJECT_OWNED_PATHS
        or relative == PROJECT_DESIGN_ROOT
        or PROJECT_DESIGN_ROOT in relative.parents
    ):
        return OWNERSHIP_PROJECT
    return OWNERSHIP_HARNESS


def agents_contract_status(project_root: Path) -> tuple[bool, str]:
    agents_path = project_root / AGENTS_PATH
    if not agents_path.is_file():
        return False, "AGENTS.md does not exist"
    text = agents_path.read_text(encoding="utf-8")
    missing = []
    if AGENTS_CONTRACT_MARKER not in text:
        missing.append(AGENTS_CONTRACT_MARKER)
    if AGENTS_CONTRACT_PATH.as_posix() not in text:
        missing.append(AGENTS_CONTRACT_PATH.as_posix())
    if missing:
        return (
            False,
            "AGENTS.md is missing the Unity Codex Harness contract reference: "
            + ", ".join(missing),
        )
    return True, "AGENTS.md references the harness-managed agent contract"


def prepare_agents_contract_migration(
    project_root: Path,
    agents_source: InstallSource,
    *,
    dry_run: bool,
) -> Path:
    destination = project_root / AGENTS_PATH
    baseline = project_root / BASELINE_ROOT / AGENTS_PATH
    if baseline.is_file():
        base = baseline
        base_kind = "recorded-template"
    else:
        base = destination
        base_kind = "legacy-local-snapshot"
    operation_id = next_operation_id(project_root)
    migration_root = create_migration_bundle(
        project_root,
        [
            ProjectTemplateChange(
                item=agents_source,
                baseline=base,
                destination=destination,
                base_kind=base_kind,
            )
        ],
        operation_id,
        dry_run=dry_run,
    )
    assert migration_root is not None
    copy_if_changed(
        agents_source.source,
        baseline,
        dry_run=dry_run,
    )
    return migration_root


def design_index_status(project_root: Path) -> tuple[bool, str]:
    index = project_root / DESIGN_INDEX_PATH
    if not index.exists():
        return True, "game design index does not exist yet"
    if not index.is_file():
        return False, f"{DESIGN_INDEX_PATH.as_posix()} is not a file"
    if DESIGN_INDEX_MARKER not in index.read_text(encoding="utf-8"):
        return False, "legacy single-file game design sheet detected"
    return True, "game design document-set index is active"


def prepare_design_document_migration(
    project_root: Path,
    index_source: InstallSource,
    design_sources: list[InstallSource],
    *,
    dry_run: bool,
) -> Path:
    destination = project_root / DESIGN_INDEX_PATH
    baseline = project_root / BASELINE_ROOT / DESIGN_INDEX_PATH
    if baseline.is_file():
        base = baseline
        base_kind = "recorded-template"
    else:
        base = destination
        base_kind = "legacy-local-snapshot"
    operation_id = next_operation_id(project_root)
    migration_root = create_migration_bundle(
        project_root,
        [
            ProjectTemplateChange(
                item=index_source,
                baseline=base,
                destination=destination,
                base_kind=base_kind,
            )
        ],
        operation_id,
        dry_run=dry_run,
        instruction=(
            "Review the legacy design sheet, then move game-wide acceptance "
            "criteria into docs/game_design/all/acceptance.md and scene-only "
            "criteria into each scenes/<scene-key>/acceptance.md. Move design "
            "decisions into the matching all, scene, or shared design file. "
            "Assign new GAME-AC-### or SCENE-<KEY>-AC-### IDs, preserve the "
            "old design-derived AC ID in 旧AC ID, and make every design item "
            "reference its upstream AC. Replace the local index only after "
            "the split document set has been reviewed."
        ),
        manifest_extra={
            "projectDocumentStructure": {
                "root": PROJECT_DESIGN_ROOT.as_posix(),
                "incomingTemplates": [
                    item.relative.as_posix() for item in design_sources
                ],
                "traceability": (
                    "acceptance criterion -> design item -> "
                    "Unity implementation mapping"
                ),
            }
        },
    )
    assert migration_root is not None
    if not dry_run:
        for item in design_sources:
            incoming = migration_root / "incoming" / item.relative
            incoming.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item.source, incoming)
    copy_if_changed(
        index_source.source,
        baseline,
        dry_run=dry_run,
    )
    return migration_root


def prepare_lock_ownership_migration(
    project_root: Path,
    lock_source: InstallSource,
    overrides_source: InstallSource,
    *,
    dry_run: bool,
) -> Path:
    destination = project_root / HARNESS_LOCK_PATH
    baseline = project_root / BASELINE_ROOT / HARNESS_LOCK_PATH
    if baseline.is_file():
        base = baseline
        base_kind = "recorded-template"
    else:
        base = lock_source.source
        base_kind = "current-harness-source"
    operation_id = next_operation_id(project_root)
    migration_root = create_migration_bundle(
        project_root,
        [
            ProjectTemplateChange(
                item=lock_source,
                baseline=base,
                destination=destination,
                base_kind=base_kind,
            )
        ],
        operation_id,
        dry_run=dry_run,
        instruction=(
            "Review the harness.lock.json base, local, incoming, and diffs. "
            "Move only approved game-specific external dependency changes "
            "into override-template/harness.overrides.json using reason, "
            "approvedBy, approvedAt, and values. Place the reviewed override "
            "at the project root, then rerun the installer with "
            "--force-file harness.lock.json."
        ),
        manifest_extra={
            "ownershipTransition": {
                "from": "project-owned",
                "to": "harness-managed",
                "overridePath": HARNESS_OVERRIDES_PATH.as_posix(),
                "overrideTemplatePath": (
                    Path("override-template") / HARNESS_OVERRIDES_PATH
                ).as_posix(),
            }
        },
    )
    assert migration_root is not None
    if not dry_run:
        override_template = (
            migration_root / "override-template" / HARNESS_OVERRIDES_PATH
        )
        override_template.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(overrides_source.source, override_template)
    copy_if_changed(
        overrides_source.source,
        project_root / BASELINE_ROOT / HARNESS_OVERRIDES_PATH,
        dry_run=dry_run,
    )
    return migration_root


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


def load_previous_install_manifest(
    project_root: Path,
) -> dict[str, object] | None:
    manifest_path = project_root / INSTALL_MANIFEST_PATH
    sidecar_path = project_root / INSTALL_MANIFEST_HASH_PATH
    if not manifest_path.exists() and not sidecar_path.exists():
        return None
    if not manifest_path.is_file() or not sidecar_path.is_file():
        raise SystemExit(
            "Installation stopped because the previous install manifest or "
            "its SHA-256 sidecar is missing. Restore both files before "
            "retiring previously distributed harness files."
        )
    sidecar_parts = sidecar_path.read_text(encoding="utf-8").strip().split()
    if (
        len(sidecar_parts) != 2
        or sidecar_parts[1] != INSTALL_MANIFEST_PATH.name
    ):
        raise SystemExit(
            "Installation stopped because the previous install manifest "
            "SHA-256 sidecar is invalid."
        )
    expected_hash = sidecar_parts[0]
    if sha256_file(manifest_path) != expected_hash:
        raise SystemExit(
            "Installation stopped because the previous install manifest "
            "SHA-256 does not match its sidecar."
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(
            f"Installation stopped because the previous install manifest "
            f"is invalid JSON: {error}"
        ) from error
    if not isinstance(manifest, dict):
        raise SystemExit(
            "Installation stopped because the previous install manifest "
            "root is not an object."
        )
    return manifest


def plan_retired_managed_files(
    project_root: Path,
) -> list[RetiredManagedFile]:
    fixed_existing_paths = [
        relative
        for relative in RETIRED_MANAGED_PATHS
        if (
            (project_root / relative).exists()
            or (project_root / relative).is_symlink()
        )
    ]
    legacy_existing_paths: list[Path] = []
    for root in RETIRED_MANAGED_ROOTS:
        destination_root = project_root / root
        if destination_root.is_symlink():
            legacy_existing_paths.append(root)
            continue
        if not destination_root.exists():
            continue
        legacy_existing_paths.extend(
            path.relative_to(project_root)
            for path in destination_root.rglob("*")
            if path.is_file() or path.is_symlink()
        )
    if not fixed_existing_paths and not legacy_existing_paths:
        return []

    manifest = load_previous_install_manifest(project_root)
    if manifest is None:
        if legacy_existing_paths:
            rendered = "\n".join(
                f"  - {path.as_posix()}"
                for path in sorted(legacy_existing_paths, key=Path.as_posix)
            )
            raise SystemExit(
                "Installation stopped before writing because legacy harness "
                "Skill files exist without a verified install manifest:\n"
                f"{rendered}\n"
                "Preserve or remove the legacy files manually, then rerun."
            )
        return []
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise SystemExit(
            "Installation stopped because the previous install manifest "
            "files value is not an array."
        )
    by_path: dict[str, dict[str, object]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        path_value = entry.get("path")
        if not isinstance(path_value, str):
            continue
        relative = Path(path_value)
        if (
            relative.is_absolute()
            or not relative.parts
            or ".." in relative.parts
        ):
            continue
        by_path[path_value] = entry
    existing_paths = sorted(
        set(fixed_existing_paths + legacy_existing_paths),
        key=Path.as_posix,
    )
    retirements: list[RetiredManagedFile] = []
    conflicts: list[str] = []
    for relative in existing_paths:
        entry = by_path.get(relative.as_posix())
        if not isinstance(entry, dict):
            if (
                relative == LEGACY_SKILLS_ROOT
                or LEGACY_SKILLS_ROOT in relative.parents
            ):
                conflicts.append(
                    f"{relative.as_posix()} is not recorded in the previous "
                    "install manifest"
                )
            continue
        if entry.get("ownership") != OWNERSHIP_HARNESS:
            if (
                relative == LEGACY_SKILLS_ROOT
                or LEGACY_SKILLS_ROOT in relative.parents
            ):
                conflicts.append(
                    f"{relative.as_posix()} was not previously "
                    "harness-managed"
                )
            continue
        destination = project_root / relative
        if destination.is_symlink() or not destination.is_file():
            conflicts.append(
                f"{relative.as_posix()} is not a regular file"
            )
            continue
        source_hash = entry.get("sourceSha256")
        if not isinstance(source_hash, str) or len(source_hash) != 64:
            conflicts.append(
                f"{relative.as_posix()} has an invalid previous source hash"
            )
            continue
        actual_hash = sha256_file(destination)
        if actual_hash != source_hash:
            conflicts.append(
                f"{relative.as_posix()} differs from its previously "
                "distributed harness-managed content"
            )
            continue
        retirements.append(
            RetiredManagedFile(
                relative=relative,
                destination=destination,
                source_hash=source_hash,
            )
        )
    if conflicts:
        rendered = "\n".join(f"  - {conflict}" for conflict in conflicts)
        raise SystemExit(
            "Installation stopped before writing because previously "
            "distributed harness-managed files cannot be retired safely:\n"
            f"{rendered}\n"
            "Preserve the local content outside the harness-managed path or "
            "restore the previously distributed version, then rerun."
        )
    return retirements


def prune_empty_legacy_skill_directories(
    project_root: Path,
    retirements: list[RetiredManagedFile],
) -> None:
    legacy_root = project_root / LEGACY_SKILLS_ROOT
    directories: set[Path] = set()
    for item in retirements:
        if not (
            item.relative == LEGACY_SKILLS_ROOT
            or LEGACY_SKILLS_ROOT in item.relative.parents
        ):
            continue
        directory = item.destination.parent
        while directory == legacy_root or legacy_root in directory.parents:
            directories.add(directory)
            directory = directory.parent
    for directory in sorted(
        directories,
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        try:
            directory.rmdir()
        except OSError:
            pass


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
    retirements: list[RetiredManagedFile],
    operation_id: str,
    *,
    dry_run: bool,
) -> Path | None:
    if not replacements and not retirements:
        return None

    backup_root = project_root / BACKUP_ROOT / operation_id
    entries = []
    for item in replacements:
        destination = project_root / item.relative
        backup = backup_root / "files" / item.relative
        entries.append(
            {
                "path": item.relative.as_posix(),
                "operation": "replace",
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
    for item in retirements:
        backup = backup_root / "files" / item.relative
        entries.append(
            {
                "path": item.relative.as_posix(),
                "operation": "retire",
                "originalSha256": item.source_hash,
                "backupPath": (
                    Path("files") / item.relative
                ).as_posix(),
            }
        )
        if not dry_run:
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item.destination, backup)

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
    instruction: str | None = None,
    manifest_extra: dict[str, object] | None = None,
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
        "instruction": instruction
        or (
            "Review base, local, incoming, and both diffs. Apply only the "
            "approved changes to the project-owned local file."
        ),
        "files": entries,
    }
    if manifest_extra:
        manifest.update(manifest_extra)
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


def harness_release(
    repository_root: Path,
) -> tuple[str, str, str, str]:
    release_path = repository_root / HARNESS_RELEASE_PATH
    release = json.loads(release_path.read_text(encoding="utf-8"))
    version = release.get("version")
    tag = release.get("tag")
    if not isinstance(version, str) or tag != f"v{version}":
        raise SystemExit(
            "Invalid harness.release.json: tag must equal v plus version."
        )
    lock = json.loads(
        (repository_root / "harness.lock.json").read_text(encoding="utf-8")
    )
    harness = lock.get("harness", {})
    if harness.get("release") != version:
        raise SystemExit(
            "Invalid release contract: harness.lock.json release does not "
            "match harness.release.json."
        )
    return (
        version,
        tag,
        sha256_file(release_path),
        str(lock.get("updatedAt", "UNKNOWN")),
    )


def install_manifest(
    repository_root: Path,
    project_root: Path,
    files: list[InstallSource],
) -> dict[str, object]:
    (
        release,
        release_tag,
        release_manifest_hash,
        lock_updated_at,
    ) = harness_release(repository_root)
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
            "releaseTag": release_tag,
            "releaseManifestSha256": release_manifest_hash,
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
    validate_no_legacy_external_skills(project_root)

    files = source_files(repository_root, args.skip_agents)
    if not args.skip_agents:
        agents_source = next(
            item for item in files if item.relative == AGENTS_PATH
        )
        agents_path = project_root / AGENTS_PATH
        if agents_path.exists():
            contract_ok, contract_detail = agents_contract_status(project_root)
            if not contract_ok:
                if not args.prepare_migration:
                    raise SystemExit(
                        "Installation stopped before writing because the "
                        "existing project-owned AGENTS.md does not activate "
                        "the Unity Codex Harness agent contract.\n"
                        f"{contract_detail}\n"
                        "Rerun with --prepare-migration to create a reviewed "
                        "AGENTS.md migration bundle, integrate the required "
                        "marker and contract path, then rerun the installer."
                    )
                tracked = tracked_local_only_paths(project_root)
                if tracked:
                    preview = "\n".join(
                        f"  - {path}" for path in tracked[:10]
                    )
                    suffix = "\n  - ..." if len(tracked) > 10 else ""
                    raise SystemExit(
                        "Migration stopped because harness local-only paths "
                        "contain files already tracked by Git:\n"
                        f"{preview}{suffix}\n"
                        "Remove them from the Git index, then rerun."
                    )
                try:
                    gitignore_action, gitignore_text = plan_gitignore_update(
                        project_root
                    )
                except ValueError as error:
                    raise SystemExit(str(error)) from error
                write_gitignore(
                    project_root,
                    gitignore_text,
                    dry_run=args.dry_run,
                )
                migration_root = prepare_agents_contract_migration(
                    project_root,
                    agents_source,
                    dry_run=args.dry_run,
                )
                action_prefix = "would " if args.dry_run else ""
                if gitignore_action != "unchanged":
                    print(f"{action_prefix}{gitignore_action}: .gitignore")
                prefix = "would create" if args.dry_run else "created"
                print(
                    f"{prefix} AGENTS.md migration: "
                    f"{migration_root.relative_to(project_root).as_posix()}"
                )
                print(
                    "Installation remains incomplete: integrate the required "
                    "AGENTS.md contract reference, then rerun the installer."
                )
                return 1
    design_ok, design_detail = design_index_status(project_root)
    if not design_ok:
        index_path = project_root / DESIGN_INDEX_PATH
        if not index_path.is_file():
            raise SystemExit(
                "Installation stopped before writing because the game design "
                f"index is invalid: {design_detail}"
            )
        if not args.prepare_migration:
            raise SystemExit(
                "Installation stopped before writing because a legacy "
                "single-file game design sheet is present.\n"
                "Rerun with --prepare-migration to create a reviewed bundle "
                "containing the legacy sheet and the incoming split "
                "acceptance/design document set."
            )
        tracked = tracked_local_only_paths(project_root)
        if tracked:
            preview = "\n".join(f"  - {path}" for path in tracked[:10])
            suffix = "\n  - ..." if len(tracked) > 10 else ""
            raise SystemExit(
                "Migration stopped because harness local-only paths contain "
                f"files already tracked by Git:\n{preview}{suffix}\n"
                "Remove them from the Git index, then rerun."
            )
        try:
            gitignore_action, gitignore_text = plan_gitignore_update(
                project_root
            )
        except ValueError as error:
            raise SystemExit(str(error)) from error
        write_gitignore(
            project_root,
            gitignore_text,
            dry_run=args.dry_run,
        )
        index_source = next(
            item for item in files if item.relative == DESIGN_INDEX_PATH
        )
        design_sources = [
            item
            for item in files
            if item.relative == PROJECT_DESIGN_ROOT
            or PROJECT_DESIGN_ROOT in item.relative.parents
        ]
        migration_root = prepare_design_document_migration(
            project_root,
            index_source,
            design_sources,
            dry_run=args.dry_run,
        )
        action_prefix = "would " if args.dry_run else ""
        if gitignore_action != "unchanged":
            print(f"{action_prefix}{gitignore_action}: .gitignore")
        prefix = "would create" if args.dry_run else "created"
        print(
            f"{prefix} game design document migration: "
            f"{migration_root.relative_to(project_root).as_posix()}"
        )
        print(
            "Installation remains incomplete: split and review acceptance "
            "criteria and design documents, activate the new index, then "
            "rerun the installer."
        )
        return 1
    force_paths = selected_force_paths(files, args.force_file)
    lock_source = next(
        item for item in files if item.relative == HARNESS_LOCK_PATH
    )
    overrides_source = next(
        item for item in files if item.relative == HARNESS_OVERRIDES_PATH
    )
    lock_destination = project_root / HARNESS_LOCK_PATH
    lock_differs = (
        lock_destination.is_file()
        and not filecmp.cmp(
            lock_source.source,
            lock_destination,
            shallow=False,
        )
    )
    lock_forced = args.force or HARNESS_LOCK_PATH in force_paths
    if lock_differs and not lock_forced:
        if not args.prepare_migration:
            raise SystemExit(
                "Installation stopped before writing because the existing "
                "harness.lock.json differs from the harness-managed standard "
                "pin set.\n"
                "Rerun with --prepare-migration to review the legacy or custom "
                "lock differences and move approved game-specific values into "
                "harness.overrides.json."
            )
        tracked = tracked_local_only_paths(project_root)
        if tracked:
            preview = "\n".join(f"  - {path}" for path in tracked[:10])
            suffix = "\n  - ..." if len(tracked) > 10 else ""
            raise SystemExit(
                "Migration stopped because harness local-only paths contain "
                f"files already tracked by Git:\n{preview}{suffix}\n"
                "Remove them from the Git index, then rerun."
            )
        try:
            gitignore_action, gitignore_text = plan_gitignore_update(
                project_root
            )
        except ValueError as error:
            raise SystemExit(str(error)) from error
        write_gitignore(
            project_root,
            gitignore_text,
            dry_run=args.dry_run,
        )
        migration_root = prepare_lock_ownership_migration(
            project_root,
            lock_source,
            overrides_source,
            dry_run=args.dry_run,
        )
        action_prefix = "would " if args.dry_run else ""
        if gitignore_action != "unchanged":
            print(f"{action_prefix}{gitignore_action}: .gitignore")
        prefix = "would create" if args.dry_run else "created"
        print(
            f"{prefix} harness.lock.json ownership migration: "
            f"{migration_root.relative_to(project_root).as_posix()}"
        )
        print(
            "Installation remains incomplete: move approved project-specific "
            "values into harness.overrides.json, then rerun with "
            "--force-file harness.lock.json."
        )
        return 1
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
    retirements = plan_retired_managed_files(project_root)
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
        if replacements or retirements or migration_changes
        else ""
    )
    backup_root = backup_replacements(
        project_root,
        replacements,
        retirements,
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

    for item in retirements:
        if not args.dry_run:
            item.destination.unlink()
        operations.append(("retire", item.relative))
    if not args.dry_run:
        prune_empty_legacy_skill_directories(project_root, retirements)

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
