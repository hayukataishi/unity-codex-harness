#!/usr/bin/env python3
"""Finalize a Unity validation run from machine-readable check results."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


RESULT_PRECEDENCE = {
    "PASS": 0,
    "NOT RUN": 1,
    "BLOCKED": 2,
    "FAIL": 3,
}


def aggregate_result(results: list[str]) -> str:
    normalized = [result if result in RESULT_PRECEDENCE else "FAIL" for result in results]
    if not normalized:
        return "NOT RUN"
    return max(normalized, key=RESULT_PRECEDENCE.__getitem__)


def artifact_records(run_dir: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file() or path.name == "RunManifest.json":
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--results", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser()
    if not run_dir.is_absolute():
        run_dir = project_root / run_dir
    run_dir = run_dir.resolve()

    results_path = Path(args.results).expanduser()
    if not results_path.is_absolute():
        results_path = project_root / results_path
    results = json.loads(results_path.read_text(encoding="utf-8"))

    manifest_path = run_dir / "RunManifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks = results.get("checks", [])
    overall = aggregate_result([check.get("result", "FAIL") for check in checks])

    completed = datetime.now(timezone.utc)
    started = datetime.fromisoformat(manifest["startedAtUtc"].replace("Z", "+00:00"))
    manifest.update(
        {
            "schemaVersion": 1,
            "completedAtUtc": completed.isoformat().replace("+00:00", "Z"),
            "durationSeconds": round((completed - started).total_seconds(), 3),
            "result": overall,
            "commands": results.get("commands", []),
            "checks": checks,
            "acceptanceCriteria": [
                {
                    "id": ac_id,
                    "result": overall,
                    "evidence": [
                        check.get("evidence", "")
                        for check in checks
                        if check.get("evidence")
                    ],
                }
                for ac_id in manifest.get("acceptanceCriterionIds", [])
            ],
        }
    )

    report_lines = [
        "# Validation Report",
        "",
        f"- Run ID: `{manifest['runId']}`",
        f"- Unity: `{manifest['unityVersion']}`",
        f"- Platform: `{manifest['targetPlatform']}`",
        f"- Result: `{overall}`",
        f"- Duration: `{manifest['durationSeconds']}s`",
        "",
        "## Acceptance Criteria",
        "",
        "| AC ID | Result | Evidence / notes |",
        "|---|---|---|",
    ]
    acceptance = manifest["acceptanceCriteria"]
    if acceptance:
        for criterion in acceptance:
            evidence = "; ".join(criterion["evidence"]) or "No evidence recorded"
            report_lines.append(
                f"| `{criterion['id']}` | `{criterion['result']}` | {evidence} |"
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
            f"| {check.get('name', 'Unknown')} | "
            f"`{check.get('result', 'FAIL')}` | "
            f"{check.get('evidence') or check.get('notes') or ''} |"
        )

    report_lines.extend(["", "## Risks and blockers", ""])
    blockers = [
        check for check in checks if check.get("result") in {"FAIL", "BLOCKED", "NOT RUN"}
    ]
    if blockers:
        report_lines.extend(
            f"- {check.get('name', 'Unknown')}: "
            f"{check.get('notes') or check.get('result')}"
            for check in blockers
        )
    else:
        report_lines.append("- None recorded.")

    (run_dir / "Report.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )
    manifest["artifactFiles"] = artifact_records(run_dir)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(overall)
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
