#!/usr/bin/env python3
"""Validate repository-local Codex Skills and Markdown references."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any


FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
LEGACY_PATTERNS = ("Unityハーネスエンジニアリング/", "[[")
GITHUB_ACTION_RE = re.compile(
    r"^\s*(?:-\s*)?uses:\s*([^\s#]+)",
    re.MULTILINE,
)
PINNED_ACTION_RE = re.compile(r"^[^@]+@[0-9a-f]{40}$")
COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PYTHON_VERSION_RE = re.compile(r"^\d+\.\d+$")
PACKAGE_REQUIREMENT_RE = re.compile(r"^(?:~=|==|!=|>=|<=|>|<)\S+$")
VALID_RESULTS = {"PASS", "FAIL", "BLOCKED", "NOT RUN"}
BUILD_PROFILE_REQUIRED_TEXT = {
    "docs/unity_design_sheet.md": (
        '<a id="build-001"></a>',
        "### BUILD-001:",
        "Assets/Settings/BuildProfiles/<Platform>/",
        "GAME_BUILD_DEVELOPMENT",
        "GAME_BUILD_QA",
        "GAME_BUILD_RELEASE",
        "-activeBuildProfile",
        "BUILD-001-AC03",
    ),
    "docs/unity_harness_engineering.md": (
        '<a id="build-profile-policy"></a>',
        "Unity 6 Build Profile運用方針",
        "Legacy Build Settings",
        "-activeBuildProfile",
    ),
    ".codex/skills/validate-unity-change/SKILL.md": (
        "Build Profile asset path",
        "-activeBuildProfile",
    ),
}
OUTDATED_BUILD_SETTINGS_TEXT = {
    "docs/unity_design_sheet.md": (
        "Build Settings（登録）",
        "| **Build Settings** |",
    ),
    "docs/unity_harness_engineering.md": (
        "Build SettingsのScene登録確認",
    ),
    "docs/mcp_and_skills_list.md": (
        "Build Settings、Tag、Layer、Input設定",
    ),
}
CINEMACHINE_3_REQUIRED_TEXT = {
    "docs/unity_design_sheet.md": (
        '<a id="graphics-001"></a>',
        "### GRAPHICS-001:",
        "CinemachineCamera + CinemachineFollow / CinemachinePositionComposer",
        "Unity.Cinemachine",
        "Tracking Target",
        "Cinemachine Channel",
        "CINEMACHINE_NO_CM2_SUPPORT",
        "GRAPHICS-001-AC03",
    ),
    "docs/unity_harness_engineering.md": (
        '<a id="cinemachine-policy"></a>',
        "Cinemachineバージョン運用方針",
        "Packages/manifest.json",
        "packages-lock.json",
        "Cinemachine Upgrader",
    ),
    ".codex/skills/implement-unity-feature/SKILL.md": (
        "Before Cinemachine work",
        "Unity.Cinemachine",
        "CinemachineCamera",
        "Cinemachine Upgrader",
    ),
    ".codex/skills/validate-unity-change/SKILL.md": (
        "For Cinemachine changes",
        "Position / Rotation Control components",
    ),
}
OUTDATED_CINEMACHINE_EXAMPLE_TEXT = {
    "docs/unity_design_sheet.md": (
        "| `FollowCamera` | プレイヤー追従 | CinemachineVirtualCamera | 10 |",
    ),
}


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


def validate_build_profile_documentation(root: Path) -> list[str]:
    errors: list[str] = []
    for relative, required_values in BUILD_PROFILE_REQUIRED_TEXT.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"missing Build Profile document: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for required in required_values:
            if required not in text:
                errors.append(
                    f"missing Build Profile guidance: {relative} -> {required}"
                )

    for relative, outdated_values in OUTDATED_BUILD_SETTINGS_TEXT.items():
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for outdated in outdated_values:
            if outdated in text:
                errors.append(
                    f"outdated Build Settings guidance: {relative} -> {outdated}"
                )
    return errors


def validate_cinemachine_documentation(root: Path) -> list[str]:
    errors: list[str] = []
    for relative, required_values in CINEMACHINE_3_REQUIRED_TEXT.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"missing Cinemachine document: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for required in required_values:
            if required not in text:
                errors.append(
                    f"missing Cinemachine 3 guidance: {relative} -> {required}"
                )

    for relative, outdated_values in OUTDATED_CINEMACHINE_EXAMPLE_TEXT.items():
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for outdated in outdated_values:
            if outdated in text:
                errors.append(
                    f"outdated Cinemachine 2 example: {relative} -> {outdated}"
                )
    return errors


def validate_harness_lock_data(
    manifest: Any,
    fixture_unity_version: str,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["harness.lock.json root must be an object"]

    if manifest.get("schemaVersion") != 1:
        errors.append("harness.lock.json schemaVersion must be 1")

    updated_at = manifest.get("updatedAt")
    try:
        date.fromisoformat(updated_at)
    except (TypeError, ValueError):
        errors.append("harness.lock.json updatedAt must be an ISO date")

    harness = manifest.get("harness")
    if not isinstance(harness, dict):
        errors.append("harness.lock.json harness must be an object")
        harness = {}

    if harness.get("unityFixtureVersion") != fixture_unity_version:
        errors.append(
            "harness.lock.json Unity fixture version does not match "
            "tests/fixtures/UnityValidationFixture"
        )

    python = harness.get("python")
    if not isinstance(python, dict):
        errors.append("harness.lock.json harness.python must be an object")
    else:
        for key in ("minimum", "ci"):
            value = python.get(key)
            if not isinstance(value, str) or not PYTHON_VERSION_RE.fullmatch(value):
                errors.append(
                    f"harness.lock.json harness.python.{key} "
                    "must be a major.minor version"
                )

    dependencies = manifest.get("externalDependencies")
    if not isinstance(dependencies, dict):
        errors.append(
            "harness.lock.json externalDependencies must be an object"
        )
        return errors

    for dependency_name in ("unityMcp", "agentSpriteForge"):
        dependency = dependencies.get(dependency_name)
        if not isinstance(dependency, dict):
            errors.append(
                f"harness.lock.json missing dependency: {dependency_name}"
            )
            continue

        repository = dependency.get("repository")
        if not isinstance(repository, str) or not repository.startswith(
            "https://github.com/"
        ):
            errors.append(
                f"harness.lock.json {dependency_name}.repository "
                "must be a GitHub HTTPS URL"
            )

        commit = dependency.get("commit")
        if not isinstance(commit, str) or not COMMIT_SHA_RE.fullmatch(commit):
            errors.append(
                f"harness.lock.json {dependency_name}.commit "
                "must be a 40-character lowercase SHA"
            )

        ref = dependency.get("ref")
        if not isinstance(ref, str) or not ref:
            errors.append(
                f"harness.lock.json {dependency_name}.ref must not be empty"
            )

        sources = dependency.get("sources")
        if (
            not isinstance(sources, list)
            or not sources
            or any(
                not isinstance(source, str)
                or not source.startswith("https://github.com/")
                for source in sources
            )
        ):
            errors.append(
                f"harness.lock.json {dependency_name}.sources "
                "must contain GitHub HTTPS URLs"
            )

        verification = dependency.get("verification")
        if not isinstance(verification, dict):
            errors.append(
                f"harness.lock.json {dependency_name}.verification "
                "must be an object"
            )
            continue
        status = verification.get("status")
        if status not in VALID_RESULTS:
            errors.append(
                f"harness.lock.json {dependency_name}.verification.status "
                f"must be one of {sorted(VALID_RESULTS)}"
            )
        reason = verification.get("reason")
        if status != "PASS" and (not isinstance(reason, str) or not reason):
            errors.append(
                f"harness.lock.json {dependency_name}.verification.reason "
                "is required unless status is PASS"
            )

    unity_mcp = dependencies.get("unityMcp")
    if isinstance(unity_mcp, dict):
        package_version = unity_mcp.get("packageVersion")
        if unity_mcp.get("ref") != f"v{package_version}":
            errors.append(
                "harness.lock.json unityMcp.ref must match packageVersion"
            )
        if unity_mcp.get("packageName") != "com.coplaydev.unity-mcp":
            errors.append(
                "harness.lock.json unityMcp.packageName is invalid"
            )
        if unity_mcp.get("unityPackagePath") != "MCPForUnity":
            errors.append(
                "harness.lock.json unityMcp.unityPackagePath is invalid"
            )

    sprite_forge = dependencies.get("agentSpriteForge")
    if isinstance(sprite_forge, dict):
        packages = sprite_forge.get("pythonPackages")
        if not isinstance(packages, dict):
            errors.append(
                "harness.lock.json agentSpriteForge.pythonPackages "
                "must be an object"
            )
        else:
            for package_name in ("numpy", "Pillow"):
                requirement = packages.get(package_name)
                if (
                    not isinstance(requirement, str)
                    or not PACKAGE_REQUIREMENT_RE.fullmatch(requirement)
                ):
                    errors.append(
                        "harness.lock.json "
                        f"agentSpriteForge.pythonPackages.{package_name} "
                        "must be a version constraint"
                    )
        if sprite_forge.get("ref") != sprite_forge.get("commit"):
            errors.append(
                "harness.lock.json agentSpriteForge.ref must equal commit"
            )

    return errors


def validate_harness_lock(root: Path) -> list[str]:
    lock_path = root / "harness.lock.json"
    if not lock_path.is_file():
        return ["missing harness.lock.json"]

    try:
        manifest = json.loads(lock_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"invalid harness.lock.json: {error}"]

    version_path = (
        root
        / "tests"
        / "fixtures"
        / "UnityValidationFixture"
        / "ProjectSettings"
        / "ProjectVersion.txt"
    )
    if not version_path.is_file():
        return ["missing Unity fixture ProjectVersion.txt"]

    match = re.search(
        r"^m_EditorVersion:\s*(\S+)\s*$",
        version_path.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    if not match:
        return ["invalid Unity fixture ProjectVersion.txt"]

    return validate_harness_lock_data(manifest, match.group(1))


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    errors = (
        validate_skills(root)
        + validate_markdown(root)
        + validate_github_actions(root)
        + validate_build_profile_documentation(root)
        + validate_cinemachine_documentation(root)
        + validate_harness_lock(root)
    )
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("Repository validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
