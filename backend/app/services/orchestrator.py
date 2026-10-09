from __future__ import annotations

from dataclasses import dataclass, asdict
import logging
from typing import Protocol

from .affinity import DEFAULT_DOMAINS, DomainQuery, normalize_entities
from .qloo import QlooError, build_insights_payload
from .scoring import apply_scores, select_coherent
from .explainability import build_explainability_graph, extract_signal_weights
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


def _split_resolved_signals(signals: list[str], resolved_signals: list[dict] | None) -> tuple[list[str], list[str]]:
    by_input = {str(row.get("input") or "").strip().casefold(): str(row.get("entity_id") or "").strip() for row in (resolved_signals or []) if row.get("input") and row.get("entity_id")}
    entity_ids, unresolved = [], []
    seen_ids: set[str] = set()
    for signal in signals:
        clean = signal.strip()
        entity_id = by_input.get(clean.casefold())
        if entity_id:
            if entity_id not in seen_ids:
                entity_ids.append(entity_id); seen_ids.add(entity_id)
        else:
            unresolved.append(clean)
    return entity_ids, unresolved


def build_tasks(*, signals: list[str], location: str | None, take: int = 5, domains: tuple[DomainQuery, ...] = DEFAULT_DOMAINS, resolved_signals: list[dict] | None = None) -> list[AgentTask]:
    entity_ids, unresolved_names = _split_resolved_signals(signals, resolved_signals)
    tasks = []
    for target in domains:
        task_location = location if target.filter_type == "urn:entity:place" else None
        payload = build_insights_payload(signal_names=unresolved_names, signal_entity_ids=entity_ids, filter_type=target.filter_type, location=task_location, take=take)
        tasks.append(AgentTask(target.domain, target.filter_type, payload))
    return tasks


def preview_agent(*, signals: list[str], location: str | None, take: int = 5) -> dict:
    tasks = build_tasks(signals=signals, location=location, take=take)
    trace = [AgentTrace("resolve_signals", "ready", f"Resolve {len(signals)} named cultural signals inside Qloo."), AgentTrace("fan_out", "ready", f"Prepare {len(tasks)} cross-domain discovery tasks."), AgentTrace("rank", "ready", "Rank candidates using Qloo affinity while retaining the raw value."), AgentTrace("coherence", "ready", "De-duplicate globally and preserve domain diversity."), AgentTrace("explain", "ready", "Use explicit per-result Qloo explainability as an auxiliary rationale signal.")]
    return {"mode": "preview", "signals": signals, "location": location, "tasks": [asdict(task) for task in tasks], "trace": [asdict(step) for step in trace]}


def _provider_resolution(provider: InsightsProvider, signals: list[str]) -> tuple[list[dict], bool, bool]:
    resolver = getattr(provider, "resolve_signals", None)
    if not callable(resolver):
        return [], False, False
    try:
        rows = resolver(signals)
        return [row for row in rows if isinstance(row, dict)], True, False
    except (QlooError, ValueError) as exc:
        logger.warning("Qloo signal resolution failed; falling back to named queries: %s", exc)
        return [], True, True


def execute_agent(provider: InsightsProvider, *, signals: list[str], location: str | None, take: int = 5, mode: str = "live", resolved_signals: list[dict] | None = None) -> dict:
    supplied_resolution = resolved_signals is not None
    resolution_failed = False
    resolution_attempted = supplied_resolution
    if resolved_signals is None:
        resolved_signals, resolution_attempted, resolution_failed = _provider_resolution(provider, signals)
    resolved_signals = resolved_signals or []
    resolved_inputs = {str(row.get("input") or "").strip().casefold() for row in resolved_signals if row.get("input") and row.get("entity_id")}
    unresolved_signals = [signal for signal in signals if signal.strip().casefold() not in resolved_inputs]
    if resolution_attempted:
        resolution_status = "ok" if resolved_inputs and not unresolved_signals else ("partial" if resolved_inputs else "fallback")
        resolution_detail = f"Resolved {len(resolved_inputs)}/{len(signals)} named signals to explicit Qloo entity IDs; {len(unresolved_signals)} remain on Qloo named-query resolution."
        if resolution_failed:
            resolution_detail += " Search resolution failed safely, so named-query fallback is in use."
    else:
        resolution_status = "ready"; resolution_detail = "The provider resolves named taste signals from the request payload."

    tasks = build_tasks(signals=signals, location=location, take=take, resolved_signals=resolved_signals)
    trace: list[AgentTrace] = [AgentTrace("resolve_signals", resolution_status, resolution_detail)]
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
            trace.append(AgentTrace("discover_" + task.domain, "error", "Qloo request failed for this domain; continuing with remaining domains.")); continue
        successful_queries += 1
        domain_items = normalize_entities(task.domain, response, take)
        items.extend(domain_items)
        aggregate_explanations[task.domain] = (response.get("query") or {}).get("explainability")
        trace.append(AgentTrace("discover_" + task.domain, "ok", f"Received {len(domain_items)} candidates for {task.domain}."))
    if successful_queries == 0:
        raise QlooError("All Qloo domain queries failed")

    scored = apply_scores(items)
    for item in scored:
        weights = extract_signal_weights(item.get("explainability"), signals, resolved_signals)
        item["signal_influences"] = [{"signal": signal, "weight": round(weight, 4)} for signal, weight in weights.items()]
    trace.append(AgentTrace("rank", "ok", f"Scored {len(scored)} candidates; affinity is dominant and remains separately visible."))
    coherent = select_coherent(scored, per_domain=2, total=8)
    trace.append(AgentTrace("coherence", "ok", f"Selected {len(coherent)} unique, cross-domain candidates from {len(scored)} scored results."))
    verification = verify_selection(coherent)
    trace.append(AgentTrace("verify", verification["status"], "All required domains are represented." if verification["safe_to_present_as_complete"] else "Missing domains: " + ", ".join(verification["missing_domains"])))
    mapped_evidence = sum(1 for item in coherent if item.get("signal_influences"))
    trace.append(AgentTrace("explain", "ok", f"Mapped explicit provider contribution evidence for {mapped_evidence}/{len(coherent)} selected candidates without inferring relationships."))

    resolution_payload = {"method": ("qloo_search" if not supplied_resolution else "provided_qloo_mapping"), "resolved": resolved_signals, "unresolved": unresolved_signals} if resolution_attempted else {"method": "provider_native", "resolved": [], "unresolved": []}
    response = {"mode": mode, "signals": signals, "location": location, "signal_resolution": resolution_payload, "items": coherent, "explainability": aggregate_explanations, "trace": [asdict(step) for step in trace], "verification": verification, "failures": failures, "blueprint": compose_blueprint(coherent, location), "graph": build_explainability_graph(signals, coherent, resolved_signals), "score_method": {"name": "Cultural Fit Score", "note": "Product-level ranking metric. It is not the Qloo affinity score; raw/normalized affinity remains exposed separately."}}
    if mode == "demo_fixture": response["warning"] = "Synthetic fixture data only. No Qloo API data has been used."
    elif failures: response["warning"] = "Some Qloo domain queries failed; this output is partial."
    return response
