from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .config import settings
from .services.affinity import discover_cross_domain
from .services.planner import build_mock_plan
from .services.qloo import QlooClient, QlooError, build_insights_payload

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Affinity Director", version="0.2.0")


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


@app.post("/api/qloo/explore")
def qloo_explore(request: QlooExploreRequest) -> dict:
    client = QlooClient()
    if not client.configured:
        raise HTTPException(status_code=503, detail="QLOO_API_KEY is not configured; use query-preview until registration is available")
    try:
        return discover_cross_domain(client, signals=request.signals, location=request.location, take=request.take)
    except (QlooError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/")
def index() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")
