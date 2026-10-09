from __future__ import annotations


_GENERIC_BY_DOMAIN = {
    "music": ("Alternative live music program", "Generic category match from the supplied taste brief."),
    "venue": ("Industrial-style creative venue", "Generic venue heuristic based on event-planning conventions."),
    "brand": ("Contemporary design partner", "Generic brand-category suggestion without affinity evidence."),
    "film": ("Independent film screening", "Generic film-program suggestion derived from the brief."),
}


def build_generic_baseline(*, signals: list[str], location: str | None) -> dict:
    """Deterministic non-Qloo baseline used to wire the A/B evaluation surface.

    This is intentionally modest: it demonstrates what an ungrounded category
    heuristic can produce. It is not presented as an LLM benchmark and will be
    replaced by a frozen LLM baseline once external model access is selected.
    """
    items = []
    for domain, (name, rationale) in _GENERIC_BY_DOMAIN.items():
        items.append(
            {
                "domain": domain,
                "name": name,
                "rationale": rationale,
                "evidence": None,
                "grounded": False,
            }
        )
    return {
        "mode": "generic_deterministic_baseline",
        "signals": signals,
        "location": location,
        "items": items,
        "warning": "Deterministic generic baseline only; this is not an LLM quality benchmark.",
    }


def comparison_metrics(baseline: dict, grounded: dict) -> dict:
    def domains(payload: dict) -> int:
        return len({str(item.get("domain") or "") for item in payload.get("items", []) if item.get("domain")})

    def unique_ratio(payload: dict) -> float:
        names = [str(item.get("name") or "").strip().casefold() for item in payload.get("items", [])]
        names = [name for name in names if name]
        return round(len(set(names)) / len(names), 4) if names else 0.0

    grounded_items = grounded.get("items", [])
    graph_coverage = (grounded.get("graph") or {}).get("evidence_coverage")
    if isinstance(graph_coverage, (int, float)) and not isinstance(graph_coverage, bool):
        evidence_coverage = round(float(graph_coverage), 4)
    else:
        explicit_evidence = sum(1 for item in grounded_items if item.get("signal_influences"))
        evidence_coverage = round(explicit_evidence / len(grounded_items), 4) if grounded_items else 0.0

    return {
        "baseline_domain_coverage": domains(baseline),
        "grounded_domain_coverage": domains(grounded),
        "baseline_unique_ratio": unique_ratio(baseline),
        "grounded_unique_ratio": unique_ratio(grounded),
        "grounded_explicit_evidence_coverage": evidence_coverage,
        "note": "These are structural diagnostics only. They do not claim that synthetic Qloo fixtures outperform the baseline in real recommendation quality.",
    }
