from __future__ import annotations


_FIXTURE_DATA = {
    "urn:entity:artist": [
        ("demo-artist-1", "Demo Art-Rock Artist", 0.94, {"Arctic Monkeys": 0.88, "A24": 0.44}),
        ("demo-artist-2", "Demo Leftfield Electronic Artist", 0.83, {"A24": 0.61, "technical streetwear": 0.38}),
        ("demo-shared", "Demo Multidisciplinary Collective", 0.79, {"A24": 0.52}),
    ],
    "urn:entity:place": [
        ("demo-place-1", "Demo Adaptive Industrial Venue", 0.92, {"Arctic Monkeys": 0.63, "A24": 0.59}),
        ("demo-place-2", "Demo Contemporary Arts Courtyard", 0.84, {"A24": 0.68}),
        ("demo-place-3", "Demo Design District Warehouse", 0.77, {"technical streetwear": 0.57}),
    ],
    "urn:entity:brand": [
        ("demo-brand-1", "Demo Technical Outerwear Partner", 0.90, {"technical streetwear": 0.91}),
        ("demo-brand-2", "Demo Independent Design Label", 0.82, {"A24": 0.46, "technical streetwear": 0.66}),
        ("demo-shared", "Demo Multidisciplinary Collective", 0.76, {"A24": 0.50}),
    ],
    "urn:entity:movie": [
        ("demo-movie-1", "Demo Independent Cinema Selection", 0.88, {"A24": 0.93}),
        ("demo-movie-2", "Demo Night-City Film Program", 0.80, {"A24": 0.70, "Arctic Monkeys": 0.30}),
        ("demo-movie-3", "Demo Design Documentary Shortlist", 0.73, {"technical streetwear": 0.43}),
    ],
}


class FixtureQlooProvider:
    """Deterministic synthetic provider used only while Qloo registration is unavailable."""

    def insights(self, payload: dict) -> dict:
        filter_type = str(payload.get("filter.type") or "")
        rows = []
        for entity_id, name, affinity, impacts in _FIXTURE_DATA.get(filter_type, []):
            rows.append(
                {
                    "entity_id": entity_id,
                    "name": name,
                    "type": filter_type,
                    "affinity": affinity,
                    "query": {
                        "explainability": {
                            "signal.interests.entities": impacts,
                        }
                    },
                }
            )
        return {
            "success": True,
            "results": {"entities": rows},
            "query": {
                "explainability": {
                    "warning": "Synthetic fixture data; not returned by Qloo."
                }
            },
        }
