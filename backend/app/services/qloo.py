from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..config import settings


class QlooClient:
    """Minimal dependency-free Qloo client for the first API smoke tests."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else settings.qloo_api_key
        self.base_url = (base_url or settings.qloo_base_url).rstrip("/")

    def insights(self, params: dict[str, str | int | float]) -> dict:
        if not self.api_key:
            raise RuntimeError("QLOO_API_KEY is not configured")
        query = urlencode(params)
        req = Request(
            f"{self.base_url}/v2/insights?{query}",
            headers={"x-api-key": self.api_key, "accept": "application/json"},
        )
        with urlopen(req, timeout=30) as response:
            return json.load(response)
