from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.fixtures import FixtureQlooProvider  # noqa: E402
from app.services.orchestrator import execute_agent  # noqa: E402


SCENARIOS = [
    {"name": "milan-night", "signals": ["Arctic Monkeys", "A24", "technical streetwear"], "location": "Milan"},
    {"name": "cross-domain", "signals": ["independent cinema", "art rock", "design culture"], "location": "Berlin"},
    {"name": "no-location", "signals": ["experimental music", "contemporary fashion", "film festivals"], "location": None},
]


def digest(result: dict) -> str:
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def evaluate_one(scenario: dict) -> dict:
    first = execute_agent(
        FixtureQlooProvider(),
        signals=scenario["signals"],
        location=scenario["location"],
        take=3,
        mode="demo_fixture",
    )
    second = execute_agent(
        FixtureQlooProvider(),
        signals=scenario["signals"],
        location=scenario["location"],
        take=3,
        mode="demo_fixture",
    )
    items = first["items"]
    domains = {item["domain"] for item in items}
    ids = [item["entity_id"] for item in items]
    return {
        "name": scenario["name"],
        "item_count": len(items),
        "domain_coverage": len(domains),
        "unique_ratio": round(len(set(ids)) / len(ids), 4) if ids else 0,
        "scored_ratio": round(sum(item["cultural_fit"] is not None for item in items) / len(items), 4) if items else 0,
        "high_confidence_ratio": round(sum(item["score_confidence"] == "high" for item in items) / len(items), 4) if items else 0,
        "mean_cultural_fit": round(sum(item["cultural_fit"] for item in items) / len(items), 2) if items else 0,
        "deterministic": digest(first) == digest(second),
        "verification_status": first.get("verification", {}).get("status"),
        "pass": len(domains) == 4 and len(ids) == len(set(ids)) and bool(items) and digest(first) == digest(second) and first.get("verification", {}).get("status") == "complete",
    }


def main() -> int:
    rows = [evaluate_one(scenario) for scenario in SCENARIOS]
    summary = {
        "mode": "synthetic_fixture_evaluation",
        "note": "This report validates orchestration invariants only; it does not measure real Qloo recommendation quality.",
        "scenarios": rows,
        "all_pass": all(row["pass"] for row in rows),
    }
    output = ROOT / "reports" / "demo_eval.json"
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if summary["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
