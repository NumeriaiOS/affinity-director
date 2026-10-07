import pytest

from app.services.affinity import normalize_entities
from app.services.fixtures import FixtureQlooProvider
from app.services.orchestrator import build_tasks, execute_agent, preview_agent
from app.services.qloo import QlooClient, QlooError, build_insights_payload
from app.services.scoring import normalize_affinity, score_candidate, select_coherent


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


def test_normalize_entities_preserves_raw_affinity_and_explainability():
    response = {
        "results": {
            "entities": [
                {
                    "name": "Example",
                    "entity_id": "abc",
                    "type": "urn:entity:artist",
                    "affinity": 0.91,
                    "query": {"explainability": {"input-a": 0.8}},
                }
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
        "affinity_raw": 0.91,
        "explainability": {"input-a": 0.8},
    }]


class FakeQloo:
    def __init__(self):
        self.calls = []

    def insights(self, payload):
        self.calls.append(payload)
        kind = payload["filter.type"].split(":")[-1]
        return {
            "results": {
                "entities": [
                    {
                        "name": kind.title() + " Candidate",
                        "entity_id": "id-" + kind,
                        "type": payload["filter.type"],
                        "affinity": 0.8,
                        "query": {"explainability": {"seed": 0.7}},
                    }
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


def test_agent_executes_all_tasks_scores_and_preserves_explainability():
    provider = FakeQloo()
    result = execute_agent(provider, signals=["Arctic Monkeys", "A24"], location="Milan", take=3)
    assert result["mode"] == "live"
    assert len(provider.calls) == 4
    assert len(result["items"]) == 4
    assert set(result["explainability"]) == {"music", "venue", "brand", "film"}
    assert all(item["affinity_raw"] == 0.8 for item in result["items"])
    assert all(item["affinity_score"] == 80.0 for item in result["items"])
    assert all(0 <= item["cultural_fit"] <= 100 for item in result["items"])
    assert all(item["score_confidence"] == "high" for item in result["items"])


def test_affinity_normalizer_supports_fractional_and_percent_scales():
    assert normalize_affinity(0.91) == 91.0
    assert normalize_affinity(91) == 91.0
    assert normalize_affinity(-1) is None
    assert normalize_affinity(101) is None


def test_missing_affinity_is_low_confidence_not_invented():
    result = score_candidate({"affinity_raw": None, "explainability": None}, rank=1)
    assert result.affinity_score is None
    assert result.confidence == "low"
    assert result.cultural_fit == 72


def test_coherence_dedupes_and_preserves_domains():
    items = [
        {"domain": "music", "name": "Shared", "entity_id": "same", "cultural_fit": 95},
        {"domain": "brand", "name": "Shared", "entity_id": "same", "cultural_fit": 80},
        {"domain": "brand", "name": "Brand B", "entity_id": "b", "cultural_fit": 88},
        {"domain": "film", "name": "Film C", "entity_id": "c", "cultural_fit": 84},
    ]
    selected = select_coherent(items, per_domain=1, total=3)
    assert len({item["entity_id"] for item in selected}) == len(selected)
    assert {item["domain"] for item in selected} == {"music", "brand", "film"}


def test_demo_fixture_is_explicitly_non_live_and_cross_domain():
    result = execute_agent(
        FixtureQlooProvider(),
        signals=["Arctic Monkeys", "A24", "technical streetwear"],
        location="Milan",
        take=3,
        mode="demo_fixture",
    )
    assert result["mode"] == "demo_fixture"
    assert "Synthetic fixture" in result["warning"]
    assert len({item["domain"] for item in result["items"]}) == 4
    assert all(item["cultural_fit"] >= 0 for item in result["items"])

from app.services.baseline import build_generic_baseline, comparison_metrics
from app.services.explainability import build_explainability_graph


def test_explainability_graph_uses_only_explicit_signal_weights():
    graph = build_explainability_graph(
        ["Arctic Monkeys", "A24"],
        [
            {
                "domain": "music",
                "name": "Candidate",
                "cultural_fit": 91,
                "explainability": {"signal.interests.entities": {"Arctic Monkeys": 0.8, "unknown": 0.99}},
            }
        ],
    )
    assert len(graph["edges"]) == 1
    assert graph["edges"][0]["weight"] == 0.8
    assert graph["evidence_coverage"] == 1.0


def test_demo_comparison_metrics_are_structural_only():
    baseline = build_generic_baseline(signals=["A24"], location="Milan")
    grounded = execute_agent(FakeQloo(), signals=["A24"], location="Milan", take=2, mode="demo_fixture")
    metrics = comparison_metrics(baseline, grounded)
    assert metrics["baseline_domain_coverage"] == 4
    assert metrics["grounded_domain_coverage"] == 4
    assert "structural diagnostics" in metrics["note"]

import io
from urllib.error import HTTPError
import app.services.qloo as qloo_module


def test_qloo_client_retries_temporary_http_error(monkeypatch):
    calls = []
    sleeps = []

    def fake_urlopen(request, timeout):
        calls.append((request.full_url, timeout))
        if len(calls) == 1:
            raise HTTPError(request.full_url, 503, "temporary", {"Retry-After": "0"}, io.BytesIO(b'{"error":"temporary"}'))
        return io.BytesIO(b'{"success":true,"results":{"entities":[]}}')

    monkeypatch.setattr(qloo_module, "urlopen", fake_urlopen)
    client = QlooClient(api_key="test", max_attempts=3, sleep_fn=sleeps.append)
    result = client.insights({"filter.type": "urn:entity:artist"})
    assert result["success"] is True
    assert len(calls) == 2
    assert sleeps == [0.0]


def test_qloo_client_does_not_retry_bad_request(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(1)
        raise HTTPError(request.full_url, 400, "bad request", {}, io.BytesIO(b'{"error":"bad"}'))

    monkeypatch.setattr(qloo_module, "urlopen", fake_urlopen)
    client = QlooClient(api_key="test", max_attempts=3, sleep_fn=lambda _: None)
    with pytest.raises(QlooError, match="HTTP 400"):
        client.insights({"filter.type": "urn:entity:artist"})
    assert len(calls) == 1

from pydantic import ValidationError
from app.main import QlooExploreRequest


def test_request_rejects_oversized_signal():
    with pytest.raises(ValidationError, match="120 characters"):
        QlooExploreRequest(signals=["x" * 121], location="Milan")


def test_request_normalizes_duplicate_signals():
    request = QlooExploreRequest(signals=[" A24 ", "a24", " Arctic   Monkeys "], location="Milan")
    assert request.signals == ["A24", "Arctic Monkeys"]
