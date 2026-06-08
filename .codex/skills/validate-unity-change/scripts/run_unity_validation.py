#!/usr/bin/env python3
"""Run deterministic Unity EditMode and PlayMode validation."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


COMPILER_ERROR_RE = re.compile(r"\berror CS\d{4}\b")


def unity_version(project_root: Path) -> str:
    version_file = project_root / "ProjectSettings" / "ProjectVersion.txt"
    for line in version_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("m_EditorVersion:"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError("Could not parse m_EditorVersion")


def resolve_unity_editor(project_root: Path, provided: str | None) -> Path:
    if provided:
        candidate = Path(provided).expanduser()
    elif os.environ.get("UNITY_EDITOR_PATH"):
        candidate = Path(os.environ["UNITY_EDITOR_PATH"]).expanduser()
    elif sys.platform == "darwin":
        version = unity_version(project_root)
        candidate = Path(
            f"/Applications/Unity/Hub/Editor/{version}/Unity.app/Contents/MacOS/Unity"
        )
    else:
        raise RuntimeError(
            "Provide --unity-editor or set UNITY_EDITOR_PATH on this platform"
        )
    candidate = candidate.resolve()
    if not candidate.is_file():
        raise RuntimeError(f"Unity Editor executable not found: {candidate}")
    return candidate


def parse_nunit_result(path: Path, exit_code: int) -> tuple[str, str]:
    if not path.is_file():
        return "FAIL", f"Unity exited {exit_code}; test result XML was not created"
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        return "FAIL", f"Invalid test result XML: {error}"

    total = int(root.attrib.get("total", root.attrib.get("testcasecount", "0")))
    failed = int(root.attrib.get("failed", "0"))
    result = root.attrib.get("result", "").lower()
    if exit_code == 0 and total > 0 and failed == 0 and result in {"passed", "success"}:
        return "PASS", f"{total} tests passed"
    return "FAIL", f"exit={exit_code}, total={total}, failed={failed}, result={result}"


def display_command(command: list[str], unity_editor: Path, project_root: Path) -> str:
    scripts_dir = Path(__file__).resolve().parent
    python_paths = {
        sys.executable,
        str(Path(sys.executable).resolve()),
    }
    rendered = []
    for value in command:
        value = value.replace(str(unity_editor), "<UNITY_EDITOR>")
        value = value.replace(str(project_root), "<UNITY_PROJECT_ROOT>")
        value = value.replace(str(scripts_dir), "<HARNESS_SCRIPTS>")
        for python_path in python_paths:
            value = value.replace(python_path, "<PYTHON>")
        rendered.append(value)
    return " ".join(rendered)


def run_command(command: list[str], timeout: int) -> int:
    try:
        completed = subprocess.run(command, check=False, timeout=timeout)
        return completed.returncode
    except subprocess.TimeoutExpired:
        return 124


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--unity-editor")
    parser.add_argument("--design-id", action="append", default=[])
    parser.add_argument(
        "--ac-id",
        action="append",
        default=[],
        help="Automated AC validated by the complete check set; repeat as needed",
    )
    parser.add_argument("--platform", default="Editor")
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    scripts_dir = Path(__file__).resolve().parent
    unity_editor = resolve_unity_editor(project_root, args.unity_editor)

    create_command = [
        sys.executable,
        str(scripts_dir / "create_validation_run.py"),
        "--project-root",
        str(project_root),
        "--platform",
        args.platform,
    ]
    for design_id in args.design_id:
        create_command.extend(["--design-id", design_id])
    for ac_id in args.ac_id:
        create_command.extend(["--ac-id", ac_id])
    run_relative = subprocess.run(
        create_command,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    run_dir = project_root / run_relative

    checks: list[dict[str, str]] = []
    commands: list[dict[str, object]] = []

    preflight_relative = f"{run_relative}/Logs/Preflight.json"
    preflight_command = [
        sys.executable,
        str(scripts_dir / "preflight_unity_project.py"),
        "--project-root",
        str(project_root),
        "--output",
        preflight_relative,
    ]
    preflight_exit = run_command(preflight_command, args.timeout_seconds)
    commands.append(
        {
            "name": "Preflight",
            "command": display_command(preflight_command, unity_editor, project_root),
            "exitCode": preflight_exit,
        }
    )
    checks.append(
        {
            "name": "Static preflight",
            "result": "PASS" if preflight_exit == 0 else "FAIL",
            "evidence": f"{run_relative}/Logs/Preflight.json",
            "notes": f"exit={preflight_exit}",
        }
    )

    test_data: list[tuple[str, str]] = [
        ("EditMode", "EditMode"),
        ("PlayMode", "PlayMode"),
    ]
    compiler_error = False
    for check_name, platform in test_data:
        result_relative = f"{run_relative}/Tests/{check_name}.xml"
        log_relative = f"{run_relative}/Logs/{check_name}.log"
        command = [
            str(unity_editor),
            "-batchmode",
            "-nographics",
            "-projectPath",
            str(project_root),
            "-runTests",
            "-testPlatform",
            platform,
            "-testResults",
            str(project_root / result_relative),
            "-logFile",
            str(project_root / log_relative),
        ]
        exit_code = run_command(command, args.timeout_seconds)
        commands.append(
            {
                "name": check_name,
                "command": display_command(command, unity_editor, project_root),
                "exitCode": exit_code,
            }
        )
        result, notes = parse_nunit_result(project_root / result_relative, exit_code)
        checks.append(
            {
                "name": check_name,
                "result": result,
                "evidence": result_relative,
                "notes": notes,
            }
        )
        log_path = project_root / log_relative
        if log_path.is_file() and COMPILER_ERROR_RE.search(
            log_path.read_text(encoding="utf-8", errors="replace")
        ):
            compiler_error = True

    checks.insert(
        1,
        {
            "name": "Compile",
            "result": "FAIL" if compiler_error else "PASS",
            "evidence": f"{run_relative}/Logs/EditMode.log",
            "notes": "C# compiler errors detected" if compiler_error else "No C# compiler errors",
        },
    )

    results_relative = f"{run_relative}/Logs/ValidationResults.json"
    results_path = project_root / results_relative
    results_path.write_text(
        json.dumps(
            {
                "commands": commands,
                "checks": checks,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    finalize_command = [
        sys.executable,
        str(scripts_dir / "finalize_validation_run.py"),
        "--project-root",
        str(project_root),
        "--run-dir",
        run_relative,
        "--results",
        results_relative,
    ]
    completed = subprocess.run(finalize_command, check=False)
    print(run_relative)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
