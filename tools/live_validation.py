#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.affinity import normalize_entities  # noqa: E402
from app.services.orchestrator import build_tasks, execute_agent  # noqa: E402
from app.services.qloo import QlooClient, QlooError  # noqa: E402


SCENARIOS = [
    {
        "name": "milan-cultural-night",
        "signals": ["Arctic Monkeys", "A24", "technical streetwear"],
        "location": "Milan",
    },
    {
        "name": "cross-domain-minimal",
        "signals": ["A24", "Japanese contemporary design"],
        "location": None,
    },
]


class ReplayProvider:
    def __init__(self, responses: dict[str, dict]) -> None:
        self.responses = responses

    def insights(self, payload: dict) -> dict:
        filter_type = str(payload.get("filter.type") or "")
        if filter_type not in self.responses:
            raise QlooError(f"Missing captured response for {filter_type}")
        return self.responses[filter_type]


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "sample"


def inspect_domain(domain: str, response: dict, take: int) -> dict:
    results = response.get("results") or {}
    rows = results.get("entities") or []
    normalized = normalize_entities(domain, response, take)
    raw_affinities = [row.get("affinity_raw") for row in normalized if row.get("affinity_raw") is not None]
    per_result_explainability = sum(1 for row in normalized if row.get("explainability"))
    aggregate = (response.get("query") or {}).get("explainability")
    locality = (response.get("query") or {}).get("locality")
    first_row = rows[0] if isinstance(rows, list) and rows and isinstance(rows[0], dict) else {}
    query = response.get("query") if isinstance(response.get("query"), dict) else {}
    return {
        "response_keys": sorted(response.keys()),
        "query_keys": sorted(query.keys()),
        "results_keys": sorted(results.keys()) if isinstance(results, dict) else [],
        "first_entity_keys": sorted(first_row.keys()),
        "raw_entity_count": len(rows) if isinstance(rows, list) else 0,
        "normalized_count": len(normalized),
        "entity_identity_count": sum(1 for row in normalized if row.get("entity_id") and row.get("name")),
        "raw_affinity_samples": raw_affinities[:5],
        "per_result_explainability_count": per_result_explainability,
        "aggregate_explainability_present": bool(aggregate),
        "locality_metadata_present": bool(locality),
        "pass": bool(normalized) and all(row.get("entity_id") and row.get("name") for row in normalized),
    }


def validate_scenario(client: QlooClient, scenario: dict, sample_dir: Path) -> dict:
    resolved_signals = client.resolve_signals(scenario["signals"])
    tasks = build_tasks(
        signals=scenario["signals"],
        location=scenario["location"],
        take=3,
        resolved_signals=resolved_signals,
    )
    captured: dict[str, dict] = {}
    domain_reports: dict[str, dict] = {}

    for task in tasks:
        response = client.insights(task.payload)
        captured[task.filter_type] = response
        sample_path = sample_dir / f"{slug(scenario['name'])}-{slug(task.domain)}.json"
        sample_path.write_text(json.dumps(response, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        domain_reports[task.domain] = inspect_domain(task.domain, response, 3)

    replay = execute_agent(
        ReplayProvider(captured),
        signals=scenario["signals"],
        location=scenario["location"],
        take=3,
        mode="live_validation_replay",
        resolved_signals=resolved_signals,
    )
    graph = replay.get("graph") or {}
    verification = replay.get("verification") or {}
    return {
        "name": scenario["name"],
        "domains": domain_reports,
        "verification": verification,
        "item_count": len(replay.get("items", [])),
        "evidence_coverage": graph.get("evidence_coverage", 0.0),
        "signal_resolution": replay.get("signal_resolution"),
        "blueprint_roles": (replay.get("blueprint") or {}).get("role_count", 0),
        "failures": replay.get("failures", []),
        "pass": all(report["pass"] for report in domain_reports.values())
        and verification.get("status") == "complete"
        and graph.get("evidence_coverage", 0.0) > 0
        and not replay.get("failures"),
    }


def main() -> int:
    if not os.getenv("QLOO_API_KEY", "").strip():
        print("BLOCKED: QLOO_API_KEY is not configured; no live validation was attempted.")
        return 2

    sample_dir = ROOT / "reports" / "live_samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    client = QlooClient()
    reports = []
    try:
        for scenario in SCENARIOS:
            reports.append(validate_scenario(client, scenario, sample_dir))
    except QlooError as exc:
        print("LIVE VALIDATION FAILED:", exc)
        return 1

    payload = {
        "mode": "real_qloo_live_validation",
        "note": "Raw API samples are stored locally under reports/live_samples and are intentionally ignored by Git.",
        "scenarios": reports,
        "all_pass": all(row["pass"] for row in reports),
    }
    output = ROOT / "reports" / "live_validation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
