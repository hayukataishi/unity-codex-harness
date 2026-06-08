#!/usr/bin/env python3
"""Validate Unity license environment variables without printing secrets."""

from __future__ import annotations

import os


def missing_license_values(environment: dict[str, str]) -> list[str]:
    email = environment.get("UNITY_EMAIL", "").strip()
    password = environment.get("UNITY_PASSWORD", "").strip()
    license_file = environment.get("UNITY_LICENSE", "").strip()
    serial = environment.get("UNITY_SERIAL", "").strip()

    missing: list[str] = []
    if not email:
        missing.append("UNITY_EMAIL")
    if not password:
        missing.append("UNITY_PASSWORD")
    if not license_file and not serial:
        missing.append("UNITY_LICENSE or UNITY_SERIAL")
    return missing


def main() -> int:
    missing = missing_license_values(dict(os.environ))
    if missing:
        rendered = ", ".join(missing)
        print(
            "Unity CI license configuration is incomplete. "
            f"Configure GitHub Actions secrets: {rendered}."
        )
        return 1
    print("Unity CI license secrets are configured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
