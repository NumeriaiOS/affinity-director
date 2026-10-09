from __future__ import annotations

from math import isfinite
from typing import Any


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if isfinite(number) else None


def _identity_map(signals: list[str], resolved_signals: list[dict] | None) -> dict[str, str]:
    clean_signals = [s.strip() for s in signals if s and s.strip()]
    identities = {signal.casefold(): signal for signal in clean_signals}
    canonical = {signal.casefold(): signal for signal in clean_signals}
    for row in resolved_signals or []:
        input_name = str(row.get("input") or "").strip()
        signal = canonical.get(input_name.casefold())
        if not signal:
            continue
        entity_id = str(row.get("entity_id") or "").strip()
        resolved_name = str(row.get("resolved_name") or "").strip()
        if entity_id:
            identities[entity_id.casefold()] = signal
        if resolved_name:
            identities[resolved_name.casefold()] = signal
    return identities


def _find_signal_weights(value: Any, identity_map: dict[str, str], output: dict[str, float]) -> None:
    if isinstance(value, dict):
        entity_id = value.get("entity_id") or value.get("id")
        score = None
        for score_key in ("score", "weight", "contribution", "avg_score"):
            score = _number(value.get(score_key))
            if score is not None:
                break
        if entity_id is not None and score is not None and 0 <= score <= 1:
            canonical = identity_map.get(str(entity_id).casefold())
            if canonical is not None:
                output[canonical] = max(output.get(canonical, 0.0), score)
        for key, child in value.items():
            canonical = identity_map.get(str(key).casefold())
            number = _number(child)
            if canonical is not None and number is not None and 0 <= number <= 1:
                output[canonical] = max(output.get(canonical, 0.0), number)
            else:
                _find_signal_weights(child, identity_map, output)
    elif isinstance(value, list):
        for child in value:
            _find_signal_weights(child, identity_map, output)


def extract_signal_weights(explainability: Any, signals: list[str], resolved_signals: list[dict] | None = None) -> dict[str, float]:
    weights: dict[str, float] = {}
    _find_signal_weights(explainability, _identity_map(signals, resolved_signals), weights)
    return dict(sorted(weights.items(), key=lambda pair: (-pair[1], pair[0])))


def build_explainability_graph(signals: list[str], items: list[dict], resolved_signals: list[dict] | None = None) -> dict:
    clean_signals = [s.strip() for s in signals if s and s.strip()]
    resolution_by_input = {str(row.get("input") or "").strip().casefold(): row for row in (resolved_signals or []) if row.get("input") and row.get("entity_id")}
    nodes = []
    for index, signal in enumerate(clean_signals):
        node = {"id": "signal:" + str(index), "kind": "signal", "label": signal}
        resolution = resolution_by_input.get(signal.casefold())
        if resolution:
            node.update({"provider_entity_id": resolution.get("entity_id"), "resolved_label": resolution.get("resolved_name"), "resolution_match": resolution.get("match")})
        nodes.append(node)
    signal_ids = {node["label"]: node["id"] for node in nodes}
    edges: list[dict] = []
    for index, item in enumerate(items):
        item_id = "candidate:" + str(index)
        nodes.append({"id": item_id, "kind": "candidate", "label": str(item.get("name") or "Unnamed candidate"), "domain": str(item.get("domain") or "unknown"), "cultural_fit": item.get("cultural_fit")})
        weights = extract_signal_weights(item.get("explainability"), clean_signals, resolved_signals)
        for signal, weight in weights.items():
            edges.append({"source": signal_ids[signal], "target": item_id, "weight": round(weight, 4)})
    candidate_count = sum(1 for node in nodes if node["kind"] == "candidate")
    evidenced_candidates = len({edge["target"] for edge in edges})
    resolved_count = sum(1 for signal in clean_signals if signal.casefold() in resolution_by_input)
    return {"nodes": nodes, "edges": edges, "evidence_coverage": round(evidenced_candidates / candidate_count, 4) if candidate_count else 0.0, "resolved_signal_count": resolved_count, "requested_signal_count": len(clean_signals), "note": "Edges use only explicit per-result contribution scores. Provider entity IDs are linked to requested signals only through explicit Qloo search resolution; no relationships are inferred."}
