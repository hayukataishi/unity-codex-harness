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
from datetime import datetime, timezone
from pathlib import Path


COMPILER_ERROR_RE = re.compile(r"\berror CS\d{4}\b")
TIMEOUT_EXIT_CODE = 124
EXECUTION_ERROR_EXIT_CODE = 127
BLOCKED_LOG_MARKERS = (
    (
        "attempt to write a readonly database",
        "Unity could not write its licensing or support database",
    ),
    (
        "Licensing initialization failed",
        "Unity licensing initialization failed",
    ),
    (
        "No valid Unity Editor license found",
        "No valid Unity Editor license was available",
    ),
    (
        "'com.unity.editor.headless' was not found",
        "The Unity headless license entitlement was unavailable",
    ),
    (
        "Unsupported protocol version",
        "Unity Editor and the Licensing Client use incompatible protocols",
    ),
)


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


def read_log(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def infrastructure_blocker(exit_code: int, log_path: Path | None) -> str | None:
    if exit_code == TIMEOUT_EXIT_CODE:
        return "Unity command timed out"
    if exit_code == EXECUTION_ERROR_EXIT_CODE:
        return "Unity process could not be started"
    log = read_log(log_path)
    for marker, reason in BLOCKED_LOG_MARKERS:
        if marker in log:
            return reason
    return None


def parse_nunit_result(
    path: Path,
    exit_code: int,
    log_path: Path | None = None,
) -> tuple[str, str]:
    if not path.is_file():
        blocker = infrastructure_blocker(exit_code, log_path)
        result = "BLOCKED" if blocker else "FAIL"
        reason = blocker or f"Unity exited {exit_code}"
        return result, f"{reason}; test result XML was not created"
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        return "FAIL", f"Invalid test result XML: {error}"

    try:
        total = int(root.attrib.get("total", root.attrib.get("testcasecount", "0")))
        failed = int(root.attrib.get("failed", "0"))
    except ValueError as error:
        return "FAIL", f"Invalid numeric test result attribute: {error}"
    result = root.attrib.get("result", "").lower()
    if exit_code == 0 and total > 0 and failed == 0 and result in {"passed", "success"}:
        return "PASS", f"{total} tests passed"
    return "FAIL", f"exit={exit_code}, total={total}, failed={failed}, result={result}"


def parse_asset_validation_result(
    path: Path,
    exit_code: int,
    log_path: Path | None = None,
) -> tuple[str, str]:
    if not path.is_file():
        blocker = infrastructure_blocker(exit_code, log_path)
        result = "BLOCKED" if blocker else "FAIL"
        reason = blocker or f"Unity exited {exit_code}"
        return (
            result,
            f"{reason}; asset validation JSON was not created",
        )
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        return "FAIL", f"Invalid asset validation JSON: {error}"

    status = report.get("status", "FAIL")
    summary = report.get("summary", {})
    errors = summary.get("errors", len(report.get("errors", [])))
    warnings = summary.get("warnings", len(report.get("warnings", [])))
    if exit_code == 0 and status == "PASS" and errors == 0:
        return "PASS", f"errors=0, warnings={warnings}"
    return (
        "FAIL",
        f"exit={exit_code}, status={status}, errors={errors}, warnings={warnings}",
    )


def parse_compile_result(
    test_result_path: Path,
    log_path: Path,
    exit_code: int,
) -> tuple[str, str]:
    log = read_log(log_path)
    if COMPILER_ERROR_RE.search(log):
        return "FAIL", "C# compiler errors detected"
    if test_result_path.is_file():
        try:
            root = ET.parse(test_result_path).getroot()
        except ET.ParseError as error:
            return "FAIL", f"Compile completion artifact is invalid: {error}"
        if root.tag != "test-run":
            return "FAIL", "Compile completion artifact is not an NUnit test run"
        return "PASS", "Valid Unity test result generated with no C# compiler errors"
    blocker = infrastructure_blocker(exit_code, log_path)
    if blocker:
        return "BLOCKED", f"{blocker}; compilation completion was not proven"
    return (
        "FAIL",
        f"Unity exited {exit_code}; compilation completion was not proven",
    )


def add_evidence(
    check: dict[str, str],
    candidates: list[tuple[Path, str]],
) -> dict[str, str]:
    for path, relative in candidates:
        if path.is_file():
            check["evidence"] = relative
            break
    return check


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
    except OSError:
        return 127


def write_unity_lockfile_diagnostic(
    project_root: Path,
    run_relative: str,
) -> str | None:
    lockfile = project_root / "Temp" / "UnityLockfile"
    if not lockfile.exists():
        return None
    try:
        stat = lockfile.stat()
    except OSError:
        return None
    diagnostic_relative = f"{run_relative}/Logs/UnityLockfile.json"
    diagnostic_path = project_root / diagnostic_relative
    diagnostic = {
        "status": "BLOCKED",
        "reason": (
            "Temp/UnityLockfile existed before Unity batchmode validation "
            "started"
        ),
        "lockfile": "Temp/UnityLockfile",
        "sizeBytes": stat.st_size,
        "modifiedAtUtc": datetime.fromtimestamp(
            stat.st_mtime,
            timezone.utc,
        ).isoformat().replace("+00:00", "Z"),
    }
    diagnostic_path.write_text(
        json.dumps(diagnostic, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return diagnostic_relative


def finalize_and_verify(
    scripts_dir: Path,
    project_root: Path,
    run_dir: Path,
    run_relative: str,
    results_relative: str,
) -> int:
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
    if not (run_dir / "RunManifest.sha256").is_file():
        subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "finalize_validation_run.py"),
                "--project-root",
                str(project_root),
                "--run-dir",
                run_relative,
                "--blocked-reason",
                f"Validation finalizer failed with exit code {completed.returncode}",
            ],
            check=False,
        )
    verify_command = [
        sys.executable,
        str(scripts_dir / "verify_validation_run.py"),
        "--project-root",
        str(project_root),
        "--run-dir",
        run_relative,
    ]
    verified = subprocess.run(verify_command, check=False)
    print(run_relative)
    return completed.returncode if verified.returncode == 0 else 1


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
    parser.add_argument(
        "--asset-config",
        default="ProjectSettings/UnityCodexHarnessAssetValidation.json",
    )
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
    results_relative = f"{run_relative}/Logs/ValidationResults.json"
    results_path = project_root / results_relative

    original_excepthook = sys.excepthook

    def finalize_uncaught_exception(
        exception_type: type[BaseException],
        exception: BaseException,
        traceback: object,
    ) -> None:
        if not (run_dir / "RunManifest.sha256").exists():
            emergency_checks = [
                *checks,
                {
                    "name": "Validation runner",
                    "result": "FAIL",
                    "notes": (
                        f"Unhandled {exception_type.__name__}: {exception}"
                    ),
                },
            ]
            try:
                results_path.write_text(
                    json.dumps(
                        {
                            "schemaVersion": 1,
                            "commands": commands,
                            "checks": emergency_checks,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                subprocess.run(
                    [
                        sys.executable,
                        str(scripts_dir / "finalize_validation_run.py"),
                        "--project-root",
                        str(project_root),
                        "--run-dir",
                        run_relative,
                        "--results",
                        results_relative,
                    ],
                    check=False,
                )
            except Exception:
                pass
        original_excepthook(exception_type, exception, traceback)

    sys.excepthook = finalize_uncaught_exception

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
    preflight_path = project_root / preflight_relative
    checks.append(
        add_evidence(
            {
                "name": "Static preflight",
                "result": "PASS" if preflight_exit == 0 else "FAIL",
                "notes": f"exit={preflight_exit}",
            },
            [(preflight_path, preflight_relative)],
        )
    )

    lockfile_relative = write_unity_lockfile_diagnostic(
        project_root,
        run_relative,
    )
    if lockfile_relative is not None:
        lockfile_path = project_root / lockfile_relative
        lock_notes = (
            "Same-project Unity lock detected before batchmode validation. "
            "Close the active Editor, or confirm the lock is stale before "
            "removing it and rerunning."
        )
        checks.append(
            add_evidence(
                {
                    "name": "Unity project lock",
                    "result": "BLOCKED",
                    "notes": lock_notes,
                },
                [(lockfile_path, lockfile_relative)],
            )
        )
        for check_name in ("Compile", "EditMode", "PlayMode", "Asset validation"):
            checks.append(
                add_evidence(
                    {
                        "name": check_name,
                        "result": "BLOCKED",
                        "notes": lock_notes,
                    },
                    [(lockfile_path, lockfile_relative)],
                )
            )
        results_path.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "commands": commands,
                    "checks": checks,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return finalize_and_verify(
            scripts_dir,
            project_root,
            run_dir,
            run_relative,
            results_relative,
        )

    edit_result_relative = f"{run_relative}/Tests/EditMode.xml"
    edit_log_relative = f"{run_relative}/Logs/EditMode.log"
    edit_result_path = project_root / edit_result_relative
    edit_log_path = project_root / edit_log_relative
    edit_command = [
        str(unity_editor),
        "-batchmode",
        "-nographics",
        "-projectPath",
        str(project_root),
        "-runTests",
        "-testPlatform",
        "EditMode",
        "-testResults",
        str(edit_result_path),
        "-logFile",
        str(edit_log_path),
    ]
    edit_exit = run_command(edit_command, args.timeout_seconds)
    commands.append(
        {
            "name": "EditMode",
            "command": display_command(edit_command, unity_editor, project_root),
            "exitCode": edit_exit,
        }
    )
    edit_result, edit_notes = parse_nunit_result(
        edit_result_path,
        edit_exit,
        edit_log_path,
    )
    compile_result, compile_notes = parse_compile_result(
        edit_result_path,
        edit_log_path,
        edit_exit,
    )
    checks.append(
        add_evidence(
            {
                "name": "Compile",
                "result": compile_result,
                "notes": compile_notes,
            },
            [(edit_log_path, edit_log_relative)],
        )
    )
    checks.append(
        add_evidence(
            {
                "name": "EditMode",
                "result": edit_result,
                "notes": edit_notes,
            },
            [
                (edit_result_path, edit_result_relative),
                (edit_log_path, edit_log_relative),
            ],
        )
    )

    if edit_result == "BLOCKED" or compile_result == "BLOCKED":
        skipped_notes = (
            "Skipped because EditMode infrastructure was blocked: "
            f"{edit_notes}"
        )
        for check_name in ("PlayMode", "Asset validation"):
            checks.append(
                add_evidence(
                    {
                        "name": check_name,
                        "result": "BLOCKED",
                        "notes": skipped_notes,
                    },
                    [(edit_log_path, edit_log_relative)],
                )
            )
    else:
        play_result_relative = f"{run_relative}/Tests/PlayMode.xml"
        play_log_relative = f"{run_relative}/Logs/PlayMode.log"
        play_result_path = project_root / play_result_relative
        play_log_path = project_root / play_log_relative
        play_command = [
            str(unity_editor),
            "-batchmode",
            "-nographics",
            "-projectPath",
            str(project_root),
            "-runTests",
            "-testPlatform",
            "PlayMode",
            "-testResults",
            str(play_result_path),
            "-logFile",
            str(play_log_path),
        ]
        play_exit = run_command(play_command, args.timeout_seconds)
        commands.append(
            {
                "name": "PlayMode",
                "command": display_command(
                    play_command,
                    unity_editor,
                    project_root,
                ),
                "exitCode": play_exit,
            }
        )
        play_result, play_notes = parse_nunit_result(
            play_result_path,
            play_exit,
            play_log_path,
        )
        checks.append(
            add_evidence(
                {
                    "name": "PlayMode",
                    "result": play_result,
                    "notes": play_notes,
                },
                [
                    (play_result_path, play_result_relative),
                    (play_log_path, play_log_relative),
                ],
            )
        )

        asset_result_relative = f"{run_relative}/Logs/AssetValidation.json"
        asset_log_relative = f"{run_relative}/Logs/AssetValidation.log"
        asset_result_path = project_root / asset_result_relative
        asset_log_path = project_root / asset_log_relative
        asset_command = [
            str(unity_editor),
            "-batchmode",
            "-nographics",
            "-projectPath",
            str(project_root),
            "-executeMethod",
            "UnityCodexHarness.Validation.Editor.AssetValidationBatch.Run",
            "-harnessAssetValidationConfig",
            args.asset_config,
            "-harnessAssetValidationOutput",
            str(asset_result_path),
            "-logFile",
            str(asset_log_path),
        ]
        asset_exit = run_command(asset_command, args.timeout_seconds)
        commands.append(
            {
                "name": "Asset validation",
                "command": display_command(
                    asset_command,
                    unity_editor,
                    project_root,
                ),
                "exitCode": asset_exit,
            }
        )
        asset_result, asset_notes = parse_asset_validation_result(
            asset_result_path,
            asset_exit,
            asset_log_path,
        )
        checks.append(
            add_evidence(
                {
                    "name": "Asset validation",
                    "result": asset_result,
                    "notes": asset_notes,
                },
                [
                    (asset_result_path, asset_result_relative),
                    (asset_log_path, asset_log_relative),
                ],
            )
        )

    results_path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "commands": commands,
                "checks": checks,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return finalize_and_verify(
        scripts_dir,
        project_root,
        run_dir,
        run_relative,
        results_relative,
    )


if __name__ == "__main__":
    raise SystemExit(main())
