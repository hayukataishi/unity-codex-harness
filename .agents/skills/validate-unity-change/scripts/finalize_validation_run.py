#!/usr/bin/env python3
"""Finalize a Unity validation run from machine-readable check results."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RESULT_PRECEDENCE = {
    "PASS": 0,
    "NOT RUN": 1,
    "BLOCKED": 2,
    "FAIL": 3,
}
VALID_RESULTS = set(RESULT_PRECEDENCE)
MANIFEST_SCHEMA_VERSION = 2
RESULTS_SCHEMA_VERSION = 1
MANIFEST_NAME = "RunManifest.json"
MANIFEST_HASH_NAME = "RunManifest.sha256"


def aggregate_result(results: list[str]) -> str:
    normalized = [result if result in RESULT_PRECEDENCE else "FAIL" for result in results]
    if not normalized:
        return "NOT RUN"
    return max(normalized, key=RESULT_PRECEDENCE.__getitem__)


def artifact_records(run_dir: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file() or path.name in {MANIFEST_NAME, MANIFEST_HASH_NAME}:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        records.append(
            {
                "path": path.relative_to(run_dir.parent.parent.parent).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": digest,
            }
        )
    return records


def atomic_write_text(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid {label}: {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Invalid {label}: root must be an object")
    return value


def resolve_within(
    project_root: Path,
    container: Path,
    value: str,
    label: str,
) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = project_root / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(container.resolve())
    except ValueError as error:
        raise ValueError(f"{label} must be inside {container}") from error
    return candidate


def validate_checks(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("Validation results must contain at least one check")
    checks: list[dict[str, Any]] = []
    for index, check in enumerate(value):
        if not isinstance(check, dict):
            raise ValueError(f"checks[{index}] must be an object")
        name = check.get("name")
        result = check.get("result")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"checks[{index}].name must be a non-empty string")
        if result not in VALID_RESULTS:
            raise ValueError(
                f"checks[{index}].result must be one of "
                f"{', '.join(sorted(VALID_RESULTS))}"
            )
        checks.append(dict(check))
    return checks


def validate_commands(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("commands must be an array")
    commands: list[dict[str, Any]] = []
    for index, command in enumerate(value):
        if not isinstance(command, dict):
            raise ValueError(f"commands[{index}] must be an object")
        name = command.get("name")
        rendered = command.get("command")
        exit_code = command.get("exitCode")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"commands[{index}].name must be a non-empty string")
        if not isinstance(rendered, str) or not rendered.strip():
            raise ValueError(
                f"commands[{index}].command must be a non-empty string"
            )
        if not isinstance(exit_code, int):
            raise ValueError(f"commands[{index}].exitCode must be an integer")
        commands.append(dict(command))
    return commands


def acceptance_results(
    declared_ids: list[str],
    provided: Any,
    default_result: str,
    checks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    evidence = [
        check.get("evidence", "")
        for check in checks
        if isinstance(check.get("evidence"), str) and check.get("evidence")
    ]
    provided_by_id: dict[str, dict[str, Any]] = {}
    if provided is not None:
        if not isinstance(provided, list):
            raise ValueError("acceptanceCriteria must be an array")
        for index, criterion in enumerate(provided):
            if not isinstance(criterion, dict):
                raise ValueError(f"acceptanceCriteria[{index}] must be an object")
            criterion_id = criterion.get("id")
            result = criterion.get("result")
            if criterion_id not in declared_ids:
                raise ValueError(
                    f"acceptanceCriteria[{index}].id was not declared by the run"
                )
            if result not in VALID_RESULTS:
                raise ValueError(
                    f"acceptanceCriteria[{index}].result must be one of "
                    f"{', '.join(sorted(VALID_RESULTS))}"
                )
            if criterion_id in provided_by_id:
                raise ValueError(
                    f"acceptanceCriteria contains duplicate id: {criterion_id}"
                )
            provided_by_id[criterion_id] = dict(criterion)

    acceptance: list[dict[str, Any]] = []
    for criterion_id in declared_ids:
        criterion = provided_by_id.get(criterion_id)
        if criterion is None:
            criterion = {
                "id": criterion_id,
                "result": default_result,
                "evidence": evidence,
            }
        else:
            criterion.setdefault("evidence", evidence)
        acceptance.append(criterion)
    return acceptance


def render_cell(value: Any) -> str:
    return str(value or "").replace("\n", " ").replace("|", "\\|")


def finalize_run(
    project_root: Path,
    run_dir: Path,
    results: dict[str, Any],
) -> str:
    project_root = project_root.resolve()
    runs_root = project_root / "Artifacts" / "ValidationRuns"
    run_dir = resolve_within(
        project_root,
        runs_root,
        str(run_dir),
        "run directory",
    )
    manifest_path = run_dir / MANIFEST_NAME
    manifest = load_json_object(manifest_path, "RunManifest.json")

    manifest_schema = manifest.get("schemaVersion", 1)
    if manifest_schema not in {1, MANIFEST_SCHEMA_VERSION}:
        raise ValueError(
            f"RunManifest.json schemaVersion must be 1 or "
            f"{MANIFEST_SCHEMA_VERSION}"
        )
    if manifest.get("state") == "COMPLETED" or manifest.get("completedAtUtc"):
        raise ValueError(f"Validation run is already completed: {manifest['runId']}")
    if (run_dir / MANIFEST_HASH_NAME).exists():
        raise ValueError(f"Validation run already has an integrity hash: {manifest['runId']}")
    if manifest.get("runId") != run_dir.name:
        raise ValueError("RunManifest.json runId does not match its directory")

    results_schema = results.get("schemaVersion", RESULTS_SCHEMA_VERSION)
    if results_schema != RESULTS_SCHEMA_VERSION:
        raise ValueError(
            f"Validation results schemaVersion must be {RESULTS_SCHEMA_VERSION}"
        )

    checks = validate_checks(results.get("checks"))
    commands = validate_commands(
        results.get("commands", manifest.get("commands", []))
    )
    check_result = aggregate_result(
        [str(check.get("result", "FAIL")) for check in checks]
    )
    declared_ids = manifest.get("acceptanceCriterionIds", [])
    if not isinstance(declared_ids, list) or not all(
        isinstance(value, str) for value in declared_ids
    ):
        raise ValueError("RunManifest.json acceptanceCriterionIds must be an array")
    if len(declared_ids) != len(set(declared_ids)):
        raise ValueError("RunManifest.json acceptanceCriterionIds contains duplicates")
    acceptance = acceptance_results(
        declared_ids,
        results.get("acceptanceCriteria"),
        check_result,
        checks,
    )
    overall = aggregate_result(
        [check_result] + [criterion["result"] for criterion in acceptance]
    )

    completed = datetime.now(timezone.utc)
    try:
        started = datetime.fromisoformat(
            str(manifest["startedAtUtc"]).replace("Z", "+00:00")
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("RunManifest.json has an invalid startedAtUtc") from error

    manifest.update(
        {
            "schemaVersion": MANIFEST_SCHEMA_VERSION,
            "state": "COMPLETED",
            "completedAtUtc": completed.isoformat().replace("+00:00", "Z"),
            "durationSeconds": max(
                0.0,
                round((completed - started).total_seconds(), 3),
            ),
            "result": overall,
            "commands": commands,
            "checks": checks,
            "acceptanceCriteria": acceptance,
        }
    )

    report_lines = [
        "# Validation Report",
        "",
        f"- Run ID: `{manifest['runId']}`",
        f"- Unity: `{manifest['unityVersion']}`",
        f"- Platform: `{manifest['targetPlatform']}`",
        "- State: `COMPLETED`",
        f"- Result: `{overall}`",
        f"- Duration: `{manifest['durationSeconds']}s`",
        "",
        "## Acceptance Criteria",
        "",
        "| AC ID | Result | Evidence / notes |",
        "|---|---|---|",
    ]
    if acceptance:
        for criterion in acceptance:
            criterion_evidence = criterion.get("evidence", [])
            if isinstance(criterion_evidence, list):
                evidence_text = "; ".join(
                    render_cell(value) for value in criterion_evidence if value
                )
            else:
                evidence_text = render_cell(criterion_evidence)
            report_lines.append(
                f"| `{render_cell(criterion['id'])}` | "
                f"`{criterion['result']}` | "
                f"{evidence_text or render_cell(criterion.get('notes')) or 'No evidence recorded'} |"
            )
    else:
        report_lines.append("| `NOT RECORDED` | `NOT RUN` | No AC ID supplied |")

    report_lines.extend(
        [
            "",
            "## Checks",
            "",
            "| Check | Result | Evidence / notes |",
            "|---|---|---|",
        ]
    )
    for check in checks:
        report_lines.append(
            f"| {render_cell(check.get('name', 'Unknown'))} | "
            f"`{check.get('result', 'FAIL')}` | "
            f"{render_cell(check.get('evidence') or check.get('notes'))} |"
        )

    report_lines.extend(["", "## Risks and blockers", ""])
    blockers = [
        check
        for check in checks
        if check.get("result") in {"FAIL", "BLOCKED", "NOT RUN"}
    ]
    blockers.extend(
        criterion
        for criterion in acceptance
        if criterion.get("result") in {"FAIL", "BLOCKED", "NOT RUN"}
    )
    if blockers:
        report_lines.extend(
            f"- {render_cell(item.get('name') or item.get('id') or 'Unknown')}: "
            f"{render_cell(item.get('notes') or item.get('result'))}"
            for item in blockers
        )
    else:
        report_lines.append("- None recorded.")

    atomic_write_text(run_dir / "Report.md", "\n".join(report_lines) + "\n")
    manifest["artifactFiles"] = artifact_records(run_dir)
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    atomic_write_text(manifest_path, manifest_text)
    digest = hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()
    atomic_write_text(
        run_dir / MANIFEST_HASH_NAME,
        f"{digest}  {MANIFEST_NAME}\n",
    )
    return overall


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--run-dir", required=True)
    completion = parser.add_mutually_exclusive_group(required=True)
    completion.add_argument("--results")
    completion.add_argument(
        "--blocked-reason",
        help="Close an unfinished run as BLOCKED with the supplied reason",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    run_dir = resolve_within(
        project_root,
        project_root / "Artifacts" / "ValidationRuns",
        args.run_dir,
        "run directory",
    )
    if args.results:
        results_path = resolve_within(
            project_root,
            run_dir,
            args.results,
            "results file",
        )
        results = load_json_object(results_path, "validation results")
    else:
        if not args.blocked_reason or not args.blocked_reason.strip():
            raise SystemExit("--blocked-reason must not be empty")
        results = {
            "schemaVersion": RESULTS_SCHEMA_VERSION,
            "commands": [],
            "checks": [
                {
                    "name": "Run completion",
                    "result": "BLOCKED",
                    "notes": args.blocked_reason,
                }
            ],
        }

    try:
        overall = finalize_run(project_root, run_dir, results)
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(str(error)) from error
    print(overall)
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
