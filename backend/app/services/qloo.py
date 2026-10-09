from __future__ import annotations

import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from typing import Callable

from ..config import settings


class QlooError(RuntimeError):
    pass


def build_insights_payload(
    *,
    signal_names: list[str] | None = None,
    signal_entity_ids: list[str] | None = None,
    filter_type: str,
    location: str | None = None,
    take: int = 8,
    explainability: bool = True,
) -> dict:
    names = [name.strip() for name in (signal_names or []) if name and name.strip()]
    entity_ids = [entity_id.strip() for entity_id in (signal_entity_ids or []) if entity_id and entity_id.strip()]
    if not names and not entity_ids:
        raise ValueError("at least one signal name or entity id is required")
    if not filter_type.startswith("urn:entity:"):
        raise ValueError("filter_type must be a Qloo entity URN")
    if not 1 <= take <= 50:
        raise ValueError("take must be between 1 and 50")

    payload: dict[str, object] = {"filter.type": filter_type, "take": take}
    if entity_ids:
        payload["signal.interests.entities"] = entity_ids
    if names:
        payload["signal.interests.entities.query"] = names
    if location and location.strip():
        payload["filter.location.query"] = location.strip()
    if explainability:
        payload["feature.explainability"] = True
    return payload


class QlooClient:
    """Small Qloo API v2 client with bounded retries and explicit failure semantics."""

    RETRYABLE_HTTP = {429, 500, 502, 503, 504}
    _resolution_cache: dict[tuple[str, str], tuple[float, dict | None]] = {}
    _resolution_ttl = 3600.0
    _resolution_cache_max = 256

    def __init__(self, api_key: str | None = None, base_url: str | None = None, *, max_attempts: int = 3, sleep_fn: Callable[[float], None] | None = None) -> None:
        if not 1 <= max_attempts <= 5:
            raise ValueError("max_attempts must be between 1 and 5")
        self.api_key = api_key if api_key is not None else settings.qloo_api_key
        self.base_url = (base_url or settings.qloo_base_url).rstrip("/")
        self.max_attempts = max_attempts
        self._sleep = sleep_fn or time.sleep

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def _retry_delay(exc: HTTPError | None, attempt: int) -> float:
        if exc is not None and exc.headers is not None:
            value = exc.headers.get("Retry-After")
            if value:
                try:
                    return min(5.0, max(0.0, float(value)))
                except ValueError:
                    pass
        return min(2.0, 0.25 * (2 ** max(0, attempt - 1)))

    def _request_json(self, request: Request) -> dict:
        if not self.api_key:
            raise QlooError("QLOO_API_KEY is not configured")
        for attempt in range(1, self.max_attempts + 1):
            try:
                with urlopen(request, timeout=30) as response:
                    result = json.load(response)
                if not isinstance(result, dict):
                    raise QlooError("Qloo returned a non-object JSON response")
                if result.get("success") is False:
                    raise QlooError("Qloo returned success=false")
                return result
            except HTTPError as exc:
                detail = exc.read(2048).decode("utf-8", errors="replace")
                if exc.code not in self.RETRYABLE_HTTP or attempt >= self.max_attempts:
                    raise QlooError(f"Qloo HTTP {exc.code}: {detail}") from exc
                self._sleep(self._retry_delay(exc, attempt))
            except URLError as exc:
                if attempt >= self.max_attempts:
                    raise QlooError(f"Qloo network error: {exc.reason}") from exc
                self._sleep(self._retry_delay(None, attempt))
        raise QlooError("Qloo request failed after bounded retries")

    def insights(self, payload: dict) -> dict:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request = Request(f"{self.base_url}/v2/insights", data=body, method="POST", headers={"x-api-key": self.api_key, "accept": "application/json", "content-type": "application/json"})
        return self._request_json(request)

    def search_entities(self, query: str, *, take: int = 5) -> list[dict]:
        clean = " ".join(query.split()).strip()
        if not clean:
            raise ValueError("search query is required")
        if not 1 <= take <= 20:
            raise ValueError("search take must be between 1 and 20")
        qs = urlencode({"query": clean, "take": take, "sort_by": "match"})
        request = Request(f"{self.base_url}/search?{qs}", method="GET", headers={"x-api-key": self.api_key, "accept": "application/json"})
        result = self._request_json(request)
        rows = result.get("results") or []
        if not isinstance(rows, list):
            raise QlooError("Qloo search returned an unexpected results shape")
        return [row for row in rows if isinstance(row, dict)]

    @staticmethod
    def _normalized_name(value: object) -> str:
        return " ".join(str(value or "").split()).strip().casefold()

    def resolve_signals(self, signal_names: list[str]) -> list[dict]:
        resolved: list[dict] = []
        seen: set[str] = set()
        now = time.time()
        for raw_name in signal_names:
            name = " ".join(raw_name.split()).strip()
            key = self._normalized_name(name)
            if not key or key in seen:
                continue
            seen.add(key)
            cache_key = (self.base_url, key)
            cached = self._resolution_cache.get(cache_key)
            selected: dict | None
            match = "ranked"
            if cached and now - cached[0] < self._resolution_ttl:
                selected = cached[1]
                if selected and self._normalized_name(selected.get("name")) == key:
                    match = "exact"
            else:
                try:
                    rows = self.search_entities(name, take=5)
                except QlooError:
                    rows = []
                usable = [row for row in rows if row.get("entity_id") or row.get("id")]
                exact = next((row for row in usable if self._normalized_name(row.get("name")) == key), None)
                selected = exact or (usable[0] if usable else None)
                match = "exact" if exact is not None else "ranked"
                if len(self._resolution_cache) >= self._resolution_cache_max:
                    oldest = min(self._resolution_cache, key=lambda k: self._resolution_cache[k][0])
                    self._resolution_cache.pop(oldest, None)
                self._resolution_cache[cache_key] = (now, selected)
            if not selected:
                continue
            entity_id = str(selected.get("entity_id") or selected.get("id") or "").strip()
            if not entity_id:
                continue
            types = selected.get("types")
            if not isinstance(types, list):
                types = [selected.get("type")] if selected.get("type") else []
            resolved.append({"input": name, "entity_id": entity_id, "resolved_name": str(selected.get("name") or name), "types": [str(value) for value in types if value], "match": match})
        return resolved

    def discover(self, *, signal_names: list[str], filter_type: str, location: str | None = None, take: int = 8) -> dict:
        payload = build_insights_payload(signal_names=signal_names, filter_type=filter_type, location=location, take=take)
        return self.insights(payload)
