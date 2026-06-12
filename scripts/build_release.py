#!/usr/bin/env python3
"""Validate and build a deterministic Unity Codex Harness release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from datetime import date
from pathlib import Path
from typing import Any


RELEASE_PATH = Path("harness.release.json")
LOCK_PATH = Path("harness.lock.json")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$"
)
ARCHIVE_FILES = (
    Path("AGENTS.md"),
    Path("CHANGELOG.md"),
    Path("LICENSE"),
    Path("README.md"),
    Path("harness.lock.json"),
    Path("harness.overrides.json"),
    Path("harness.release.json"),
    Path("docs/mcp_and_skills_list.md"),
    Path("docs/unity_design_sheet.md"),
    Path("docs/unity_harness_agent_contract.md"),
    Path("docs/unity_harness_capabilities.md"),
    Path("docs/unity_harness_engineering.md"),
    Path("docs/unity_harness_release.md"),
    Path("docs/unity_harness_requirements.md"),
)
ARCHIVE_TREES = (
    Path(".codex/agents"),
    Path(".agents/skills"),
    Path("docs/game_design"),
    Path("scripts"),
    Path("templates/unity"),
)
FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and build the versioned harness release artifact."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate release metadata without building an artifact.",
    )
    parser.add_argument(
        "--tag",
        help="Require this Git tag to match harness.release.json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Directory for the release ZIP, manifest, and checksums.",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"missing release contract file: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path} root must be an object")
    return value


def nested_object(
    value: dict[str, Any],
    key: str,
    errors: list[str],
    context: str,
) -> dict[str, Any]:
    nested = value.get(key)
    if not isinstance(nested, dict):
        errors.append(f"{context}.{key} must be an object")
        return {}
    return nested


def safe_repository_path(
    value: object,
    errors: list[str],
    context: str,
) -> Path | None:
    if not isinstance(value, str) or not value:
        errors.append(f"{context} must be a repository-relative path")
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        errors.append(f"{context} must be a safe repository-relative path")
        return None
    return path


def validate_release(
    repository_root: Path,
    expected_tag: str | None = None,
) -> list[str]:
    errors: list[str] = []
    try:
        release = load_json_object(repository_root / RELEASE_PATH)
        lock = load_json_object(repository_root / LOCK_PATH)
    except ValueError as error:
        return [str(error)]

    if release.get("schemaVersion") != 1:
        errors.append("harness.release.json schemaVersion must be 1")
    if release.get("name") != "unity-codex-harness":
        errors.append(
            "harness.release.json name must be unity-codex-harness"
        )

    version = release.get("version")
    if not isinstance(version, str) or not SEMVER_RE.fullmatch(version):
        errors.append(
            "harness.release.json version must be a valid Semantic Version"
        )
        version = "INVALID"
    tag = release.get("tag")
    expected_release_tag = f"v{version}"
    if tag != expected_release_tag:
        errors.append(
            "harness.release.json tag must equal v plus the release version"
        )
    if expected_tag is not None and tag != expected_tag:
        errors.append(
            f"release tag mismatch: metadata has {tag!r}, "
            f"workflow requested {expected_tag!r}"
        )
    if release.get("channel") != "stable":
        errors.append("harness.release.json channel must be stable")

    released_at = release.get("releasedAt")
    if not isinstance(released_at, str):
        errors.append("harness.release.json releasedAt must be an ISO date")
    else:
        try:
            date.fromisoformat(released_at)
        except ValueError:
            errors.append(
                "harness.release.json releasedAt must be an ISO date"
            )

    if release.get("installManifestSchema") != 2:
        errors.append(
            "harness.release.json installManifestSchema must be 2"
        )

    artifact = nested_object(release, "artifact", errors, "release")
    expected_archive = f"unity-codex-harness-{version}.zip"
    if artifact.get("archive") != expected_archive:
        errors.append(
            "harness.release.json artifact.archive must match the version"
        )
    if artifact.get("manifest") != "release-manifest.json":
        errors.append(
            "harness.release.json artifact.manifest is invalid"
        )
    if artifact.get("checksums") != "SHA256SUMS":
        errors.append(
            "harness.release.json artifact.checksums is invalid"
        )

    compatibility = nested_object(
        release,
        "compatibility",
        errors,
        "release",
    )
    codex = nested_object(
        compatibility,
        "codex",
        errors,
        "release.compatibility",
    )
    unity = nested_object(
        compatibility,
        "unity",
        errors,
        "release.compatibility",
    )
    python = nested_object(
        compatibility,
        "python",
        errors,
        "release.compatibility",
    )
    codex_band = codex.get("compatibilityBand")
    codex_tested = codex.get("tested")
    if not isinstance(codex_band, str) or not codex_band:
        errors.append("Codex compatibilityBand must not be empty")
    if (
        not isinstance(codex_tested, list)
        or not codex_tested
        or any(not isinstance(item, str) or not item for item in codex_tested)
    ):
        errors.append("Codex tested versions must be a non-empty string array")
    if codex.get("cli") not in {"PASS", "NOT RUN"}:
        errors.append("Codex CLI compatibility must be PASS or NOT RUN")
    for surface in ("ide", "app"):
        if codex.get(surface) not in {"PASS", "NOT RUN"}:
            errors.append(
                f"Codex {surface} compatibility must be PASS or NOT RUN"
            )
    unity_band = unity.get("compatibilityBand")
    unity_tested = unity.get("tested")
    if not isinstance(unity_band, str) or not unity_band:
        errors.append("Unity compatibilityBand must not be empty")
    if (
        not isinstance(unity_tested, list)
        or not unity_tested
        or any(not isinstance(item, str) or not item for item in unity_tested)
    ):
        errors.append("Unity tested versions must be a non-empty string array")
    if unity.get("fixture") not in {"PASS", "NOT RUN"}:
        errors.append("Unity fixture compatibility must be PASS or NOT RUN")
    for key in ("minimum", "ci"):
        value = python.get(key)
        if not isinstance(value, str) or not value:
            errors.append(f"Python release compatibility {key} is required")

    migration = nested_object(release, "migration", errors, "release")
    supported_from = migration.get("supportedFrom")
    if (
        not isinstance(supported_from, list)
        or not supported_from
        or any(
            not isinstance(item, str) or not item
            for item in supported_from
        )
    ):
        errors.append("release migration supportedFrom must not be empty")
    for key in ("policy", "guide"):
        target = migration.get(key)
        if not isinstance(target, str) or "#" not in target:
            errors.append(f"release.migration.{key} must include an anchor")
            continue
        relative_text, anchor = target.split("#", 1)
        relative = safe_repository_path(
            relative_text,
            errors,
            f"release.migration.{key}",
        )
        if relative is None or not anchor:
            continue
        path = repository_root / relative
        if not path.is_file():
            errors.append(f"missing migration document: {relative}")
        elif f'<a id="{anchor}"></a>' not in path.read_text(encoding="utf-8"):
            errors.append(
                f"missing migration anchor: {relative}#{anchor}"
            )
    release_notes = safe_repository_path(
        release.get("releaseNotes"),
        errors,
        "releaseNotes",
    )
    if release_notes is not None and not (
        repository_root / release_notes
    ).is_file():
        errors.append(f"missing release notes: {release_notes}")

    lock_harness = nested_object(lock, "harness", errors, "lock")
    if lock_harness.get("release") != version:
        errors.append(
            "harness.lock.json harness.release must match release version"
        )
    if lock.get("updatedAt") != released_at:
        errors.append(
            "harness.lock.json updatedAt must match the release date"
        )
    lock_python = nested_object(
        lock_harness,
        "python",
        errors,
        "lock.harness",
    )
    if lock_python != python:
        errors.append(
            "harness.lock.json Python compatibility must match release metadata"
        )
    if lock_harness.get("unityFixtureVersion") not in unity.get("tested", []):
        errors.append(
            "harness.lock.json Unity fixture must be a tested release version"
        )

    required_text = {
        "CHANGELOG.md": (
            f"## [{version}] - {released_at}",
            "Semantic Versioning",
            "### Migration",
        ),
        "docs/unity_harness_release.md": (
            f"| Harness version | `{version}` |",
            f"| Git tag | `{tag}` |",
            '<a id="migration-policy"></a>',
            "Compatibility matrix",
            "SHA256SUMS",
        ),
        release_notes.as_posix() if release_notes is not None else "INVALID": (
            f"# Unity Codex Harness {tag}",
            "## Compatibility",
            "## Migration",
            "## Known limitations",
        ),
        "README.md": (
            "harness.release.json",
            "scripts/build_release.py",
            "SHA256SUMS",
        ),
    }
    for relative, values in required_text.items():
        path = repository_root / relative
        if not path.is_file():
            errors.append(f"missing release documentation: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for required in values:
            if required not in text:
                errors.append(
                    f"missing release documentation: {relative} -> {required}"
                )

    for relative in (*ARCHIVE_FILES, *ARCHIVE_TREES):
        source = repository_root / relative
        if not source.exists():
            errors.append(f"missing release artifact source: {relative}")
        elif source.is_symlink():
            errors.append(f"release artifact source is a symlink: {relative}")
    for relative in release_files(repository_root):
        if relative == Path(
            "docs/unity_harness_evaluation_2026-06-08.md"
        ):
            errors.append(
                "source-only evaluation report must not be archived"
            )
        if relative.parts and relative.parts[0] in {"tests", ".github"}:
            errors.append(
                f"development-only path must not be archived: {relative}"
            )
    return errors


def release_files(repository_root: Path) -> list[Path]:
    relative_paths = set(ARCHIVE_FILES)
    release = load_json_object(repository_root / RELEASE_PATH)
    release_notes = release.get("releaseNotes")
    if isinstance(release_notes, str):
        relative_paths.add(Path(release_notes))
    for relative_root in ARCHIVE_TREES:
        source_root = repository_root / relative_root
        for path in source_root.rglob("*"):
            if (
                not path.is_file()
                or path.is_symlink()
                or "__pycache__" in path.parts
                or path.suffix == ".pyc"
                or path.name == ".DS_Store"
            ):
                continue
            relative_paths.add(path.relative_to(repository_root))
    return sorted(relative_paths, key=lambda path: path.as_posix())


def zip_info(archive_path: str, executable: bool) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(archive_path, FIXED_ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    mode = 0o100755 if executable else 0o100644
    info.external_attr = mode << 16
    return info


def build_release(
    repository_root: Path,
    output_root: Path,
) -> tuple[Path, Path, Path]:
    release = load_json_object(repository_root / RELEASE_PATH)
    version = str(release["version"])
    artifact = release["artifact"]
    assert isinstance(artifact, dict)
    archive_path = output_root / str(artifact["archive"])
    manifest_path = output_root / str(artifact["manifest"])
    checksums_path = output_root / str(artifact["checksums"])
    output_root.mkdir(parents=True, exist_ok=True)

    archive_prefix = f"unity-codex-harness-{version}"
    files = release_files(repository_root)
    with zipfile.ZipFile(
        archive_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for relative in files:
            source = repository_root / relative
            executable = relative.suffix == ".py"
            archive_name = f"{archive_prefix}/{relative.as_posix()}"
            archive.writestr(
                zip_info(archive_name, executable),
                source.read_bytes(),
            )

    archive_hash = sha256_file(archive_path)
    release_manifest = {
        "schemaVersion": 1,
        "name": release["name"],
        "version": version,
        "tag": release["tag"],
        "releasedAt": release["releasedAt"],
        "sourceContractSha256": sha256_file(
            repository_root / RELEASE_PATH
        ),
        "artifact": {
            "path": archive_path.name,
            "sha256": archive_hash,
            "size": archive_path.stat().st_size,
            "fileCount": len(files),
        },
    }
    manifest_path.write_text(
        json_text(release_manifest),
        encoding="utf-8",
    )
    manifest_hash = sha256_file(manifest_path)
    checksums_path.write_text(
        (
            f"{archive_hash}  {archive_path.name}\n"
            f"{manifest_hash}  {manifest_path.name}\n"
        ),
        encoding="utf-8",
    )
    return archive_path, manifest_path, checksums_path


def main() -> int:
    args = parse_args()
    repository_root = Path(__file__).resolve().parent.parent
    errors = validate_release(repository_root, args.tag)
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("Release contract: OK")

    if args.output is not None:
        output_root = args.output.expanduser().resolve()
        archive, manifest, checksums = build_release(
            repository_root,
            output_root,
        )
        for path in (archive, manifest, checksums):
            print(path)
    elif not args.check:
        print("No artifact built; pass --output <directory>.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
