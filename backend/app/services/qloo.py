from __future__ import annotations

import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Callable

from ..config import settings


class QlooError(RuntimeError):
    pass


def build_insights_payload(
    *,
    signal_names: list[str],
    filter_type: str,
    location: str | None = None,
    take: int = 8,
    explainability: bool = True,
) -> dict:
    names = [name.strip() for name in signal_names if name and name.strip()]
    if not names:
        raise ValueError("at least one signal name is required")
    if not filter_type.startswith("urn:entity:"):
        raise ValueError("filter_type must be a Qloo entity URN")
    if not 1 <= take <= 50:
        raise ValueError("take must be between 1 and 50")

    payload: dict[str, object] = {
        "filter.type": filter_type,
        "signal.interests.entities.query": names,
        "take": take,
    }
    if location and location.strip():
        payload["filter.location.query"] = location.strip()
    if explainability:
        payload["feature.explainability"] = True
    return payload


class QlooClient:
    """Small Qloo API v2 client with bounded retries and explicit failure semantics."""

    RETRYABLE_HTTP = {429, 500, 502, 503, 504}

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        *,
        max_attempts: int = 3,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
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

    def insights(self, payload: dict) -> dict:
        if not self.api_key:
            raise QlooError("QLOO_API_KEY is not configured")

        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request = Request(
            f"{self.base_url}/v2/insights",
            data=body,
            method="POST",
            headers={
                "x-api-key": self.api_key,
                "accept": "application/json",
                "content-type": "application/json",
            },
        )

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

    def discover(
        self,
        *,
        signal_names: list[str],
        filter_type: str,
        location: str | None = None,
        take: int = 8,
    ) -> dict:
        payload = build_insights_payload(
            signal_names=signal_names,
            filter_type=filter_type,
            location=location,
            take=take,
        )
        return self.insights(payload)
