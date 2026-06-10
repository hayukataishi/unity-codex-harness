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
CROSS_CUTTING_REQUIRED_TEXT = {
    "docs/unity_design_sheet.md": (
        '<a id="cross-cutting-gate"></a>',
        "## 20. 横断機能採否ゲート",
        '<a id="project-001"></a>',
        "### PROJECT-001:",
        "PROJECT-001-AC03",
        "| `採用` |",
        "| `不採用` |",
        "| `保留` |",
        "| Accessibility |",
        "| Localization |",
        "| Multiplayer / Online |",
        "| Account / Authentication / Cloud Save |",
        "| Analytics / Crash Reporting |",
        "| Privacy / Consent / Compliance |",
        "| Security / Abuse Prevention |",
        "| LiveOps / Remote Config |",
        "| IAP / Ads / Entitlements |",
        "| Moderation / Community |",
        "| Modding / UGC |",
        "| XR |",
        "| Performance / Device Budgets |",
        "| Diagnostics / Debug / Cheat Controls |",
        "Vertical Slice、Alpha、Release Candidate",
    ),
    "docs/unity_harness_engineering.md": (
        '<a id="cross-cutting-policy"></a>',
        "### 横断機能採否ゲート",
        "空欄を不採用と解釈しない",
        "Codexは法務判断を代替せず",
    ),
    ".codex/skills/maintain-game-design/SKILL.md": (
        "## Cross-cutting adoption gate",
        "`採用`, `不採用`, or `保留`",
        "legal, store-policy, child-safety, or security",
    ),
    ".codex/skills/implement-unity-feature/SKILL.md": (
        "Check the cross-cutting adoption matrix",
        "`保留` or contradicts",
    ),
    ".codex/skills/validate-unity-change/SKILL.md": (
        "For cross-cutting changes",
        "implementation under `不採用` or `保留`",
    ),
    ".codex/skills/report-unity-work/SKILL.md": (
        "For cross-cutting changes",
        "reevaluation trigger",
    ),
    "README.md": (
        "### 横断機能を先に採否判断する",
        "`採用`、`不採用`、`保留`",
    ),
}
OUTDATED_CROSS_CUTTING_APPENDIX_TEXT = {
    "docs/unity_design_sheet.md": (
        "**ネットワーク同期** … マルチプレイなら必須",
        "**ローカライズ** … 多言語対応",
        "**Unity Gaming Services** …",
        "**VR / AR 対応** …",
    ),
}
ARCHITECTURE_PROFILE_REQUIRED_TEXT = {
    "docs/unity_design_sheet.md": (
        '<a id="architecture-profile-gate"></a>',
        "### ARCH-001:",
        "| `Small` |",
        "| `Standard` |",
        "| `Large` |",
        "選択理由",
        "移行条件",
        "`No Engine References`",
        "Service Locator",
        "ARCH-001-AC03",
    ),
    "docs/unity_harness_engineering.md": (
        '<a id="architecture-profile-policy"></a>',
        "### アーキテクチャプロファイル決定ゲート",
        "`Small`、`Standard`、`Large`",
        "Service Locatorは規模別の推奨方式にしない",
        "機能またはModule単位で段階的に移行する",
    ),
    ".codex/skills/maintain-game-design/SKILL.md": (
        "## Architecture profile gate",
        "smallest profile",
        "Do not recommend Service Locator",
    ),
    ".codex/skills/implement-unity-feature/SKILL.md": (
        "selected `Small`, `Standard`, or `Large` profile",
        "Do not create",
        "Do not introduce a DI container, Service Locator",
    ),
    ".codex/skills/validate-unity-change/SKILL.md": (
        "selected architecture profile",
        "unapproved DI container, Service Locator",
        "`No Engine References` assemblies",
    ),
    ".codex/skills/report-unity-work/SKILL.md": (
        "For architecture work",
        "selected profile",
        "migration trigger",
    ),
    "docs/mcp_and_skills_list.md": (
        "Small / Standard / Largeアーキテクチャプロファイル",
        "4 AssemblyはStandardの基準例",
    ),
    "README.md": (
        "### 規模に合うアーキテクチャを選ぶ",
        "`Small`",
        "`Standard`",
        "`Large`",
        "Service Locatorは規模別の推奨方式として新規採用しません",
    ),
}
OUTDATED_ARCHITECTURE_GUIDANCE = {
    "docs/unity_design_sheet.md": (
        "新規プロジェクトは次の4 Assemblyから開始する。",
        "| ServiceLocator | ☐ | 中規模向け |",
        "ScriptableObject Event Channel** | シーン跨ぎ・疎結合な通知（推奨）",
    ),
    ".codex/skills/implement-unity-feature/SKILL.md": (
        "Preserve layer direction: Presentation → Application → Domain",
    ),
}
SAVE_COMPATIBILITY_REQUIRED_TEXT = {
    "docs/unity_design_sheet.md": (
        '<a id="save-001"></a>',
        "### SAVE-001:",
        "| Atomic write |",
        "| Backup / rollback |",
        "| Integrity |",
        "`schemaVersion`",
        "`N → N+1`",
        "Cloud conflict",
        "PlayerPrefs",
        "Assets/Game/Tests/Fixtures/SaveData/<SchemaVersion>/",
        "SAVE-001-AC04",
    ),
    "docs/unity_harness_engineering.md": (
        '<a id="save-compatibility-policy"></a>',
        "### セーブデータ耐障害性・互換性ゲート",
        "Primary Saveを直接truncateして上書きしない",
        "未来Versionの非破壊拒否",
        "実在ユーザーのSave",
    ),
    ".codex/skills/maintain-game-design/SKILL.md": (
        "## Save compatibility gate",
        "sequential `N -> N+1` migrations",
        "anonymous fixtures",
    ),
    ".codex/skills/implement-unity-feature/SKILL.md": (
        "### Save data",
        "Never overwrite a valid primary save in place",
        "unknown future schema",
        "anonymous synthetic fixtures",
    ),
    ".codex/skills/validate-unity-change/SKILL.md": (
        "**Save compatibility**",
        "migration tests for every",
        "unknown future schemas",
        "Cloud Save is adopted",
    ),
    ".codex/skills/report-unity-work/SKILL.md": (
        "For save work",
        "supported-oldest schema",
        "atomic-write and backup results",
    ),
    "docs/mcp_and_skills_list.md": (
        "セーブデータ耐障害性・互換性",
        "対応旧Version fixture",
    ),
    "README.md": (
        "### セーブの破損・Version差を先に設計する",
        "Primaryを直接上書きせず",
        "未来Version",
        "`PlayerPrefs`は音量など",
    ),
}
OUTDATED_SAVE_GUIDANCE = {
    "docs/unity_design_sheet.md": (
        "保存方式      : JSON ファイル / PlayerPrefs / 暗号化  （いずれか）",
        "バージョン管理 : セーブデータの version フィールドでマイグレーション対応",
    ),
}
SOURCE_CONTROL_REQUIRED_TEXT = {
    "docs/unity_design_sheet.md": (
        '<a id="project-002"></a>',
        "### PROJECT-002:",
        "| Branch strategy |",
        "| LFS criteria |",
        "`.png`、`.wav`、`.fbx`などの拡張子だけで全ファイルを一律LFS化しない",
        "Git attributesはファイルsize条件を直接表現しない",
        "Visible Meta Files",
        "Force Text",
        "UnityYAMLMerge",
        "`git lfs migrate`",
        "PROJECT-002-AC04",
    ),
    "docs/unity_harness_engineering.md": (
        '<a id="project-version-control-policy"></a>',
        "### Git・大容量アセット・Unity Merge決定ゲート",
        "`main / develop / feature/*`を固定形にしない",
        "`.png`は自動的なLFS対象ではない",
        "Visible Meta Files",
        "履歴rewrite",
    ),
    ".codex/skills/maintain-game-design/SKILL.md": (
        "## Repository and asset gate",
        "Do not prescribe `main / develop / feature/*`",
        "An extension such as `.png` is not sufficient",
    ),
    ".codex/skills/implement-unity-feature/SKILL.md": (
        "read `PROJECT-002`",
        "Do not put `.meta` files in",
        "Use UnityYAMLMerge only",
    ),
    ".codex/skills/validate-unity-change/SKILL.md": (
        "For repository or asset changes",
        "`git check-attr`",
        "`git lfs fsck`",
        "`Visible Meta Files`",
    ),
    ".codex/skills/report-unity-work/SKILL.md": (
        "For repository and large-asset work",
        "LFS paths and size rule",
        "history-migration impact",
    ),
    "docs/mcp_and_skills_list.md": (
        "Git・大容量アセット運用",
        "UnityYAMLMerge",
    ),
    "README.md": (
        "### Gitと大容量アセット運用を選ぶ",
        "`main / develop / feature/*`を固定せず",
        "`.png`などの拡張子一律ではなく",
        "インストーラーはゲーム固有のBranch",
    ),
}
OUTDATED_SOURCE_CONTROL_GUIDANCE = {
    "docs/unity_design_sheet.md": (
        "Git LFS       : .psd .png .fbx .wav 等を対象",
        "ブランチ運用  : main / develop / feature/*",
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
VALIDATION_RUN_REQUIRED_TEXT = {
    "docs/unity_design_sheet.md": (
        '<a id="debug-001"></a>',
        "### DEBUG-001:",
        "作成時の`RUNNING`",
        "finalize後の`COMPLETED`",
        "RunManifest.sha256",
        "DEBUG-001-AC03",
        "DEBUG-001-AC04",
        "未生成path",
    ),
    "docs/unity_harness_engineering.md": (
        "Validation Runのライフサイクル",
        "schema version 2",
        "--blocked-reason",
        "verify_validation_run.py",
        "有効なNUnit XML",
        "未生成path",
    ),
    ".codex/skills/validate-unity-change/SKILL.md": (
        "## Finalize and verify",
        "--blocked-reason",
        "verify_validation_run.py",
        "Never add an expected but missing",
    ),
    ".codex/skills/validate-unity-change/scripts/create_validation_run.py": (
        '"schemaVersion": 2',
        '"state": "RUNNING"',
    ),
    ".codex/skills/validate-unity-change/scripts/finalize_validation_run.py": (
        'MANIFEST_SCHEMA_VERSION = 2',
        'MANIFEST_HASH_NAME = "RunManifest.sha256"',
        "Validation run is already completed",
    ),
    ".codex/skills/validate-unity-change/scripts/verify_validation_run.py": (
        'SCHEMA_VERSION = 2',
        "artifact SHA-256 mismatch",
        "missing evidence",
        "unrecorded artifact",
    ),
}
TEMPLATE_REGRESSION_REQUIRED_TEXT = {
    "docs/unity_design_sheet.md": (
        '<a id="debug-002"></a>',
        "### DEBUG-002:",
        "DEBUG-002-AC04",
        '<a id="debug-003"></a>',
        "### DEBUG-003:",
        "DEBUG-003-AC04",
        '<a id="debug-004"></a>',
        "### DEBUG-004:",
        "DEBUG-004-AC04",
        "Run ID衝突",
        "競合やdry-run時",
    ),
    "docs/unity_harness_engineering.md": (
        "テンプレート自己回帰テスト基準",
        "Unity fixture契約",
        "Installer CLI",
        "Static preflight",
        "unittest discover",
    ),
    ".github/workflows/validate-harness.yml": (
        'python3 -m unittest discover -s tests -p "test_*.py" -v',
    ),
    "tests/test_installer_cli.py": (
        "class InstallerCliRegressionTests",
        "test_conflict_stops_before_any_update",
        "test_force_replaces_conflicting_harness_file",
        "test_reinstall_is_idempotent",
    ),
    "tests/test_preflight_unity_project.py": (
        "class PreflightRegressionTests",
        "test_detects_missing_and_orphan_meta",
        "test_detects_invalid_and_duplicate_guid",
        "test_detects_missing_script_marker",
    ),
    "tests/test_validation_run_creation.py": (
        "class ValidationRunCreationRegressionTests",
        "test_run_id_collision_uses_two_digit_suffix",
        "test_run_id_collision_limit_fails_explicitly",
    ),
    "tests/test_unity_fixture_contract.py": (
        "class UnityFixtureContractTests",
        "test_required_saved_assets_have_meta_files",
        "test_assembly_boundaries_are_explicit",
        "test_asset_validation_config_covers_saved_assets",
    ),
    "tests/test_external_dependencies.py": (
        "class ExternalDependencyCheckTests",
        "test_missing_dependencies_report_fixed_install_steps",
        "test_pinned_project_installation_passes",
        "test_unity_mcp_version_mismatch_fails",
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


def validate_cross_cutting_documentation(root: Path) -> list[str]:
    errors: list[str] = []
    for relative, required_values in CROSS_CUTTING_REQUIRED_TEXT.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"missing cross-cutting document: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for required in required_values:
            if required not in text:
                errors.append(
                    f"missing cross-cutting adoption guidance: "
                    f"{relative} -> {required}"
                )

    for relative, outdated_values in (
        OUTDATED_CROSS_CUTTING_APPENDIX_TEXT.items()
    ):
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for outdated in outdated_values:
            if outdated in text:
                errors.append(
                    f"cross-cutting topic remains appendix-only: "
                    f"{relative} -> {outdated}"
                )
    return errors


def validate_architecture_profile_documentation(root: Path) -> list[str]:
    errors: list[str] = []
    for relative, required_values in ARCHITECTURE_PROFILE_REQUIRED_TEXT.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"missing architecture profile document: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for required in required_values:
            if required not in text:
                errors.append(
                    f"missing architecture profile guidance: "
                    f"{relative} -> {required}"
                )

    for relative, outdated_values in OUTDATED_ARCHITECTURE_GUIDANCE.items():
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for outdated in outdated_values:
            if outdated in text:
                errors.append(
                    f"overprescriptive architecture guidance: "
                    f"{relative} -> {outdated}"
                )
    return errors


def validate_save_compatibility_documentation(root: Path) -> list[str]:
    errors: list[str] = []
    for relative, required_values in SAVE_COMPATIBILITY_REQUIRED_TEXT.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"missing save compatibility document: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for required in required_values:
            if required not in text:
                errors.append(
                    f"missing save compatibility guidance: "
                    f"{relative} -> {required}"
                )

    for relative, outdated_values in OUTDATED_SAVE_GUIDANCE.items():
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for outdated in outdated_values:
            if outdated in text:
                errors.append(
                    f"unsafe minimal save guidance: {relative} -> {outdated}"
                )
    return errors


def validate_source_control_documentation(root: Path) -> list[str]:
    errors: list[str] = []
    for relative, required_values in SOURCE_CONTROL_REQUIRED_TEXT.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"missing source-control document: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for required in required_values:
            if required not in text:
                errors.append(
                    f"missing source-control guidance: "
                    f"{relative} -> {required}"
                )

    for relative, outdated_values in OUTDATED_SOURCE_CONTROL_GUIDANCE.items():
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for outdated in outdated_values:
            if outdated in text:
                errors.append(
                    f"overprescriptive source-control guidance: "
                    f"{relative} -> {outdated}"
                )
    return errors


def validate_validation_run_lifecycle(root: Path) -> list[str]:
    errors: list[str] = []
    for relative, required_values in VALIDATION_RUN_REQUIRED_TEXT.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"missing Validation Run lifecycle file: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for required in required_values:
            if required not in text:
                errors.append(
                    f"missing Validation Run lifecycle guidance: "
                    f"{relative} -> {required}"
                )
    return errors


def validate_template_regression_suite(root: Path) -> list[str]:
    errors: list[str] = []
    for relative, required_values in TEMPLATE_REGRESSION_REQUIRED_TEXT.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"missing template regression file: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for required in required_values:
            if required not in text:
                errors.append(
                    f"missing template regression coverage: "
                    f"{relative} -> {required}"
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

        distribution = dependency.get("distribution")
        if not isinstance(distribution, dict):
            errors.append(
                f"harness.lock.json {dependency_name}.distribution "
                "must be an object"
            )
        else:
            if distribution.get("bundled") is not False:
                errors.append(
                    f"harness.lock.json {dependency_name}.distribution.bundled "
                    "must be false"
                )
            if distribution.get("installMode") != "explicit-user-action":
                errors.append(
                    "harness.lock.json "
                    f"{dependency_name}.distribution.installMode "
                    "must be explicit-user-action"
                )
            license_name = distribution.get("license")
            if not isinstance(license_name, str) or not license_name:
                errors.append(
                    f"harness.lock.json {dependency_name}.distribution.license "
                    "must not be empty"
                )
            license_url = distribution.get("licenseUrl")
            if (
                not isinstance(license_url, str)
                or not license_url.startswith("https://github.com/")
            ):
                errors.append(
                    "harness.lock.json "
                    f"{dependency_name}.distribution.licenseUrl "
                    "must be a GitHub HTTPS URL"
                )

        install = dependency.get("install")
        if not isinstance(install, dict):
            errors.append(
                f"harness.lock.json {dependency_name}.install must be an object"
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
        install = unity_mcp.get("install")
        expected_package_url = (
            f"{unity_mcp.get('repository')}.git"
            f"?path=/{unity_mcp.get('unityPackagePath')}"
            f"#{unity_mcp.get('commit')}"
        )
        if (
            not isinstance(install, dict)
            or install.get("unityPackageUrl") != expected_package_url
        ):
            errors.append(
                "harness.lock.json unityMcp.install.unityPackageUrl "
                "must pin the recorded commit"
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
        install = sprite_forge.get("install")
        if isinstance(install, dict):
            project_path = install.get("projectCheckoutPath")
            user_path = install.get("userCheckoutPath")
            skill_names = install.get("skillNames")
            if project_path != ".codex/external/agent-sprite-forge":
                errors.append(
                    "harness.lock.json "
                    "agentSpriteForge.install.projectCheckoutPath is invalid"
                )
            if user_path != "external/agent-sprite-forge":
                errors.append(
                    "harness.lock.json "
                    "agentSpriteForge.install.userCheckoutPath is invalid"
                )
            if skill_names != ["generate2dsprite", "generate2dmap"]:
                errors.append(
                    "harness.lock.json "
                    "agentSpriteForge.install.skillNames is invalid"
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
        + validate_cross_cutting_documentation(root)
        + validate_architecture_profile_documentation(root)
        + validate_save_compatibility_documentation(root)
        + validate_source_control_documentation(root)
        + validate_cinemachine_documentation(root)
        + validate_validation_run_lifecycle(root)
        + validate_template_regression_suite(root)
        + validate_harness_lock(root)
    )
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("Repository validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
