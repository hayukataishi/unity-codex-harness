#!/usr/bin/env python3
"""Check optional external Unity Codex harness dependencies."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any


LOCK_FILE = "harness.lock.json"
OVERRIDES_FILE = "harness.overrides.json"
UNITY_MANIFEST = Path("Packages/manifest.json")
COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check pinned Unity MCP and external Codex Skill installations. "
            "This command never downloads or modifies external software."
        )
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Unity project root containing the harness lock and overrides",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable JSON report",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SystemExit(f"Missing required file: {path}") from error
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid JSON: {path}: {error}") from error


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SystemExit(f"Invalid {LOCK_FILE}: {label} must be an object")
    return value


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = deep_merge(current, value)
        else:
            merged[key] = deepcopy(value)
    return merged


def validate_override_values(
    standard: dict[str, Any],
    values: dict[str, Any],
    label: str,
) -> None:
    for key, value in values.items():
        if key not in standard:
            raise SystemExit(
                f"Invalid {OVERRIDES_FILE}: unknown field {label}.{key}"
            )
        standard_value = standard[key]
        if isinstance(standard_value, dict):
            if not isinstance(value, dict):
                raise SystemExit(
                    f"Invalid {OVERRIDES_FILE}: {label}.{key} must be an object"
                )
            validate_override_values(
                standard_value,
                value,
                f"{label}.{key}",
            )
        elif isinstance(value, dict):
            raise SystemExit(
                f"Invalid {OVERRIDES_FILE}: {label}.{key} must not be an object"
            )


def load_effective_dependencies(
    project_root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    lock = require_mapping(
        load_json(project_root / LOCK_FILE),
        LOCK_FILE,
    )
    standard_dependencies = require_mapping(
        lock.get("externalDependencies"),
        "externalDependencies",
    )
    overrides_path = project_root / OVERRIDES_FILE
    if not overrides_path.is_file():
        effective = deepcopy(standard_dependencies)
        validate_effective_dependencies(effective)
        return effective, []

    overrides = require_mapping(
        load_json(overrides_path),
        OVERRIDES_FILE,
    )
    unknown_root_keys = sorted(
        set(overrides) - {"schemaVersion", "externalDependencies"}
    )
    if unknown_root_keys:
        raise SystemExit(
            f"Invalid {OVERRIDES_FILE}: unknown root fields "
            + ", ".join(unknown_root_keys)
        )
    if overrides.get("schemaVersion") != 1:
        raise SystemExit(f"Invalid {OVERRIDES_FILE}: schemaVersion must be 1")
    override_dependencies = require_mapping(
        overrides.get("externalDependencies"),
        "externalDependencies",
    )
    effective = deepcopy(standard_dependencies)
    active: list[dict[str, Any]] = []
    for dependency_name, record_value in override_dependencies.items():
        if dependency_name not in standard_dependencies:
            raise SystemExit(
                f"Invalid {OVERRIDES_FILE}: unknown dependency "
                f"{dependency_name}"
            )
        record = require_mapping(
            record_value,
            f"{dependency_name} override",
        )
        unknown_record_keys = sorted(
            set(record) - {"reason", "approvedBy", "approvedAt", "values"}
        )
        if unknown_record_keys:
            raise SystemExit(
                f"Invalid {OVERRIDES_FILE}: unknown fields for "
                f"{dependency_name}: "
                + ", ".join(unknown_record_keys)
            )
        reason = record.get("reason")
        approved_by = record.get("approvedBy")
        approved_at = record.get("approvedAt")
        values = record.get("values")
        if not isinstance(reason, str) or not reason.strip():
            raise SystemExit(
                f"Invalid {OVERRIDES_FILE}: "
                f"{dependency_name}.reason is required"
            )
        if not isinstance(approved_by, str) or not approved_by.strip():
            raise SystemExit(
                f"Invalid {OVERRIDES_FILE}: "
                f"{dependency_name}.approvedBy is required"
            )
        try:
            date.fromisoformat(approved_at)
        except (TypeError, ValueError):
            raise SystemExit(
                f"Invalid {OVERRIDES_FILE}: "
                f"{dependency_name}.approvedAt must be an ISO date"
            ) from None
        if not isinstance(values, dict) or not values:
            raise SystemExit(
                f"Invalid {OVERRIDES_FILE}: "
                f"{dependency_name}.values must be a non-empty object"
            )
        standard_dependency = require_mapping(
            standard_dependencies[dependency_name],
            dependency_name,
        )
        validate_override_values(
            standard_dependency,
            values,
            dependency_name,
        )
        effective[dependency_name] = deep_merge(
            standard_dependency,
            values,
        )
        active.append(
            {
                "dependency": dependency_name,
                "reason": reason,
                "approvedBy": approved_by,
                "approvedAt": approved_at,
                "overriddenFields": sorted(values),
            }
        )
    validate_effective_dependencies(effective)
    return effective, active


def validate_effective_dependencies(
    dependencies: dict[str, Any],
) -> None:
    for dependency_name in ("unityMcp", "agentSpriteForge"):
        dependency = require_mapping(
            dependencies.get(dependency_name),
            dependency_name,
        )
        commit = dependency.get("commit")
        if not isinstance(commit, str) or not COMMIT_SHA_RE.fullmatch(commit):
            raise SystemExit(
                f"Invalid effective dependency: "
                f"{dependency_name}.commit must be a pinned SHA"
            )
        distribution = require_mapping(
            dependency.get("distribution"),
            f"{dependency_name}.distribution",
        )
        if (
            distribution.get("bundled") is not False
            or distribution.get("installMode") != "explicit-user-action"
        ):
            raise SystemExit(
                f"Invalid effective dependency: {dependency_name} must remain "
                "unbundled and require explicit user action"
            )

    unity_mcp = require_mapping(dependencies["unityMcp"], "unityMcp")
    expected_package_url = (
        f"{unity_mcp.get('repository')}.git"
        f"?path=/{unity_mcp.get('unityPackagePath')}"
        f"#{unity_mcp.get('commit')}"
    )
    unity_install = require_mapping(
        unity_mcp.get("install"),
        "unityMcp.install",
    )
    if unity_install.get("unityPackageUrl") != expected_package_url:
        raise SystemExit(
            "Invalid effective dependency: unityMcp.install.unityPackageUrl "
            "must pin the effective commit"
        )

    sprite_forge = require_mapping(
        dependencies["agentSpriteForge"],
        "agentSpriteForge",
    )
    if sprite_forge.get("ref") != sprite_forge.get("commit"):
        raise SystemExit(
            "Invalid effective dependency: "
            "agentSpriteForge.ref must equal commit"
        )


def unique_paths(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.expanduser().resolve()
        if resolved not in seen:
            seen.add(resolved)
            result.append(resolved)
    return result


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def git_head(repository: Path) -> str | None:
    if not (repository / ".git").exists():
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def check_unity_mcp(
    project_root: Path,
    dependency: dict[str, Any],
) -> dict[str, Any]:
    install = require_mapping(dependency.get("install"), "unityMcp.install")
    distribution = require_mapping(
        dependency.get("distribution"),
        "unityMcp.distribution",
    )
    expected = install.get("unityPackageUrl")
    package_name = dependency.get("packageName")
    manifest_path = project_root / UNITY_MANIFEST
    manifest = load_json(manifest_path)
    manifest = require_mapping(manifest, UNITY_MANIFEST.as_posix())
    dependencies = require_mapping(
        manifest.get("dependencies"),
        f"{UNITY_MANIFEST.as_posix()}.dependencies",
    )
    actual = dependencies.get(package_name)

    if actual is None:
        status = "MISSING"
        detail = f"{package_name} is not listed in {UNITY_MANIFEST.as_posix()}"
    elif actual != expected:
        status = "VERSION_MISMATCH"
        detail = f"expected {expected}, found {actual}"
    else:
        status = "PASS"
        detail = f"pinned package reference found: {actual}"

    return {
        "name": "Unity MCP",
        "status": status,
        "detail": detail,
        "expected": expected,
        "actual": actual,
        "license": distribution.get("license"),
        "licenseUrl": distribution.get("licenseUrl"),
        "connectionStatus": "NOT CHECKED",
    }


def check_agent_sprite_forge(
    project_root: Path,
    dependency: dict[str, Any],
) -> dict[str, Any]:
    install = require_mapping(
        dependency.get("install"),
        "agentSpriteForge.install",
    )
    distribution = require_mapping(
        dependency.get("distribution"),
        "agentSpriteForge.distribution",
    )
    expected_commit = dependency.get("commit")
    skill_names = install.get("skillNames")
    if not isinstance(skill_names, list) or not all(
        isinstance(name, str) and name for name in skill_names
    ):
        raise SystemExit(
            f"Invalid {LOCK_FILE}: agentSpriteForge.install.skillNames"
        )

    checkout_roots = unique_paths(
        [
            project_root / install["projectCheckoutPath"],
            codex_home() / install["userCheckoutPath"],
        ]
    )
    skill_roots = unique_paths(
        [
            project_root / ".codex/skills",
            codex_home() / "skills",
        ]
    )
    checkout_heads = [
        {"path": str(path), "commit": git_head(path)}
        for path in checkout_roots
        if path.exists()
    ]
    pinned_checkout = next(
        (
            item
            for item in checkout_heads
            if item["commit"] == expected_commit
        ),
        None,
    )
    installed_skills = {
        name: next(
            (
                str(root / name)
                for root in skill_roots
                if (root / name / "SKILL.md").is_file()
            ),
            None,
        )
        for name in skill_names
    }
    missing_skills = [
        name for name, path in installed_skills.items() if path is None
    ]

    if not checkout_heads:
        status = "MISSING"
        detail = "no managed agent-sprite-forge checkout was found"
    elif pinned_checkout is None:
        status = "VERSION_MISMATCH"
        found = ", ".join(
            item["commit"] or "not-a-git-checkout" for item in checkout_heads
        )
        detail = f"expected checkout {expected_commit}, found {found}"
    elif missing_skills:
        status = "MISSING"
        detail = f"missing Codex Skills: {', '.join(missing_skills)}"
    else:
        status = "PASS"
        detail = f"pinned checkout and Skills found at {pinned_checkout['path']}"

    return {
        "name": "agent-sprite-forge",
        "status": status,
        "detail": detail,
        "expectedCommit": expected_commit,
        "checkouts": checkout_heads,
        "skills": installed_skills,
        "license": distribution.get("license"),
        "licenseUrl": distribution.get("licenseUrl"),
    }


def install_instructions(
    project_root: Path,
    unity_mcp: dict[str, Any],
    sprite_forge: dict[str, Any],
) -> list[str]:
    sprite_install = sprite_forge["install"]
    project_checkout = project_root / sprite_install["projectCheckoutPath"]
    skill_root = project_root / ".codex/skills"
    repository = sprite_forge["repository"]
    commit = sprite_forge["commit"]
    skill_names = sprite_install["skillNames"]
    copy_commands = [
        f'cp -R "{project_checkout / "skills" / name}" "{skill_root / name}"'
        for name in skill_names
    ]
    return [
        "Review each upstream license at the fixed URL before installation.",
        (
            "Unity MCP: in Unity Package Manager, choose Add package from git URL "
            f"and enter {unity_mcp['install']['unityPackageUrl']}"
        ),
        (
            "Unity MCP: open Window > MCP for Unity, start the server, configure "
            "the Codex client, then confirm the Editor reports Connected."
        ),
        f'mkdir -p "{project_checkout.parent}" "{skill_root}"',
        f'git clone "{repository}" "{project_checkout}"',
        f'git -C "{project_checkout}" checkout --detach "{commit}"',
        (
            f'python3 -m pip install -r "{project_checkout / "requirements.txt"}"'
        ),
        *copy_commands,
        "Restart Codex after installing or updating external Skills.",
    ]


def build_report(project_root: Path) -> dict[str, Any]:
    dependencies, active_overrides = load_effective_dependencies(project_root)
    unity_mcp = require_mapping(dependencies.get("unityMcp"), "unityMcp")
    sprite_forge = require_mapping(
        dependencies.get("agentSpriteForge"),
        "agentSpriteForge",
    )
    checks = [
        check_unity_mcp(project_root, unity_mcp),
        check_agent_sprite_forge(project_root, sprite_forge),
    ]
    return {
        "schemaVersion": 1,
        "projectRoot": str(project_root),
        "result": (
            "PASS"
            if all(check["status"] == "PASS" for check in checks)
            else "ACTION REQUIRED"
        ),
        "checks": checks,
        "standardLock": LOCK_FILE,
        "projectOverrides": OVERRIDES_FILE,
        "activeOverrides": active_overrides,
        "instructions": install_instructions(
            project_root,
            unity_mcp,
            sprite_forge,
        ),
        "notes": [
            "External dependencies are not bundled by this harness.",
            (
                "Standard pins come from the harness-managed harness.lock.json; "
                "approved project differences come from harness.overrides.json."
            ),
            "This static check does not prove an active Unity MCP connection.",
        ],
    }


def print_text_report(report: dict[str, Any]) -> None:
    print(f"External dependency check: {report['result']}")
    for check in report["checks"]:
        print(f"- {check['name']}: {check['status']} - {check['detail']}")
    if report["result"] != "PASS":
        print("\nInstallation steps:")
        for index, instruction in enumerate(report["instructions"], start=1):
            print(f"{index}. {instruction}")
    print("\nNotes:")
    for note in report["notes"]:
        print(f"- {note}")


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    report = build_report(project_root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text_report(report)
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
