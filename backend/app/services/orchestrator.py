from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Protocol

from .affinity import DEFAULT_DOMAINS, DomainQuery, normalize_entities
from .qloo import build_insights_payload


class InsightsProvider(Protocol):
    def insights(self, payload: dict) -> dict: ...


@dataclass(frozen=True)
class AgentTask:
    domain: str
    filter_type: str
    payload: dict


@dataclass(frozen=True)
class AgentTrace:
    step: str
    status: str
    detail: str


def build_tasks(
    *,
    signals: list[str],
    location: str | None,
    take: int = 5,
    domains: tuple[DomainQuery, ...] = DEFAULT_DOMAINS,
) -> list[AgentTask]:
    tasks = []
    for target in domains:
        task_location = location if target.filter_type == "urn:entity:place" else None
        payload = build_insights_payload(
            signal_names=signals,
            filter_type=target.filter_type,
            location=task_location,
            take=take,
        )
        tasks.append(AgentTask(target.domain, target.filter_type, payload))
    return tasks


def preview_agent(*, signals: list[str], location: str | None, take: int = 5) -> dict:
    tasks = build_tasks(signals=signals, location=location, take=take)
    trace = [
        AgentTrace("resolve_signals", "ready", f"Resolve {len(signals)} named cultural signals inside Qloo Insights."),
        AgentTrace("fan_out", "ready", f"Prepare {len(tasks)} cross-domain discovery tasks."),
        AgentTrace("rank", "ready", "Rank candidates using Qloo affinity outputs."),
        AgentTrace("coherence", "ready", "Remove duplicate entities and preserve domain diversity."),
        AgentTrace("explain", "ready", "Retain Qloo explainability metadata for judge-facing rationale."),
    ]
    return {
        "mode": "preview",
        "signals": signals,
        "location": location,
        "tasks": [asdict(task) for task in tasks],
        "trace": [asdict(step) for step in trace],
    }


def _dedupe(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result = []
    for item in items:
        key = str(item.get("entity_id") or item.get("name") or "").strip().casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def execute_agent(
    provider: InsightsProvider,
    *,
    signals: list[str],
    location: str | None,
    take: int = 5,
) -> dict:
    tasks = build_tasks(signals=signals, location=location, take=take)
    trace: list[AgentTrace] = [
        AgentTrace("resolve_signals", "running", "Qloo will resolve named entities from the request payload."),
    ]
    items: list[dict] = []
    explanations: dict[str, object] = {}

    for task in tasks:
        response = provider.insights(task.payload)
        domain_items = normalize_entities(task.domain, response, take)
        items.extend(domain_items)
        explanations[task.domain] = (response.get("query") or {}).get("explainability")
        trace.append(AgentTrace("discover_" + task.domain, "ok", f"Received {len(domain_items)} candidates for {task.domain}."))

    before = len(items)
    items = _dedupe(items)
    trace.append(AgentTrace("coherence", "ok", f"Kept {len(items)} unique candidates from {before} cross-domain results."))
    trace.append(AgentTrace("explain", "ok", "Preserved Qloo explainability metadata by domain."))

    return {
        "mode": "live",
        "signals": signals,
        "location": location,
        "items": items,
        "explainability": explanations,
        "trace": [asdict(step) for step in trace],
    }
