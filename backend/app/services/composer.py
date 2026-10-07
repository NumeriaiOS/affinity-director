from __future__ import annotations


def compose_blueprint(items: list[dict], location: str | None) -> dict:
    """Compose selected candidates into an actionable cross-domain blueprint.

    The composer never invents new cultural entities. It only assigns product
    roles to candidates already selected by the grounded/coherence pipeline.
    """
    best_by_domain: dict[str, dict] = {}
    for item in items:
        domain = str(item.get("domain") or "unknown")
        current = best_by_domain.get(domain)
        if current is None or int(item.get("cultural_fit") or 0) > int(current.get("cultural_fit") or 0):
            best_by_domain[domain] = item

    role_labels = {
        "venue": "Spatial anchor",
        "music": "Sound direction",
        "brand": "Partner layer",
        "film": "Visual/cultural layer",
    }
    sequence = []
    for domain in ("venue", "music", "brand", "film"):
        item = best_by_domain.get(domain)
        if item is None:
            continue
        sequence.append(
            {
                "domain": domain,
                "role": role_labels[domain],
                "name": item.get("name"),
                "cultural_fit": item.get("cultural_fit"),
                "confidence": item.get("score_confidence"),
            }
        )

    fits = [int(entry["cultural_fit"]) for entry in sequence if isinstance(entry.get("cultural_fit"), int)]
    evidence_count = sum(1 for item in best_by_domain.values() if item.get("explainability"))
    return {
        "title": (location.strip() + " experience blueprint") if location and location.strip() else "Cross-domain experience blueprint",
        "location": location,
        "sequence": sequence,
        "mean_cultural_fit": round(sum(fits) / len(fits), 1) if fits else None,
        "explicit_evidence_roles": evidence_count,
        "role_count": len(sequence),
        "note": "The blueprint composes already-selected candidates and does not create new affinity claims.",
    }
