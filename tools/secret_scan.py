#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_pat": re.compile(r"(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "openai_key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "stripe_live_key": re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{16,}"),
}
RISKY_NAMES = re.compile(r"(^|/)(?:\.env(?:\..+)?|id_rsa|id_ed25519|credentials?(?:\..+)?|secrets?(?:\..+)?)$", re.I)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)


def main() -> int:
    files = [line for line in git("ls-files").stdout.splitlines() if line]
    findings: list[str] = []
    for rel in files:
        if RISKY_NAMES.search(rel) and rel != ".env.example":
            findings.append(f"risky tracked filename: {rel}")
        path = ROOT / rel
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for name, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{name} pattern in tracked file: {rel}")

    history = git("log", "-p", "--all", "--", ".")
    if history.returncode == 0:
        for name, pattern in PATTERNS.items():
            if pattern.search(history.stdout):
                findings.append(f"{name} pattern found in git history")

    if findings:
        print("SECRET SCAN FAILED")
        for finding in sorted(set(findings)):
            print(f"- {finding}")
        return 1
    print(f"SECRET SCAN PASSED: {len(files)} tracked files checked; no known secret patterns found in current tree or git patch history.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
