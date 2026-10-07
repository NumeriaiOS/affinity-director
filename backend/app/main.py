from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from .config import settings
from .services.fixtures import FixtureQlooProvider
from .services.baseline import build_generic_baseline, comparison_metrics
from .services.orchestrator import execute_agent, preview_agent
from .services.planner import build_mock_plan
from .services.qloo import QlooClient, QlooError, build_insights_payload

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Affinity Director", version="0.4.0")


class PlanRequest(BaseModel):
    brief: str = Field(min_length=10, max_length=2000)


class QlooPreviewRequest(BaseModel):
    signals: list[str] = Field(min_length=1, max_length=12)
    filter_type: str = "urn:entity:artist"
    location: str | None = None
    take: int = Field(default=8, ge=1, le=50)


class QlooExploreRequest(BaseModel):
    signals: list[str] = Field(min_length=1, max_length=12)
    location: str | None = None
    take: int = Field(default=5, ge=1, le=20)

    @field_validator("signals")
    @classmethod
    def clean_signals(cls, values: list[str]) -> list[str]:
        cleaned = []
        seen = set()
        for value in values:
            item = " ".join(value.split()).strip()
            key = item.casefold()
            if item and key not in seen:
                seen.add(key)
                cleaned.append(item)
        if not cleaned:
            raise ValueError("at least one non-empty signal is required")
        return cleaned


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "qloo_configured": bool(settings.qloo_api_key), "version": app.version}


@app.post("/api/plan")
def plan(request: PlanRequest) -> dict:
    if not request.brief.strip():
        raise HTTPException(status_code=400, detail="brief is required")
    return build_mock_plan(request.brief)


@app.post("/api/qloo/query-preview")
def qloo_query_preview(request: QlooPreviewRequest) -> dict:
    try:
        payload = build_insights_payload(
            signal_names=request.signals,
            filter_type=request.filter_type,
            location=request.location,
            take=request.take,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"mode": "preview", "endpoint": "/v2/insights", "method": "POST", "payload": payload}


@app.post("/api/agent/preview")
def agent_preview(request: QlooExploreRequest) -> dict:
    return preview_agent(signals=request.signals, location=request.location, take=request.take)


@app.post("/api/agent/demo")
def agent_demo(request: QlooExploreRequest) -> dict:
    return execute_agent(
        FixtureQlooProvider(),
        signals=request.signals,
        location=request.location,
        take=request.take,
        mode="demo_fixture",
    )


@app.post("/api/agent/compare-demo")
def agent_compare_demo(request: QlooExploreRequest) -> dict:
    baseline = build_generic_baseline(signals=request.signals, location=request.location)
    grounded = execute_agent(
        FixtureQlooProvider(),
        signals=request.signals,
        location=request.location,
        take=request.take,
        mode="demo_fixture",
    )
    return {
        "mode": "comparison_demo",
        "baseline": baseline,
        "grounded": grounded,
        "metrics": comparison_metrics(baseline, grounded),
        "warning": "Synthetic evaluation surface only. Real Qloo data is required before making recommendation-quality claims.",
    }


@app.post("/api/agent/compare")
def agent_compare(request: QlooExploreRequest) -> dict:
    baseline = build_generic_baseline(signals=request.signals, location=request.location)
    client = QlooClient()
    provider = client if client.configured else FixtureQlooProvider()
    provider_mode = "live" if client.configured else "demo_fixture"
    try:
        grounded = execute_agent(
            provider,
            signals=request.signals,
            location=request.location,
            take=request.take,
            mode=provider_mode,
        )
    except (QlooError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "mode": "comparison_live" if client.configured else "comparison_demo",
        "baseline": baseline,
        "grounded": grounded,
        "metrics": comparison_metrics(baseline, grounded),
        "warning": None if client.configured else "Synthetic Qloo fixture data only. Real Qloo data is required before making recommendation-quality claims.",
    }


@app.post("/api/qloo/explore")
def qloo_explore(request: QlooExploreRequest) -> dict:
    client = QlooClient()
    if not client.configured:
        raise HTTPException(status_code=503, detail="QLOO_API_KEY is not configured; use agent/demo until registration is available")
    try:
        return execute_agent(client, signals=request.signals, location=request.location, take=request.take, mode="live")
    except (QlooError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/")
def index() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")
