from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class PlanItem:
    domain: str
    name: str
    rationale: str
    cultural_fit: int


MOCK_CANDIDATES = [
    PlanItem("music", "Indie / art-rock programming", "Balances guitar-led energy with a design-conscious audience.", 91),
    PlanItem("venue", "Adaptive industrial venue", "Strong fit for audiences spanning alternative music, fashion and visual culture.", 89),
    PlanItem("food", "Contemporary East-Asian street-food partners", "Extends the brief across categories without repeating the same signal.", 87),
    PlanItem("brand", "Independent technical-streetwear activation", "Creates a credible bridge between fashion affinity and event utility.", 84),
    PlanItem("visual", "Cinematic low-light installation", "Connects film taste with the spatial identity of the experience.", 86),
]


def build_mock_plan(brief: str) -> dict:
    normalized = " ".join(brief.split()).strip()
    trace = [
        {"step": "brief_parse", "status": "ok", "detail": "Extracted audience signals and planning objective."},
        {"step": "entity_resolution", "status": "mock", "detail": "Qloo entity resolution placeholder until API key is configured."},
        {"step": "cross_domain_search", "status": "mock", "detail": "Generated candidate domains for music, place, food, brand and visual style."},
        {"step": "cultural_fit_scoring", "status": "mock", "detail": "Applied deterministic placeholder scores; live mode will use Qloo affinities."},
        {"step": "coherence_check", "status": "ok", "detail": "Rejected duplicate-domain suggestions and preserved cross-domain variety."},
    ]
    return {
        "mode": "mock",
        "brief": normalized,
        "headline": "Cross-domain experience direction",
        "items": [asdict(item) for item in MOCK_CANDIDATES],
        "trace": trace,
        "warning": "Mock mode: no Qloo data has been used yet.",
    }
