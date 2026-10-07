import pytest

from app.services.qloo import QlooClient, QlooError, build_insights_payload
from app.services.affinity import normalize_entities


def test_build_insights_payload_resolves_named_entities():
    payload = build_insights_payload(
        signal_names=["Arctic Monkeys", "A24"],
        filter_type="urn:entity:brand",
        location="Milan",
        take=6,
    )
    assert payload["signal.interests.entities.query"] == ["Arctic Monkeys", "A24"]
    assert payload["filter.location.query"] == "Milan"
    assert payload["feature.explainability"] is True
    assert payload["take"] == 6


def test_client_refuses_live_call_without_key():
    client = QlooClient(api_key="", base_url="https://api.qloo.com")
    with pytest.raises(QlooError, match="QLOO_API_KEY"):
        client.insights({"filter.type": "urn:entity:artist"})


def test_normalize_entities_tolerates_response_variants():
    response = {
        "results": {
            "entities": [
                {"name": "Example", "entity_id": "abc", "type": "urn:entity:artist", "affinity": 0.91}
            ]
        }
    }
    rows = normalize_entities("music", response)
    assert rows == [{
        "domain": "music",
        "name": "Example",
        "entity_id": "abc",
        "type": "urn:entity:artist",
        "subtype": None,
        "affinity": 0.91,
    }]

from app.services.orchestrator import build_tasks, execute_agent, preview_agent


class FakeQloo:
    def __init__(self):
        self.calls = []

    def insights(self, payload):
        self.calls.append(payload)
        kind = payload["filter.type"].split(":")[-1]
        return {
            "results": {
                "entities": [
                    {"name": kind.title() + " Candidate", "entity_id": "id-" + kind, "type": payload["filter.type"], "affinity": 0.8}
                ]
            },
            "query": {"explainability": {"source": "fixture"}},
        }


def test_agent_preview_builds_cross_domain_tasks():
    result = preview_agent(signals=["Arctic Monkeys", "A24"], location="Milan", take=4)
    assert len(result["tasks"]) == 4
    assert {task["domain"] for task in result["tasks"]} == {"music", "venue", "brand", "film"}
    venue = next(task for task in result["tasks"] if task["domain"] == "venue")
    assert venue["payload"]["filter.location.query"] == "Milan"


def test_agent_executes_all_tasks_and_preserves_explainability():
    provider = FakeQloo()
    result = execute_agent(provider, signals=["Arctic Monkeys", "A24"], location="Milan", take=3)
    assert result["mode"] == "live"
    assert len(provider.calls) == 4
    assert len(result["items"]) == 4
    assert set(result["explainability"]) == {"music", "venue", "brand", "film"}
