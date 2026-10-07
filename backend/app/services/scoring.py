from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any


@dataclass(frozen=True)
class ScoreBreakdown:
    cultural_fit: int
    affinity_score: float | None
    rank_score: float
    explainability_score: float | None
    confidence: str


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if isfinite(number) else None


def normalize_affinity(value: Any) -> float | None:
    """Normalize common Qloo affinity representations to a 0-100 display scale.

    We retain the raw value elsewhere. Some API examples expose fractional values,
    while Qloo's Insights UI describes affinity on a 0-100 scale. Values outside
    those ranges are treated as unknown rather than silently distorted.
    """
    number = _number(value)
    if number is None or number < 0:
        return None
    if number <= 1:
        return round(number * 100.0, 2)
    if number <= 100:
        return round(number, 2)
    return None


def _collect_unit_interval_numbers(value: Any, output: list[float]) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _collect_unit_interval_numbers(child, output)
    elif isinstance(value, list):
        for child in value:
            _collect_unit_interval_numbers(child, output)
    else:
        number = _number(value)
        if number is not None and 0 <= number <= 1:
            output.append(number)


def explainability_strength(value: Any) -> float | None:
    """Summarize per-result explainability impacts when present.

    Qloo documents normalized explainability contributions in the 0-1 range.
    The result is an auxiliary 0-100 diagnostic, not a replacement for affinity.
    """
    values: list[float] = []
    _collect_unit_interval_numbers(value, values)
    if not values:
        return None
    # Strongest inputs are more useful for a judge-facing rationale than a long
    # tail of tiny contributions, so average at most the top three.
    top = sorted(values, reverse=True)[:3]
    return round(sum(top) / len(top) * 100.0, 2)


def score_candidate(candidate: dict, rank: int) -> ScoreBreakdown:
    affinity_score = normalize_affinity(candidate.get("affinity_raw"))
    rank_score = max(0.0, 100.0 - max(0, rank - 1) * 8.0)
    explain_score = explainability_strength(candidate.get("explainability"))

    if affinity_score is not None:
        # Affinity remains the dominant signal. Rank is used only as a small
        # stabilizer; explainability is a modest bonus when Qloo supplies it.
        weights = [(affinity_score, 0.82), (rank_score, 0.12)]
        if explain_score is not None:
            weights.append((explain_score, 0.06))
        else:
            # Re-normalize instead of inventing explainability.
            weights = [(affinity_score, 0.8723), (rank_score, 0.1277)]
        fit = sum(value * weight for value, weight in weights)
        confidence = "high" if explain_score is not None else "medium"
    else:
        # Missing affinity means we only know Qloo's ordering. Keep the score
        # visibly conservative and mark it low-confidence.
        fit = rank_score * 0.72
        confidence = "low"

    return ScoreBreakdown(
        cultural_fit=max(0, min(100, round(fit))),
        affinity_score=affinity_score,
        rank_score=round(rank_score, 2),
        explainability_score=explain_score,
        confidence=confidence,
    )


def apply_scores(items: list[dict]) -> list[dict]:
    domain_rank: dict[str, int] = {}
    scored: list[dict] = []
    for item in items:
        domain = str(item.get("domain") or "unknown")
        domain_rank[domain] = domain_rank.get(domain, 0) + 1
        breakdown = score_candidate(item, domain_rank[domain])
        enriched = dict(item)
        enriched.update(
            {
                "cultural_fit": breakdown.cultural_fit,
                "affinity_score": breakdown.affinity_score,
                "rank_score": breakdown.rank_score,
                "explainability_score": breakdown.explainability_score,
                "score_confidence": breakdown.confidence,
            }
        )
        scored.append(enriched)
    return scored


def select_coherent(items: list[dict], *, per_domain: int = 2, total: int = 8) -> list[dict]:
    """Select a diverse result set without hiding the underlying Qloo ranking."""
    if per_domain < 1 or total < 1:
        raise ValueError("coherence limits must be positive")

    # De-duplicate globally first, preferring the higher Cultural Fit candidate.
    ordered = sorted(items, key=lambda row: (-int(row.get("cultural_fit") or 0), str(row.get("name") or "")))
    seen: set[str] = set()
    unique: list[dict] = []
    for item in ordered:
        key = str(item.get("entity_id") or item.get("name") or "").strip().casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item)

    buckets: dict[str, list[dict]] = {}
    for item in unique:
        buckets.setdefault(str(item.get("domain") or "unknown"), []).append(item)

    # Round-robin across domains ensures one strong domain cannot crowd out the
    # rest of the experience design.
    selected: list[dict] = []
    domain_names = sorted(
        buckets,
        key=lambda name: -(buckets[name][0].get("cultural_fit") or 0),
    )
    for slot in range(per_domain):
        for domain in domain_names:
            bucket = buckets[domain]
            if slot < len(bucket):
                selected.append(bucket[slot])
                if len(selected) >= total:
                    return selected
    return selected
