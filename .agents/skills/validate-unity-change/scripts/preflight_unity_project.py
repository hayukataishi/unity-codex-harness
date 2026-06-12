#!/usr/bin/env python3
"""Run deterministic static preflight checks on a Unity project."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from pathlib import Path


GUID_RE = re.compile(r"^guid:\s*([0-9a-fA-F]{32})\s*$", re.MULTILINE)
MISSING_SCRIPT_RE = re.compile(r"m_Script:\s*\{fileID:\s*0(?:,|\})")
SERIALIZED_EXTENSIONS = {
    ".anim",
    ".asset",
    ".controller",
    ".mat",
    ".overridecontroller",
    ".playable",
    ".prefab",
    ".unity",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root",
        default=None,
        help="Unity project root; defaults to UNITY_PROJECT_ROOT",
    )
    parser.add_argument("--output", help="Optional JSON output path")
    return parser.parse_args()


def is_hidden_relative(path: Path, root: Path) -> bool:
    return any(part.startswith(".") for part in path.relative_to(root).parts)


def main() -> int:
    args = parse_args()
    root_value = args.project_root or os.environ.get("UNITY_PROJECT_ROOT")
    if not root_value:
        raise SystemExit("Provide --project-root or set UNITY_PROJECT_ROOT")

    root = Path(root_value).expanduser().resolve()
    assets = root / "Assets"
    required = [
        assets,
        root / "Packages",
        root / "Packages" / "manifest.json",
        root / "ProjectSettings",
        root / "ProjectSettings" / "ProjectVersion.txt",
    ]
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    for path in required:
        if not path.exists():
            errors.append({"code": "MISSING_REQUIRED_PATH", "path": str(path)})

    if not assets.is_dir():
        report = {
            "projectRoot": str(root),
            "status": "FAIL",
            "errors": errors,
            "warnings": warnings,
            "summary": {"errors": len(errors), "warnings": len(warnings)},
        }
        return write_report(report, args.output, root)

    meta_guids: dict[str, list[str]] = defaultdict(list)
    checked_assets = 0
    checked_meta = 0

    for path in assets.rglob("*"):
        if is_hidden_relative(path, assets):
            continue
        relative = path.relative_to(root).as_posix()

        if path.name.endswith(".meta"):
            if not path.is_file():
                continue
            checked_meta += 1
            target = Path(str(path)[:-5])
            if not target.exists():
                errors.append({"code": "ORPHAN_META", "path": relative})
            text = path.read_text(encoding="utf-8", errors="replace")
            match = GUID_RE.search(text)
            if not match:
                errors.append({"code": "MISSING_OR_INVALID_GUID", "path": relative})
            else:
                meta_guids[match.group(1).lower()].append(relative)
            continue

        checked_assets += 1
        meta = Path(str(path) + ".meta")
        if not meta.is_file():
            errors.append({"code": "MISSING_META", "path": relative})

        if path.is_file() and path.suffix.lower() in SERIALIZED_EXTENSIONS:
            text = path.read_text(encoding="utf-8", errors="replace")
            if MISSING_SCRIPT_RE.search(text):
                errors.append({"code": "MISSING_SCRIPT_MARKER", "path": relative})

    for guid, paths in sorted(meta_guids.items()):
        if len(paths) > 1:
            errors.append(
                {
                    "code": "DUPLICATE_GUID",
                    "guid": guid,
                    "paths": ", ".join(paths),
                }
            )

    version_file = root / "ProjectSettings" / "ProjectVersion.txt"
    unity_version = "NOT_FOUND"
    if version_file.is_file():
        for line in version_file.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines():
            if line.startswith("m_EditorVersion:"):
                unity_version = line.split(":", 1)[1].strip()
                break
        if unity_version == "NOT_FOUND":
            warnings.append(
                {
                    "code": "UNITY_VERSION_NOT_PARSED",
                    "path": version_file.relative_to(root).as_posix(),
                }
            )

    report = {
        "projectRoot": str(root),
        "unityVersion": unity_version,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "checkedAssetsAndDirectories": checked_assets,
            "checkedMetaFiles": checked_meta,
            "errors": len(errors),
            "warnings": len(warnings),
        },
    }
    return write_report(report, args.output, root)


def write_report(report: dict, output: str | None, project_root: Path) -> int:
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if output:
        output_path = Path(output).expanduser()
        if not output_path.is_absolute():
            output_path = project_root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
