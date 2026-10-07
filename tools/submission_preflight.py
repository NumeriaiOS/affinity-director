#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def exists(*names: str) -> bool:
    return any((ROOT / name).exists() for name in names)


def valid_public_url(value: str) -> bool:
    if not value.strip():
        return False
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    host = (parsed.hostname or "").casefold()
    return host not in {"localhost", "127.0.0.1", "::1"}


def env_bool(name: str) -> bool:
    return os.getenv(name, "").strip().casefold() in {"1", "true", "yes", "on"}


def live_validation_passed() -> bool:
    path = ROOT / "reports" / "live_validation.json"
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return payload.get("mode") == "real_qloo_live_validation" and payload.get("all_pass") is True


def secret_scan_passed() -> bool:
    result = subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(ROOT / "tools/secret_scan.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def git_clean() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and not result.stdout.strip()


def build_report() -> dict:
    checks = {
        "dockerfile": exists("Dockerfile"),
        "readme": exists("README.md"),
        "license": exists("LICENSE", "LICENSE.md", "LICENSE.txt"),
        "env_example": exists(".env.example"),
        "backend_requirements": exists("backend/requirements.txt"),
        "submission_checklist": exists("docs/SUBMISSION_CHECKLIST.md"),
        "judge_testing": exists("submission/JUDGE_TESTING.md"),
        "devpost_draft": exists("submission/DEVPOST_DRAFT.md"),
        "ci_workflow": exists(".github/workflows/ci.yml"),
        "secret_scan": secret_scan_passed(),
        "git_clean": git_clean(),
    }
    external = {
        "qloo_live_validation": live_validation_passed(),
        "qloo_live_enabled": env_bool("QLOO_LIVE_ENABLED"),
        "external_demo_url": valid_public_url(os.getenv("PUBLIC_DEMO_URL", "")),
        "public_repository_url": valid_public_url(os.getenv("PUBLIC_REPO_URL", "")),
    }
    local_blockers = [name for name, ok in checks.items() if not ok]
    external_blockers = [name for name, ok in external.items() if not ok]
    return {
        "checks": checks,
        "external_checks": external,
        "local_blockers": local_blockers,
        "external_blockers": external_blockers,
        "ready_for_submission": not local_blockers and not external_blockers,
        "note": "Set PUBLIC_DEMO_URL and PUBLIC_REPO_URL only when those resources are actually public. QLOO_LIVE_ENABLED should be enabled only after reports/live_validation.json passes.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="exit non-zero while any submission blocker remains")
    args = parser.parse_args()
    report = build_report()
    print(json.dumps(report, indent=2))
    return 1 if args.strict and not report["ready_for_submission"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
