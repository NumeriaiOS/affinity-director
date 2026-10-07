from app.services.planner import build_mock_plan


def test_mock_plan_has_cross_domain_items():
    result = build_mock_plan("Plan an event for an audience with several cultural interests")
    assert result["mode"] == "mock"
    assert len({item["domain"] for item in result["items"]}) >= 4
    assert all(0 <= item["cultural_fit"] <= 100 for item in result["items"])
