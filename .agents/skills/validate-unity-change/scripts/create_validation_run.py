#!/usr/bin/env python3
"""Create a new immutable Unity validation-run directory."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def unity_version(project_root: Path) -> str:
    version_file = project_root / "ProjectSettings" / "ProjectVersion.txt"
    if not version_file.is_file():
        return "NOT_FOUND: ProjectSettings/ProjectVersion.txt"
    for line in version_file.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("m_EditorVersion:"):
            return line.split(":", 1)[1].strip()
    return "NOT_FOUND: m_EditorVersion"


def git_commit(project_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "NOT_AVAILABLE"


def unique_run_dir(base: Path, timestamp: datetime) -> tuple[str, Path]:
    stem = timestamp.strftime("%Y%m%dT%H%M%SZ")
    for index in range(100):
        run_id = stem if index == 0 else f"{stem}-{index:02d}"
        candidate = base / run_id
        try:
            candidate.mkdir(parents=True, exist_ok=False)
            return run_id, candidate
        except FileExistsError:
            continue
    raise RuntimeError("Could not allocate a unique validation RunId")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root",
        default=None,
        help="Unity project root; defaults to UNITY_PROJECT_ROOT",
    )
    parser.add_argument("--design-id", action="append", default=[])
    parser.add_argument("--ac-id", action="append", default=[])
    parser.add_argument("--platform", default="NOT_RECORDED")
    parser.add_argument("--command", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    import os

    root_value = args.project_root or os.environ.get("UNITY_PROJECT_ROOT")
    if not root_value:
        raise SystemExit("Provide --project-root or set UNITY_PROJECT_ROOT")

    project_root = Path(root_value).expanduser().resolve()
    required = [
        project_root / "Assets",
        project_root / "Packages",
        project_root / "ProjectSettings" / "ProjectVersion.txt",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Not a Unity project; missing: " + ", ".join(missing))

    now = datetime.now(timezone.utc)
    run_id, run_dir = unique_run_dir(
        project_root / "Artifacts" / "ValidationRuns", now
    )
    for relative in (
        "Tests/Coverage",
        "Logs",
        "Evidence",
        "Profiler",
        "Builds",
    ):
        (run_dir / relative).mkdir(parents=True, exist_ok=True)

    manifest = {
        "schemaVersion": 2,
        "runId": run_id,
        "startedAtUtc": now.isoformat().replace("+00:00", "Z"),
        "gitCommit": git_commit(project_root),
        "unityVersion": unity_version(project_root),
        "targetPlatform": args.platform,
        "commands": args.command,
        "designIds": args.design_id,
        "acceptanceCriterionIds": args.ac_id,
        "state": "RUNNING",
        "result": "NOT RUN",
        "artifacts": {
            "report": f"Artifacts/ValidationRuns/{run_id}/Report.md",
            "logs": f"Artifacts/ValidationRuns/{run_id}/Logs",
            "tests": f"Artifacts/ValidationRuns/{run_id}/Tests",
            "evidence": f"Artifacts/ValidationRuns/{run_id}/Evidence",
        },
    }
    (run_dir / "RunManifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (run_dir / "Report.md").write_text(
        "# Validation Report\n\n"
        f"- Run ID: `{run_id}`\n"
        f"- Unity: `{manifest['unityVersion']}`\n"
        f"- Platform: `{args.platform}`\n"
        "- State: `RUNNING`\n"
        "- Result: `NOT RUN`\n"
        f"- Design IDs: {', '.join(args.design_id) or 'NOT RECORDED'}\n"
        f"- AC IDs: {', '.join(args.ac_id) or 'NOT RECORDED'}\n\n"
        "## Acceptance Criteria\n\n"
        "| AC ID | Result | Evidence / notes |\n"
        "|---|---|---|\n\n"
        "## Checks\n\n"
        "- Compile: `NOT RUN`\n"
        "- EditMode: `NOT RUN`\n"
        "- PlayMode: `NOT RUN`\n"
        "- Asset validation: `NOT RUN`\n"
        "- Build: `NOT RUN`\n\n"
        "## Risks and blockers\n\n",
        encoding="utf-8",
    )
    print(run_dir.relative_to(project_root).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
