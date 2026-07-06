#!/usr/bin/env python3
"""Verify a completed Unity validation run and its integrity records."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


MANIFEST_NAME = "RunManifest.json"
MANIFEST_HASH_NAME = "RunManifest.sha256"
SCHEMA_VERSION = 2
VALID_RESULTS = {"PASS", "FAIL", "BLOCKED", "NOT RUN"}


def load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} root must be an object")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def append_evidence_value(values: list[str], value: Any) -> None:
    if isinstance(value, str):
        values.append(value)
    elif isinstance(value, dict) and isinstance(value.get("path"), str):
        values.append(value["path"])
    elif isinstance(value, list):
        for item in value:
            append_evidence_value(values, item)


def evidence_values(manifest: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for check in manifest.get("checks", []):
        if isinstance(check, dict):
            append_evidence_value(values, check.get("evidence"))
    for criterion in manifest.get("acceptanceCriteria", []):
        if not isinstance(criterion, dict):
            continue
        append_evidence_value(values, criterion.get("evidence", []))
    return values


def verify_run(project_root: Path, run_dir: Path) -> list[str]:
    errors: list[str] = []
    project_root = project_root.resolve()
    runs_root = (project_root / "Artifacts" / "ValidationRuns").resolve()
    run_dir = run_dir.resolve()
    try:
        run_dir.relative_to(runs_root)
    except ValueError:
        return [f"run directory must be inside {runs_root}"]

    manifest_path = run_dir / MANIFEST_NAME
    sidecar_path = run_dir / MANIFEST_HASH_NAME
    if not manifest_path.is_file():
        return [f"missing {MANIFEST_NAME}"]
    if not sidecar_path.is_file():
        errors.append(f"missing {MANIFEST_HASH_NAME}")

    try:
        manifest = load_json_object(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return [f"invalid {MANIFEST_NAME}: {error}"]

    if manifest.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if manifest.get("runId") != run_dir.name:
        errors.append("runId does not match the run directory")
    if manifest.get("state") != "COMPLETED":
        errors.append("state must be COMPLETED")
    if manifest.get("result") not in VALID_RESULTS:
        errors.append("result is invalid")
    try:
        datetime.fromisoformat(
            str(manifest["startedAtUtc"]).replace("Z", "+00:00")
        )
        datetime.fromisoformat(
            str(manifest["completedAtUtc"]).replace("Z", "+00:00")
        )
    except (KeyError, TypeError, ValueError):
        errors.append("startedAtUtc and completedAtUtc must be ISO timestamps")
    duration = manifest.get("durationSeconds")
    if not isinstance(duration, (int, float)) or duration < 0:
        errors.append("durationSeconds must be a non-negative number")

    for evidence in evidence_values(manifest):
        if not evidence.startswith("Artifacts/"):
            continue
        evidence_path = (project_root / evidence).resolve()
        try:
            evidence_path.relative_to(run_dir)
        except ValueError:
            errors.append(f"evidence path escapes run directory: {evidence}")
            continue
        if not evidence_path.exists():
            errors.append(f"missing evidence: {evidence}")

    if sidecar_path.is_file():
        sidecar_parts = sidecar_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).split(maxsplit=1)
        if not sidecar_parts:
            errors.append(f"{MANIFEST_HASH_NAME} is empty")
        else:
            expected = sidecar_parts[0]
            actual = sha256(manifest_path)
            if expected != actual:
                errors.append(f"{MANIFEST_NAME} SHA-256 mismatch")

    records = manifest.get("artifactFiles")
    if not isinstance(records, list):
        errors.append("artifactFiles must be an array")
        records = []

    recorded_paths: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"artifactFiles[{index}] must be an object")
            continue
        relative = record.get("path")
        if not isinstance(relative, str):
            errors.append(f"artifactFiles[{index}].path must be a string")
            continue
        path = (project_root / relative).resolve()
        try:
            path.relative_to(run_dir)
        except ValueError:
            errors.append(f"artifact path escapes run directory: {relative}")
            continue
        recorded_paths.add(relative)
        if not path.is_file():
            errors.append(f"missing artifact: {relative}")
            continue
        if record.get("bytes") != path.stat().st_size:
            errors.append(f"artifact size mismatch: {relative}")
        if record.get("sha256") != sha256(path):
            errors.append(f"artifact SHA-256 mismatch: {relative}")

    actual_paths = {
        path.relative_to(project_root).as_posix()
        for path in run_dir.rglob("*")
        if path.is_file() and path.name not in {MANIFEST_NAME, MANIFEST_HASH_NAME}
    }
    for relative in sorted(actual_paths - recorded_paths):
        errors.append(f"unrecorded artifact: {relative}")
    for relative in sorted(recorded_paths - actual_paths):
        errors.append(f"recorded artifact is absent: {relative}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--run-dir", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser()
    if not run_dir.is_absolute():
        run_dir = project_root / run_dir
    errors = verify_run(project_root, run_dir)
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("Validation run verification: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
