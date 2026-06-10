#!/usr/bin/env python3
"""Validate the pinned GameCI Unity image locally and on Docker Hub."""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


OCI_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class RemoteVerificationError(RuntimeError):
    """Raised when Docker Hub metadata cannot prove image availability."""


def load_manifest(lock_path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(lock_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"lock file does not exist: {lock_path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"lock file is not valid JSON: {error}") from error

    if not isinstance(manifest, dict):
        raise ValueError("lock file root must be an object")
    return manifest


def gameci_configuration(manifest: dict[str, Any]) -> dict[str, Any]:
    ci = manifest.get("ci")
    if not isinstance(ci, dict):
        raise ValueError("harness.lock.json ci must be an object")

    gameci = ci.get("gameCI")
    if not isinstance(gameci, dict):
        raise ValueError("harness.lock.json ci.gameCI must be an object")
    return gameci


def validate_lock_configuration(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    harness = manifest.get("harness")
    if not isinstance(harness, dict):
        return ["harness.lock.json harness must be an object"]

    unity_version = harness.get("unityFixtureVersion")
    if not isinstance(unity_version, str) or not unity_version:
        errors.append(
            "harness.lock.json harness.unityFixtureVersion must not be empty"
        )

    try:
        gameci = gameci_configuration(manifest)
    except ValueError as error:
        return errors + [str(error)]

    test_runner = gameci.get("unityTestRunner")
    if not isinstance(test_runner, dict):
        errors.append(
            "harness.lock.json ci.gameCI.unityTestRunner must be an object"
        )
    else:
        repository = test_runner.get("repository")
        if repository != "https://github.com/game-ci/unity-test-runner":
            errors.append(
                "harness.lock.json GameCI test runner repository is invalid"
            )
        commit = test_runner.get("commit")
        if not isinstance(commit, str) or not COMMIT_SHA_RE.fullmatch(commit):
            errors.append(
                "harness.lock.json GameCI test runner commit must be pinned"
            )

    image = gameci.get("editorImage")
    if not isinstance(image, dict):
        errors.append(
            "harness.lock.json ci.gameCI.editorImage must be an object"
        )
        return errors

    repository = image.get("repository")
    tag = image.get("tag")
    digest = image.get("digest")
    reference = image.get("reference")
    image_version = image.get("imageVersion")
    platform = image.get("platform")
    api_url = image.get("dockerHubApiUrl")

    if repository != "unityci/editor":
        errors.append("GameCI editor image repository must be unityci/editor")
    if image_version != "3.2.2":
        errors.append("GameCI editor image version must be 3.2.2")
    if platform != "linux-il2cpp":
        errors.append("GameCI editor image platform must be linux-il2cpp")

    expected_tag = (
        f"ubuntu-{unity_version}-linux-il2cpp-{image_version}"
        if isinstance(unity_version, str)
        and isinstance(image_version, str)
        else None
    )
    if tag != expected_tag:
        errors.append(
            "GameCI editor image tag must match the Unity fixture version, "
            "platform, and image version"
        )

    if not isinstance(digest, str) or not OCI_DIGEST_RE.fullmatch(digest):
        errors.append("GameCI editor image digest must be a sha256 OCI digest")

    expected_reference = (
        f"{repository}:{tag}@{digest}"
        if all(isinstance(value, str) for value in (repository, tag, digest))
        else None
    )
    if reference != expected_reference:
        errors.append("GameCI editor image reference must pin tag and digest")

    expected_api_url = (
        "https://hub.docker.com/v2/repositories/"
        f"{repository}/tags/{tag}"
        if isinstance(repository, str) and isinstance(tag, str)
        else None
    )
    if api_url != expected_api_url:
        errors.append("GameCI Docker Hub API URL must match the pinned tag")

    availability = image.get("availability")
    if not isinstance(availability, dict):
        errors.append("GameCI editor image availability must be an object")
    elif availability.get("status") != "PASS":
        errors.append("GameCI editor image availability status must be PASS")

    remote_execution = gameci.get("remoteExecution")
    if not isinstance(remote_execution, dict):
        errors.append("GameCI remoteExecution must be an object")
    elif remote_execution.get("status") not in {
        "PASS",
        "FAIL",
        "BLOCKED",
        "NOT RUN",
    }:
        errors.append("GameCI remoteExecution status is invalid")

    return errors


def validate_remote_payload(
    payload: Any,
    expected_tag: str,
    expected_digest: str,
) -> list[str]:
    if not isinstance(payload, dict):
        return ["Docker Hub response root must be an object"]

    errors: list[str] = []
    if payload.get("name") != expected_tag:
        errors.append("Docker Hub returned a different image tag")
    if payload.get("tag_status") != "active":
        errors.append("Docker Hub image tag is not active")
    if payload.get("digest") != expected_digest:
        errors.append("Docker Hub image digest does not match harness.lock.json")

    images = payload.get("images")
    if not isinstance(images, list) or not any(
        isinstance(image, dict)
        and image.get("architecture") == "amd64"
        and image.get("os") == "linux"
        and image.get("status") == "active"
        for image in images
    ):
        errors.append("Docker Hub tag has no active linux/amd64 image")
    return errors


def fetch_remote_payload(
    api_url: str,
    timeout: float,
    attempts: int,
) -> dict[str, Any]:
    request = urllib.request.Request(
        api_url,
        headers={"User-Agent": "unity-codex-harness-gameci-check/1"},
    )
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.load(response)
            if not isinstance(payload, dict):
                raise RemoteVerificationError(
                    "Docker Hub response root must be an object"
                )
            return payload
        except (
            OSError,
            urllib.error.HTTPError,
            urllib.error.URLError,
            json.JSONDecodeError,
        ) as error:
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(1)

    raise RemoteVerificationError(
        "Docker Hub metadata request was unavailable after "
        f"{attempts} attempt(s): {last_error}"
    )


def verify_remote_image(
    manifest: dict[str, Any],
    timeout: float = 20,
    attempts: int = 3,
) -> list[str]:
    gameci = gameci_configuration(manifest)
    image = gameci["editorImage"]
    payload = fetch_remote_payload(
        image["dockerHubApiUrl"],
        timeout,
        attempts,
    )
    return validate_remote_payload(payload, image["tag"], image["digest"])


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="Validate the GameCI image pinned in harness.lock.json."
    )
    parser.add_argument(
        "--lock-file",
        type=Path,
        default=root / "harness.lock.json",
    )
    parser.add_argument(
        "--verify-remote",
        action="store_true",
        help="Query Docker Hub and verify the active tag and OCI digest.",
    )
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--attempts", type=int, default=3)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = load_manifest(args.lock_file.resolve())
    except ValueError as error:
        print(f"GameCI image check: FAIL - {error}")
        return 1

    errors = validate_lock_configuration(manifest)
    if errors:
        for error in errors:
            print(f"GameCI image check: FAIL - {error}")
        return 1

    if args.verify_remote:
        try:
            errors = verify_remote_image(
                manifest,
                timeout=args.timeout,
                attempts=args.attempts,
            )
        except RemoteVerificationError as error:
            print(f"GameCI image check: BLOCKED - {error}")
            return 2
        if errors:
            for error in errors:
                print(f"GameCI image check: FAIL - {error}")
            return 1

    image = gameci_configuration(manifest)["editorImage"]
    mode = "remote metadata verified" if args.verify_remote else "lock verified"
    print(f"GameCI image check: PASS - {image['reference']} ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
