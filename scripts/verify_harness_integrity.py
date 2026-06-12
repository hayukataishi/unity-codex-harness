#!/usr/bin/env python3
"""Verify installed harness-managed files against the install manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


MANIFEST_PATH = Path(".unity-codex-harness/install-manifest.json")
MANIFEST_HASH_PATH = Path(".unity-codex-harness/install-manifest.sha256")
RELEASE_PATH = Path("harness.release.json")
AGENTS_PATH = Path("AGENTS.md")
AGENTS_CONTRACT_PATH = Path("docs/unity_harness_agent_contract.md")
AGENTS_CONTRACT_MARKER = (
    "<!-- UNITY_CODEX_HARNESS_AGENT_CONTRACT: REQUIRED -->"
)
SUPPORTED_SCHEMA_VERSION = 2
OWNERSHIP_HARNESS = "harness-managed"
OWNERSHIP_PROJECT = "project-owned"
VALID_OWNERSHIP = {OWNERSHIP_HARNESS, OWNERSHIP_PROJECT}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify installed harness-managed files against "
            ".unity-codex-harness/install-manifest.json."
        )
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Unity project root containing .unity-codex-harness",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative_path(value: Any, label: str) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value or "\\" in value:
        return None, f"invalid {label}: {value!r}"
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or ":" in pure.parts[0]
        or any(part in ("", ".", "..") for part in pure.parts)
    ):
        return None, f"unsafe {label}: {value!r}"
    return Path(*pure.parts), None


def ignored_runtime_file(path: Path) -> bool:
    return (
        "__pycache__" in path.parts
        or path.name == ".DS_Store"
        or path.suffix == ".pyc"
    )


def load_manifest(
    project_root: Path,
) -> tuple[dict[str, Any] | None, list[str]]:
    manifest_path = project_root / MANIFEST_PATH
    sidecar_path = project_root / MANIFEST_HASH_PATH
    errors: list[str] = []

    if not manifest_path.is_file():
        return None, [f"missing install manifest: {MANIFEST_PATH.as_posix()}"]
    if not sidecar_path.is_file():
        return None, [
            f"missing install manifest hash: {MANIFEST_HASH_PATH.as_posix()}"
        ]

    sidecar_parts = sidecar_path.read_text(encoding="utf-8").strip().split()
    if len(sidecar_parts) != 2 or sidecar_parts[1] != MANIFEST_PATH.name:
        return None, [
            f"invalid install manifest hash file: "
            f"{MANIFEST_HASH_PATH.as_posix()}"
        ]
    expected_manifest_hash = sidecar_parts[0]
    if not SHA256_RE.fullmatch(expected_manifest_hash):
        return None, [
            f"invalid install manifest SHA-256: {expected_manifest_hash!r}"
        ]
    actual_manifest_hash = sha256_file(manifest_path)
    if actual_manifest_hash != expected_manifest_hash:
        return None, [
            "install manifest SHA-256 mismatch: "
            f"expected {expected_manifest_hash}, got {actual_manifest_hash}"
        ]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return None, [f"invalid install manifest JSON: {error}"]
    if not isinstance(manifest, dict):
        errors.append("install manifest root must be an object")
        return None, errors
    return manifest, errors


def validate_integrity(project_root: Path) -> list[str]:
    project_root = project_root.resolve()
    manifest, errors = load_manifest(project_root)
    if manifest is None:
        return errors

    if manifest.get("schemaVersion") != SUPPORTED_SCHEMA_VERSION:
        errors.append(
            "unsupported install manifest schemaVersion: "
            f"{manifest.get('schemaVersion')!r}"
        )

    entries = manifest.get("files")
    if not isinstance(entries, list):
        errors.append("install manifest files must be an array")
        return errors

    managed_paths: set[Path] = set()
    all_paths: set[Path] = set()
    source_hashes: dict[Path, str] = {}
    agents_contract_required = False
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"install manifest file entry {index} must be an object")
            continue
        relative, path_error = safe_relative_path(
            entry.get("path"),
            f"install manifest path at index {index}",
        )
        if path_error:
            errors.append(path_error)
            continue
        assert relative is not None
        if relative in all_paths:
            errors.append(f"duplicate install manifest path: {relative.as_posix()}")
            continue
        all_paths.add(relative)

        ownership = entry.get("ownership")
        if ownership not in VALID_OWNERSHIP:
            errors.append(
                f"invalid ownership for {relative.as_posix()}: {ownership!r}"
            )
            continue
        if relative == AGENTS_PATH:
            agents_contract_required = True
        source_hash = entry.get("sourceSha256")
        if not isinstance(source_hash, str) or not SHA256_RE.fullmatch(source_hash):
            errors.append(
                f"invalid source SHA-256 for {relative.as_posix()}: "
                f"{source_hash!r}"
            )
            continue
        source_hashes[relative] = source_hash
        if ownership != OWNERSHIP_HARNESS:
            continue

        managed_paths.add(relative)
        destination = project_root / relative
        if destination.is_symlink():
            errors.append(
                f"harness-managed path must not be a symlink: "
                f"{relative.as_posix()}"
            )
            continue
        if not destination.is_file():
            errors.append(
                f"missing harness-managed file: {relative.as_posix()}"
            )
            continue
        actual_hash = sha256_file(destination)
        if actual_hash != source_hash:
            errors.append(
                f"harness-managed SHA-256 mismatch: {relative.as_posix()} "
                f"(expected {source_hash}, got {actual_hash})"
            )

    if not managed_paths:
        errors.append("install manifest contains no harness-managed files")

    harness = manifest.get("harness")
    if not isinstance(harness, dict):
        errors.append("install manifest harness must be an object")
    else:
        release_path = project_root / RELEASE_PATH
        release_hash = source_hashes.get(RELEASE_PATH)
        if release_hash is None:
            errors.append(
                "install manifest must record harness.release.json"
            )
        elif harness.get("releaseManifestSha256") != release_hash:
            errors.append(
                "install manifest releaseManifestSha256 must match the "
                "harness.release.json source SHA-256"
            )
        if release_path.is_file() and not release_path.is_symlink():
            try:
                release = json.loads(
                    release_path.read_text(encoding="utf-8")
                )
            except json.JSONDecodeError as error:
                errors.append(f"invalid harness.release.json: {error}")
            else:
                if not isinstance(release, dict):
                    errors.append(
                        "harness.release.json root must be an object"
                    )
                else:
                    version = release.get("version")
                    tag = release.get("tag")
                    if harness.get("release") != version:
                        errors.append(
                            "install manifest harness.release does not match "
                            "harness.release.json"
                        )
                    if harness.get("releaseTag") != tag:
                        errors.append(
                            "install manifest harness.releaseTag does not "
                            "match harness.release.json"
                        )

    if agents_contract_required:
        agents_path = project_root / AGENTS_PATH
        if not agents_path.is_file():
            errors.append(
                "missing project-owned AGENTS.md required by the install "
                "manifest"
            )
        else:
            text = agents_path.read_text(encoding="utf-8")
            if AGENTS_CONTRACT_MARKER not in text:
                errors.append(
                    "AGENTS.md is missing required harness contract marker: "
                    f"{AGENTS_CONTRACT_MARKER}"
                )
            if AGENTS_CONTRACT_PATH.as_posix() not in text:
                errors.append(
                    "AGENTS.md is missing required harness contract path: "
                    f"{AGENTS_CONTRACT_PATH.as_posix()}"
                )

    roots = manifest.get("exclusiveManagedRoots")
    if not isinstance(roots, list):
        errors.append("install manifest exclusiveManagedRoots must be an array")
        return errors

    seen_roots: set[Path] = set()
    for index, value in enumerate(roots):
        relative_root, root_error = safe_relative_path(
            value,
            f"exclusive managed root at index {index}",
        )
        if root_error:
            errors.append(root_error)
            continue
        assert relative_root is not None
        if relative_root in seen_roots:
            errors.append(
                f"duplicate exclusive managed root: {relative_root.as_posix()}"
            )
            continue
        seen_roots.add(relative_root)
        destination_root = project_root / relative_root
        if destination_root.is_symlink():
            errors.append(
                f"exclusive managed root must not be a symlink: "
                f"{relative_root.as_posix()}"
            )
            continue
        if not destination_root.exists():
            continue
        if not destination_root.is_dir():
            errors.append(
                f"exclusive managed root is not a directory: "
                f"{relative_root.as_posix()}"
            )
            continue
        for candidate in sorted(destination_root.rglob("*")):
            if candidate.is_dir() and not candidate.is_symlink():
                continue
            relative = candidate.relative_to(project_root)
            if ignored_runtime_file(relative):
                continue
            if candidate.is_symlink():
                errors.append(
                    f"unexpected symlink in exclusive managed root: "
                    f"{relative.as_posix()}"
                )
            elif candidate.is_file() and relative not in managed_paths:
                errors.append(
                    f"unexpected file in exclusive managed root: "
                    f"{relative.as_posix()}"
                )

    return errors


def main() -> int:
    args = parse_args()
    errors = validate_integrity(args.project_root)
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("Harness integrity verification: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
