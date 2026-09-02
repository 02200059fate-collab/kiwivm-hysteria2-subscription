#!/usr/bin/env python3
"""Fail CI when common live-secret patterns or generated private files appear."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__"}
FORBIDDEN_NAMES = {
    ".env",
    "api_key",
    "node_uri",
    "token",
    "usage-cache.json",
}
PATTERNS = {
    "private key": re.compile(r"BEGIN (?:OPENSSH|RSA|EC|DSA) PRIVATE KEY"),
    "Hysteria URI with credentials": re.compile(r"hysteria2://[^@\s<]{16,}@"),
    "private subscription URL": re.compile(r"https?://[^\s]+/sub/[a-f0-9]{24,}"),
    "likely KiwiVM API key": re.compile(r"(?i)(?:api[_ -]?key)[\s:=\"']+[a-f0-9]{24,}"),
}


def main() -> int:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        relative = path.relative_to(ROOT)
        if path.name in FORBIDDEN_NAMES:
            findings.append(f"forbidden generated file: {relative}")
            continue
        if path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{label}: {relative}")

    if findings:
        print("Secret scan failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("Secret scan passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
