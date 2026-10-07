from __future__ import annotations

from math import isfinite
from typing import Any


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if isfinite(number) else None


def _find_signal_weights(value: Any, signal_map: dict[str, str], output: dict[str, float]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            canonical = signal_map.get(str(key).casefold())
            number = _number(child)
            if canonical is not None and number is not None and 0 <= number <= 1:
                output[canonical] = max(output.get(canonical, 0.0), number)
            else:
                _find_signal_weights(child, signal_map, output)
    elif isinstance(value, list):
        for child in value:
            _find_signal_weights(child, signal_map, output)


def build_explainability_graph(signals: list[str], items: list[dict]) -> dict:
    """Build a small judge-facing graph from per-item explainability metadata.

    The graph only creates weighted edges when a signal name can be matched to an
    explicit numeric contribution in provider metadata. Missing evidence stays
    missing rather than being inferred.
    """
    clean_signals = [s.strip() for s in signals if s and s.strip()]
    signal_map = {s.casefold(): s for s in clean_signals}
    nodes = [
        {"id": "signal:" + str(index), "kind": "signal", "label": signal}
        for index, signal in enumerate(clean_signals)
    ]
    signal_ids = {node["label"]: node["id"] for node in nodes}
    edges: list[dict] = []

    for index, item in enumerate(items):
        item_id = "candidate:" + str(index)
        nodes.append(
            {
                "id": item_id,
                "kind": "candidate",
                "label": str(item.get("name") or "Unnamed candidate"),
                "domain": str(item.get("domain") or "unknown"),
                "cultural_fit": item.get("cultural_fit"),
            }
        )
        weights: dict[str, float] = {}
        _find_signal_weights(item.get("explainability"), signal_map, weights)
        for signal, weight in sorted(weights.items(), key=lambda pair: (-pair[1], pair[0])):
            edges.append(
                {
                    "source": signal_ids[signal],
                    "target": item_id,
                    "weight": round(weight, 4),
                }
            )

    candidate_count = sum(1 for node in nodes if node["kind"] == "candidate")
    evidenced_candidates = len({edge["target"] for edge in edges})
    return {
        "nodes": nodes,
        "edges": edges,
        "evidence_coverage": round(evidenced_candidates / candidate_count, 4) if candidate_count else 0.0,
        "note": "Edges are emitted only from explicit per-result explainability contributions; no relationships are inferred.",
    }
