from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .config import settings
from .services.planner import build_mock_plan

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Affinity Director", version="0.1.0")


class PlanRequest(BaseModel):
    brief: str = Field(min_length=10, max_length=2000)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "qloo_configured": bool(settings.qloo_api_key)}


@app.post("/api/plan")
def plan(request: PlanRequest) -> dict:
    if not request.brief.strip():
        raise HTTPException(status_code=400, detail="brief is required")
    return build_mock_plan(request.brief)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")
