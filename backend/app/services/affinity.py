from __future__ import annotations

from dataclasses import dataclass

from .qloo import QlooClient


@dataclass(frozen=True)
class DomainQuery:
    domain: str
    filter_type: str


DEFAULT_DOMAINS = (
    DomainQuery("music", "urn:entity:artist"),
    DomainQuery("venue", "urn:entity:place"),
    DomainQuery("brand", "urn:entity:brand"),
    DomainQuery("film", "urn:entity:movie"),
)


def _entity_rows(response: dict) -> list[dict]:
    results = response.get("results") or {}
    entities = results.get("entities") or []
    return [row for row in entities if isinstance(row, dict)]


def _score(row: dict) -> float | None:
    for key in ("affinity", "affinity_score", "score"):
        value = row.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    properties = row.get("properties") or {}
    for key in ("affinity", "affinity_score", "score"):
        value = properties.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def normalize_entities(domain: str, response: dict, limit: int = 5) -> list[dict]:
    normalized = []
    for row in _entity_rows(response)[:limit]:
        normalized.append(
            {
                "domain": domain,
                "name": row.get("name") or row.get("title") or "Unnamed Qloo entity",
                "entity_id": row.get("entity_id") or row.get("id"),
                "type": row.get("type"),
                "subtype": row.get("subtype"),
                "affinity_raw": _score(row),
                "explainability": (row.get("query") or {}).get("explainability"),
            }
        )
    return normalized


def discover_cross_domain(
    client: QlooClient,
    *,
    signals: list[str],
    location: str | None = None,
    domains: tuple[DomainQuery, ...] = DEFAULT_DOMAINS,
    take: int = 5,
) -> dict:
    output: dict[str, object] = {"signals": signals, "location": location, "domains": {}}
    for target in domains:
        response = client.discover(
            signal_names=signals,
            filter_type=target.filter_type,
            location=location if target.filter_type == "urn:entity:place" else None,
            take=take,
        )
        output["domains"][target.domain] = {
            "entities": normalize_entities(target.domain, response, take),
            "explainability": (response.get("query") or {}).get("explainability"),
        }
    return output
