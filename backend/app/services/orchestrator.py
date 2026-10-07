from __future__ import annotations

from dataclasses import dataclass, asdict
import logging
from typing import Protocol

from .affinity import DEFAULT_DOMAINS, DomainQuery, normalize_entities
from .qloo import QlooError, build_insights_payload
from .scoring import apply_scores, select_coherent
from .explainability import build_explainability_graph
from .composer import compose_blueprint
from .verifier import verify_selection


logger = logging.getLogger(__name__)


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
        AgentTrace("rank", "ready", "Rank candidates using Qloo affinity while retaining the raw value."),
        AgentTrace("coherence", "ready", "De-duplicate globally and preserve domain diversity."),
        AgentTrace("explain", "ready", "Use per-result Qloo explainability as an auxiliary rationale signal."),
    ]
    return {
        "mode": "preview",
        "signals": signals,
        "location": location,
        "tasks": [asdict(task) for task in tasks],
        "trace": [asdict(step) for step in trace],
    }


def execute_agent(
    provider: InsightsProvider,
    *,
    signals: list[str],
    location: str | None,
    take: int = 5,
    mode: str = "live",
) -> dict:
    tasks = build_tasks(signals=signals, location=location, take=take)
    trace: list[AgentTrace] = [
        AgentTrace("resolve_signals", "running", "The provider resolves named taste signals from the request payload."),
    ]
    items: list[dict] = []
    aggregate_explanations: dict[str, object] = {}
    failures: list[dict[str, str]] = []
    successful_queries = 0

    for task in tasks:
        try:
            response = provider.insights(task.payload)
        except QlooError as exc:
            logger.warning("Qloo domain query failed for %s: %s", task.domain, exc)
            failures.append({"domain": task.domain, "reason": "provider_error"})
            trace.append(AgentTrace("discover_" + task.domain, "error", "Qloo request failed for this domain; continuing with remaining domains."))
            continue
        successful_queries += 1
        domain_items = normalize_entities(task.domain, response, take)
        items.extend(domain_items)
        aggregate_explanations[task.domain] = (response.get("query") or {}).get("explainability")
        trace.append(AgentTrace("discover_" + task.domain, "ok", f"Received {len(domain_items)} candidates for {task.domain}."))

    if successful_queries == 0:
        raise QlooError("All Qloo domain queries failed")

    scored = apply_scores(items)
    trace.append(AgentTrace("rank", "ok", f"Scored {len(scored)} candidates; affinity is dominant and remains separately visible."))

    coherent = select_coherent(scored, per_domain=2, total=8)
    trace.append(AgentTrace("coherence", "ok", f"Selected {len(coherent)} unique, cross-domain candidates from {len(scored)} scored results."))
    verification = verify_selection(coherent)
    trace.append(
        AgentTrace(
            "verify",
            verification["status"],
            "All required domains are represented." if verification["safe_to_present_as_complete"] else "Missing domains: " + ", ".join(verification["missing_domains"]),
        )
    )
    trace.append(AgentTrace("explain", "ok", "Retained per-candidate and aggregate explainability metadata where supplied."))

    response = {
        "mode": mode,
        "signals": signals,
        "location": location,
        "items": coherent,
        "explainability": aggregate_explanations,
        "trace": [asdict(step) for step in trace],
        "verification": verification,
        "failures": failures,
        "blueprint": compose_blueprint(coherent, location),
        "graph": build_explainability_graph(signals, coherent),
        "score_method": {
            "name": "Cultural Fit Score",
            "note": "Product-level ranking metric. It is not the Qloo affinity score; raw/normalized affinity remains exposed separately.",
        },
    }
    if mode == "demo_fixture":
        response["warning"] = "Synthetic fixture data only. No Qloo API data has been used."
    elif failures:
        response["warning"] = "Some Qloo domain queries failed; this output is partial."
    return response
